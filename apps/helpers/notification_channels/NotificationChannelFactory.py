from . import *


class NotificationChannelFactory(object):

    factories = {}

    def __init__(self):
        self.factories = {}

    def get_channel(self, channel_type):
        klass = self.factories.get(channel_type)
        if self.factories.get(channel_type) is None:
            klass = globals()['{}NotificationChannel'.format(channel_type)]
            self.factories[channel_type] = klass
        return klass()
