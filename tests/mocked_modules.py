import sys
from unittest.mock import Mock

sys.modules["cec_control.cec_lib"] = Mock()
sys.modules["cec_control.cec_lib"].find_cec_devices = Mock(return_value=list())
sys.modules["uinput"] = Mock()
sys.modules["uinput"].Device = Mock()
sys.modules["uinput"].KEY_UP = "U_KEY_UP"
