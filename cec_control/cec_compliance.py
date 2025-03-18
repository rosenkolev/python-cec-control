import re
import subprocess
from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class CECDevice:
    address: str = ""
    type: str = ""
    cec_version: Optional[str] = None
    status: Optional[str] = None

@dataclass
class CECSystem:
    address: str = ""
    devices: Dict[int, CECDevice] = field(default_factory=dict)

def parse_cec_data(data: str) -> CECSystem:
    system = CECSystem()
    
    # Extract physical address of this device
    match = re.search(r"Physical Address\s+:\s+([0-9\.]+)", data)
    if match:
        system.address = match.group(1)
    
    # Extract devices
    device_pattern = re.finditer(
        r"System Information for device (\d+) \((.*?)\) from device .*?:.*?" 
        r"CEC Version\s+:\s+(.*?)\n.*?"
        r"Physical Address\s+:\s+([0-9\.]+)\n.*?"
        r"Primary Device Type\s+:\s+(.*?)\n.*?"
        r"Power Status\s+:\s+(.*?)\n",
        data, re.DOTALL
    )
    
    for match in device_pattern:
        device_id = int(match.group(1))
        system.devices[device_id] = CECDevice(
            address=match.group(4).strip(),
            type=match.group(5).strip(),
            cec_version=match.group(3),
            status=match.group(6),
        )
    
    return system

def run_cec_compliance(interface: str) -> CECSystem:
    result = subprocess.run(['cec-compliance', '-d' + interface], capture_output=True, text=True)
    return parse_cec_data(result.stdout)
