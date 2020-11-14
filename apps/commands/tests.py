from django.test import TestCase
from .models import CommandConfig


class TestCommand(TestCase):
    def test_create(self):
        u = CommandConfig(name='command', config={}, cmd='command-line')
        u.save()
        self.assert_(u.pk > 0)
