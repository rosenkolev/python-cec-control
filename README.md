# CEC Control

Control your linux machine by a connected device HDMI-CEC

The py package contain 2 libraries that handle CEC communication and a command cline tool `cec-control`.

## Packages

### cec_control.cec_lib

A C++ extension package what wrap Linux Kernel CEC functionality.

#### Methods

| Method |  |
|-|-|
| `find_cec_devices()` | Find CEC devices in /dev/cec* |
| `open_cec(device_path: str)` | Open CEC device for read |
| `close_cec()` | Closes CEC device for read |
| `set_logical_address()` | Set logical address to the current device |
| `update_logical_address_info()` | Update CEC logical address information. |
| `detect_devices()` | Detects network devices by a CEC ref |
| `create_net_device()` | Create a network device |
| `ping_net_dev()` | Ping a network device. |
| `get_net_dev_physical_addr()` | Get network device physical address. |
| `get_net_device_vendor_id()` | Get network device vendor id. |
| `get_net_device_osd_name()` | Get network device OSD name. |
| `get_device_power_status()` | Get network device power state. |
| `send_msg_set_stream_path()` | Set stream path. |
| `send_msg_active_source()` | Get network device active source physical address. |
| `send_msg_request_active_source()` | Request network device active source. |
| `send_msg_report_power_status()` | Report power on state to device. |
| `get_msg_init()` | Start listening to a CEC ref |
| `get_msg()` | Get a CEC message |

## Development

```shell
python3 -m venv .venv
source .venv/bin/activate
pip3 install setuptools pybind11
# register paths
python -m pybind11 --includes
```

run 

```
pip install .
```