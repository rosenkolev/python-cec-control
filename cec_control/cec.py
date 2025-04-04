import logging
import time
from typing import Callable

import cec_control.cec_lib as cec_lib

from .cec_lib_types import (
    VENDORS,
    CecDeviceType,
    CecMessage,
    CecMessageType,
    CecNetworkDevice,
    CecNetworkDeviceType,
    CecPowerState,
    CecRef,
    CecUserControlKeys,
)


class CancellationToken:
    def __init__(self):
        self.is_running = True
        self.action = lambda: logging.warning("No cancellation action")

    @property
    def is_cancelled(self):
        return not self.is_running

    def cancel(self):
        if self.is_running:
            self.is_running = False
            self.action()


def to_kv_str(key: str, val: str, spaces=4, line=True):
    return (" " * spaces) + key + ": " + val + ("\n" if line else "")


class Cec:
    @staticmethod
    def find_cec_devices():
        paths = cec_lib.find_cec_devices()
        return list(map(Cec, paths))

    def __init__(self, path: str):
        self._path = path
        self._ref: CecRef | None = None

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

    def set_type(self, type: CecDeviceType):
        type_enum = cec_lib.CecDeviceType(type.value)
        return (
            self.opened
            and self._ref.can_set_logical_address
            and type_enum is not None
            and cec_lib.set_logical_address(self._ref, type_enum)
            and cec_lib.update_logical_address_info(self._ref)
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

            x = self._ref.info
            result += (
                to_kv_str("Adapter", x.adapter)
                + to_kv_str("Name", x.osd_name)
                + to_kv_str("Physical Address", x.physical_address_text)
                + "    Capabilities:\n"
            )

            if self._ref.can_transmit:
                result += (" " * 8) + "Transmit\n"
            if self._ref.can_set_logical_address:
                result += (" " * 8) + "Logical Address\n"

            result += (
                to_kv_str("Available Logical Address", x.available_logical_address)
                + to_kv_str("Logical Addresses Count", x.logical_address_count)
                + to_kv_str("Logical Address", x.logical_address)
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

    def check(self, seconds: int, max_count=1000000):
        self.last_check_elapsed = WaitCounter.ts() - self.start_time
        return self.last_check_elapsed < seconds or self.count < max_count

    def tick(self, sleep_sec=0):
        if sleep_sec > 0:
            time.sleep(sleep_sec)

        self.count += 1


class CecDevice:
    def __init__(self, dev):
        self._dev: CecNetworkDevice = dev
        self._phys_addr: int | None = None
        self._vendor_id: int | None = None

    @property
    def logical_address(self) -> int:
        return self._dev.device_id

    @property
    def physical_address(self) -> int:
        if self._phys_addr is None:
            self._phys_addr = cec_lib.get_net_dev_physical_addr(self._dev)

        return self._phys_addr

    @property
    def source_physical_address(self) -> int:
        return self._dev.source_phys_addr

    @property
    def vendor_id(self) -> int:
        if self._vendor_id is None:
            self._vendor_id = cec_lib.get_net_device_vendor_id(self._dev)

        return self._vendor_id

    @property
    def vendor_name(self) -> str:
        return VENDORS.get(self.vendor_id, "")

    @property
    def osd_name(self) -> str:
        return cec_lib.get_net_device_osd_name(self._dev)

    @property
    def power_state(self) -> CecPowerState:
        return cec_lib.get_net_dev_pwr_state(self._dev)

    @property
    def is_power_on(self):
        return self.power_state == CecPowerState.On

    @property
    def is_active(self) -> bool:
        return cec_lib.ping_net_dev(self._dev)

    @property
    def active_source(self) -> int:
        return cec_lib.get_net_dev_active_source_phys_addr(self._dev)

    @property
    def is_active_source_current_device(self) -> bool:
        self.active_source == self.source_physical_address

    def report_cec_active_source(self, addr=None):
        if addr is None:
            addr = self.source_physical_address

        return cec_lib.set_net_dev_active_source(self._dev, addr)

    def report_power_on(self) -> bool:
        return cec_lib.report_net_device_pwr_on(self._dev)

    def __repr__(self):
        type = CecNetworkDeviceType(self._dev.device_id)
        return (
            f"{type.name} ({type.value})"
            + to_kv_str("Name", self.osd_name)
            + to_kv_str("Physical Address", self.physical_address)
            + to_kv_str("Vendor", f"{self.vendor_id} ({self.vendor_name})")
            + to_kv_str("Power State", self.power_state)
            + to_kv_str("Active Source", self.active_source)
        )


MAX_TRACE_COUNT = 1000000


class CecController:
    @staticmethod
    def is_cec_message(msg: CecMessage | None):
        return (
            msg is not None
            and msg.has_event
            and (msg.has_message or msg.initial_state or msg.state_change_phys_addr > 0)
        )

    @staticmethod
    def print_message(msg: CecMessage):
        cec_val = "Message"
        if msg.initial_state:
            cec_val += "  Initial State\n"
        if msg.state_change:
            cec_val += f"  State changed PA: {msg.state_change_phys_addr}\n"
        if msg.has_message:
            type = (
                CecMessageType(msg.message_code)
                if msg.message_code in CecDeviceType
                else ""
            )
            cec_val += f"  Message {msg.message_code} ({type}) with status {msg.message_status}\n"
            cec_val += f"    from {msg.message_from} to {msg.message_to}"
        if msg.message_code == CecMessageType.SetStreamPath.value:
            cec_val += f"    Address: {msg.message_address}"
        if (
            msg.message_code == CecMessageType.UserControlPressed
            or msg.message_code == CecMessageType.UserControlReleased
        ):
            cec_val += f"    Key: {msg.message_address}"

        logging.info(cec_lib)

    def __init__(self, cec: Cec, token: CancellationToken = None):
        self._ref = cec._ref
        self._token = token if token is not None else CancellationToken()

    def wait_for_cec_message(
        self,
        seconds: int,
        handler: Callable[[CecMessage], bool | None],
        max_count=MAX_TRACE_COUNT,
    ) -> CecMessage | None:
        c = WaitCounter()
        while self._token.is_running and c.check(seconds, max_count):
            ev: CecMessage = cec_lib.get_msg(self._ref)
            if CecController.is_cec_message(ev) and handler(ev) is True:
                return ev

        return None

    def wait_for_message(self, type: CecMessageType, seconds: int):
        return self.wait_for_cec_message(
            seconds, lambda x: x.has_message and CecMessageType(x.message_code) == type
        )

    def wait_for_initial_state(self, seconds) -> CecMessage | None:
        return self.wait_for_cec_message(
            seconds,
            lambda x: (
                x.initial_state
                and x.state_change_phys_addr == self._ref.info.physical_address
            ),
        )

    def handle_input_activation(self, device: CecDevice):
        pwr_msg = self.wait_for_message(CecMessageType.GiveDevicePowerStatus, 1.5)
        if pwr_msg is not None:
            device.report_power_on()

        srm_msg = self.wait_for_message(CecMessageType.SetStreamPath, 1.5)
        if srm_msg is not None:
            device.report_cec_active_source()

    def handle_remote_pressed(self, seconds, fn: Callable[[CecUserControlKeys], None]):
        def on_message(msg: CecMessage):
            if msg.message_code == CecMessageType.UserControlPressed.value:
                fn(CecUserControlKeys(msg.message_command))

        self.wait_for_cec_message(seconds, on_message)

    def trace(self, seconds: int, max_count=MAX_TRACE_COUNT) -> None:
        self.wait_for_cec_message(seconds, CecController.print_message, max_count)
