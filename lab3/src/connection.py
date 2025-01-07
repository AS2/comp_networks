from threading import Thread, Lock, Barrier
from copy import copy

from resend_protocol_base import *
from SR import *
from GBN import *
from lossy_queue import *

class Connection:
    def protocol_stratagy(self, resend_protocol: ResendProtocol, window_size:int, timeout:float, name:str):
        if resend_protocol == ResendProtocol.GBN:
            self._protocol = GBNPolicy(name=name, window_size=window_size, timeout=timeout)
        elif resend_protocol == ResendProtocol.SRP:
            self._protocol = SRPolicy(name=name, window_size=window_size, timeout=timeout)
        return
    
    def __init__(self, name:str, resend_protocol: ResendProtocol, window_size:int, timeout:float, loss_chance:float):
        self._channel_main = LossyQueue(loss_chance=loss_chance)
        self._channel_back = LossyQueue()
        self._name = name
        
        self.protocol_stratagy(resend_protocol, window_size, timeout, name)
        
        self._get_timeout = 1.0
        self._sender_thread = None
        self._receiver_thread = None
        self._msg_flag = False
        self._result_list = []
        self.mutex = Lock()

    def push(self, data=None, logging:bool=False):
        self.mutex.acquire()
        
        self._channel_main.clear()
        self._channel_back.clear()
        self._sender_thread = Thread(target=self._protocol.send_procedure,
                                     args=(self._channel_main, self._channel_back, data, logging))
        self._receiver_thread = Thread(target=self._protocol.recieve_procedure,
                                       args=(self._channel_main, self._channel_back, self._result_list, logging))
        self._sender_thread.start()
        self._receiver_thread.start()
        self._sender_thread.join()
        self._receiver_thread.join()
        self._msg_flag = True
        #print(self._msg_flag)
        self.mutex.release()

    def get(self):
        start = time.time()
        result = None
        while True:
            self.mutex.acquire()
            if self._msg_flag:
                self._msg_flag = False
                result = copy(self._result_list)
                self._result_list.clear()
                self.mutex.release()
                break
            if time.time() - start >= self._get_timeout:
                self.mutex.release()
                return result
            self.mutex.release()
            time.sleep(0.1)
        #print(f'{self._name}: popped {self._result[0]}')
        return result
