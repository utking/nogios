from . import GenericStatusHandler
from apps.helpers.notification_channels import GenericNotificationChannel


class ServiceStatusHandler(GenericStatusHandler):

    def handle(self, channel: GenericNotificationChannel, recipient=None, status_item=None):
        super().handle(channel=channel, recipient=recipient, status_item=status_item)
