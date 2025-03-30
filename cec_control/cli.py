from argparse import ArgumentParser
from cec_control.cec import Cec, CecDevice, CecNetworkDeviceType, WaitCounter

class CecControl:
    def __init__(self):
        self.cec: Cec = None

    @staticmethod
    def print():
        interfaces = Cec.find_cec_devices()
        for cec in interfaces:
            with cec:
                print(repr(cec))
                if cec.is_registered:
                    print("    Network Devices:")
                    devices = cec.devices()
                    for dev in devices:
                        print("        - " + repr(dev))

    def init(self):
        """Find the TV"""
        interfaces = Cec.find_cec_devices()
        for cec in interfaces:
            with cec:
                if not cec.is_active_cec:
                    continue

                if not cec.is_registered:
                    cec.set_type("Playback")

                device = cec.create_device(CecNetworkDeviceType.TV)
                if device.is_active:
                    self.cec = cec
                    break

    def wait_for_active_source(self):
        counter = WaitCounter()
        if self.cec is None:
            print("No active TV")
            return

        with self.cec as cec:
            addr = cec.physical_address
            tv = cec.create_device(CecNetworkDeviceType.TV)

            print(f"TV {tv.logical_address} ({tv.physical_address})")
            print(f"  - Name {tv.osd_name}")
            print(f"  - Vendor {tv.vendor_id}")
            print(f"  - State {tv.power_state}")
            print(f"  - Source {tv.active_source}")
            print("------------------")
            cec.monitor().wait_for_msgs(seconds=60)
            # while counter.check(60):
            #     is_on = tv.is_power_on
            #     print(f"TV is ON {is_on}")
            #     act_src = tv.active_source == addr
            #     print(f"active source is {act_src}")
            #     if is_on and act_src:
            #         print("power is ON and active source is set")
            #         cec.monitor().wait_for_msgs(60)
            #     counter.tick(1)

def main():
    parser = ArgumentParser(description="CLI tool using C++ extension")
    parser.add_argument("-l", "--list", action="store_true", help="List devices")
    args = parser.parse_args()

    if args.list:
        CecControl.print()
        return

    control = CecControl()
    control.init()
    control.wait_for_active_source()

    # interfaces = Cec.find_cec_devices()
    
    # print(f"Found {len(interfaces)} CEC interfaces")
    # print_topology(interfaces)
    # print("---------------")

    # with interfaces[0] as cec:
    #     if cec.set_type("Playback"):
    #         print("registered as playback")
    #         print("---------------")
    #         cec.monitor().wait_for_msgs(60)
    #         print("---------------")
    #         cec.set_type("Unregistered")
    #         print("---------------")
    #         print_topology(interfaces)

    # if args.list:
    #     pass

    print("DONE")
    

if __name__ == "__main__":
    main()
