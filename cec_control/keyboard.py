import logging

import uinput

from cec_control.cec_lib_types import CecUserControlKeys


class UInputKeyboard:
    def __init__(self, keymap: dict[CecUserControlKeys, str]):
        self.keymap = dict({})
        self.keys = list()
        for k, v in keymap.items():
            if hasattr(uinput, v):
                key = getattr(uinput, v)
                self.keymap.setdefault(k, key)
                self.keys.append(key)

        self.device = uinput.Device(self.keys)

    def emit_key(self, key: CecUserControlKeys):
        ev = self.keymap.get(key)
        if ev is not None:
            self.device.emit_click(ev)

    def close(self):
        self.device.destroy()
        logging.debug("uinput device closed")
