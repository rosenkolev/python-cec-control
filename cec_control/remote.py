import uinput
import logging

DEFAULT_KEYMAP= {
    'LEFT': uinput.KEY_LEFT,
    'UP': uinput.KEY_UP,
    'RIGHT': uinput.KEY_LEFT,
    'DOWN': uinput.KEY_DOWN,
    'SELECT': uinput.KEY_ENTER,
    'BACK': uinput.KEY_ESC,
}

class CecRemote:
    @staticmethod
    def create_device(keymap: dict[str,]):
        keys = []
        for value in keymap.values():
            keys.append(value)
    
        return uinput.Device(keys)

    def __init__(self, keymap = DEFAULT_KEYMAP):
        self.device = CecRemote.create_device(keymap)
        self.keymap = keymap

    def emit(self, key_code: str):
        key = key_code.upper()
        if key in self.keymap:
            logging.debug('key = ' + key)
            self.device.emit(self.keymap.get(key),0)

    def close(self):
        self.device.destroy()
        logging.debug('udevice closed')
