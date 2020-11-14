import re
from .config_loader import load_file
from .GenericLoader import GenericLoader


class CommandsLoader(GenericLoader):

    commands = []
    name_re = re.compile('^[a-zA-Z_][a-zA-Z0-9_-]*[a-zA-Z0-9]+$')
    required_fields = [
        'name',
        'cmd',
    ]

    def __init__(self, base_path=None):
        super().__init__(base_path=base_path)

    def load(self):
        self.commands = []
        self.config_files.clear()
        command_names = []

        self.get_config_files()
        for full_path in self.config_files:
            cur_config = load_file(full_path)
            if cur_config is None:
                raise Exception('Commands Error in {}'.format(full_path))
            items = cur_config.get('commands')
            if items is None or not isinstance(items, list):
                raise Exception('{} - commands is not an array'.format(full_path))

            for command in items:
                self.check_required(command)
                if not self.name_re.match(command['name']):
                    raise Exception('Command name {} must be of {}'.format(
                        command['name'], self.name_re.pattern))
                self.check_already_exists(command['name'], command_names)
                command_names.append(command['name'])
                self.commands.append(command)

        print('Loading commands from {} Completed: {} commands'.format(self.BASE_PATH, len(self.commands)))
        return self.commands
