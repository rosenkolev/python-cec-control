#include <pybind11/stl.h>
#include <pybind11/pybind11.h>

#ifndef EXTENSION_H
#define EXTENSION_H

struct CecInfo {
	std::string device_path;
    std::string adapter;
    std::string phys_addr_txt;
    std::string osd_name;
	unsigned caps;
	unsigned available_log_addrs;
    unsigned phys_addr;
    unsigned log_addrs;
    unsigned char log_addr;
	unsigned short log_addr_mask;
};

struct CecRef {
    int fd;
    CecInfo info;

    bool can_transmit = false;
    bool can_set_log_addr = false;
    
    bool isOpen() const {
        return fd >= 0;
    }
};

struct CecNetworkDevice {
    unsigned dev_id;
    int fd;
    unsigned source_log_addr;
    unsigned source_phys_addr;
    bool active;
};

struct CecBusMsg {
    bool has_event;
    bool initial_state;
    bool state_change;
    unsigned state_change_phys_addr;
    bool lost_events;
    bool msg;
    __u8 msg_from;
    __u8 msg_to;
    __u8 msg_status;
    __u8 msg_code;
    __u8 msg_address;
    __u8 msg_cmd;
    bool msg_transmitted;
    bool disconnected;
};

enum class CecDeviceType {
    Unregistered,
    TV,
    Record,
    Playback,
    Tuner,
    Audio,
    Processor
};

std::vector<std::string> find_cec_devices();
void close_cec(CecRef *ref);
CecRef open_cec(std::string device_path);
bool set_logical_address(CecRef *cec, CecDeviceType type);
bool update_logical_address_info(CecRef *ref);
CecNetworkDevice create_net_device(CecRef *cec, __u8 log_addr);
std::vector<CecNetworkDevice> detect_devices(CecRef *cec);
__u16 get_net_dev_physical_addr(CecNetworkDevice *dev);
__u32 get_net_device_vendor_id(CecNetworkDevice *dev);
std::string get_net_device_osd_name(CecNetworkDevice *dev);
__u8 get_device_power_status(CecNetworkDevice *dev);
bool ping_net_dev(CecNetworkDevice *dev);
bool send_msg_report_power_status(CecNetworkDevice *dev);
bool send_msg_set_stream_path(CecNetworkDevice *dev, __u16 phys_addr);
bool send_msg_request_active_source(CecNetworkDevice *dev);
bool send_msg_active_source(CecNetworkDevice *dev, __u16 phys_addr);
bool get_msg_init(CecRef *cec);
CecBusMsg get_msg(CecRef *cec);

#endif