"""
@author: albrdev
@email: albrdev@gmail.com
@date: 2019-05-14
"""

from enum import IntEnum
from collections import namedtuple
import struct
from modules.networking import PacketID

class CommandID(IntEnum):
    """
    Enum subclass for packet ID:s
    """
    MOTORSETTINGS   = 2
    MOTORSPEED      = 3
    MOTORSTOP       = 4

PacketMotorSpeed = namedtuple('PacketMotorSpeed', ['speed_left', 'speed_right']) # Motor speed packet structure
PacketMotorSpeed.FORMAT = '!bb' # Binary data format: Network byte order, Speed (left motor) (1 byte), Speed (right motor) (1 byte)
PacketMotorSpeed.SIZE = struct.calcsize(PacketMotorSpeed.FORMAT) # Calculates size of the above fields (2 bytes)

PacketMotorSettings = namedtuple('PacketMotorSettings', ['stop_distance']) # Motor settings packet structure
PacketMotorSettings.FORMAT = '!H' # Binary data format: Network byte order, Stop distance (2 bytes)
PacketMotorSettings.SIZE = struct.calcsize(PacketMotorSettings.FORMAT) # Calculates size of the above fields (2 bytes)
