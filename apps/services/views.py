from django.shortcuts import render, get_object_or_404, redirect
from apps.helpers.ServicesLoader import ServicesLoader
from apps.services.models import ServiceConfig, ServiceStatus, ServiceToRun
from apps.hosts.models import HostConfig
from apps.status.models import ServiceStatusHistory
from apps.commands.models import CommandConfig
from apps.contacts.models import NotificationRecords
from apps.commands.views import reload_commands
from apps.time_periods.models import TimePeriodConfig
from apps.time_periods.views import reload_time_periods
from apps.contacts.views import load_contacts
from apps.helpers.contacts import notify_service_contacts, enqueue_service_notification
from apps.helpers.time_periods import is_in_periods
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.http import JsonResponse
from django.forms.models import model_to_dict
from yaml import dump
from datetime import datetime


def index(request):
    items = ServiceConfig.objects.get_all()
    return render(request, 'services/index.html', {'items': items, 'title': 'Services'})


def services_json(request):
    services = ServiceConfig.objects.get_all()
    items = []
    for service in services:
        items.append(model_to_dict(service))
    return JsonResponse({'items': items})


@cache_page(60 * 60)
def statuses(request):
    items = ServiceStatus.objects.order_by('name').all()
    return render(request, 'services/statuses.html', {'items': items, 'title': 'Service statuses'})


@cache_page(60 * 60)
def statuses_json(request):
    status_items = ServiceStatus.objects.order_by('name').all()
    items = []
    for item in status_items:
        items.append(model_to_dict(item))

    return JsonResponse({'items': items})


def by_type(request, name):
    items = ServiceConfig.objects.get_all().filter(type=name)
    return render(request, 'services/index.html', {'items': items, 'title': 'Services by type'})


def by_type_json(request, name):
    services = ServiceConfig.objects.get_all().filter(type=name)
    items = []
    for service in services:
        items.append(model_to_dict(service))
    return JsonResponse({'items': items})


def by_location(request, name):
    items = ServiceConfig.objects.get_all().filter(location=name)
    return render(request, 'services/index.html', {'items': items, 'title': 'Service by location'})


def by_location_json(request, name):
    services = ServiceConfig.objects.get_all().filter(location=name)
    items = []
    for service in services:
        items.append(model_to_dict(service))
    return JsonResponse({'items': items})


def command(request, name):
    item = get_object_or_404(klass=CommandConfig, name=name)
    return redirect('/commands/view/{}'.format(item.id))


def view(request, name: str):
    item = get_object_or_404(klass=ServiceConfig, name=name)
    item_config = dump(item.config)
    return render(request, 'services/view.html', {'item': item, 'config': item_config, 'title': 'Service details'})


def view_json(request, name: str):
    item = get_object_or_404(klass=ServiceConfig, name=name)
    return JsonResponse({'item': model_to_dict(item)})


def hosts(request, name: str):
    item = get_object_or_404(klass=ServiceConfig, name=name)
    items = item.get_hosts()
    return render(request, 'hosts/index.html', {'items': items, 'title': 'Service hosts'})


def hosts_json(request, name: str):
    item = get_object_or_404(klass=ServiceConfig, name=name)
    host_items = item.get_hosts()
    items = []
    for host in host_items:
        items.append(model_to_dict(host))
    return JsonResponse({'items': items})


def reload_services(users: list, groups: list, cmds: list, time_periods: list, save=True):
    base_path = settings.CONFIG_BASE_PATH / 'services'
    loader = ServicesLoader(
        base_path=base_path, contacts={
            'users': list(map(lambda u: u['name'], users)),
            'groups': list(map(lambda g: g['name'], groups))
        },
        commands=list(map(lambda c: c['name'], cmds)),
        time_periods=time_periods)
    items = loader.load()
    if save:
        ServiceConfig.objects.all().delete()
        for item in items:
            ServiceConfig.create_config(item)
        __compile_services()


def reload_config(request):
    reload_config_json(request)
    return redirect(index)


def reload_config_json(request):
    time_periods = reload_time_periods()
    commands = reload_commands()
    users, groups = load_contacts()
    reload_services(users=users, groups=groups, cmds=commands, time_periods=time_periods)
    return JsonResponse({'status': 'OK'})


def __repopulate_services_to_run(services: list):
    for service in services:
        attempts = service.config.get('retry_attempts')
        if attempts is None:
            attempts = settings.DEFAULT_RETRY_ATTEMPTS

        host_items = service.get_hosts()
        for host in host_items:
            history_items = ServiceStatusHistory.objects.filter(name=service.name,
                                                                host_name=host.host_name).all()[:attempts]

            failed_checks = 0
            output = ''
            status = 'PENDING'
            item_time = None
            for history_item in history_items:
                if failed_checks == 0 and history_item.status_id in ['OK', 'UNKNOWN']:
                    status = history_item.status_id
                    output = history_item.output
                    item_time = history_item.created_at
                    break
                elif history_item.status_id in settings.FAILURE_STATUSES:
                    # The latest check is failing, counting failed attempts
                    if output == '':
                        output = history_item.output
                    if item_time is None:
                        item_time = history_item.created_at
                    failed_checks = failed_checks + 1
                elif history_item.status_id == 'OK':
                    # No more old CRITICAL in the history, stop checking
                    status = 'CRITICAL'
                    break
                else:
                    # Stop on other statuses (PENDING and UNKNOWN)
                    break

            service_to_run = ServiceToRun(host_name=host.host_name, command=service.command,
                                          attempts=failed_checks, name=service.name,
                                          hard_status=failed_checks >= attempts,
                                          command_arguments=service.command_arguments,
                                          current_status_id=status, output=output)
            service_to_run.save()
            if service_to_run.pk is None:
                print(service_to_run, 'was not saved')
            else:
                if item_time is not None:
                    ServiceToRun.objects.filter(host_name=host.host_name,
                                                name=service.name).update(executed_at=item_time)


def __compile_services():
    ServiceToRun.objects.all().delete()
    services = ServiceConfig.objects.get_all()
    __repopulate_services_to_run(services=services)  # TODO: perhaps merging can be more efficient


def save_service_status(name: str, host_name: str, status_code: str, output: str, ret_code: int):
    service = ServiceConfig.objects.get_item(name=name)
    status = ServiceStatus.objects.get_item(name=status_code)
    host = HostConfig.objects.get_item(host_name=host_name)
    last_run = ServiceToRun.objects.filter(host_name=host_name, name=name).first()

    if service is None or status is None or host is None or last_run is None:
        return {"error": "Wrong parameters"}
    service_status = ServiceStatusHistory.objects.add_item(name=name, host_name=host_name,
                                                           status=status, output=output, ret_code=ret_code)
    if service_status.pk is not None:
        ret, notify = ServiceToRun.objects.update_last_runs(host_name=host_name, name=name,
                                                            status_code=status_code, output=output)
        time_period_name = ServiceConfig.objects.get_time_period(service_name=name)
        if time_period_name is not None:
            periods = TimePeriodConfig.objects.get_parsed(time_period_name)
            is_in_time_period = is_in_periods(periods=periods)
            # print('Checking TP {} for {}::{} is {}'.format(time_period_name, host_name, name, is_in_time_period))
        else:
            is_in_time_period = True
        if notify and notification_expired(host=host, service=service) and is_in_time_period:
            if settings.USE_NOTIFICATIONS_QUEUE:
                enqueue_service_notification(service.config['contacts'],
                                             status_item=model_to_dict(service_status))
            else:
                notify_service_contacts(service.config['contacts'], service_status)
            notification_sent = NotificationRecords.objects.filter(host_name=host_name, service_name=name).first()
            if notification_sent is None:
                notification_sent = NotificationRecords(host_name=host_name, service_name=name,
                                                        status=status_code,
                                                        sent_at=datetime.now())
            else:
                notification_sent.sent_at = datetime.now()
            notification_sent.save()

    return {"status": service_status.pk}


def notification_expired(host: HostConfig, service: ServiceConfig = None):
    if service is None:
        last = NotificationRecords.objects.get_last_sent(host_name=host.host_name, service_name='host')
        interval = settings.DEFAULT_NOTIFICATION_INTERVAL
    else:
        interval = service.get_notifications_interval()
        last = NotificationRecords.objects.get_last_sent(host_name=host.host_name, service_name=service.name)
    if last is None:
        return True
    now = datetime.now()
    timediff = (now - last.sent_at).total_seconds()
    return timediff >= (interval * 60)
