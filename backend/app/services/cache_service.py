from collections import OrderedDict
from copy import deepcopy
from threading import Lock
from time import monotonic

class CacheService:
    def __init__(self, capacity=128, ttl=300):
        self.capacity, self.ttl = capacity, ttl
        self.values = OrderedDict()
        self.lock = Lock()

    def get(self, key):
        with self.lock:
            entry = self.values.get(key)
            if entry and entry[0] > monotonic():
                self.values.move_to_end(key)
                return deepcopy(entry[1])
            self.values.pop(key, None)

    def put(self, key, value):
        with self.lock:
            self.values[key] = (monotonic() + self.ttl, deepcopy(value))
            self.values.move_to_end(key)
            while len(self.values) > self.capacity:
                self.values.popitem(last=False)
