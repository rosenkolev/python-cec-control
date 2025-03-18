import subprocess
import logging
import re
import time
import threading

from typing import List, Callable
from collections import namedtuple

def get_logical_addr(val: str):
    match = re.search(r"Logical Address\s+:\s+(\d+)", val)
    return '0' if match is None else match.group(1)

def cec_register_as_playback(interface: str, name: str):
    result = subprocess.run(['cec-ctl', '-d' + interface, '--playback', '-o', name], capture_output=True, text=True)
    logging.debug(result.stdout)
    return get_logical_addr(result.stdout) == '4'

def cec_unregister(interface: str):
    logging.info('unregister')
    result = subprocess.run(['cec-ctl', '-d' + interface, '--unregistered'], capture_output=True, text=True)
    logging.debug(result.stdout)
    return get_logical_addr(result.stdout) == '15'

CommandInfo = namedtuple('CommandInfo', ['sender', 'command'])
CommandData = namedtuple('CommandData', ['key', 'value'])

class CECCommand:
    command: str = None
    sender: str = None
    key: str = None
    value: str = None

    @staticmethod
    def get_command_info(data: str) -> (CommandInfo | None):
        # examples
        # Received from TV to Playback Device 1 (0 to 4): USER_CONTROL_PRESSED (0x44):
        # Transmit from Playback Device 1 to TV (4 to 0):
        match = re.match(r"Received from (\w+) to [\w\s\d\(\)\_]+: ([\w\_]+)", data)
        return None if match is None else CommandInfo(match.group(1), match.group(2))
    
    @staticmethod
    def get_recieved_code(data: str) -> (bool | None):
        match = re.match(r"\s*CEC_RECEIVE returned (\d)", data)
        return None if match is None else match.group(1) == '0'
    
    @staticmethod
    def get_command_data(data: str) -> (CommandData | None):
        match = re.match(r"\s*([\w\-\_]+):\s*([\w\-\_]+)", data)
        return None if match is None else CommandData(match.group(1), match.group(2))

CEC_CMD=CECCommand()
CEC_COMMANDS = ['USER_CONTROL_PRESSED', 'USER_CONTROL_PRESSED']

def cec_parse(data: str, on_command: Callable[[CECCommand],None], addr: str):
    global CEC_CMD
    if CEC_CMD.command is None:
        if f"Event: State Change: PA: {addr}" in data:
            logging.info('Device ready to go')
            return

        info = CECCommand.get_command_info(data)
        if info is not None and info.command in CEC_COMMANDS:
            CEC_CMD.command = info.command
            CEC_CMD.sender = info.sender
        
        return
    
    success = CECCommand.get_recieved_code(data)
    if success is not None:
        if success is True:
            on_command(CEC_CMD)

        CEC_CMD = CECCommand()
        return

    result = CECCommand.get_command_data(data)
    if result is None:
        logging.error('Error data for command ' + CEC_CMD.command)
        logging.error(data)
        CEC_CMD = CECCommand()
    else:
        CEC_CMD.key = result.key
        CEC_CMD.value = result.value

def cec_track(device: str, name: str, addr: str, cec_version: str, on_command: Callable[[CECCommand],None]):
    cec_arg = '--cec-version-1.4' if cec_version != '2.0' else ''
    token = CancellationToken()
    run_subprocess_in_background(
        ['cec-ctl',
            '-d' + device, '-t0',
            '--playback', '-o', name,
            '-T', '-M',
            cec_arg,
            '--active-source', 'phys-addr=' + addr,
            '--report-power-status', 'pwr-state=0'],
        lambda line: cec_parse(line, on_command, addr),
        token
    )
    return token

### subprocess functions ###

class CancellationToken:
    def __init__(self):
        self._running = True
        self.action = lambda: logging.warning('No cancelation action')
        self.cancelled = lambda: logging.debug('Cancelled')
    
    def cancel(self):
        if self._running:
            self._running = False
            self.action();

    def is_cancelled(self):
        return self._running is False
    
    def trigger_cancelled(self):
        self.cancelled()

def run_subprocess_in_background(
        command: List[str],
        ondata: Callable[[str],None],
        cancellationToken: CancellationToken,
        wait_for_output_sec = 0.2):
    """Start a subprocess and continuously monitor the stdout of the process, until process is terminated.
    """
    logging.debug(' '.join(command))
    def exec(inner_command,inner_ondata,token: CancellationToken):
        process = subprocess.Popen(inner_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
        token.action = lambda: process.terminate()
        try:
            while True:
                if token.is_cancelled():
                    break

                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:  # Process has exited
                        break

                    time.sleep(wait_for_output_sec)
                    continue

                inner_ondata(line.strip())

        except KeyboardInterrupt:
            logging.info("Process interrupted.")
        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            token.trigger_cancelled()
    
    # Run the output reading in a separate thread
    thread = threading.Thread(target=exec, args=(command,ondata,cancellationToken,), daemon=True)
    thread.start()
