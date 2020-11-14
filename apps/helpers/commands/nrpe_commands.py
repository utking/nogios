import socket
import ssl
from json import dumps
from django.conf import settings
from .generic_commands import GenericCommandsHelper

import array
from struct import *

'''
# 'v3_packet' C structure from NRPE code
    typedef struct _v3_packet {
        int16_t		packet_version;     # h
        int16_t		packet_type;        # h
        u_int32_t	crc32_value;        # I
        int16_t		result_code;        # h
        int16_t		alignment;          # h
        int32_t		buffer_length;      # i
        char		buffer[1];          # c
    } v3_packet;

# 'v2_packet' C structure from NRPE code
    typedef struct _v2_packet {
        int16_t		packet_version;     # h
        int16_t		packet_type;        # h
        u_int32_t	crc32_value;        # I
        int16_t		result_code;        # h
        char		buffer[MAX_PACKETBUFFER_LENGTH];    # c
    } v2_packet;
'''


class NrpeCommandsHelper(GenericCommandsHelper):

    NRPE_PACKET_VERSION_2 = 2
    NRPE_PACKET_VERSION_3 = 3
    QUERY_PACKET = 1
    RESPONSE_PACKET = 2
    MAX_PACKETBUFFER_LENGTH = 1024

    V3_PACKET_FORMAT = b'h h I h h i %ds'
    V2_PACKET_FORMAT = b'h h I h %ds' % (MAX_PACKETBUFFER_LENGTH + 2)

    def __init__(self, port=5666, packet_version=None):
        super().__init__()
        self.CRC32_TABLE = array.array('L')
        self.DEST_PORT = port
        self.__generate_crc32_table()
        if packet_version is None:
            self.packet_version = settings.NRPE_PACKET_VERSION
        self.packet_version = packet_version

    def __calculate_crc32(self, buffer: bytes):
        crc = 0xFFFFFFFF
        buffer_size = len(buffer)
        for current_index in range(0, buffer_size):
            this_char = int(buffer[current_index])
            crc = ((crc >> 8) & 0x00FFFFFF) ^ self.CRC32_TABLE[(crc ^ this_char) & 0xFF]
        return crc ^ 0xFFFFFFFF

    def __generate_crc32_table(self):
        poly = 0xEDB88320
        for i in range(0, 256):
            self.CRC32_TABLE.append(0)
        for i in range(0, 256):
            crc = i
            for j in range(8, 0, -1):
                if crc & 1 > 0:
                    crc = (crc >> 1) ^ poly
                else:
                    crc = crc >> 1
            self.CRC32_TABLE[i] = crc

    def send(self, host_name: str, command: dict):
        dest = host_name
        data = b''
        command_object = self.prepare_command_object(command=command)

        if command_object is not None:

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
            command = (cmd.strip() + '!' + '!'.join(list(map(lambda x: str(x), args)))).encode()

            packet = self.__prepare_data(nrpe_packet_version=self.packet_version, cmd=command)
            try:
                with socket.create_connection((dest, self.DEST_PORT)) as sock:
                    with ssl.wrap_socket(
                        sock,
                        ciphers="ADH-AES256-SHA:@SECLEVEL=0",
                        ssl_version=ssl.PROTOCOL_TLSv1_2,
                    ) as conn:
                        conn.send(packet)
                        resp = conn.recv(self.BUFFER_SIZE)
                        ret_code, output = self.__parse_response(resp=resp)
                        conn.close()

                        status = self.STATUS_MAP.get(ret_code)
                        if status is None:
                            status = 'WARNING'

                        data = dumps({
                            'host_name': host_name,
                            'name': service_name,
                            'status_code': status,
                            'ret_code': ret_code,
                            'output': output.strip(),
                        }).encode()

            except Exception as e:
                print('NRPE_AGENT::SOCK_ERROR - Dest {}:{}; {}'.format(host_name, self.DEST_PORT, str(e)))

        return len(data) > 0, data.decode()

    def __prepare_data(self, nrpe_packet_version: int, cmd: bytes):
        cmd_len = len(cmd.decode())
        al = 0
        version = 'v{}'.format(nrpe_packet_version)
        if version == 'v3':
            packet_struct = Struct(self.V3_PACKET_FORMAT % cmd_len)
            packet = packet_struct.pack(socket.htons(self.NRPE_PACKET_VERSION_3),
                                        socket.htons(self.QUERY_PACKET),
                                        0, al, 0,
                                        socket.htonl(cmd_len), cmd)
        else:
            packet_struct = Struct(self.V2_PACKET_FORMAT)
            packet = packet_struct.pack(socket.htons(self.NRPE_PACKET_VERSION_2),
                                        socket.htons(self.QUERY_PACKET),
                                        socket.htonl(0), 0, cmd)

        crc32 = self.__calculate_crc32(buffer=packet)

        if version == 'v3':
            packet = packet_struct.pack(socket.htons(self.NRPE_PACKET_VERSION_3),
                                        socket.htons(self.QUERY_PACKET),
                                        socket.htonl(crc32), al, 0,
                                        socket.htonl(cmd_len), cmd)
        else:
            packet = packet_struct.pack(socket.htons(self.NRPE_PACKET_VERSION_2),
                                        socket.htons(self.QUERY_PACKET),
                                        socket.htonl(crc32), 0, cmd)
        return packet

    def __parse_response(self, resp: bytes):
        s = Struct(b'!h h I h')
        (p_ver, p_type, p_crc32, p_result) = s.unpack(resp[:10])
        out = b''
        if p_ver == self.NRPE_PACKET_VERSION_2:
            s = Struct('{}s'.format(len(resp) - 10))
            (out,) = s.unpack(resp[10:])
        elif p_ver == self.NRPE_PACKET_VERSION_3:
            s = Struct('!h l')
            (p_align, p_buf_len) = s.unpack(resp[10:16])
            s = Struct('{}s'.format(p_buf_len))
            (out,) = s.unpack(resp[16:])

        return p_result, out.decode().strip('\x00')  # \x00 must be stripped explicitly


if __name__ == '__main__':
    ch = NrpeCommandsHelper(packet_version=2)
    ok, resp = ch.send(host_name='127.0.0.1',
                       command={
                           'cmd': 'check_users',
                           'args': [1, 2],
                           'host_name': 'srv-dev-001.local.domain',
                           'service_name': 'check_users',
                       })
    print(ok, resp)
