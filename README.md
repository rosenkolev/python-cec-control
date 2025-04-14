# CEC Control

Control your linux machine by a connected device (TV) HDMI-CEC.

Then you press the UP, DOWN, LEFT, RIGHT, SELECT, BACK keys on the TV remote the PC will respond with appropriate keyboard command.

The py package contain 2 libraries that handle CEC communication and a command cline tool `cec-control`.

## Usage

### Install

```shell
pip install cec-control
```

### Usage

```shell
# list all CEC devices
cec-control --list

# run host control
cec-control
```

#### Use as a module

```python
from cec_control import CecCli, UInputKeyboard, CecUserControlKeys, CecDeviceType, CecNetworkDeviceType

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
```

## Packages

### cec_control.cec_lib

A C++ extension package wraps Linux Kernel CEC functionality.

#### Methods

* [`find_cec_devices()`](/docs/cec_control__cec_lib.md#find_cec_devices) - Find CEC devices in /dev/cec*.
* `open_cec(device_path: str)` - Open CEC device for read.
* `close_cec(cec: CecRef)` - Closes CEC device for read.
* `set_logical_address(cec: CecRef, type: CecDeviceType)` - Set logical address to the current device.
* `update_logical_address_info(cec: CecRef)` - Update CEC logical address information.
* `detect_devices(cec: CecRef)` - Detects network devices by a CEC ref.
* `create_net_device(cec: CecRef, id: int)` - Create a network device.
* `ping_net_dev(dev: CecNetworkDevice)` - Ping a network device.
* `get_net_dev_physical_addr(dev: CecNetworkDevice)` - Get network device physical address.
* `get_net_device_vendor_id(dev: CecNetworkDevice)` - Get network device vendor id.
* `get_net_device_osd_name(dev: CecNetworkDevice)` - Get network device OSD name.
* `get_device_power_status(dev: CecNetworkDevice)` - Get network device power state.
* `send_msg_set_stream_path(dev: CecNetworkDevice, phys_addr: int)` - Set stream path.
* `send_msg_active_source(dev: CecNetworkDevice, phys_addr: int)` - Get network device active source physical address.
* `send_msg_request_active_source(dev: CecNetworkDevice)` - Request network device active source.
* `send_msg_report_power_status(dev: CecNetworkDevice)` - Report power on state to device.
* `get_msg_init(cec: CecRef)` - Start listening to a CEC ref.
* `get_msg(cec: CecRef)` - Get a CEC message.

> [!NOTE]  
> For models take a look at the [cec_control.cec_lib -> Models DOC](/docs/cec_control__cec_lib.md#models)

### cec_control

A python wrapper around the low level methods and a control to track incoming keys and send them to the OS keyboard.

### Classes

* `Cec` - A CEC device wrapper (eg. `/dev/cec0`). It can open/close the device for operation. register on network, etc.
* `CecDevice` - Another CEC device on the CEC network (eg. TV, Recorder, AudioSystem). Gets the other device address, power state, etc.
* `CecController` - A class that can track CEC messages on the network and automatically respond to CEC requests like `GIVE_DEVICE_POWER`.
* `CecCli` - Class that is used by the CLI tool to initiate CEC communication with a TV and track remote keys.

## Development

<!-- cspell:ignore pybind, rosenkolev -->

### Setup virtual environment

```shell
# setup venv
python3 -m venv .venv
# activate in current shell/terminal
source .venv/bin/activate
# install requirements
pip3 install -r .\requirements.txt
# register paths for the C++ binder
python -m pybind11 --includes
```

### Build and run 

```
pip install . && cec-control
```

### ROADMAP

* [ ] Add a CLI command for the PC to WAKE the TV
* [ ] Add some more commands from PC to TV

## Source code

The source code is located at [rosenkolev/python-cec-control](https://github.com/rosenkolev/python-cec-control)
