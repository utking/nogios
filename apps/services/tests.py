from django.test import TestCase
from .models import ServiceToRun, ServiceStatus, ServiceConfig, ServiceDowntime, ServiceAcknowledgement


class TestServiceStatus(TestCase):
    def test_create(self):
        status_name = 'OK'
        u = ServiceStatus(name=status_name, alias=status_name)
        u.save()
        self.assert_(u.pk == status_name)


class TestServiceToRun(TestCase):
    def test_create(self):
        status_name = 'OK'
        u = ServiceStatus(name=status_name, alias=status_name)
        u.save()
        self.assert_(u.pk == status_name)
        u = ServiceToRun(host_name='host-1', current_status_id=status_name,
                         name='service-1', command='command-line',
                         command_arguments=[1, 2, 3])
        u.save()
        self.assert_(u.pk > 0)


class TestService(TestCase):
    def test_create(self):
        u = ServiceConfig(name='service-1', hosts='.*', config={},
                          command='command-lime', command_arguments=[1, 2, 3])
        u.save()
        self.assert_(u.pk > 0)
