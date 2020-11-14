from .config_loader import load_file
from .GenericLoader import GenericLoader


class HostsLoader(GenericLoader):

    hosts = []
    required_fields = [
        'name',
        'address',
        'contacts',
    ]

    def __init__(self, base_path=None, contacts=None, time_periods=None):
        super().__init__(base_path=base_path, contacts=contacts, time_periods=time_periods)

    def load(self):
        self.hosts = []
        self.config_files.clear()
        host_names = []

        self.get_config_files()
        for full_path in self.config_files:
            has_multiple_items = True
            cur_config = load_file(full_path)
            if cur_config is None:
                raise Exception('Host Error in {}'.format(full_path))
            hosts = cur_config.get('hosts')
            if hosts is None or not isinstance(hosts, list):
                has_multiple_items = False
            if not has_multiple_items and cur_config.get('host') is None:
                raise Exception('{} - no hosts defined in the file'.format(full_path))
            elif not has_multiple_items:
                hosts = [cur_config.get('host')]
            for host in hosts:
                if host is None:
                    raise Exception('{} has an improperly configured host'.format(full_path))
                self.check_required(host)
                self.check_already_exists(host['name'], host_names)
                if self.validate_contacts(host) and self.validate_time_periods(host):
                    host_names.append(host['name'])
                    self.hosts.append(host)

        print('Loading hosts from {} Completed - {} hosts'.format(self.BASE_PATH, len(self.hosts)))
        return self.hosts
