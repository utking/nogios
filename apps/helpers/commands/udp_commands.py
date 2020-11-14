import socket
import json
from .generic_commands import GenericCommandsHelper


class UdpCommandsHelper(GenericCommandsHelper):

    def __init__(self, port=1811):
        super().__init__()
        self.DEST_PORT = port

    def send(self, host_name: str, command: dict):
        dest = host_name
        bytes_sent = 0
        command_object = self.prepare_command_object(command=command)
        if command_object is not None:
            message = '{}'.format(json.dumps(command_object)).encode()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            bytes_sent = sock.sendto(message, (dest, self.DEST_PORT))
        return bytes_sent > 0, bytes_sent
