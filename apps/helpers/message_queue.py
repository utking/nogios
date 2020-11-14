import pika
from json import dumps
from django.conf import settings
# from apps.status.models import ServiceStatusHistory, HostStatusHistory


class MessageQueueSender(object):

    def __init__(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.NOTIFICATIONS_QUEUE_HOST,
                    virtual_host=settings.NOTIFICATIONS_QUEUE_NAME,
                    credentials=pika.PlainCredentials(
                        username=settings.NOTIFICATIONS_QUEUE_USER,
                        password=settings.NOTIFICATIONS_QUEUE_PASSWORD
                    ))
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=settings.NOTIFICATIONS_QUEUE_NAME, durable=True)
        except Exception as e:
            print('ERROR: Failed to connect to RabbitMQ: ', str(e))

    def send(self, data: dict):
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=settings.NOTIFICATIONS_QUEUE_NAME,
                body=dumps(data)
            )
        except Exception as ex:
            print("ERROR: RabbitMQ - unable to publish a message:", str(ex))
