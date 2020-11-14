from apps.helpers.notification_channels import NotificationChannelFactory, MessageQueueNotificationChannel
from apps.helpers.status_handlers import HostStatusHandler, ServiceStatusHandler
from apps.contacts.models import UserContactConfig, GroupContactConfig
from apps.status.models import HostStatusHistory, ServiceStatusHistory


def notify_host_contacts(contacts: dict, status_item: HostStatusHistory):
    contact_items = extract_users(contacts)
    status_handler = HostStatusHandler()
    channel_factory = NotificationChannelFactory()
    for user in UserContactConfig.objects.get_users_in(names=list(contact_items)):
        channel = channel_factory.get_channel(user.channel)
        status_handler.handle(channel=channel, recipient=user.destination, status_item=status_item)


def enqueue_host_notification(contacts: dict, status_item: HostStatusHistory):
    contact_items = extract_users(contacts)
    channel = MessageQueueNotificationChannel()
    for user in UserContactConfig.objects.get_users_in(names=list(contact_items)):
        channel.send(data={
            'type': 'host',
            'channel': user.channel,
            'destination': user.destination,
            'status': status_item
        })


def notify_service_contacts(contacts: dict, status_item: ServiceStatusHistory):
    contact_items = extract_users(contacts)
    status_handler = ServiceStatusHandler()
    channel_factory = NotificationChannelFactory()
    for item in contact_items:
        user = UserContactConfig.objects.get_user(name=item)
        channel = channel_factory.get_channel(user.channel)
        status_handler.handle(channel=channel, recipient=user.destination, status_item=status_item)


def enqueue_service_notification(contacts: dict, status_item: ServiceStatusHistory):
    contact_items = extract_users(contacts)
    channel = MessageQueueNotificationChannel()
    for item in contact_items:
        user = UserContactConfig.objects.get_user(name=item)
        channel.send(data={
            'type': 'service',
            'channel': user.channel,
            'destination': user.destination,
            'status': status_item
        })


def extract_users(contacts: dict):
    users = []
    groups = []
    contacts_items = set()
    if contacts.get('users') is not None and isinstance(contacts.get('users'), list):
        users = contacts['users']
    if contacts.get('groups') is not None and isinstance(contacts.get('groups'), list):
        groups = contacts['groups']

    for user in users:
        contacts_items.add(user)
    for group in groups:
        group_item = GroupContactConfig.objects.get_group(name=group)
        for user in get_group_members(group_item):
            contacts_items.add(user)

    return contacts_items


def get_group_members(group: dict):
    if group is not None and group.config is not None \
            and group.config.get('members') is not None and isinstance(group.config['members'], list):
        return group.config['members']

    return []
