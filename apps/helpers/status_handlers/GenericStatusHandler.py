from apps.helpers.notification_channels import GenericNotificationChannel


class GenericStatusHandler(object):

    def handle(self, channel: GenericNotificationChannel, recipient=None, status_item=None):
        print('Send {}::{} to {} over {}'.format(
            type(self).__name__, status_item, recipient, type(channel).__name__))
        channel.send(recipient=recipient, data=status_item)
