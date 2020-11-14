from . import config_loader


class GenericLoader(object):
    BASE_PATH = None
    required_fields = None
    config_files = set()
    contacts = {'users': [], 'groups': []}
    commands = []
    time_periods = []

    def __init__(self, base_path=None, contacts=None, commands=None, time_periods=None):
        self.BASE_PATH = base_path
        if contacts is not None:
            self.contacts = contacts
        if commands is not None:
            self.commands = commands
        if time_periods is not None and isinstance(time_periods, list):
            self.time_periods = list(map(lambda x: x.get('name'), time_periods))

        if not isinstance(self.required_fields, list):
            raise Exception('Required fields list must be provided', type(self).__name__)

    def get_config_files(self):
        self.config_files = config_loader.ConfigLoader(self.BASE_PATH).get_config_files()

    def check_required(self, config=None):
        for field in self.required_fields:
            if config.get(field) is None:
                if field == 'name':
                    name = config
                else:
                    name = config['name']
                raise Exception('{} {} has no required field "{}"'.format(
                    type(self).__name__,
                    name,
                    field))
        return False

    def check_already_exists(self, item, items):
        if item in items:
            raise Exception('{} {} is already in the config'.format(type(self).__name__, item))

    def validate_contacts(self, config=None):
        contacts = config.get('contacts')

        if contacts.get('users') is not None:
            checked_users = set()
            for user in contacts['users']:
                if user not in self.contacts['users']:
                    raise Exception('User {} does not exist for {} {}'.format(
                        user, type(self).__name__, config['name']))
                if user in checked_users:
                    raise Exception('Duplicate user {} for {} {}'.format(
                        user, type(self).__name__, config['name']))
                checked_users.add(user)
        elif contacts.get('groups') is not None:
            checked_groups = set()
            for group in contacts['groups']:
                if group not in self.contacts['groups']:
                    raise Exception('Group {} does not exist for {} {}'.format(
                        group, type(self).__name__, config['name']))
                if group in checked_groups:
                    raise Exception('Duplicate group {} for {} {}'.format(
                        group, type(self).__name__, config['name']))
                checked_groups.add(group)
        else:
            raise Exception('{} {} does not have contacts configured'.format(
                type(self).__name__, config['name']))

        return True

    def validate_time_periods(self, config=None):
        time_period = config.get('time_period')

        if time_period is not None:
            if time_period not in self.time_periods:
                raise Exception('Time period {} does not exist for {} {}'.format(
                    time_period, type(self).__name__, config['name']))

        return True
