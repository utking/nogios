from . import GenericNotificationChannel


class MsTeamsNotificationChannel(GenericNotificationChannel):

    def send(self, recipient=None, data=None):
        super().send(recipient=recipient, data=data)
