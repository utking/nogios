from django.db import models
from django.core.cache import cache


class UserConfigManager(models.Manager):

    def get_all(self):
        key = 'user_config'
        items = cache.get(key)
        if items is None:
            items = self.order_by('name').all()
            cache.set(key, items, 300)
        return items

    def get_user(self, name: str):
        key = 'user_{}'.format(name)
        item = cache.get(key)
        if item is None:
            item = self.filter(name=name).first()
            cache.set(key, item, 300)
        return item

    def get_users_in(self, names: list):
        return self.filter(name__in=names).all()


class GroupConfigManager(models.Manager):

    def get_all(self):
        key = 'group_config'
        items = cache.get(key)
        if items is None:
            items = self.order_by('name').all()
            cache.set(key, items, 300)
        return items

    def get_group(self, name):
        key = 'group_{}'.format(name)
        item = cache.get(key)
        if item is None:
            item = self.filter(name=name).first()
            cache.set(key, item, 300)
        return item


class NotificationRecordsManager(models.Manager):

    def get_last_sent(self, host_name: str, service_name: str):
        key = 'sent_{}_{}'.format(host_name, service_name)
        item = cache.get(key)
        if item is None:
            item = self.filter(host_name=host_name, service_name=service_name).first()
            if item is not None:
                cache.set(key, item, 60)
        return item


class UserContactConfig(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=True)
    channel = models.CharField(max_length=32, null=False)
    destination = models.CharField(max_length=250, default='')
    config = models.JSONField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserConfigManager()


class GroupContactConfig(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=True)
    config = models.JSONField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = GroupConfigManager()


class NotificationRecords(models.Model):
    id = models.AutoField(primary_key=True)
    host_name = models.CharField(max_length=64)
    service_name = models.CharField(max_length=64)
    status = models.CharField(max_length=16, null=False)
    sent_at = models.DateTimeField(null=False)

    objects = NotificationRecordsManager()

    def __str__(self):
        return '{}::{} sent a {} notification {}'.format(self.host_name, self.service_name, self.status, self.sent_at)

    class Meta:
        unique_together = (('host_name', 'service_name'),)
