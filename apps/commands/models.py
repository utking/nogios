from django.db import models
from django.core.cache import cache


class CommandConfigManager(models.Manager):
    def clear_cache(self, name: str):
        key = 'command_config_{}'.format(name)
        cache.set(key, None, 1)

    def get_item(self, name: str):
        key = 'command_config_{}'.format(name)
        item = cache.get(key)
        if item is None:
            item = self.filter(name=name).first()
            cache.set(key, item, 3600)
        return item


class CommandConfig(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=True)
    alias = models.CharField(max_length=128)
    cmd = models.CharField(max_length=256)
    config = models.JSONField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CommandConfigManager()
