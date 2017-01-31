import enum
import queue
import threading
from typing import Callable

import usb


class DreamCheekyThread(threading.Thread):
    def __init__(
            self,
            device: usb.core.Device,
            event_handler: Callable[['DreamCheekyEvent'], None] = None,
            enqueue_events: bool = False
    ):
        super().__init__()
        self.device = device
        self.event_handler = event_handler
        self.enqueue_events = enqueue_events
        self.event_queue = queue.Queue(128)


class EventType(enum.Enum):
    pass


class DreamCheekyEvent:
    def __init__(self, thread: DreamCheekyThread, device: usb.core.Device, event_type: EventType):
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