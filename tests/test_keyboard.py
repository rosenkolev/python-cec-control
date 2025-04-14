from cec_control.cec_lib_types import CecUserControlKeys
from cec_control.keyboard import UInputKeyboard, uinput


def test__UInputKeyboard_should_init():
    keyboard = UInputKeyboard(dict({CecUserControlKeys.Up: "KEY_UP"}))

    assert keyboard.keys == ["U_KEY_UP"]
    uinput.Device.assert_called_once_with(["U_KEY_UP"])
