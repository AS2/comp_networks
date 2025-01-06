from collections import namedtuple
from enum import IntEnum

class MsgType(IntEnum):
    NONE = 0
    ACK = 1
    DATA = 2
    TERM = 3
    ERR = 4
    
    
class Message():
    message_type = 0
    message_data = None
    message_idx = -1
    
    def __init__(self, msg_type: MsgType, msg_data, msg_idx: int):
        self.message_data = msg_data
        self.message_type = msg_type
        self.message_idx = msg_idx
        return
    
class FilePart():
    part_idx = -1
    data = None
    
    def __init__(self, data, idx):
        self.data = data
        self.part_idx = idx

class FileMetadata():
    data = None
    size = -1
    parts_cnt = -1

    def __init__(self, data, parts_cnt : int):
        self.data = data
        self.size = len(data)
        self.parts_cnt = parts_cnt
        return
