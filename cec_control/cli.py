from argparse import ArgumentParser
from cec_control.cec import Cec

def print_topology(interfaces: list[Cec]):
    for cec in interfaces:
        with cec:
            print(repr(cec))
            if cec.is_registered:
                print("    Network Devices:")
                devices = cec.devices()
                for dev in devices:
                    print("        - " + repr(dev))

def main():
    parser = ArgumentParser(description="CLI tool using C++ extension")
    parser.add_argument("-l", "--list", action="store_true", help="List devices")
    args = parser.parse_args()

    interfaces: list[Cec] = Cec.find_cec_devices()
    
    print(f"Found {len(interfaces)} CEC interfaces")
    print_topology(interfaces)
    print("---------------")

    with interfaces[0] as cec:
        if cec.set_type("Playback"):
            print("registered as playback")
            print("---------------")
            cec.monitor().wait_for_msgs(60)
            print("---------------")
            cec.set_type("Unregistered")
            print("---------------")
            print_topology(interfaces)

    if args.list:
        pass

    print("DONE")
    

if __name__ == "__main__":
    main()
