import enum
import time

from base_logger import Logger
from lossy_queue import *
from resend_protocol_base import *
from primitives import *

class Status(enum.Enum):
    ACTIVE = enum.auto()
    OUTDATED = enum.auto()
    DERIVED = enum.auto()


class NodeInfo:
    def __init__(self, status=Status.OUTDATED):
        self.status = status
        self.timestamp = time.time()


class SRPolicy(IResendBehaviour):
    def __init__(self, name, window_size, timeout = 0.1):
        self._window_size = window_size
        self._timeout = timeout
        self.logger = Logger(f'SRP "{name}"')
        
    def send_procedure(self, fs2r: LossyQueue, fr2s: LossyQueue, data_to_send : tp.List, logging: bool) -> None:
        data_len = len(data_to_send)
        term_index = data_len - 1
        approved = 0
        window_size = min(self._window_size, data_len)
        nodes = {i: NodeInfo() for i in range(window_size)}

        while approved < data_len:
            if fr2s:
                msg = self.logger.channel_pop(fr2s, logging)
                approved += 1
                nodes[msg.message_idx].status = Status.DERIVED

            for node in nodes.values():
                if time.time() - node.timestamp > self._timeout and node.status != Status.DERIVED:
                    node.status = Status.OUTDATED

            keys = list(nodes.keys())
            for index in keys:
                assert len(nodes) == window_size
                max_key = max(nodes.keys())
                code = MsgType.TERM if index == term_index else MsgType.NONE
                if nodes[index].status == Status.OUTDATED:
                    nodes[index].timestamp = time.time()
                    nodes[index].status = Status.ACTIVE
                    package = Message(msg_idx=index, msg_type=code, msg_data=data_to_send[index])
                    self.logger.channel_append(fs2r, package, logging)
                elif nodes[index].status == Status.DERIVED:
                    if max_key < term_index:
                        del nodes[index]
                        nodes[max_key + 1] = NodeInfo()
        
        return
        
    def recieve_procedure(self, fs2r: LossyQueue, fr2s: LossyQueue, result_data : tp.List, logging: bool) -> None:
        data = {}
        data_array = []
        term_flag = False
        while True:
            if fs2r:
                msg = self.logger.channel_pop(fs2r, logging)
                if msg.message_type == MsgType.TERM:
                    term_flag = True
                data[msg.message_idx] = msg.message_data
                package = Message(msg_idx=msg.message_idx, msg_type=MsgType.ACK, msg_data=None)
                self.logger.channel_append(fr2s, package, logging)
                
                if term_flag and sorted(list(data.keys())) == list(range(len(data))):
                    break

        data_array = [None] * (max(data.keys()) + 1)
        for key in data.keys():
            data_array[key] = data[key]
        result_data.append(data_array)
