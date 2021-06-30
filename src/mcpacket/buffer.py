import struct

class Buffer:

    def __init__(self, data=b""):
        self._buf = data
        self._pos = 0
        self._client = None

    def pack(self, fmt, value):
        self._buf += struct.pack(fmt, value)

    def pack_byte(self, value):
        self.pack('>B', value)

    def pack_long(self, value):
        self.pack('>L', value)

    def pack_short(self, value):
        self.pack('>H', value)

    def pack_buffer(self, buffer):
        self._buf += buffer._buf

    def pack_bytes(self, byte_string):
        self._buf += byte_string

    def pack_string(self, string):
        string_bytes = bytes(string, 'utf-8')
        byte_length = len(string_bytes)
        buf = Buffer()
        buf.pack_varint(byte_length)
        buf.pack_bytes(string_bytes)
        self.pack_buffer(buf)

    def pack_varint(self, value):
        if value < 0:
            value += 1 << 32
        buf = Buffer()
        for i in range(10):
            b = value & 0x7F
            value >>= 7
            buf.pack_byte(b | (0x80 if value > 0 else 0))
            if value == 0:
                break
        self.pack_buffer(buf)

    def set_client(self, client):
        self._client = client

    def at(self, index):
        return self._buf[index]

    def read(self, length):
        data = b""
        for i in range(self._pos, length+self._pos):
            if self._client:
                data += self._client.recv(1)
            else:
                data += self.at(i)
        self._pos += length
        return data

    def unpack(self, fmt):
        data = self.read(struct.calcsize(fmt))
        return struct.unpack(fmt, data)[0]

    def unpack_byte(self):
        return self.unpack('>B')

    def unpack_long(self):
        return self.unpack('>L')

    def unpack_varint(self):
        value = 0
        for i in range(10):
            b = self.unpack_byte()
            value |= (b & 0x7F) << i * 7
            if b & 0x80 != 128:
                break
        return value

    def unpack_string(self):
        length = self.unpack_varint()
        data = self.read(length)
        return data.decode('utf-8')

    def create_packet(self):
        buf = Buffer()
        buf.pack_varint(len(self._buf))
        buf.pack_bytes(self._buf)
        return buf
