import cec_lib
import time

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

    def open(self):
        if not self.opened:
            self._ref = cec_lib.open_cec(self._path)

    def close(self):
        if self.opened:
            cec_lib.close_cec(self._ref)

    def devices(self):
        devs = cec_lib.detect_devices(self._ref)
        return list(map(CecDevice, devs))
    
    def monitor(self):
        monitor_ref = cec_lib.start_msg_monitor(self._ref)
        return CecMonitor(monitor_ref)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        result = self._path
        if self.opened:
            x = self._ref.info
            result += "\n ".join([
                f"Adapter: {x.adapter}",
                f"Available Logical Address: {x.available_logical_address}",
                f"Logical Address: {x.logical_address}",
                f"Physical Address {x.physical_address}",
                "Capabilities:",
                f"  Transmit: {"YES" if self._ref.can_transmit else "NO"}",
                f"  Logical Address: {"YES" if self._ref.can_set_logical_address else "NO"}"
            ])

        return result

class CecDevice:
    def __init__(self, dev):
        self._dev = dev

    def __repr__(self):
        return f"Device {self._dev.physical_address}"

class CecMonitor:
    def __init__(self, mref):
        self._ref = mref
    
    def wait_for_msgs(self, seconds=10, max_events=5):
        start_time = time.monotonic()  # Use monotonic for accurate timing
        events = []  # Store collected events

        while (time.monotonic() - start_time) < seconds and max_events > 0:
            ev = cec_lib.deque_msg(self._ref)
            if ev:
                events.append(ev)
                max_events -= 1  # Decrement count

        return events  # Return collected events