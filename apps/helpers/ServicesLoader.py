from .config_loader import load_file
from .GenericLoader import GenericLoader
import re


class ServicesLoader(GenericLoader):

    services = []
    name_re = re.compile('^[a-zA-Z_][a-zA-Z0-9_-]*[a-zA-Z0-9]+$')
    required_fields = [
        'name',
        'hosts',
        'command',
        'contacts'
    ]

    def __init__(self, base_path=None, contacts=None, commands=None, time_periods=None):
        super(ServicesLoader, self).__init__(base_path=base_path, contacts=contacts,
                                             commands=commands, time_periods=time_periods)

    def load(self):
        self.services = []
        self.config_files.clear()
        service_names = []

        self.get_config_files()
        for full_path in self.config_files:
            has_multiple_items = True
            cur_config = load_file(full_path)
            if cur_config is None:
                raise Exception('Service Error in {}'.format(full_path))
            services = cur_config.get('services')
            if services is None or not isinstance(services, list):
                has_multiple_items = False
            if not has_multiple_items and cur_config.get('service') is None:
                raise Exception('{} - no services defined in the file'.format(full_path))
            elif not has_multiple_items:
                services = [cur_config.get('service')]
            for service in services:
                if service is None:
                    raise Exception('{} has an improperly configured service'.format(full_path))
                if not self.name_re.match(service['name']):
                    raise Exception('Command name {} must be of {}'.format(
                        service['name'], self.name_re.pattern))
                self.check_required(service)
                self.check_already_exists(service['name'], service_names)
                if self.__validate_command(service) and self.validate_contacts(service) and\
                        self.validate_time_periods(service):
                    service_names.append(service['name'])
                    self.services.append(service)

        print('Loading services from {} Completed: {} services'.format(self.BASE_PATH, len(self.services)))
        return self.services

    def __validate_command(self, service=None):
        if service['command'] not in self.commands:
            raise Exception('{} {} does not exist for service {}'.format(
                type(self).__name__, service['command'], service['name']))
        return True
