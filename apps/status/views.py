from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.forms.models import model_to_dict
from apps.status.models import HostStatusHistory, ServiceStatusHistory
from apps.services.models import ServiceToRun, ServiceConfig
from apps.services.models import ServiceAcknowledgement as ServiceAck, ServiceDowntime
from apps.hosts.models import HostToRun, HostConfig
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from collections import OrderedDict
from datetime import datetime
from json import loads


def host_services(request, host_name):
    items = {host_name: []}
    for service_item in ServiceToRun.objects.filter(host_name=host_name).order_by('name').all():
        ack = ServiceAck.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        down = ServiceDowntime.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        if ack is not None:
            service_item.ack = ack
        if down is not None:
            service_item.down = down
        service_config = ServiceConfig.objects.get_item(service_item.name)
        if service_config is not None:
            service_item.config = service_config.config
        if service_item.current_status_id in settings.FAILURE_STATUSES:
            service_item.failing_since = ServiceStatusHistory.objects.get_failing_since_date(
                name=service_item.name, host_name=service_item.host_name
            )
        service_item.retry_attempts = ServiceConfig.objects.get_retry_attempts(service_item.name)
        items[service_item.host_name].append(service_item)

    return render(request, 'status/services.html', {
        'items': items,
        'host_name': host_name,
        'title': 'Host service statuses',
    })


def host_services_json(request, host_name):
    items = {host_name: []}
    for service_item in ServiceToRun.objects.filter(host_name=host_name).order_by('name').all():
        ack = ServiceAck.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        down = ServiceDowntime.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        item = model_to_dict(service_item)
        if ack is not None:
            item['ack'] = True
        if down is not None:
            item['down'] = True
        service_config = ServiceConfig.objects.get_item(service_item.name)
        if service_config is not None:
            item['config'] = service_config.config
        item['executed_at'] = service_item.executed_at.strftime('%Y-%m-%d %H:%M:%S')
        if service_item.current_status_id in settings.FAILURE_STATUSES:
            item['failing_since'] = ServiceStatusHistory.objects.get_failing_since_date(
                name=service_item.name, host_name=service_item.host_name
            )
        item['retry_attempts'] = ServiceConfig.objects.get_retry_attempts(service_item.name)
        items[service_item.host_name].append(item)

    return JsonResponse({'items': items})


def services(request):
    services_aggregated = {}
    for service_item in ServiceToRun.objects.all():
        ack = ServiceAck.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        down = ServiceDowntime.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        if ack is not None:
            service_item.ack = ack
        if down is not None:
            service_item.down = down
        service_config = ServiceConfig.objects.get_item(service_item.name)
        if service_config is not None:
            service_item.config = service_config.config
        if services_aggregated.get(service_item.host_name) is None:
            services_aggregated[service_item.host_name] = []
        if service_item.current_status_id in settings.FAILURE_STATUSES:
            service_item.failing_since = ServiceStatusHistory.objects.get_failing_since_date(
                name=service_item.name, host_name=service_item.host_name
            )
        if service_item.attempts > 0:
            service_item.retry_attempts = ServiceConfig.objects.get_retry_attempts(service_item.name)
        services_aggregated[service_item.host_name].append(service_item)

    items = OrderedDict(sorted(services_aggregated.items()))

    return render(request, 'status/services.html', {'items': items, 'title': 'Service statuses'})


def services_json(request):
    services_aggregated = {}
    for service_item in ServiceToRun.objects.all():
        ack = ServiceAck.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        down = ServiceDowntime.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        item = model_to_dict(service_item)
        if ack is not None:
            item['ack'] = True
        if down is not None:
            item['down'] = True
        service_config = ServiceConfig.objects.get_item(service_item.name)
        if service_config is not None:
            item['config'] = service_config.config
        if services_aggregated.get(service_item.host_name) is None:
            services_aggregated[service_item.host_name] = []
        if service_item.current_status_id in settings.FAILURE_STATUSES:
            item['failing_since'] = ServiceStatusHistory.objects.get_failing_since_date(
                name=service_item.name, host_name=service_item.host_name
            )
        if service_item.attempts > 0:
            item['retry_attempts'] = ServiceConfig.objects.get_retry_attempts(service_item.name)
        item['executed_at'] = service_item.executed_at.strftime('%Y-%m-%d %H:%M:%S')
        services_aggregated[service_item.host_name].append(item)

    items = OrderedDict(sorted(services_aggregated.items()))

    return JsonResponse({'items': items})


def unhandled(request):
    services_aggregated = {}
    for service_item in ServiceToRun.objects.get_unhandled():
        ack = ServiceAck.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        down = ServiceDowntime.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        if ack is not None or down is not None:
            continue
        service_config = ServiceConfig.objects.get_item(service_item.name)
        if service_config is not None:
            service_item.config = service_config.config
        if services_aggregated.get(service_item.host_name) is None:
            services_aggregated[service_item.host_name] = []
        if service_item.current_status_id in settings.FAILURE_STATUSES:
            service_item.failing_since = ServiceStatusHistory.objects.get_failing_since_date(
                name=service_item.name, host_name=service_item.host_name
            )
        if service_item.attempts > 0:
            service_item.retry_attempts = ServiceConfig.objects.get_retry_attempts(service_item.name)
        services_aggregated[service_item.host_name].append(service_item)

    items = OrderedDict(sorted(services_aggregated.items()))

    return render(request, 'status/services.html', {'items': items, 'title': 'Unhandled services'})


def unhandled_json(request):
    services_aggregated = {}
    for service_item in ServiceToRun.objects.get_unhandled():
        ack = ServiceAck.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        down = ServiceDowntime.objects.get_item(name=service_item.name, host_name=service_item.host_name)
        item = model_to_dict(service_item)
        if ack is not None or down is not None:
            continue
        service_config = ServiceConfig.objects.get_item(service_item.name)
        if service_config is not None:
            item['config'] = service_config.config
        if services_aggregated.get(service_item.host_name) is None:
            services_aggregated[service_item.host_name] = []
        if service_item.attempts > 0:
            item['retry_attempts'] = ServiceConfig.objects.get_retry_attempts(service_item.name)
        if service_item.current_status_id in settings.FAILURE_STATUSES:
            item['failing_since'] = ServiceStatusHistory.objects.get_failing_since_date(
                name=service_item.name, host_name=service_item.host_name
            )
        item['executed_at'] = service_item.executed_at.strftime('%Y-%m-%d %H:%M:%S')
        services_aggregated[service_item.host_name].append(item)

    items = OrderedDict(sorted(services_aggregated.items()))

    return JsonResponse({'items': items})


def hosts(request):
    items = []
    for host_item in HostToRun.objects.all():
        ack = ServiceAck.objects.get_item(name='host', host_name=host_item.host_name)
        down = ServiceDowntime.objects.get_item(name='host', host_name=host_item.host_name)
        host_config = HostConfig.objects.get_item(host_name=host_item.host_name)
        if host_config is not None:
            host_item.config = host_config.config
        if ack is not None:
            host_item.ack = ack
        if down is not None:
            host_item.down = down
        if host_item.attempts > 0:
            host_item.retry_attempts = HostConfig.objects.get_retry_attempts(host_item.host_name)
        items.append(host_item)

    return render(request, 'status/hosts.html', {'items': items, 'title': 'Host statuses'})


def hosts_json(request):
    items = []
    for host_item in HostToRun.objects.all():
        ack = ServiceAck.objects.get_item(name='host', host_name=host_item.host_name)
        down = ServiceDowntime.objects.get_item(name='host', host_name=host_item.host_name)
        host_config = HostConfig.objects.get_item(host_name=host_item.host_name)
        item = model_to_dict(host_item)
        if host_item.attempts > 0:
            item['retry_attempts'] = HostConfig.objects.get_retry_attempts(host_item.host_name)
        if host_config is not None:
            item['config'] = host_config.config
        if ack is not None:
            item['ack'] = True
        if down is not None:
            item['down'] = True
        item['executed_at'] = host_item.executed_at.strftime('%Y-%m-%d %H:%M:%S')
        items.append(item)

    return JsonResponse({'items': items})


def service(request, host_name: str, service_name: str):
    items = ServiceStatusHistory.objects.filter(host_name=host_name, name=service_name) # [:15]
    ack = ServiceAck.objects.get_item(host_name=host_name, name=service_name)
    down = ServiceDowntime.objects.get_item(host_name=host_name, name=service_name)

    return render(request, 'status/service_history.html', {
        'items': items,
        'host_name': host_name,
        'name': service_name,
        'ack': ack,
        'down': down,
        'title': 'Service history',
    })


def service_json(request, host_name: str, service_name: str):
    service_items = ServiceStatusHistory.objects.filter(host_name=host_name, name=service_name) # [:15]
    ack = ServiceAck.objects.get_item(host_name=host_name, name=service_name)
    down = ServiceDowntime.objects.get_item(host_name=host_name, name=service_name)
    items = []
    for service_item in service_items:
        item = model_to_dict(service_item)
        item['created_at'] = service_item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        items.append(item)

    return JsonResponse({
        'items': items,
        'host_name': host_name,
        'name': service_name,
        'ack': ack is not None,
        'down': model_to_dict(down) if down is not None else False,
        'title': 'Service history',
    })


@csrf_exempt
@require_http_methods(['POST'])
def service_ack(request):
    host_name = request.POST.get('host_name', None)
    service_name = request.POST.get('name', None)

    host = HostConfig.objects.get_item(host_name=host_name)
    service = ServiceConfig.objects.get_item(name=service_name)

    if host is not None and service is not None:
        ack = ServiceAck.objects.get_item(host_name=host_name, name=service_name)
        if ack is None:
            ack = ServiceAck(name=service_name, host_name=host_name)
            ack.save()
        else:
            ServiceAck.objects.remove_item(host_name=host_name, name=service_name)

    return redirect('/status/service/{}/{}'.format(host_name, service_name))


@csrf_exempt
@require_http_methods(['POST'])
def service_ack_json(request):
    params = loads(request.body)
    host_name = params.get('host_name', None)
    service_name = params.get('name', None)

    host = HostConfig.objects.get_item(host_name=host_name)
    service = ServiceConfig.objects.get_item(name=service_name)

    if host is not None and service is not None:
        ack = ServiceAck.objects.get_item(host_name=host_name, name=service_name)
        if ack is None:
            ack = ServiceAck(name=service_name, host_name=host_name)
            ack.save()
            return JsonResponse({'ack': True})
        else:
            ServiceAck.objects.remove_item(host_name=host_name, name=service_name)
            return JsonResponse({'ack': None})
    else:
        return JsonResponse({'ack': False})


@csrf_exempt
@require_http_methods(['POST'])
def host_ack(request):
    host_name = request.POST.get('host_name', None)
    host = HostConfig.objects.get_item(host_name=host_name)

    if host is not None:
        ack = ServiceAck.objects.get_item(host_name=host_name, name='host')
        if ack is None:
            ack = ServiceAck(name='host', host_name=host_name)
            ack.save()
        else:
            ServiceAck.objects.remove_item(host_name=host_name, name='host')

    return redirect('/status/host/{}'.format(host_name))


@csrf_exempt
@require_http_methods(['POST'])
def service_down(request):
    host_name = request.POST.get('host_name', None)
    service_name = request.POST.get('name', None)
    started_at = request.POST.get('started_at', None)
    expire_at = request.POST.get('expire_at', None)
    info = request.POST.get('info', '')[:128]

    try:
        dt_start = datetime.strptime(started_at, '%Y-%m-%dT%H:%M')
    except:
        dt_start = datetime.now()

    try:
        dt = datetime.strptime(expire_at, '%Y-%m-%dT%H:%M')
        if (datetime.now() - dt).total_seconds() > 0:
            return redirect('/status/host/{}'.format(host_name))
    except:
        dt = None

    host = HostConfig.objects.get_item(host_name=host_name)
    service = ServiceConfig.objects.get_item(name=service_name)

    if host is not None and service is not None and expire_at is not None:
        down = ServiceDowntime.objects.get_item(host_name=host_name, name=service_name)
        if down is None:
            if dt is not None:
                down = ServiceDowntime(name=service_name, host_name=host_name, info=info,
                                       started_at=dt_start, expires_at=dt)
                try:
                    down.save()
                except:
                    pass
        else:
            ServiceDowntime.objects.remove_item(host_name=host_name, name=service_name)

    return redirect('/status/service/{}/{}'.format(host_name, service_name))


@csrf_exempt
@require_http_methods(['POST'])
def service_down_json(request):
    params = loads(request.body)
    host_name = params.get('host_name', None)
    service_name = params.get('name', None)
    started_at = params.get('started_at', None)
    expires_at = params.get('expires_at', None)
    info = params.get('info', '')[:128]

    try:
        dt_start = datetime.strptime(started_at, '%Y-%m-%dT%H:%M')
    except:
        dt_start = datetime.now()

    try:
        dt = datetime.strptime(expires_at, '%Y-%m-%dT%H:%M')
        if (datetime.now() - dt).total_seconds() > 0:
            return JsonResponse({'down': False, 'error': 'Expiration date must be in the future'})
    except:
        dt = None

    host = HostConfig.objects.get_item(host_name=host_name)
    service = ServiceConfig.objects.get_item(name=service_name)

    if host is not None and service is not None and expires_at is not None:
        down = ServiceDowntime.objects.get_item(host_name=host_name, name=service_name)
        if down is None:
            if dt is not None:
                down = ServiceDowntime(name=service_name, host_name=host_name, info=info,
                                       started_at=dt_start, expires_at=dt)
                try:
                    down.save()
                    return JsonResponse({'down': model_to_dict(down)})
                except Exception as e:
                    return JsonResponse({'down': False, 'error': str(e)})
        else:
            ServiceDowntime.objects.remove_item(host_name=host_name, name=service_name)

    return JsonResponse({'down': False})


@csrf_exempt
@require_http_methods(['POST'])
def host_down(request):
    host_name = request.POST.get('host_name', None)
    expire_at = request.POST.get('expire_at', None)
    started_at = request.POST.get('started_at', None)
    info = request.POST.get('info', '')[:128]
    host = HostConfig.objects.get_item(host_name=host_name)

    try:
        dt_start = datetime.strptime(started_at, '%Y-%m-%dT%H:%M')
    except:
        dt_start = datetime.now()

    try:
        dt = datetime.strptime(expire_at, '%Y-%m-%dT%H:%M')
        if (datetime.now() - dt).total_seconds() > 0:
            return redirect('/status/host/{}'.format(host_name))
    except:
        dt = None

    if host is not None and expire_at is not None:
        down = ServiceDowntime.objects.get_item(host_name=host_name, name='host')
        if down is None:
            if dt is not None:
                down = ServiceDowntime(name='host', host_name=host_name, info=info,
                                       started_at=dt_start, expires_at=dt)
                try:
                    down.save()
                except:
                    pass
        else:
            ServiceDowntime.objects.remove_item(host_name=host_name, name='host')

    return redirect('/status/host/{}'.format(host_name))


def host(request, host_name: str):
    items = HostStatusHistory.objects.filter(host_name=host_name).all() # [:15]
    ack = ServiceAck.objects.get_item(host_name=host_name, name='host')
    down = ServiceDowntime.objects.get_item(host_name=host_name, name='host')

    return render(request, 'status/host_history.html', {
        'items': items,
        'host_name': host_name,
        'ack': ack,
        'down': down,
        'title': 'Host status history',
    })


def host_json(request, host_name: str):
    history_items = HostStatusHistory.objects.filter(host_name=host_name).all() # [:15]
    ack = ServiceAck.objects.get_item(host_name=host_name, name='host')
    down = ServiceDowntime.objects.get_item(host_name=host_name, name='host')
    items = []
    for history_item in history_items:
        item = model_to_dict(history_item)
        item['created_at'] = history_item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        items.append(item)

    return JsonResponse({
        'items': items,
        'host_name': host_name,
        'ack': ack is not None,
        'down': down is not None,
    })
