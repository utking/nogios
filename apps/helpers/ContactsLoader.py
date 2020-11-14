from apps.helpers.GenericLoader import GenericLoader
from apps.helpers.config_loader import load_file


class ContactsLoader(GenericLoader):

    users = []
    groups = []
    required_fields = [
        'name',
    ]
    user_required_fields = [
        'channel',
        'destination',
    ]
    group_required_fields = [
        'members',
    ]

    def __init__(self, base_path=None):
        super().__init__(base_path=base_path)

    def load(self):
        self.groups = []
        self.users = []
        self.config_files.clear()
        group_names = []
        user_names = []

        self.get_config_files()
        for full_path in self.config_files:
            cur_config = load_file(full_path)
            if cur_config is None:
                raise Exception('Contacts Error in {}'.format(full_path))
            users = cur_config.get('users')
            groups = cur_config.get('groups')

            if groups is None and users is None:
                raise Exception('{} - neither users nor groups are defined in the file'.format(full_path))
            if users is not None:
                for user in users:
                    self.check_required(user)
                    self.__user_check_required(user)
                    self.check_already_exists(user['name'], user_names)
                    user_names.append(user['name'])
                    self.users.append(user)
            if groups is not None:
                for group in groups:
                    self.check_required(group)
                    self.__group_check_required(group)
                    self.check_already_exists(group['name'], group_names)
                    group_names.append(group['name'])
                    self.groups.append(group)

        print('Loading contacts from {} Completed: {} users and {} groups'.format(
            self.BASE_PATH, len(self.users), len(self.groups)))
        return self.users, self.groups

    def __user_check_required(self, config=None):
        for field in self.user_required_fields:
            if config.get(field) is None:
                raise Exception('User {} has no required field "{}"'.format(
                    config['name'],
                    field))
        return False

    def __group_check_required(self, config=None):
        for field in self.group_required_fields:
            if config.get(field) is None:
                raise Exception('Group {} has no required field "{}"'.format(
                    config['name'],
                    field))
        return False
