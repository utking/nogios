from . import GenericNotificationChannel
from apps.helpers.emails import EmailSender


class EmailNotificationChannel(GenericNotificationChannel):

    def send(self, recipient=None, data=None):
        channel = EmailSender()
        channel.send_email(recipient, data=data)
