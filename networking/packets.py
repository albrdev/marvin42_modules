"""
@author: albrdev
@email: albrdev@gmail.com
@date: 2019-05-14
"""

from enum import IntEnum
from collections import namedtuple
import struct

class PacketID(IntEnum):
    """
    Enum base class for packet ID:s
    """
    FALSE           = 0
    TRUE            = 1

#PacketHeader = namedtuple('PacketHeader', ['header_checksum', 'data_checksum', 'type', 'size']) # Future suggestions of packet header structure
PacketHeader = namedtuple('PacketHeader', ['type', 'size']) # Current packet header structure
PacketHeader.FORMAT = '!BH' # Binary data format: Network byte order, Header type (1 byte), Data size value (2 bytes)
PacketHeader.SIZE = struct.calcsize(PacketHeader.FORMAT) # Calculates size of the above fields (3 bytes)
