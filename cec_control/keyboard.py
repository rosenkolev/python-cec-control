import logging
from typing import ClassVar, Literal

import uinput

KeyName = Literal["KEY_LEFT", "KEY_UP", "KEY_RIGHT", "KEY_DOWN", "KEY_ENTER", "KEY_ESC"]
KeyMap = ClassVar[dict[str, KeyName]]

class Keyboard:
    def __init__(self, keymap: KeyMap):
        self.keymap = {v: getattr(uinput, v) for k, v in keymap.items() if hasattr(uinput, v)}
        self.device = uinput.Device(list(self.keymap.values()))

    def emit(self, key: str):
        if key in self.keymap:
            logging.debug("key = " + key)
            self.device.emit(self.keymap.get(key), 0)

    def close(self):
        self.device.destroy()
        logging.debug("udevice closed")
