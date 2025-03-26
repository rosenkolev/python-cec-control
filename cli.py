from argparse import ArgumentParser

import cec_lib

def main():
    parser = ArgumentParser(description="CLI tool using C++ extension")
    parser.add_argument("-l", "--list", action="store_true", help="List devices")
    args = parser.parse_args()

    if args.list:
        print("Listing CEC devices")
        ints = cec_lib.get_cec_interfaces()
        for info in ints:
            print(f"{info.path}\n Adapter: {info.adapter}\n Available Logical Address: {info.available_logical_address}\n Logical Address: {info.logical_address}\n Physical Address {info.physical_address}\n Mask: {info.logical_address_mask}\n Caps: {info.caps}")
            devs = cec_lib.get_devices(info)
            for dev in devs:
                print(f"Devica Physical Address: {dev.physical_address}")

    print("DONE")
    

if __name__ == "__main__":
    main()
