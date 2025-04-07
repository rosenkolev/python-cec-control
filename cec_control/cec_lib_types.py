from enum import Enum
from typing import Protocol


class CecDeviceType(Enum):
    Unregistered = 0
    TV = 1
    Record = 2
    Playback = 3
    Tuner = 4
    Audio = 5
    Processor = 6


class CecNetworkDeviceType(Enum):
    TV = 0
    RecordingDevice1 = 1
    RecordingDevice2 = 2
    Tuner1 = 3
    PlaybackDevice1 = 4
    AudioSystem = 5
    Tuner2 = 6
    Tuner3 = 7
    PlaybackDevice2 = 8
    RecordingDevice3 = 9
    Tuner4 = 10
    PlaybackDevice3 = 11
    Backup1 = 12
    Backup2 = 13
    Specific = 14
    Unregistered = 15


class CecPowerState(Enum):
    Unknown = 15
    On = 0
    StandBy = 1
    ToOn = 2
    ToStandBy = 3


class CecMessageRxStatus(Enum):
    Unknown = 0
    Ok = 1
    Timeout = 2
    FeatureAbort = 4
    Aborted = 5


class CecMessageTxStatus(Enum):
    Unknown = 0
    Ok = 1
    Lost = 2
    Nack = 4
    LowDrive = 8
    Error = 16
    MaxRetries = 32
    Aborted = 64
    Timeout = 128


class CecUserControlKeys(Enum):
    Select = 0x00
    Up = 0x01
    Down = 0x02
    Left = 0x03
    Right = 0x04
    RightUp = 0x05
    RightDown = 0x06
    LeftUp = 0x07
    LeftDown = 0x08
    ContentsMenu = 0x0B
    Back = 0x0D
    Num0 = 0x20
    Num1 = 0x21
    Num2 = 0x22
    Num3 = 0x23
    Num4 = 0x24
    Num5 = 0x25
    Num6 = 0x26
    Num7 = 0x27
    Num8 = 0x28
    Num9 = 0x29
    Enter = 0x2B
    Clear = 0x2C
    ChannelUp = 0x30
    ChannelDown = 0x31
    PreviousChannel = 0x32
    SoundSelect = 0x33
    InputSelect = 0x34
    DisplayInformation = 0x35
    Help = 0x36
    Power = 0x40
    VolumeUp = 0x41
    VolumeDown = 0x42
    Mute = 0x43
    Play = 0x44
    Stop = 0x45
    Pause = 0x46


class CecMessageType(Enum):
    Unknown = 0
    GiveTunerDeviceStatus = 8
    GiveDeckStatus = 26
    GiveAudioStatus = 113
    GiveSystemAudioModeStatus = 125
    GivePhysicalAddress = 131
    GiveDeviceVendorId = 140
    GiveDevicePowerStatus = 143
    GetMenuLanguage = 145
    GiveFeatures = 165
    GiveOsdName = 370
    UserControlPressed = 0x44  # 68
    UserControlReleased = 0x45  # 69

    ReportPhysicalAddress = 132
    SetStreamPath = 134
    ReportPowerStatus = 144
    ActiveSource = 130


class CecMessage(Protocol):
    has_event: bool
    initial_state: bool
    state_change: bool
    state_change_phys_addr: int
    lost_events: int
    has_message: bool
    message_from: int
    message_to: int
    message_status: int
    message_code: int
    message_address: int
    message_command: int
    message_transmitted: bool
    disconnected: bool


class CecInfo(Protocol):
    path: str
    adapter: str
    caps: int
    osd_name: str
    available_logical_address: int
    physical_address: int
    physical_address_text: str
    logical_address: int
    logical_address_count: int
    logical_address_mask: int


class CecRef(Protocol):
    can_transmit: bool
    can_set_logical_address: bool
    info: CecInfo


class CecNetworkDevice(Protocol):
    device_id: int
    source_phys_addr: int


VENDORS = dict(
    {
        0x000039: "Toshiba",
        0x000CE7: "Toshiba",
        0x0000F0: "Samsung",
        0x0005CD: "Denon",
        0x000678: "Marantz",
        0x000982: "Loewe",
        0x0009B0: "Onkyo",
        0x000C03: "HDMI",
        0x001582: "Pulse-Eight",
        0x001950: "Harman Kardon",
        0x9C645E: "Harman Kardon",
        0x001A11: "Google",
        0x0020C7: "Akai",
        0x002467: "AOC",
        0x005060: "Cisco",
        0x008045: "Panasonic",
        0x00903E: "Philips",
        0x009053: "Daewoo",
        0x00A0DE: "Yamaha",
        0x00D0D5: "Grundig",
        0x00D38D: "Hospitality Profile",
        0x00E036: "Pioneer",
        0x00E091: "LG",
        0x08001F: "Sharp",
        0x534850: "Sharp",
        0x080046: "Sony",
        0x18C086: "Broadcom",
        0x6B746D: "Vizio",
        0x8065E9: "Benq",
    }
)
