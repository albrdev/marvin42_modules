from enum import IntEnum
from collections import namedtuple
import struct
from modules.networking import PacketID

class CommandID(IntEnum):
    MOTORSPEED      = 2
    MOTORSETTINGS   = 3

PacketMotorSpeed = namedtuple('PacketMotorSpeed', ['speed_left', 'speed_right'])
PacketMotorSpeed.FORMAT = '!ii'
PacketMotorSpeed.SIZE = struct.calcsize(PacketMotorSpeed.FORMAT)

PacketMotorSettings = namedtuple('PacketMotorSettings', ['stop_distance'])
PacketMotorSettings.FORMAT = '!i'
PacketMotorSettings.SIZE = struct.calcsize(PacketMotorSettings.FORMAT)
