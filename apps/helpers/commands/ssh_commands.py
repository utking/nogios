from .generic_commands import GenericCommandsHelper
from paramiko import SSHClient, AutoAddPolicy, ssh_exception
from django.conf import settings
from json import dumps
from time import sleep


class SshCommandsHelper(GenericCommandsHelper):

    def __init__(self, port=22):
        super().__init__()
        self.DEST_PORT = port

    def runs_multiple(self):
        return True

    def send(self, host_addr: str, command: dict, port=None, user='root'):
        ssh_port = self.DEST_PORT
        if port is not None:
            ssh_port = port

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
        command = cmd.strip() + ' ' + ' '.join(list(map(lambda x: str(x), args)))

        try:
            client = SSHClient()
            client.load_system_host_keys()
            client.load_host_keys(settings.SSH_KNOWN_HOSTS)
            client.set_missing_host_key_policy(AutoAddPolicy())

            attempt = 1
            while attempt < self.CONNECT_RETRIES:

                try:
                    client.connect(host_addr, port=ssh_port, username=user, banner_timeout=300,
                                   key_filename=settings.SSH_KEY_PATH, timeout=20,
                                   passphrase=settings.SSH_KEY_PASS_PHRASE)
                    break
                except ssh_exception.SSHException as e:
                    if str(e) == 'Error reading SSH protocol banner':
                        print(e)
                        attempt = attempt + 1
                        sleep(2)
                        continue
                    print('SSH transport is available!')
                    break

            stdin, stdout, stderr = client.exec_command(command=command, timeout=60)
            ret_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            output = output + stderr.read().decode('utf-8')
            status = self.STATUS_MAP.get(ret_code)
            if status is None:
                status = 'WARNING'

            data = dumps({
                'host_name': host_name,
                'name': service_name,
                'status_code': status,
                'ret_code': ret_code,
                'output': output,
            }).encode()

            stdin.close()
            stdout.close()
            stderr.close()

            client.close()
        except Exception as e:
            print('SSH Agent Error for {}'.format(host_addr), str(e))

        return len(data) > 0, data.decode()

    def send_multiple(self, host_addr: str, commands: list, port=None, user='root'):
        responses = []
        ssh_port = self.DEST_PORT
        if port is not None:
            ssh_port = port

        try:
            client = SSHClient()
            client.load_system_host_keys()
            client.load_host_keys(settings.SSH_KNOWN_HOSTS)
            client.set_missing_host_key_policy(AutoAddPolicy())

            attempt = 1
            while attempt < self.CONNECT_RETRIES:

                try:
                    client.connect(host_addr, port=ssh_port, username=user, banner_timeout=300,
                                   key_filename=settings.SSH_KEY_PATH, timeout=20,
                                   passphrase=settings.SSH_KEY_PASS_PHRASE)
                    break
                except ssh_exception.SSHException as e:
                    if str(e) == 'Error reading SSH protocol banner':
                        print(e)
                        attempt = attempt + 1
                        sleep(2)
                        continue
                    print('SSH transport is available!')
                    break

            for command in commands:
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
                command = cmd.strip() + ' ' + ' '.join(list(map(lambda x: str(x), args)))

                stdin, stdout, stderr = client.exec_command(command=command, timeout=60)
                ret_code = stdout.channel.recv_exit_status()
                output = stdout.read().decode('utf-8')
                output = output + stderr.read().decode('utf-8')
                status = self.STATUS_MAP.get(ret_code)
                if status is None:
                    status = 'WARNING'

                data = dumps({
                    'host_name': host_name,
                    'name': service_name,
                    'status_code': status,
                    'ret_code': ret_code,
                    'output': output,
                }).encode()

                responses.append((len(data) > 0, data.decode()))

                stdin.close()
                stdout.close()
                stderr.close()

            client.close()
        except Exception as e:
            print('SSH Agent Error for {}'.format(host_addr), str(e))

        return responses
