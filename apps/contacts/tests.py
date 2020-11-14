from django.test import TestCase
from .models import UserContactConfig, GroupContactConfig, NotificationRecords


class UserTests(TestCase):
    def test_create(self):
        u = UserContactConfig(name='test-user', channel='Email', config={})
        u.save()
        self.assert_(u.pk > 0)


class GroupTests(TestCase):
    def test_create(self):
        u = GroupContactConfig(name='test-users', config={})
        u.save()
        self.assert_(u.pk > 0)


class NotificationChannelTests(TestCase):
    def test_create(self):
        u = NotificationRecords(host_name='host-1', service_name='service-1', status='OK', sent_at='2020-01-01')
        u.save()
        self.assert_(u.pk > 0)
