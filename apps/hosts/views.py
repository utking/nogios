from django.shortcuts import render, get_object_or_404, redirect
from apps.contacts.views import reload_contacts
from apps.services.views import notification_expired
from apps.contacts.models import NotificationRecords
from apps.time_periods.models import TimePeriodConfig
from apps.helpers.HostsLoader import HostsLoader
from apps.helpers.contacts import notify_host_contacts, enqueue_host_notification
from apps.helpers.time_periods import is_in_periods
from apps.hosts.models import HostConfig, HostStatus, HostToRun
from apps.status.models import HostStatusHistory
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.views.decorators.cache import cache_page
from django.conf import settings
from datetime import datetime


def index(request):
    items = HostConfig.objects.get_all()
    return render(request, 'hosts/index.html', {'items': items, 'title': 'Hosts'})


def hosts_json(request):
    hosts = HostConfig.objects.get_all()
    items = []
    for host in hosts:
        items.append(model_to_dict(host))
    return JsonResponse({'items': items})


@cache_page(60 * 60)
def statuses(request):
    items = HostStatus.objects.order_by('name').all()
    return render(request, 'hosts/statuses.html', {'items': items, 'title': 'Host statuses'})


@cache_page(60 * 60)
def statuses_json(request):
    status_items = HostStatus.objects.order_by('name').all()
    items = []
    for item in status_items:
        items.append(model_to_dict(item))

    return JsonResponse({'items': items})


def view(request, name: str):
    item = get_object_or_404(klass=HostConfig, host_name=name)
    return render(request, 'hosts/view.html', {'item': item, 'title': 'Host details'})


def view_json(request, name: str):
    item = get_object_or_404(klass=HostConfig, host_name=name)
    return JsonResponse({'item': model_to_dict(item)})


def by_location(request, name: str):
    items = HostConfig.objects.get_all().filter(location=name)
    return render(request, 'hosts/index.html', {'items': items, 'title': 'Hosts by location'})


def by_location_json(request, name: str):
    hosts = HostConfig.objects.get_all().filter(location=name)
    items = []
    for host in hosts:
        items.append(model_to_dict(host))
    return JsonResponse({'items': items})


def reload_hosts(users: list, groups: list, time_periods: list, save=True):
    base_path = settings.CONFIG_BASE_PATH / 'hosts'
    loader = HostsLoader(
        base_path=base_path,
        contacts={
            'users': list(map(lambda u: u['name'], users)),
            'groups': list(map(lambda g: g['name'], groups))
        },
        time_periods=time_periods
    )
    items = loader.load()

    if save:
        HostConfig.objects.clear_cache()
        HostConfig.objects.all().delete()
        for item in items:
            HostConfig.objects.clear_interval_cache(host_name=item['name'])
            HostConfig.create_config(item)
        __compile_hosts()
    return items


def reload_config(request):
    reload_config_json(request)
    return redirect(index)


def reload_config_json(request):
    users, groups = reload_contacts()
    reload_hosts(users=users, groups=groups)
    return JsonResponse({'status': 'OK'})


def __repopulate_hosts_to_run(hosts: list):
    for host in hosts:
        attempts = host.config.get('retry_attempts')
        if attempts is None:
            attempts = settings.DEFAULT_RETRY_ATTEMPTS
        history_items = HostStatusHistory.objects.filter(host_name=host.host_name).all()[:attempts]

        failed_checks = 0
        output = ''
        status = 'PENDING'
        item_time = None
        for history_item in history_items:
            if failed_checks == 0 and history_item.status_id in ['UP', 'UNKNOWN']:
                status = history_item.status_id
                output = history_item.output
                item_time = history_item.created_at
                break
            elif history_item.status_id == 'DOWN':
                # The latest check is DOWN, counting failed attempts
                if output == '':
                    output = history_item.output
                if item_time is None:
                    item_time = history_item.created_at
                failed_checks = failed_checks + 1
            elif history_item.status_id == 'UP':
                # No more old DOWN in the history, stop checking
                status = 'DOWN'
                break
            else:
                # Stop on other statuses (PENDING and UNKNOWN)
                break

        host_to_run = HostToRun(host_name=host.host_name,
                                address=host.address,
                                attempts=failed_checks,
                                output=output,
                                hard_status=failed_checks >= attempts,
                                current_status_id=status)
        host_to_run.save()
        if host_to_run.pk is None:
            print(host_to_run, 'was not saved')
        else:
            if item_time is not None:
                HostToRun.objects.filter(host_name=host.host_name).update(executed_at=item_time)


def __compile_hosts():
    HostToRun.objects.all().delete()
    hosts = HostConfig.objects.get_all()
    __repopulate_hosts_to_run(hosts=hosts)  # TODO: perhaps merging can be more efficient


def save_host_status(host_name: str, status_code: str, output: str):
    host = HostConfig.objects.get_item(host_name=host_name)
    status = HostStatus.objects.get_item(name=status_code)

    if host is None or status is None:
        return {"error": "Wrong parameters"}
    host_status = HostStatusHistory.objects.add_item(host_name=host_name, status=status, output=output)
    if host_status.pk is not None:
        ret, notify = HostToRun.objects.update_last_run(host_name=host_name, status_code=status_code, output=output)
        time_period_name = HostConfig.objects.get_time_period(host_name=host_name)
        if time_period_name is not None:
            periods = TimePeriodConfig.objects.get_parsed(time_period_name)
            is_in_time_period = is_in_periods(periods=periods)
            # print('Checking TP {} for {} is {}'.format(time_period_name, host_name, is_in_time_period))
        else:
            is_in_time_period = True
        if notify and notification_expired(host=host, service=None) and is_in_time_period:
            if settings.USE_NOTIFICATIONS_QUEUE:
                enqueue_host_notification(host.config['contacts'],
                                          status_item=model_to_dict(host_status))
            else:
                notify_host_contacts(host.config['contacts'], status_item=host_status)
            notification_sent = NotificationRecords.objects.filter(host_name=host_name, service_name='host').first()
            if notification_sent is None:
                notification_sent = NotificationRecords(host_name=host_name, service_name='host',
                                                        status=status_code,
                                                        sent_at=datetime.now())
            else:
                notification_sent.sent_at = datetime.now()
            notification_sent.save()

    return {"status": host_status.pk}
