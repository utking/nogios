from django.db import models
from django.core.cache import cache


class TimePeriodConfigManager(models.Manager):
    def clear_cache(self, name: str):
        key = 'period_config_{}'.format(name)
        cache.set(key, None, 1)

    def get_item(self, name: str):
        key = 'period_config_{}'.format(name)
        item = cache.get(key)
        if item is None:
            item = self.filter(name=name).first()
            cache.set(key, item, 3600)
        return item

    def get_parsed(self, name: str):
        key = 'period_config_{}'.format(name)
        parsed = cache.get(key)
        if parsed is None:
            period = self.filter(name=name).first()
            if period is not None:
                parsed = period.config.get('parsed')
                cache.set(key, parsed, 3600)
        return parsed


class TimePeriodConfig(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=True)
    alias = models.CharField(max_length=128)
    config = models.JSONField(max_length=4096)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TimePeriodConfigManager()
