import atexit
import logging
import signal
import sys

from argparse import ArgumentParser

from cec_control.cec import (
    CancellationToken,
    Cec,
    CecController,
    CecDeviceType,
    CecNetworkDeviceType,
    Wait,
)
from cec_control.cec_lib_types import CecMessageType, CecPowerState, CecUserControlKeys
from cec_control.keyboard import Keyboard


class CecControl:
    def __init__(self, keymap: dict):
        self.cec: Cec = None
        self.token = CancellationToken()
        self.remote = Keyboard(keymap)

    @staticmethod
    def print():
        interfaces = Cec.find_cec_devices()
        for cec in interfaces:
            with cec:
                print(repr(cec))
                if cec.is_registered:
                    print("    Network Devices:")
                    devices = cec.devices()
                    for dev in devices:
                        print(f"        - {dev!r}")

    def init_cec(self):
        """Find the TV"""
        interfaces = Cec.find_cec_devices()
        for cec in interfaces:
            with cec:
                if not cec.is_active_cec:
                    continue

                if not cec.is_registered and not cec.set_type(CecDeviceType.Playback):
                    continue

                if not cec.is_registered:
                    print("Failed to register as playback device")
                    continue

                print("Registered as playback device")
                device = cec.create_device(CecNetworkDeviceType.TV)
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
                    if not ctl.get_active_source(tv) == cec.physical_address:
                        ev = ctl.cycle_msg_until(30, tv, CecMessageType.SetStreamPath)
                        if ev is None:
                            logging.debug("No active source")
                            continue
                    else:
                        logging.debug("Active source already set")

                    if not self.token.is_running:
                        break

                    logging.debug("Start listening for remote presses")

                    ctl.handle_remote_pressed(
                        3600,
                        self._handle_key,
                    )  # 1 hour

    def _handle_key(self, key: CecUserControlKeys | None):
        if key is not None:
            self.remote.emit_key(key.name)


def main():
    parser = ArgumentParser(description="CLI tool using C++ extension")
    parser.add_argument("-l", "--list", action="store_true", help="List devices")
    parser.add_argument("-t", "--test", action="store_true", help="Test keyboard")
    parser.add_argument(
        "--debug",
        dest="level",
        action="store_const",
        default=logging.INFO,
        help="Print debug messages",
        const=logging.DEBUG,
    )
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=args.level)

    if args.list:
        CecControl.print()
        return

    control = CecControl(
        {
            CecUserControlKeys.Select.name: "KEY_ENTER",
            CecUserControlKeys.Back.name: "KEY_ESC",
            CecUserControlKeys.Up.name: "KEY_UP",
            CecUserControlKeys.Right.name: "KEY_RIGHT",
            CecUserControlKeys.Down.name: "KEY_DOWN",
            CecUserControlKeys.Left.name: "KEY_LEFT",
        }
    )

    control.init_cec()
    control.start_monitoring_tv()


if __name__ == "__main__":
    main()
