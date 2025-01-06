import time

from base_logger import Logger
from lossy_queue import *
from resend_protocol_base import *
from primitives import *

class GBNPolicy(IResendBehaviour):
    def __init__(self, name, window_size, timeout = 0.1):
        self._window_size = window_size
        self._timeout = timeout
        self.logger = Logger(f'GBN "{name}"')
        
    def send_procedure(self, fs2r: LossyQueue, fr2s: LossyQueue, data_to_send : tp.List, logging: bool) -> None:
        if not data_to_send:
            data_to_send = None,
        current_index = 0
        approved_index = -1
        term_index = len(data_to_send) - 1
        begin_waiting = time.time()
        
        while approved_index < term_index:
            if time.time() - begin_waiting > self._timeout:
                begin_waiting = time.time()
                current_index = approved_index + 1
                continue
            
            if fr2s:
                msg = self.logger.channel_pop(fr2s, False)
                begin_waiting = time.time()
                if msg.message_idx == approved_index + 1 and msg.message_type == MsgType.ACK:
                    approved_index += 1
                else:
                    current_index = approved_index + 1
                continue
            
            if current_index <= min(approved_index + self._window_size, term_index):
                code = MsgType.TERM if current_index == term_index else MsgType.NONE
                package = Message(msg_idx=current_index, msg_type=code, msg_data=data_to_send[current_index])
                self.logger.channel_append(fs2r, package, logging)
                current_index += 1
                continue
                        
        return
        
    def recieve_procedure(self, fs2r: LossyQueue, fr2s: LossyQueue, result_data : tp.List, logging: bool) -> None:
        expected = 0
        data = []
        while True:
            if fs2r:
                msg = self.logger.channel_pop(fs2r, logging)
                if msg.message_idx == expected:
                    package = Message(msg_idx=msg.message_idx, msg_type=MsgType.ACK, msg_data=None)
                    self.logger.channel_append(fr2s, package, False)
                    expected += 1
                    if msg.message_data is not None:
                        data.append(msg.message_data)
                    if msg.message_type == MsgType.TERM:
                        result_data.append(data)
                        return
                else:
                    answer = 'expected {}, got {}'.format(expected, msg.message_idx)
                    package = Message(msg_idx=-1, msg_type=MsgType.ERR, msg_data=answer)
                    self.logger.channel_append(fr2s, package, False)
                continue
