from .generic_commands import GenericCommandsHelper
from subprocess import Popen, PIPE
import shlex
from json import dumps


class LocalShellCommandsHelper(GenericCommandsHelper):

    TIMEOUT = 30

    def __init__(self):
        super().__init__()

    def send(self, host_name: str, command: dict):
        data = ''.encode()

        command_object = self.prepare_command_object(command=command)
        cmd = command_object.get('cmd')
        args = self.get_arguments(command_object)
        host_name = command_object.get('host_name')
        service_name = command_object.get('service_name')

        if cmd is None or not isinstance(cmd, str) or cmd.strip() == '':
            print('No command to execute')
            return None
        if host_name is None or not isinstance(host_name, str) or host_name.strip() == '':
            print('Unknown hostname')
            return None

        host_name = host_name.strip()
        command = (cmd.strip() + ' ' + ' '.join(list(map(lambda x: str(x), args))))
        command = command.replace('$HOST$', host_name)
        if command is not None and isinstance(command, str):
            ret_code, stdout, stderr = self.execute_command(command)
            status = self.STATUS_MAP.get(ret_code)
            if status is None:
                status = 'WARNING'

            data = dumps({
                'host_name': host_name,
                'name': service_name,
                'status_code': status,
                'ret_code': ret_code,
                'output': '{}{}'.format('\n'.join(stdout), '\n'.join(stderr)),
            }).encode()

        return len(data) > 0, data.decode()

    def execute_command(self, raw_cmd: str):
        commands = raw_cmd.split('|')
        stdin = None
        prev_cmd = None
        if len(commands) > 0:
            for command_line in commands:
                command_array = shlex.split(command_line)
                if stdin is None:
                    ret = Popen(command_array, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                else:
                    ret = Popen(command_array, stdin=stdin, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                    prev_cmd.stdout.close()
                stdin = ret.stdout
                prev_cmd = ret
            try:
                cmd_stdout, cmd_stderr = ret.communicate(timeout=self.TIMEOUT)
                code = ret.returncode
            except:
                cmd_stdout, cmd_stderr = '', 'timed out, {}s'.format(self.TIMEOUT)
                code = 2
            return code, '', cmd_stderr.split('\n')
        return -1, [], []
