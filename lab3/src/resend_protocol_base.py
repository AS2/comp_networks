import typing as tp
import enum
from abc import ABC, abstractmethod

from lossy_queue import LossyQueue

class IResendBehaviour(ABC):
    def __init__():
        pass
    
    @abstractmethod
    def send_procedure(fs2r: LossyQueue, fr2s: LossyQueue, data_to_send : tp.List, logging: bool) -> None:
        """Basic string"""
        
    @abstractmethod
    def recieve_procedure(fs2r: LossyQueue, fr2s: LossyQueue, result_data : tp.List, logging: bool) -> None:
        """Basic string"""
        
class ResendProtocol(enum.Enum):
    SRP = enum.auto()
    GBN = enum.auto()
