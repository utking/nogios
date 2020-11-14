from subprocess import Popen
import shlex
from json import dumps
from django.conf import settings
from .generic_commands import GenericCommandsHelper


class CheckNrpeCommandsHelper(GenericCommandsHelper):

    def __init__(self):
        super().__init__()
        self.CHECK_NRPE_PATH = settings.CHECK_NRPE_PATH

    def execute_command(self, host_name: str, command: str, args: list):
        command_prefix = '{} -H {} -c {}'.format(self.CHECK_NRPE_PATH, host_name, command)
        if isinstance(args, list) and len(args) > 0:
            command_prefix = '{} -a {}'.format(
                command_prefix,
                ' '.join(list(map(lambda x: str(x), args)))
            )
        command_array = shlex.split('{}'.format(command_prefix))
        ret = Popen(command_array, universal_newlines=True)
        cmd_stdout, cmd_stderr = ret.communicate()
        code = ret.returncode

        return code, cmd_stdout, cmd_stderr

    def send(self, host_name: str, command: dict):
        ret_code, stdout, stderr = self.execute_command(
            host_name=host_name,
            command=command['cmd'],
            args=command['args'])
        output = ''
        if stdout is not None:
            output = output + stdout
        if stderr is not None:
            output = output + stderr
        status = self.STATUS_MAP.get(ret_code)
        if status is None:
            status = 'WARNING'
        return ret_code == 0, dumps({
            'name': command['service_name'],
            'host_name': command['host_name'],
            'status_code': status,
            'ret_code': ret_code,
            'output': output,
        })


if __name__ == '__main__':
    ch = CheckNrpeCommandsHelper()
    ok, resp = ch.send(
        host_name='127.0.0.1',
        command={
            'cmd': 'check_users',
            'args': [1, 2],
            'host_name': 'srv-dev-001.local.domain',
            'service_name': 'check_users',
        }
    )
    print(ok, resp)
