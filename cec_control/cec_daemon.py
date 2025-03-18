import logging
import atexit
import signal
import sys
import threading

from argparse import ArgumentParser

from .cec_ctl import cec_register_as_playback, cec_unregister, cec_track, CECCommand
from .cec_compliance import run_cec_compliance
from .remote import CecRemote

class CecDaemon:
    @staticmethod
    def arg_parse():
        """Parge command arguments
        """
        parser = ArgumentParser()
        parser.add_argument('-d', '--device', dest='device', default="0",     help='Select device')
        parser.add_argument('-n', '--name',   dest='name',   default="Radxa", help='The name shown in the CEC network')
        parser.add_argument('--debug',        dest='level',  default=logging.INFO, help='Print debug messages', action='store_const', const=logging.DEBUG)

        return parser.parse_args()

    def __init__(self):
        args = CecDaemon.arg_parse()
        self.name = args.name
        self.interface = args.device
        self._remote = CecRemote()
        self._registered = False
        self._event = threading.Event()

        logging.basicConfig(stream=sys.stdout, level=args.level)

    def register(self):
        if cec_register_as_playback(self.interface, self.name):
            self._registered = True
            logging.info('Register as playback device')
        else:
            logging.warning('No CEC devices')
            self._exit()

    def select_device(self, type = 'TV'):
        data = run_cec_compliance(self.interface)
        devices = data.devices.values()
        if len(devices) > 0:
            logging.info(f"Found cec devices")
        
        self.phisical_address = data.address
        self.device = next((x for x in devices if x.status.upper() == 'ON' and x.type.upper() == type), None)
        if self.device is None:
            logging.warning(f"No active {type} device")
            self._exit()

    def start_monitor(self):
        token = cec_track(
            self.interface,
            self.name,
            self.phisical_address,
            self.device.cec_version,
            lambda command: self._on_command(command))
        
        token.cancelled = lambda: self._exit()

        # attach exit handlers
        def on_exit(*args):
            token.cancel()

        atexit.register(on_exit)
        signal.signal(signal.SIGTERM, on_exit)
        signal.signal(signal.SIGINT, on_exit)
        
    def run(self):
        self.register()        
        self.select_device()

        logging.info(f"Source {self.name} at /div/cec{self.interface} with address {self.phisical_address}")
        logging.info(f"Destination {self.device.type} support CEC={self.device.cec_version} with address {self.device.address}")
        
        self.start_monitor()
        self._run_loop()

    def _run_loop(self):
        try:
            while self._event.wait(5) is False:
                pass
        except KeyboardInterrupt:
            pass
        finally:
            logging.info('loop exited')

    def _on_command(self, command: CECCommand):
        if command.command == 'USER_CONTROL_PRESSED':
            self._remote.emit(command.value)

    def _exit(self, code = 0):
        self._remote.close()

        if self._registered:
            cec_unregister(self.interface)
            self._registered = False

        self._event.set()
        sys.exit(code)

def run():
    """ Run the daemon
    """
    daemon = CecDaemon()
    daemon.run()
