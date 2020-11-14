from . import GenericNotificationChannel
from apps.helpers.message_queue import MessageQueueSender


class MessageQueueNotificationChannel(GenericNotificationChannel):

    def send(self, recipient=None, data=None):
        channel = MessageQueueSender()
        channel.send(data=data)
