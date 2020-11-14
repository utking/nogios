from django.test import TestCase
from .models import HostConfig, HostToRun, HostStatus


class TestHostStatus(TestCase):
    def test_create(self):
        status_name = 'UP'
        u = HostStatus(name=status_name, alias=status_name)
        u.save()
        self.assert_(u.pk == status_name)


class TestHostToRun(TestCase):
    def test_create(self):
        status_name = 'UP'
        u = HostStatus(name=status_name, alias=status_name)
        u.save()
        self.assert_(u.pk == status_name)
        u = HostToRun(host_name='host-1', current_status_id=status_name)
        u.save()
        self.assert_(u.pk > 0)


class TestHost(TestCase):
    def test_create(self):
        u = HostConfig(host_name='host-1', address='127.0.0.1', config={})
        u.save()
        self.assert_(u.pk > 0)
