import enum
import typing as tp
from random import random
from threading import Lock

class MessageCode(enum.Enum):
    OK = enum.auto()
    LOST = enum.auto()

class Message():
    def __init__(self, info_number:int=-1, message_pos:int=-1, data:str="", status:MessageCode=MessageCode.OK):
        self.info_number = info_number
        self.message_pos = message_pos
        self.data = data
        self.status = status
        pass

class LossyMessageQueue():
    def __init__(self, lost_propability:float=0.0):
        self.queue = []
        self.lost_propability = lost_propability
        self.mutex = Lock()
        pass

    def is_empty(self) -> bool:
        self.mutex.acquire()
        res = (len(self.queue) == 0)
        self.mutex.release()
        return res

    def pop_message(self) -> Message:
        self.mutex.acquire()
        result = self.queue[0]
        self.queue.pop(0)
        self.mutex.release()
        return result

    def __is_lost(self, msg) -> Message:
        curr_pred = random()
        if (curr_pred <= self.lost_propability):
            msg.status = MessageCode.LOST
        return msg


    def push_message(self, msg:Message) -> None:
        self.mutex.acquire()
        modified_msg = self.__is_lost(msg)
        self.queue.append(msg)
        self.mutex.release()
