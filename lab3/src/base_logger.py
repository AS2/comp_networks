import enum
from lossy_queue import LossyQueue
from primitives import Message

class StatsEnum(enum.Enum):
    msg_derived = 'derived'
    msg_lost = 'lost'
    msg_popped = 'popped'


class Logger:
    def __init__(self, name : str):
        self.name = name
        self.stats = {}
        self.clear_stats()

    def clear_stats(self) -> None:
        self.stats = {stat: 0 for stat in StatsEnum}

    def channel_pop(self, channel : LossyQueue, need_print : bool=True) -> Message:
        package = channel.pop()
        self.stats[StatsEnum.msg_popped] += 1
        if need_print:
            print('[{}] popped {}'.format(self.name, package.message_data))
        return package

    def channel_append(self, channel : LossyQueue, package : Message, need_print : bool=True) -> None:
        result = channel.append(package)
        result = StatsEnum.msg_derived if result else StatsEnum.msg_lost
        self.stats[result] += 1
        if need_print:
            print('[{}] appended {} ({})'.format(self.name, package.message_data, result.value))
