import enum as _enum
import queue as _queue
import threading as _threading
from abc import ABC as _ABC
from typing import Callable as _Callable

import usb as _usb


class DreamCheekyThread(_threading.Thread, _ABC):
    def __init__(
            self,
            device: _usb.core.Device,
            event_handler: _Callable[['DreamCheekyEvent'], None] = None,
            enqueue_events: bool = False
    ):
        super().__init__()
        self.device = device
        self.event_handler = event_handler
        self.enqueue_events = enqueue_events
        self.event_queue = _queue.Queue(128)


class EventType(_enum.Enum):
    pass


class DreamCheekyEvent(_ABC):
    def __init__(self, thread: DreamCheekyThread, device: _usb.core.Device, event_type: EventType):
        self.__thread = thread
        self.__device = device
        self.__type = event_type

    @property
    def thread(self):
        return self.__thread

    @property
    def device(self):
        return self.__device

    @property
    def type(self):
        return self.__type