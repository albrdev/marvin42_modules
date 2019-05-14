from enum import IntEnum
from collections import namedtuple
import struct

class PacketID(IntEnum):
    FALSE           = 0
    TRUE            = 1

#PacketHeader = namedtuple('PacketHeader', ['header_checksum', 'data_checksum', 'type', 'size'])
PacketHeader = namedtuple('PacketHeader', ['type', 'size'])
PacketHeader.FORMAT = '!BH'
PacketHeader.SIZE = struct.calcsize(PacketHeader.FORMAT)
