from django.test import TestCase
from .models import HostStatusHistory, ServiceStatusHistory, HostStatus, ServiceStatus


class TestServiceStatusHistory(TestCase):
    def test_create(self):
        status_name = 'OK'
        u = ServiceStatus(name=status_name, alias=status_name)
        u.save()
        self.assert_(u.pk == status_name)
        u = ServiceStatusHistory(host_name='host-1', name='service-1', ret_code=0, status_id=status_name)
        u.save()
        self.assert_(u.pk > 0)


class TestHostStatusHistory(TestCase):
    def test_create(self):
        status_name = 'UP'
        u = HostStatus(name=status_name, alias=status_name)
        u.save()
        self.assert_(u.pk == status_name)
        u = HostStatusHistory(host_name='host-1', status_id=status_name)
        u.save()
        self.assert_(u.pk > 0)
