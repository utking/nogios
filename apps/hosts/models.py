from django.db import models
from django.conf import settings
from django.core.cache import cache


class HostToRunManager(models.Manager):

    def update_last_run(self, host_name: str, status_code: str, output: str):
        last_run = self.filter(host_name=host_name).first()
        if last_run is None:
            return None, False
        retry_attempts = settings.DEFAULT_RETRY_ATTEMPTS
        host_config = HostConfig.objects.get_item(host_name=host_name)
        if host_config is not None and host_config.config.get('retry_attempts') is not None:
            retry_attempts = host_config.config.get('retry_attempts')
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


class HostStatusManager(models.Manager):
    def get_item(self, name: str):
        key = 'host_status_{}'.format(name)
        item = cache.get(key)
        if item is None:
            item = self.filter(name=name).first()
            cache.set(key, item, 3600)
        return item


class HostConfigManager(models.Manager):

    def clear_interval_cache(self, host_name: str = None):
        if host_name is not None:
            cache.set('host_retry_{}'.format(host_name), None, 1)

    def clear_cache(self):
        cache.set('host_config', None, 1)

    def get_time_period(self, host_name: str):
        key = 'host_tp_{}'.format(host_name)
        period = cache.get(key)
        if period is None:
            config = self.filter(host_name=host_name).first()
            if config is not None and config.config.get('time_period') is not None:
                period = config.config.get('time_period')
            cache.set(key, period, 3600)
        return period

    def get_retry_attempts(self, host_name: str):
        key = 'host_retry_{}'.format(host_name)
        retry_attempts = cache.get(key)
        if retry_attempts is None:
            retry_attempts = settings.DEFAULT_RETRY_ATTEMPTS
            host_config = self.filter(host_name=host_name).first()
            if host_config is not None and host_config.config.get('retry_attempts') is not None:
                retry_attempts = int(host_config.config.get('retry_attempts'))
            cache.set(key, retry_attempts, 3600)
        return retry_attempts

    def get_all(self):
        key = 'host_config'
        items = cache.get(key)
        if items is None:
            items = self.order_by('host_name').all()
            cache.set(key, items, 3600)
        return items

    def get_item(self, host_name: str):
        key = 'host_{}'.format(host_name)
        item = cache.get(key)
        if item is None:
            item = self.filter(host_name=host_name).first()
            cache.set(key, item, 3600)
        return item


class HostConfig(models.Model):
    id = models.AutoField(primary_key=True)
    host_name = models.CharField(max_length=64, unique=True)
    address = models.CharField(max_length=64, unique=True)
    location = models.CharField(max_length=64)
    config = models.JSONField(max_length=4096)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HostConfigManager()

    @staticmethod
    def create_config(item: dict):
        if item.get('location') is None:
            location = settings.DEFAULT_LOCATION
        else:
            location = item['location']
        host = HostConfig(host_name=item['name'], address=item['address'], config=item, location=location)
        host.save()
        return host.pk > 0


class HostStatus(models.Model):
    name = models.CharField(primary_key=True, max_length=8, unique=True)
    alias = models.CharField(max_length=32)

    objects = HostStatusManager()


class HostToRun(models.Model):

    id = models.AutoField(primary_key=True)
    host_name = models.CharField(max_length=64, null=False, db_index=True, unique=True)
    address = models.CharField(max_length=64, unique=True)
    output = models.CharField(max_length=2048)
    attempts = models.SmallIntegerField(default=0, null=False)
    hard_status = models.BooleanField(null=False, default=False, db_index=True)
    current_status = models.ForeignKey(HostStatus, on_delete=models.RESTRICT, db_index=True)
    executed_at = models.DateTimeField(auto_now=True)

    objects = HostToRunManager()

    def __str__(self):
        return "Host {} is {} after {} attempts, last run {}".format(
            self.host_name,
            self.current_status_id,
            self.attempts,
            self.executed_at)

    class Meta:
        ordering = ['host_name']
