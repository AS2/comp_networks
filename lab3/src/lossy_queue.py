from random import random


class LossyQueue:
    def __init__(self, loss_chance=0.0):
        self._loss_chance = min(1.0, max(0.0, loss_chance))
        self._queue = []

    @property
    def loss_chance(self):
        return self._loss_chance

    @loss_chance.setter
    def loss_chance(self, loss_chance):
        self._loss_chance = min(1.0, max(0.0, loss_chance))

    def __len__(self):
        return len(self._queue)

    def __bool__(self):
        return bool(self._queue)

    def append(self, package):
        if random() >= self.loss_chance:
            self._queue.append(package)
            return True
        return False

    def pop(self):
        return self._queue.pop(0)

    def clear(self):
        self._queue.clear()
        
    def is_empty(self) -> bool:
        res = (len(self._queue) == 0)
        return res


