import datetime
import threading
from typing import Callable

import usb

from py_dream_cheeky import DreamCheekyThread, EventType, DreamCheekyEvent

BUTTON_VENDOR_ID = 0x1d34
BUTTON_PRODUCT_ID = 0x000d


def find_button_devices():
    return list(usb.core.find(find_all=True, idVendor=BUTTON_VENDOR_ID, idProduct=BUTTON_PRODUCT_ID))


class ButtonEventType(EventType):
    BUTTON_PRESS = "press"
    BUTTON_RELEASE = "release"
    BUTTON_CLICK = "click"
    BUTTON_HOLD = "hold"
    BUTTON_DOUBLE_CLICK = "double click"
    LID_OPEN = "lid open"
    LID_CLOSE = "lid close"


class DreamCheekyButtonThread(DreamCheekyThread):
    """A DreamCheekyButtonThread detects lid/button events for a single button device.

    :param device: A USB button device to monitor.  If None, then the first USB button device in the system is used.
    :param hold_duration: The duration in milliseconds to generate a DreamCheeky.BUTTON_HOLD event (default 1000).
    :param event_handler: A function to be called asynchronously when lid and button events are generated (default None)
    :param enqueue_events: If True, then ButtonEvents are added to the event queue (default False).
    """
    def __init__(
            self,
            device: usb.core.Device = None,
            event_handler: Callable[[DreamCheekyEvent], None] = None,
            enqueue_events: bool = False,
            hold_duration: int = 1000
    ):
        super().__init__(device, event_handler, enqueue_events)

        self.running = False

        self.read_timeout = 100
        self.hold_duration = datetime.timedelta(milliseconds=hold_duration)
        self.double_click_delay = datetime.timedelta(milliseconds=300)

        self.interface = None
        self.endpoint = None

    def init(self):
        if self.device is None:
            self.device = usb.core.find(idVendor=BUTTON_VENDOR_ID, idProduct=BUTTON_PRODUCT_ID)
        if self.device is None:
            raise RuntimeError('Device not found')

        if self.device.is_kernel_driver_active(0):
            self.device.detach_kernel_driver(0)

        config = self.device.get_active_configuration()
        self.interface = config[(0, 0)]

        self.endpoint = usb.util.find_descriptor(
            self.interface,
            custom_match=lambda e: (usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
        )

        self.running = True

    def run(self):
        self.init()

        previous_lid_open = previous_button_pressed = False
        hold_detected = False
        last_press_time = last_click_time = datetime.datetime.fromtimestamp(0)

        while self.running:
            try:
                lid_open, button_pressed = self.read_button_data()
                now = datetime.datetime.now()

                ################################################################################
                # Lid events
                if lid_open and not previous_lid_open:
                    self.handle_event(ButtonEventType.LID_OPEN)
                if not lid_open and previous_lid_open:
                    self.handle_event(ButtonEventType.LID_CLOSE)

                ################################################################################
                # Button events

                # Detect long hold
                if button_pressed and previous_button_pressed:
                    if not hold_detected and now - last_press_time >= self.hold_duration:
                        hold_detected = True
                        self.handle_event(ButtonEventType.BUTTON_HOLD)

                # Detect single click and double click
                if not button_pressed and previous_button_pressed:
                    # if now - last_press_time < self.hold_duration:
                    if not hold_detected:
                        if now - last_click_time < self.double_click_delay:
                            self.handle_event(ButtonEventType.BUTTON_DOUBLE_CLICK)
                        else:
                            self.handle_event(ButtonEventType.BUTTON_CLICK)
                        last_click_time = now

                if button_pressed and not previous_button_pressed:
                    self.handle_event(ButtonEventType.BUTTON_PRESS)
                    last_press_time = now
                if not button_pressed and previous_button_pressed:
                    self.handle_event(ButtonEventType.BUTTON_RELEASE)

                previous_lid_open, previous_button_pressed = lid_open, button_pressed
                if not button_pressed:
                    hold_detected = False

            except usb.core.USBError as error:
                if 'Operation timed out' in error.args:
                    continue

        usb.util.release_interface(self.device, self.interface)
        self.device.attach_kernel_driver(0)

    def read_button_data(self):
        """ Returns (is_lid_open: bool, is_button_pressed: bool).  Raises usb.core.USBError after self.read_timeout. """
        self.device.ctrl_transfer(
            0x21,
            0x09,
            0x00,
            0x00,
            [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02],
            0
        )

        data = self.device.read(
            self.endpoint.bEndpointAddress,
            self.endpoint.wMaxPacketSize,
            self.read_timeout
        )

        return bool(data[0] & 2), not data[0] % 2

    def stop(self):
        self.running = False

    def handle_event(self, event_type):
        if not isinstance(event_type, ButtonEventType):
            raise ValueError('event_type must be a ButtonEvent')

        event = DreamCheekyEvent(self, self.device, event_type)

        if self.enqueue_events:
            self.event_queue.put_nowait(event)

        if self.event_handler is not None:
            t = threading.Thread(target=self.event_handler, args=(event,))
            t.start()

    def get_event_queue(self):
        return self.event_queue
