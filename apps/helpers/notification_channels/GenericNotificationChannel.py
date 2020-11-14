class GenericNotificationChannel(object):

    def send(self, recipient=None, data=None):
        print('{} sends a notification to {}'.format(type(self).__name__, recipient), data)
