from . import GenericNotificationChannel
from apps.helpers.jira import JiraSender


class JiraNotificationChannel(GenericNotificationChannel):

    def send(self, recipient=None, data=None):
        channel = JiraSender()
        channel.create_ticket(project=recipient, data=data)
