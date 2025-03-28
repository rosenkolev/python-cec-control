import cec_control.cec_lib as cec_lib
import time
from typing import Literal

class Cec:
    @staticmethod
    def find_cec_devices():
        paths = cec_lib.find_cec_devices()
        return list(map(Cec, paths))

    def __init__(self, path: str):
        self._path = path
        self._ref = None

    @property
    def opened(self) -> bool:
        return self._ref is not None and self._ref.isOpen()
    
    @property
    def is_active_cec(self) -> bool:
        return self._ref is not None and self._ref.info.caps > 0
    
    @property
    def is_registered(self) -> bool:
        return self._ref is not None and self._ref.info.logical_address > 0

    def open(self):
        if not self.opened:
            self._ref = cec_lib.open_cec(self._path)

    def close(self):
        if self.opened:
            cec_lib.close_cec(self._ref)

    def set_type(self, type: Literal['Unregistered', 'TV', 'Playback', 'Processor', 'Record', 'Audio', 'Tuner']):
        type_enum = cec_lib.CecDeviceType.__members__.get(type, None)

        return (
                self.opened and
                self._ref.can_set_logical_address and
                type_enum is not None and
                cec_lib.set_logical_address(self._ref, type_enum)
            )

    def devices(self):
        if self.is_registered:
            devs = cec_lib.detect_devices(self._ref)
            return list(map(CecDevice, devs))

        return None
    
    def monitor(self):
        monitor_ref = cec_lib.start_msg_monitor(self._ref)
        return CecMonitor(monitor_ref)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        result = self._path + "\n"
        if self.is_active_cec:
            prt = lambda x,y: f"    {x}: {y}\n"
            x = self._ref.info
            result += (
                prt("Adapter", x.adapter) +
                prt("Name", x.osd_name) +
                prt("Physical Address", x.physical_address_text) +
                "    Capabilities:\n"
            )

            if self._ref.can_transmit:
                result += (" " * 8) + "Transmit\n"
            if self._ref.can_set_logical_address:
                result += (" " * 8) + "Logical Address\n"

            result += (
                prt("Available Logical Address", x.available_logical_address) +
                prt("Logical Addresses Count", x.logical_address)
            )

        return result

class CecDevice:
    def __init__(self, dev):
        self._dev = dev

    def __repr__(self):
        return f"Device {self._dev.physical_address}"

class CecMonitor:
    def __init__(self, mref):
        self._ref = mref
    
    def wait_for_msgs(self, seconds=10, max_events=10):
        start_time = time.monotonic()  # Use monotonic for accurate timing
        events = []  # Store collected events

        while (time.monotonic() - start_time) < seconds and max_events > 0:
            ev = cec_lib.deque_msg(self._ref)
            if ev.disconnected:
                print("disconnected")
                continue
             
            has_msg = ev.success
            print(f". {time.monotonic() - start_time} sec, {max_events} events, {"YES" if has_msg else "NO"}")

            if has_msg:
                events.append(ev)
                max_events -= 1  # Decrement count

        return events  # Return collected events
    
