import cec_control.cec_lib as cec_lib
import time
from enum import Enum
from typing import Literal

class CecNetworkDeviceType(Enum):
    TV = 0
    RecordingDevice1 = 1
    RecordingDevice2 = 2
    Tuner1 = 3
    PlaybackDevice1 = 4
    AudioSystem = 5
    Tuner2 = 6
    Tuner3 = 7
    PlaybackDevice2 = 8
    RecordingDevice3 = 9
    Tuner4 = 10
    PlaybackDevice3 = 11
    Backup1 = 12
    Backup2 = 13
    Specific = 14
    Unregistered = 15

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
        return self._ref is not None and self._ref.info.logical_address_count > 0
    
    @property
    def physical_address(self) -> int:
        return self._ref is not None and self._ref.info.physical_address

    def open(self):
        if not self.opened:
            self._ref = cec_lib.open_cec(self._path)

    def close(self):
        if self.opened:
            cec_lib.close_cec(self._ref)
            self._ref = None

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

    def create_device(self, dev_type: CecNetworkDeviceType):
        if self.is_registered:
            logical_address = dev_type.value
            return CecDevice(cec_lib.create_net_device(self._ref, logical_address))

    def monitor(self):
        monitor_ref = cec_lib.start_msg_monitor(self._ref)
        return CecMonitor(monitor_ref)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        return self._path

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
                prt("Logical Addresses Count", x.logical_address_count) +
                prt("Logical Address", x.logical_address)
            )

        return result

class WaitCounter:
    @staticmethod
    def ts():
        return time.monotonic()

    def __init__(self):
        self.start_time = WaitCounter.ts()
        self.last_check_elapsed = None
        self.count = 0
    
    def check(self, seconds: int, max_count = 1000000):
        self.last_check_elapsed = WaitCounter.ts() - self.start_time
        return self.last_check_elapsed < seconds or self.count < max_count

    def tick(self, sleep_sec = 0):
        if sleep_sec > 0:
            time.sleep(sleep_sec)

        self.count += 1

class CecDevice:
    def __init__(self, dev):
        self._dev = dev
        self._phys_addr = None

    @property
    def logical_address(self) -> int:
        return self._dev.device_id

    @property
    def physical_address(self) -> int:
        if self._phys_addr is None:
            self._phys_addr = cec_lib.get_net_dev_physical_addr(self._dev)
        
        return self._phys_addr

    @property
    def vendor_id(self) -> int:
        return cec_lib.get_net_device_vendor_id(self._dev)
    
    @property
    def osd_name(self) -> str:
        return cec_lib.get_net_device_osd_name(self._dev)

    @property
    def power_state(self):
        return cec_lib.get_net_dev_pwr_state(self._dev)

    @property
    def is_power_on(self):
        self.power_state == cec_lib.CecPowerState.ON

    @property
    def is_active(self):
        return cec_lib.ping_net_dev(self._dev)

    @property
    def active_source(self) -> int:
        return cec_lib.get_net_dev_active_source_phys_addr(self._dev)

    @active_source.setter
    def active_source(self, value: int) -> None:
        if not cec_lib.set_net_dev_active_source(self._dev, value):
            raise Exception(f"{self.label} active source not set to addr {value}")

    def __repr__(self):
        return self._dev.device_id

class CecMonitor:
    def __init__(self, mref):
        self._ref = mref
    
    def wait_for_msgs(self, seconds=10, max_events=10):
        c = WaitCounter()
        events = []  # Store collected events

        while c.check(seconds, max_count=max_events):
            ev = cec_lib.deque_msg(self._ref)
            if ev.disconnected:
                print("disconnected")
                continue
             
            has_msg = ev.success
            print(f". {c.last_check_elapsed} sec, {max_events} events, {"YES" if has_msg else "NO"}")

            if has_msg:
                events.append(ev)
                c.tick()

        return events  # Return collected events
    
