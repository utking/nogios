from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from apps.status.models import ServiceStatusHistory, HostStatusHistory


class EmailSender(object):

    def __init__(self):
        self.sender = settings.EMAIL_FROM

    def send_email(self, to: str, data: dict):
        receivers = [to]
        object_type = type(data)
        if object_type == HostStatusHistory:
            status_for = 'Host'
        elif object_type == ServiceStatusHistory:
            status_for = 'Service'
        else:
            status_for = '{}'.format(data)

        try:
            send_mail(
                subject='[Nogios] {}'.format(data),
                message=render_to_string('mail_template.html', {
                    'message': data,
                    'host_name': data.host_name,
                    'status': data.status.name,
                    'output': data.output,
                    'status_for': status_for,
                }),
                from_email=self.sender,
                recipient_list=receivers,
                fail_silently=False,
            )
        except Exception as ex:
            print("Error: unable to send email:", ex)
