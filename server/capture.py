import pigpio
import time
import threading
from server.decoder import decode
from server.event_bus import bus
from datetime import datetime

D0_PIN = 17
D1_PIN = 27
TIMEOUT_MS = 50

class WiegandCapture:
    def __init__(self, pi):
        self.pi = pi
        self.bits = []
        self.timer = None

        pi.set_mode(D0_PIN, pigpio.INPUT)
        pi.set_mode(D1_PIN, pigpio.INPUT)
        pi.set_pull_up_down(D0_PIN, pigpio.PUD_UP)
        pi.set_pull_up_down(D1_PIN, pigpio.PUD_UP)

        pi.callback(D0_PIN, pigpio.FALLING_EDGE, self._d0_pulse)
        pi.callback(D1_PIN, pigpio.FALLING_EDGE, self._d1_pulse)

        print("Wiegand capture running on GPIO 17 (D0) and GPIO 27 (D1)")

    def _d0_pulse(self, gpio, level, tick):
        self.bits.append('0')
        self._reset_timer()

    def _d1_pulse(self, gpio, level, tick):
        self.bits.append('1')
        self._reset_timer()

    def _reset_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(TIMEOUT_MS / 1000, self._process)
        self.timer.start()

    def _process(self):
        if not self.bits:
            return

        bit_string = ''.join(self.bits)
        self.bits = []

        print(f"Raw bits received: {bit_string} ({len(bit_string)} bits)")

        scan = decode(bit_string)
        scan["timestamp"] = datetime.now().isoformat()
        bus.publish(scan)


def start_capture():
    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: Could not connect to pigpiod. Is it running?")
        return
    capture = WiegandCapture(pi)
    print("Capture daemon started. Waiting for card scans...")
