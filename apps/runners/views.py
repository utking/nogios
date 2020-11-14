from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import _thread
from datetime import datetime
from apps.helpers.PingHelper import ping
from apps.services.models import ServiceToRun, ServiceAcknowledgement as ServiceAck, ServiceDowntime, ServiceConfig
from apps.hosts.models import HostToRun, HostConfig
from apps.commands.models import CommandConfig
from apps.services.views import save_service_status
from apps.hosts.views import save_host_status
from apps.helpers.commands.command_channel_factory import CommandChannelFactory
from django.conf import settings
from json import loads


def __host_check_thread(host_name, host_ip):
    try:
        ip, time_min, time_avg, time_max, lost = ping(host_ip)
        status = 'UP' if lost < 100 else 'DOWN'
        output = 'IP {} - avg. time {} ms, lost {}%'.format(ip, time_avg, lost)
    except Exception as e:
        status = 'UNKNOWN'
        output = str(e)
        print('Error', output)

    save_host_status(host_name=host_name, status_code=status, output=output)


def __service_check_thread(host_name: str, host_ip: str, command: dict, channel_name: str = None):
    channel = CommandChannelFactory.get_channel(channel_name)
    try:
        if isinstance(command, dict):
            ok, resp = channel.send(host_ip, command=command)
            process_response(ok=ok, resp=resp)
        else:
            responses = channel.send_multiple(host_ip, commands=command)
            for (ok, resp) in responses:
                process_response(ok=ok, resp=resp)
    except Exception as e:
        raise Exception('Error {}'.format(str(e)))


def process_response(ok: bool, resp=None):
    if ok and isinstance(resp, str):
        resp_object = loads(resp)
        name = resp_object.get('name')
        host_name = resp_object.get('host_name')
        status_code = resp_object.get('status_code')
        output = resp_object.get('output')
        ret_code = resp_object.get('ret_code')
        resp = save_service_status(name=name, host_name=host_name, status_code=status_code,
                                   output=output, ret_code=ret_code)
        if resp.get('error') is not None:
            raise Exception('Error saving check response: {}'.format(resp.get('error')))


def __check_hosts(check_interval: int):
    now = datetime.now()
    for host in HostToRun.objects.all():
        ack = ServiceAck.objects.get_item(name='host', host_name=host.host_name)
        down = ServiceDowntime.objects.get_item(name='host', host_name=host.host_name)
        if ack is not None:
            print("{} is Acknowledged. Won't be checked".format(host.host_name))
            continue
        if down is not None:
            print("{} is in Maint mode until {}. Won't be checked".format(host.host_name, down.expires_at))
            continue
        time_diff = (now - host.executed_at.replace(tzinfo=None)).total_seconds() / 60
        if time_diff < check_interval and host.current_status_id not in ['PENDING', 'UNKNOWN']:
            continue
        try:
            _thread.start_new_thread(__host_check_thread, (host.host_name, host.address))
        except SystemExit as e:
            print('Error checking host {}; {}'.format(host.host_name, e))


def __check_services(check_interval: int):
    now = datetime.now()
    services_over_ssh = {}
    for service in ServiceToRun.objects.all():
        ack = ServiceAck.objects.get_item(name=service.name, host_name=service.host_name)
        down = ServiceDowntime.objects.get_item(name=service.name, host_name=service.host_name)
        if ack is not None:
            print("{}::{} is Acknowledged. Won't be checked".format(service.host_name, service.name))
            continue
        if down is not None:
            print("{}::{} is in Maint mode until {}. Won't be checked".format(service.host_name,
                                                                              service.name, down.expires_at))
            continue
        time_diff = (now - service.executed_at.replace(tzinfo=None)).total_seconds() / 60
        if time_diff < check_interval and service.current_status_id not in ['PENDING', 'UNKNOWN']:
            continue
        try:
            host = HostConfig.objects.get_item(host_name=service.host_name)
            command = CommandConfig.objects.get_item(name=service.command)
            service_channel = ServiceConfig.objects.get_channel(service.name)
            if host is None:
                raise Exception('FAIL: Host {} not found'.format(service.host_name))
            if command is None:
                raise Exception('FAIL: Command {} not found'.format(service.command))

            if service_channel == 'Ssh':
                if services_over_ssh.get(service.host_name) is None:
                    services_over_ssh[service.host_name] = {
                        'host': host,
                        'services': []
                    }
                services_over_ssh[service.host_name]['services'].append(service)
            else:
                argv = service.command_arguments
                channel_name = ServiceConfig.objects.get_channel(service_name=service.name)
                print('{} - {}[{}]::{}'.format(channel_name, service.host_name, host.address, service.name))
                _thread.start_new_thread(__service_check_thread,
                                         (service.host_name,
                                          host.address,
                                          {
                                              'cmd': command.cmd,
                                              'args': argv,
                                              'service_name': service.name,
                                              'host_name': service.host_name,
                                              'command_name': command.name,
                                          },
                                          channel_name))
        except SystemExit as e:
            print('Error checking service {}::{}; {}'.format(service.host_name, service.name, e))

    if len(services_over_ssh.keys()) > 0:
        run_combined_checks_over_ssh(services_over_ssh)


def run_combined_checks_over_ssh(services_over_ssh: dict):
    for host_name in services_over_ssh.keys():
        host = services_over_ssh.get(host_name)['host']
        services = services_over_ssh.get(host_name)['services']
        commands_to_run = []
        for service in services:
            argv = service.command_arguments
            command = CommandConfig.objects.get_item(name=service.command)
            commands_to_run.append(
                {
                    'cmd': command.cmd,
                    'args': argv,
                    'service_name': service.name,
                    'host_name': service.host_name,
                    'command_name': command.name,
                }
            )
            print('{} - {}[{}]::{}'.format('Ssh', host_name, host.address, service.name))
        try:
            _thread.start_new_thread(__service_check_thread,
                                     (
                                         host_name,
                                         host.address,
                                         commands_to_run,
                                         'Ssh'
                                     ))
        except SystemExit as e:
            print('Error checking service over Ssh {}; {}'.format(host_name, e))


@csrf_exempt
@require_http_methods(['POST', 'GET'])
def run_checks(request):
    default_check_interval = settings.DEFAULT_CHECK_INTERVAL
    # for every check, pull its schedule and run if it is time
    print('run host checks')
    __check_hosts(default_check_interval)
    print('run service checks')
    __check_services(default_check_interval)
    return JsonResponse({'status': 'Ok', 'datetime': str(datetime.now())})


@csrf_exempt
@require_http_methods(['POST', 'GET'])
def cleanup_downtime(request):
    print('run cleanup downtime')
    for item in ServiceDowntime.objects.filter(expires_at__lt=datetime.now()).all():
        ServiceDowntime.objects.remove_item(host_name=item.host_name, name=item.name)
    ServiceDowntime.objects.filter(expires_at__lt=datetime.now()).delete()
    return JsonResponse({'status': 'Ok', 'datetime': str(datetime.now())})
