import logging
from typing import Callable

import cec_control.cec_lib as cec_lib
from cec_control._utils import CancellationToken, MemoryCache, Wait, to_enum

from .cec_lib_types import (
    VENDORS,
    CecDeviceType,
    CecMessage,
    CecMessageRxStatus,
    CecMessageTxStatus,
    CecMessageType,
    CecNetworkDevice,
    CecNetworkDeviceType,
    CecPowerState,
    CecRef,
    CecUserControlKeys,
)


def to_kv_str(key: str, val: str, spaces=4, line=True):
    return (" " * spaces) + key + ": " + val + ("\n" if line else "")


def addr_to_str(addr: int) -> str:
    return f"{addr >> 12}.{(addr >> 8) & 15}.{(addr >> 4) & 15}.{addr  & 15}"


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
                + to_kv_str(
                    "Physical Address",
                    f"{addr_to_str(x.physical_address)} ({x.physical_address})",
                )
                + "    Capabilities:\n"
            )

            if self._ref.can_transmit:
                result += (" " * 8) + "Transmit\n"
            if self._ref.can_set_logical_address:
                result += (" " * 8) + "Logical Address\n"

            result += (
                to_kv_str(
                    "Available Logical Address", x.available_logical_address.__str__()
                )
                + to_kv_str(
                    "Logical Addresses Count", x.logical_address_count.__str__()
                )
                + to_kv_str("Logical Address", x.logical_address.__str__())
            )

        return result


class CecDevice:
    def __init__(self, dev):
        self._data = MemoryCache()
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
        return self._data.get_or_set(
            "osd_name", lambda: cec_lib.get_net_device_osd_name(self._dev), ttl=0.5
        )

    @property
    def power_state(self) -> CecPowerState:
        status = self._data.get_or_set(
            "power_status", lambda: cec_lib.get_device_power_status(self._dev), ttl=0.5
        )

        logging.info(f"status: {status}")
        return to_enum(status, CecPowerState, CecPowerState.Unknown)

    @property
    def is_power_on(self):
        return self.power_state == CecPowerState.On

    @property
    def is_active(self) -> bool:
        return cec_lib.ping_net_dev(self._dev)

    def set_stream_path(self) -> bool:
        return cec_lib.send_msg_set_stream_path(self._dev, self.physical_address)

    def request_active_source(self) -> bool:
        return cec_lib.send_msg_request_active_source(self._dev)

    def report_active_source(self, addr=None) -> bool:
        if addr is None:
            addr = self.source_physical_address

        return cec_lib.send_msg_active_source(self._dev, addr)

    def report_power_on(self) -> bool:
        return cec_lib.send_msg_report_power_status(self._dev)

    def __repr__(self):
        type = CecNetworkDeviceType(self._dev.device_id)

        return (
            f"{type.name} ({type.value})\n"
            + to_kv_str("Name", self.osd_name)
            + to_kv_str("Physical Address", self.physical_address.__str__())
            + to_kv_str("Vendor", f"{self.vendor_id} ({self.vendor_name})")
            + to_kv_str("Power State", self.power_state.__str__())
        )


class CecController:
    @staticmethod
    def msg_to_str(msg: CecMessage):
        def addr_info(add):
            return f"{addr_to_str(add)} ({add})"

        cec_val = "\n"
        if msg.initial_state:
            cec_val += "  Initial State\n"
        if msg.state_change:
            cec_val += f"  State changed PA: {addr_info(msg.state_change_phys_addr)}\n"
        if msg.has_message:
            if msg.message_transmitted and msg.disconnected:
                cec_val += "  Device was disconnected."
                return cec_val

            s_code = msg.message_status
            status = (
                to_enum(s_code, CecMessageTxStatus, CecMessageTxStatus.Unknown)
                if msg.message_transmitted
                else to_enum(s_code, CecMessageRxStatus, CecMessageRxStatus.Unknown)
            )
            cec_val += "  " + ("Transmitted" if msg.message_transmitted else "Received")
            cec_val += f" {msg.message_code} with status {s_code} ({ status })\n"
            cec_val += f"    from {msg.message_from} to {msg.message_to}"

            if (
                msg.message_code == CecMessageType.SetStreamPath.value
                or msg.message_code == CecMessageType.ActiveSource.value
            ):
                cec_val += f"    Address: {msg.message_address}"
            if (
                msg.message_code == CecMessageType.UserControlPressed
                or msg.message_code == CecMessageType.UserControlReleased
            ):
                cec_val += f"    Key: {msg.message_address}"

        return cec_val

    def __init__(self, cec: Cec, token: CancellationToken = None):
        self._ref = cec._ref
        self._token = token if token is not None else CancellationToken()

    def wait_for_cec_message(
        self,
        seconds: int,
        handler: Callable[[CecMessage, CecMessageType], bool | None],
        show=False,
        all_msgs=False,
    ) -> CecMessage | None:
        if not cec_lib.get_msg_init(self._ref):
            logging.error("Failed to initialize")
            return None

        c = Wait(seconds)
        while self._token.is_running and c.waiting:
            ev: CecMessage = cec_lib.get_msg(self._ref)
            if ev is not None and (
                ev.has_event
                or (ev.has_message and (all_msgs or not ev.message_transmitted))
            ):
                type = to_enum(ev.message_code, CecMessageType, CecMessageType.Unknown)
                msg = f"{c!r}:{type}:{CecController.msg_to_str(ev)}"
                logging.info(msg) if show else logging.debug(msg)
                if handler(ev, type) is True:
                    return ev

        return None

    def wait_for_message(self, type: CecMessageType, seconds: int):
        return self.wait_for_cec_message(
            seconds, lambda x, msg_type: x.has_message and msg_type == type
        )

    def cycle_msg_until(self, seconds, device: CecDevice, type: CecMessageType):
        def on_message(msg: CecMessage, msg_type: CecDeviceType):
            if msg.has_message:
                match msg_type:
                    case CecMessageType.GiveDevicePowerStatus:
                        if not device.report_power_on():
                            logging.error("Unable to report power on")
                    case CecMessageType.SetStreamPath:
                        if not device.report_active_source():
                            logging.error("Unable to report active source")

            return msg_type == type

        return self.wait_for_cec_message(seconds, on_message)

    def handle_remote_pressed(
        self, seconds, fn: Callable[[CecUserControlKeys | None], None]
    ):
        def on_message(msg: CecMessage, msg_type: CecMessageType):
            if msg.has_message and msg_type == CecMessageType.UserControlPressed:
                fn(to_enum(msg.message_command, CecUserControlKeys))

        self.wait_for_cec_message(seconds, on_message)

    def get_active_source(self, device: CecDevice):
        logging.debug("request active source")
        if device.request_active_source():
            logging.debug("wait active source")
            next_msg = self.wait_for_cec_message(1.5, lambda x, _: x.initial_state)
            return None if next_msg is None else next_msg.state_change_phys_addr

    def trace(self, seconds: int) -> None:
        self.wait_for_cec_message(seconds, lambda x, _: False, show=True, all_msgs=True)
