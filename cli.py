from argparse import ArgumentParser
from cec import Cec

def main():
    parser = ArgumentParser(description="CLI tool using C++ extension")
    parser.add_argument("-l", "--list", action="store_true", help="List devices")
    args = parser.parse_args()

    interfaces: list[Cec] = Cec.find_cec_devices()
    
    print(f"Found {len(interfaces)} CEC interfaces")
    for cec in interfaces:
        with cec:
            print(repr(cec))
            print("Network Devices:")
            devices = cec.devices()
            for dev in devices:
                print(repr(dev))

    print("---------------")
    
    interfaces[0].monitor().wait_for_msgs()

    if args.list:
        pass

    print("DONE")
    

if __name__ == "__main__":
    main()
