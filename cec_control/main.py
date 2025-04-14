import logging
import sys
from argparse import ArgumentParser

from cec_control.cec_cli import CecCli
from cec_control.cec_lib_types import (
    CecDeviceType,
    CecNetworkDeviceType,
    CecUserControlKeys,
)
from cec_control.keyboard import UInputKeyboard


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
        CecCli.print()
        return

    control = CecCli(
        remote=UInputKeyboard(
            {
                CecUserControlKeys.Select: "KEY_ENTER",
                CecUserControlKeys.Back: "KEY_ESC",
                CecUserControlKeys.Up: "KEY_UP",
                CecUserControlKeys.Right: "KEY_RIGHT",
                CecUserControlKeys.Down: "KEY_DOWN",
                CecUserControlKeys.Left: "KEY_LEFT",
            }
        )
    )

    control.register_on_network_and_find_device(
        CecDeviceType.Playback, CecNetworkDeviceType.TV
    )
    control.start_monitoring_tv()


if __name__ == "__main__":
    main()
