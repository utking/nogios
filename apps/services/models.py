from django.db import models
from django.conf import settings
import re
from datetime import datetime
from apps.hosts.models import HostConfig
from django.core.cache import cache


class ServiceStatusManager(models.Manager):
    def get_item(self, name: str):
        key = 'svc_status_{}'.format(name)
        item = cache.get(key)
        if item is None:
            item = self.filter(name=name).first()
            cache.set(key, item, 3600)
        return item


class ServiceConfigManager(models.Manager):

    def clear_cache(self, name: str):
        cache.set('svc_retry_{}'.format(name), None, 1)
        cache.set('svc_ntf_int_{}'.format(name), None, 1)
        cache.set('svc_retry_{}'.format(name), None, 1)
        cache.set('svc_tp_{}'.format(name), None, 1)
        cache.set('svc_ch_{}'.format(name), None, 1)
        cache.set('svc_{}'.format(name), None, 1)

    def get_retry_attempts(self, service_name: str):
        key = 'svc_retry_{}'.format(service_name)
        retry_attempts = cache.get(key)
        if retry_attempts is None:
            retry_attempts = settings.DEFAULT_RETRY_ATTEMPTS
            service_config = self.filter(name=service_name).first()
            if service_config is not None and service_config.config.get('retry_attempts') is not None:
                retry_attempts = int(service_config.config.get('retry_attempts'))
            cache.set(key, retry_attempts, 3600)
        return retry_attempts

    def get_time_period(self, service_name: str):
        key = 'svc_tp_{}'.format(service_name)
        period = cache.get(key)
        if period is None:
            service_config = self.filter(name=service_name).first()
            if service_config is not None and service_config.config.get('time_period') is not None:
                period = service_config.config.get('time_period')
            cache.set(key, period, 3600)
        return period

    def get_notifications_interval(self, service_name: str):
        key = 'svc_ntf_int_{}'.format(service_name)
        interval = cache.get(key)
        if interval is None:
            interval = settings.DEFAULT_NOTIFICATION_INTERVAL
            service_config = self.filter(name=service_name).first()
            if service_config is not None and service_config.config.get('notification_interval') is not None:
                interval = int(service_config.config.get('notification_interval'))
            cache.set(key, interval, 3600)
        return interval

    def get_channel(self, service_name: str):
        key = 'svc_ch_{}'.format(service_name)
        channel = cache.get(key)
        if channel is None:
            channel = settings.DEFAULT_CHECK_CHANNEL
            service_config = self.filter(name=service_name).first()
            if service_config is not None and service_config.config.get('channel') is not None:
                channel = service_config.config.get('channel')
            cache.set(key, channel, 3600)
        return channel

    def get_all(self):
        key = 'service_config'
        items = cache.get(key)
        if items is None:
            items = self.order_by('name').all()
            cache.set(key, items, 3600)
        return items

    def get_item(self, name: str):
        key = 'svc_{}'.format(name)
        item = cache.get(key)
        if item is None:
            item = self.filter(name=name).first()
            cache.set(key, item, 3600)
        return item


class ServiceToRunManager(models.Manager):

    def get_unhandled(self):
        return ServiceToRun.objects.filter(current_status_id__in=settings.FAILURE_STATUSES).all()

    def update_last_runs(self, host_name: str, name: str, status_code: str, output: str):
        last_run = self.filter(host_name=host_name, name=name).first()
        if last_run is None:
            return None, False
        retry_attempts = settings.DEFAULT_RETRY_ATTEMPTS
        service_config = ServiceConfig.objects.get_item(name=name)
        if service_config is not None and service_config.config.get('retry_attempts') is not None:
            retry_attempts = service_config.config.get('retry_attempts')
        notify = False
        hard_status = False
        if status_code in settings.FAILURE_STATUSES:
            updated_attempts = last_run.attempts + 1
            if updated_attempts >= retry_attempts:
                hard_status = True
                updated_attempts = retry_attempts
                notify = True
        else:
            updated_attempts = 0
            if last_run.current_status_id in settings.FAILURE_STATUSES and \
                    status_code not in settings.FAILURE_STATUSES:
                notify = True

        last_run.current_status_id = status_code
        last_run.attempts = updated_attempts
        last_run.hard_status = hard_status
        last_run.output = output
        last_run.save()
        return last_run.pk > 0, notify


class ServiceConfig(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=True)
    command = models.CharField(max_length=64)
    command_arguments = models.JSONField(max_length=1024)
    location = models.CharField(max_length=64)
    type = models.CharField(max_length=32)
    hosts = models.CharField(max_length=4096, default='')
    excluded_hosts = models.CharField(max_length=4096, default='')
    config = models.JSONField(max_length=4096)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ServiceConfigManager()

    def get_notifications_interval(self):
        key = 'svc_ntf_int_{}'.format(self.name)
        interval = cache.get(key)
        if interval is None:
            interval = settings.DEFAULT_NOTIFICATION_INTERVAL
            if self.config.get('notification_interval') is not None:
                interval = int(self.config.get('notification_interval'))
            cache.set(key, interval, 3600)
        return interval

    def get_hosts(self):
        if not self.hosts.startswith('^'):
            self.hosts = '^{}'.format(self.hosts)
        if not self.hosts.endswith('$'):
            self.hosts = '{}$'.format(self.hosts)

        if not self.excluded_hosts.startswith('^'):
            self.excluded_hosts = '^{}'.format(self.excluded_hosts)
        if not self.excluded_hosts.endswith('$'):
            self.excluded_hosts = '{}$'.format(self.excluded_hosts)

        search_re = re.compile(self.hosts)
        excluded_search_re = re.compile(self.excluded_hosts)
        items = HostConfig.objects.order_by('host_name').filter(
            host_name__iregex=search_re.pattern
        ).exclude(
            host_name__iregex=excluded_search_re.pattern
        )
        return items

    @staticmethod
    def create_config(item):
        config_hosts = ''
        command_arguments = []
        excluded_config_hosts = ''
        if item.get('location') is None:
            location = settings.DEFAULT_LOCATION
        else:
            location = item['location']
        if item.get('hosts') is not None:
            config_hosts = item['hosts']
        if item.get('command_arguments') is not None:
            command_arguments = item['command_arguments']
        if item.get('excluded_hosts') is not None:
            excluded_config_hosts = item['excluded_hosts']
        ServiceConfig.objects.clear_cache(item['name'])
        config = ServiceConfig(name=item['name'], type=item['type'], location=location,
                               config=item, hosts=config_hosts, command=item['command'],
                               command_arguments=command_arguments,
                               excluded_hosts=excluded_config_hosts)
        config.save()
        return config.pk > 0


class ServiceStatus(models.Model):
    name = models.CharField(primary_key=True, max_length=8, unique=True)
    alias = models.CharField(max_length=32)

    objects = ServiceStatusManager()


class ServiceToRun(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, null=False, db_index=True)
    host_name = models.CharField(max_length=64, null=False, db_index=True)
    command = models.CharField(max_length=64, null=False)
    command_arguments = models.JSONField(max_length=1024)
    output = models.CharField(max_length=2048)
    attempts = models.SmallIntegerField(default=0, null=False)
    hard_status = models.BooleanField(null=False, default=False, db_index=True)
    current_status = models.ForeignKey(ServiceStatus, on_delete=models.RESTRICT, db_index=True)
    executed_at = models.DateTimeField(auto_now=True)

    objects = ServiceToRunManager()

    def __str__(self):
        return "Service {}::{} is {} after {} attempts, last run {}".format(
            self.host_name, self.name,
            self.current_status_id,
            self.attempts,
            self.executed_at)

    class Meta:
        ordering = ['name']
        unique_together = (('host_name', 'name'),)


class ServiceAcknowledgementManager(models.Manager):

    def get_item(self, name: str, host_name: str):
        key = 'svc_ack_{}_{}'.format(name, host_name)
        item = cache.get(key)
        if item is None:
            item = self.filter(name=name, host_name=host_name).first()
            cache.set(key, item, 600)
        return item

    def remove_item(self, name: str, host_name: str):
        ack = self.filter(name=name, host_name=host_name).first()
        key = 'svc_ack_{}_{}'.format(name, host_name)
        item = cache.get(key)
        if item is not None:
            cache.set(key, None)
        if ack is not None:
            ack.delete()
        return item


class ServiceAcknowledgement(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, null=False)
    host_name = models.CharField(max_length=64, null=False)
    created_at = models.DateTimeField(auto_now=True)

    objects = ServiceAcknowledgementManager()

    class Meta:
        unique_together = (('host_name', 'name'),)


class ServiceDowntimeManager(models.Manager):

    def get_item(self, name: str, host_name: str):
        key = 'svc_down_{}_{}'.format(name, host_name)
        item = cache.get(key)
        if item is None:
            item = self.filter(name=name, host_name=host_name,
                               started_at__lte=datetime.now(),
                               expires_at__gt=datetime.now()).first()
            cache.set(key, item, 1200)
        elif (datetime.now() - item.expires_at).total_seconds() > 0:
            cache.set(key, None, 1)
            item = None
        return item

    def remove_item(self, name: str, host_name: str):
        down = self.filter(name=name, host_name=host_name).first()
        key = 'svc_down_{}_{}'.format(name, host_name)
        item = cache.get(key)
        if item is not None:
            cache.set(key, None)
        if down is not None:
            down.delete()
        return item


class ServiceDowntime(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, null=False)
    host_name = models.CharField(max_length=64, null=False)
    info = models.CharField(max_length=128, null=False, default='')
    expires_at = models.DateTimeField(null=False)
    started_at = models.DateTimeField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ServiceDowntimeManager()

    class Meta:
        unique_together = (('host_name', 'name'),)
