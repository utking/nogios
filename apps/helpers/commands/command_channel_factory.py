from . import *


class CommandChannelFactory(object):

    @staticmethod
    def get_channel(channel_type):
        klass = globals()['{}CommandsHelper'.format(channel_type)]
        return klass()
