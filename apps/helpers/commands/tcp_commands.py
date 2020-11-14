import socket
import ssl
import json
from django.conf import settings
from .generic_commands import GenericCommandsHelper


class TcpCommandsHelper(GenericCommandsHelper):

    def __init__(self, port=1812):
        super().__init__()
        self.DEST_PORT = port

    def send(self, host_name: str, command: dict):
        dest = host_name
        data = ''.encode()
        command_object = self.prepare_command_object(command=command)
        if command_object is not None:
            message = '{}'.format(json.dumps(command_object)).encode()
            with socket.create_connection((dest, self.DEST_PORT)) as sock:
                with ssl.wrap_socket(
                        sock,
                        ciphers=settings.SSL_CIPHER_FILTER,
                        ssl_version=ssl.PROTOCOL_TLSv1_2,
                ) as conn:
                    try:
                        conn.send(message)
                        data = conn.recv(self.BUFFER_SIZE)
                    except Exception as e:
                        print('TCP_AGENT::SOCK_ERROR - Dest {}:{}; {}'.format(dest, self.DEST_PORT, str(e)))
                        raise Exception(e)

        return len(data) > 0, data.decode()


if __name__ == '__main__':
    s = TcpCommandsHelper()
    s.send('127.0.0.1', command={
                           'cmd': 'echo',
                           'args': [1, 2],
                           'host_name': 'srv-dev-001.local.domain',
                           'service_name': 'check_users',
                       })
