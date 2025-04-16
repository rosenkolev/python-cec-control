import atexit
import logging
import signal
from typing import Protocol

from cec_control.cec import (
    CancellationToken,
    Cec,
    CecController,
    CecDeviceType,
    CecNetworkDeviceType,
    Wait,
)
from cec_control.cec_lib_types import (
    CecMessage,
    CecMessageType,
    CecPowerState,
    CecUserControlKeys,
)
from cec_control._utils import to_enum


class OsKeyboardController(Protocol):
    def __init__(self, keymap: dict[CecUserControlKeys, str]):
        pass

    def emit_key(key: CecUserControlKeys) -> None:
        pass


class CecCli:
    def __init__(self, remote: OsKeyboardController):
        self.cec: Cec = None
        self.token = CancellationToken()
        self.remote = remote

    @staticmethod
    def print():
        interfaces = Cec.find_cec_devices()
        info = ""
        for cec in interfaces:
            with cec:
                info += "\n" + repr(cec)
                if cec.is_registered:
                    info += "\n    Network Devices:\n\n"
                    devices = cec.devices()
                    for dev in devices:
                        info += f"    {dev!r}"

        logging.info(info)

    def register_on_network_and_find_device(
        self, cec_type: CecDeviceType, device_type: CecNetworkDeviceType
    ):
        interfaces = Cec.find_cec_devices()
        for cec in interfaces:
            with cec:
                if not cec.is_active_cec:
                    continue

                if not cec.is_registered and not cec.set_type(cec_type):
                    continue

                if not cec.is_registered:
                    logging.error("Failed to register as CEC device")
                    continue

                logging.info("Registered as CEC device")
                device = cec.create_device(device_type)
                if device.is_active:
                    self.cec = cec
                    break

    def attach_on_process_exit(self):
        def on_exit(*args):
            self.token.cancel()

        atexit.register(on_exit)
        signal.signal(signal.SIGTERM, on_exit)
        signal.signal(signal.SIGINT, on_exit)

    def start_monitoring_tv(self):
        if self.cec is None:
            logging.error("No active CEC device")
            return

        with self.cec as cec:
            tv = cec.create_device(CecNetworkDeviceType.TV)
            if not tv.is_active:
                logging.error("No active TV")
                return

            self.attach_on_process_exit()

            logging.debug(f"{cec!r}")
            # logging.debug(f"{tv!r}")

            ctl = CecController(cec, self.token)
            while self.token.is_running:

                if not tv.power_state == CecPowerState.On:
                    logging.debug("Device is OFF")
                    Wait.for_fn(60, lambda: tv.is_power_on, self.token, sleep_sec=1)
                else:
                    logging.debug("Device is ON")
                    ctl.handle_cec_messages(
                        1800,
                        tv,
                        [CecMessageType.UserControlPressed],
                        self._handle_pressed_msg,
                    )  # 30 min

    def _handle_pressed_msg(self, msg: CecMessage, type: CecMessageType):
        key = to_enum(msg.message_command, CecUserControlKeys, None)
        if key is not None:
            self.remote.emit_key(key)
