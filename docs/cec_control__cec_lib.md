# cec_control.cec_lib

## Methods

### find_cec_devices() -> list[str]

Find all CEC devices at /dev/cec*.

**Returns**

*list[str]* - Returns a list of all CEC devices

### open_cec(device_path: str) -> CecRef

Open the CEC device for read/write and retrieve basic device information.

- **device_path** (*str*): The device path.

**Returns**

*CecRef* - Returns a reference to the open device.

**Example**

```python
import cec_control.cec_lib as cec_lib

ref = cec_lib.open_cec("/dev/cec0")
ref.isOpen() # true

cec_lib.close_cec(ref)
```

### close_cec(cec: CecRef) -> None

Closes the CEC device.

- **cec** (*CecRef*): The CEC reference.

**Example**

See [open_cec](#open_cecdevice_path-str---cecref)

## Models

### CecRef

- **can_transmit** (*bool*): Can the CEC transmit messages.
- **can_set_logical_address** (*bool*): Can the CEC set logical address.
- **isOpen()** (*bool*): Is the CEC device opened.
- **info** (*[CecInfo](#cecinfo)*): CEC device information.

### CecInfo

- **path** (*str*): The CEC device path.
- **adapter** (*str*): CEC adapter name.
- **caps** (*int*): CEC capabilities.
- **available_logical_address** (*int*): Available logical address.
- **physical_address** (*int*): Physical address.
- **logical_address** (*int*): Logical address.
- **logical_address_count** (*int*): Logical addresses count.
- **logical_address_mask** (*int*): Logical address mask.
- **osd_name** (*str*): The OSD name.

