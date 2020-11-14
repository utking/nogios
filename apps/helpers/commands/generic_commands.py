class GenericCommandsHelper(object):

    DEST_PORT = 1811
    BUFFER_SIZE = 1024
    CONNECT_RETRIES = 10

    STATUS_MAP = {
        0: 'OK',
        1: 'WARNING',
        2: 'CRITICAL',
        3: 'UNKNOWN',
        4: 'BLOCKER',
    }

    def __init__(self):
        super().__init__()

    @staticmethod
    def prepare_command_object(command=None):
        if isinstance(command, str):
            return {'cmd': command}
        elif isinstance(command, dict):
            return command.copy()
        else:
            return None

    @staticmethod
    def get_arguments(command: dict = None):
        args = command.get('args')
        if not isinstance(args, list):
            args = []
        return args

    def send(self, host_name: str, command: dict):
        return False, 0
