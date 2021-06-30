import socket
import json
import time

from types import SimpleNamespace

from mcpacket import buffer

class Protocol:

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer = buffer.Buffer()
        self.buffer.set_client(self.client)

        self.open = False

        self.info = None
        self.player_max = -1
        self.player_count = -1
        self.favicon_data = None
        self.description = None
        self.player_list = []
        self.ping_time = -1

    def connect(self):
        if self.open:
            self.client.shutdown(1)
            self.buffer = buffer.Buffer()
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.buffer.set_client(self.client)

        self.client.connect((self.host, self.port))
        self._update_info()
        self.open = True

    def _update_info(self):
        self.info = self.get_server_info()
        self.player_max = self.info.players.max
        self.player_count = self.info.players.online
        if hasattr(self.info, 'favicon'):
            self.favicon_data = self.info.favicon
        self.description = self.info.description
        if hasattr(self.info.players, 'sample'):
            self.player_list = self.info.players.sample

    def send_buffer(self, buffer):
        self.client.send(buffer._buf)

    def send_data(self, data):
        self.client.send(data)

    def send_packet(self, buffer):
        self.send_buffer(buffer.create_packet())

    def send_handshake(self, next_state=1, version=4):
        buf = buffer.Buffer()
        buf.pack_byte(0)
        buf.pack_varint(version)
        buf.pack_string(self.host)
        buf.pack_short(self.port)
        buf.pack_varint(next_state)
        self.send_packet(buf)

    def recv_buffer(self, length):
        data = self.client.recv(length)
        self.buffer.pack_bytes(data)

    def send_request(self):
        self.send_data(b"\x01\x00")

    def send_ping(self):
        now = time.perf_counter_ns() // 1000000
        buf = buffer.Buffer()
        buf.pack_byte(0x09)
        buf.pack_byte(0x01)
        buf.pack_long(now)
        self.send_packet(buf)

    def get_server_info(self):
        self.send_handshake(1)
        self.send_request()

        size = self.buffer.unpack_varint()
        pid = self.buffer.unpack_varint()

        response_text = self.buffer.unpack_string()
        response = json.loads(response_text, object_hook=lambda d: SimpleNamespace(**d))

        self.send_ping()
        size = self.buffer.unpack_varint()
        pid = self.buffer.unpack_varint()
        ping_time = self.buffer.unpack_long()
        
        self.ping_time = ping_time // 1000000

        return response

