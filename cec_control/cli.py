import atexit
import logging
import signal
import sys
from threading import Thread
from argparse import ArgumentParser

from cec_control.cec import (
    CancellationToken,
    Cec,
    CecController,
    CecDeviceType,
    CecNetworkDeviceType,
)
from cec_control.cec_lib_types import CecUserControlKeys
from cec_control.keyboard import Keyboard, KeyMap


class CecControl:
    def __init__(self):
        self.cec: Cec = None
        self.token = CancellationToken()

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

    def init(self):
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

    def start_monitoring_tv(self, keymap: KeyMap):
        if self.cec is None:
            logging.error("No active CEC device")
            return

        with self.cec as cec:
            tv = cec.create_device(CecNetworkDeviceType.TV)
            if not tv.is_active:
                logging.error("No active TV")
                return

            self.attach_on_process_exit()

            logging.info(f"{cec!r}")
            logging.info(f"{tv!r}")

            # logging.info("--------- TRACE ----------")
            # def threaded_function(cec, token):
            #     ctl2 = CecController(cec, token)
            #     ctl2.trace(60)

            # thread =  Thread(target = threaded_function, args = (cec, self.token,), daemon=True)
            # thread.start()
            # logging.info("--------- TRACE ----------")

            proxy = Keyboard(keymap)
            ctl = CecController(cec, self.token)
            while self.token.is_running:
                source = ctl.get_active_source(tv)
                logging.warning(f"AS: {source} == {cec.physical_address}")

                if not (tv.is_power_on and source == cec.physical_address):
                    logging.debug("Active source not on current device")
                    if ctl.wait_for_initial_state(30) is None:
                        continue

                    logging.debug("Handle input communication")
                    ctl.handle_input_activation(tv)
                else:
                    logging.info("Active source already set")

                if self.token.is_running:
                    break

                logging.info(f"active-source: {tv.is_active_source_current_device}")
                logging.debug("Start listening for remote presses")
                ctl.handle_remote_pressed(
                    3600, lambda key: proxy.emit(key.name)
                )  # 1 hour


def main():
    parser = ArgumentParser(description="CLI tool using C++ extension")
    parser.add_argument("-l", "--list", action="store_true", help="List devices")
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

    control = CecControl()
    control.init()
    control.start_monitoring_tv(
        keymap={
            CecUserControlKeys.Select.name: "KEY_ENTER",
            CecUserControlKeys.Back.name: "KEY_ESC",
            CecUserControlKeys.Up.name: "KEY_UP",
            CecUserControlKeys.Right.name: "KEY_RIGHT",
            CecUserControlKeys.Down.name: "KEY_DOWN",
            CecUserControlKeys.Left.name: "KEY_LEFT",
        }
    )


if __name__ == "__main__":
    main()
