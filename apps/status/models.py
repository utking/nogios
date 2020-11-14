from django.db import models
from apps.hosts.models import HostStatus
from apps.services.models import ServiceStatus
from datetime import datetime


class ServiceStatusHistoryManager(models.Manager):
    def get_failing_since_date(self, name: str, host_name: str):
        last_ok = self.filter(status_id='OK', name=name, host_name=host_name).first()
        if last_ok is not None:
            started_failing = self.filter(name=name, host_name=host_name, id__gt=last_ok.id)\
                .order_by('created_at').first()
        else:
            started_failing = self.filter(name=name, host_name=host_name).order_by('created_at').first()
        if started_failing is not None:
            return started_failing.created_at
        return None

    def add_item(self, name: str, host_name: str, status, output: str, ret_code: int):
        service_statuses = self.filter(name=name, host_name=host_name)
        if service_statuses is not None and len(service_statuses) > 0:
            service_status = service_statuses[0]
        else:
            service_status = None
        if service_status is not None:
            if status.name == 'OK' and service_status.status_id == status.name:
                service_status.created_at = datetime.now()
                service_status.output = output
                service_status.save()
                return service_status

        service_status = ServiceStatusHistory(name=name, host_name=host_name, status=status,
                                              output=output, ret_code=ret_code)
        service_status.save()
        return service_status


class HostStatusHistoryManager(models.Manager):
    def add_item(self, host_name: str, status, output: str):
        host_statuses = self.filter(host_name=host_name)
        if host_statuses is not None and len(host_statuses) > 0:
            host_status = host_statuses[0]
        else:
            host_status = None
        if host_status is not None:
            if status.name == 'UP' and host_status.status_id == status.name:
                host_status.created_at = datetime.now()
                host_status.output = output
                host_status.save()
                return host_status

        host_status = HostStatusHistory(host_name=host_name, status=status, output=output)
        host_status.save()
        return host_status


class HostStatusHistory(models.Model):
    host_name = models.CharField(max_length=64)
    status = models.ForeignKey(HostStatus, on_delete=models.RESTRICT)
    output = models.CharField(max_length=256, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)

    objects = HostStatusHistoryManager()

    def __str__(self):
        return '{} status is {}'.format(self.host_name, self.status.name)

    class Meta:
        ordering = ['host_name', '-created_at']
        indexes = [
            models.Index(fields=['host_name', '-created_at', ]),
        ]


class ServiceStatusHistory(models.Model):
    name = models.CharField(max_length=64, null=False)
    host_name = models.CharField(max_length=64, null=False)
    output = models.CharField(max_length=1024)
    ret_code = models.SmallIntegerField(null=False)
    status = models.ForeignKey(ServiceStatus, on_delete=models.RESTRICT)
    created_at = models.DateTimeField(auto_now_add=True, null=False)

    objects = ServiceStatusHistoryManager()

    def __str__(self):
        return '{}::{} status is {} at {}'.format(self.host_name, self.name, self.status.name, self.created_at)

    class Meta:
        ordering = ['host_name', 'name', '-created_at']
        indexes = [
            models.Index(fields=['host_name', 'name', '-created_at', ]),
        ]
