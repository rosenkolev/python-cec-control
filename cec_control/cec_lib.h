#include <pybind11/stl.h>
#include <pybind11/pybind11.h>

#ifndef EXTENSION_H
#define EXTENSION_H

enum class CecPowerState {
    UNKNOWN,
    ON,
    OFF,
    TRANSITION
};

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

    bool hasInfo() const {
        return !info.device_path.empty();
    }
};

struct CecNetworkDevice {
    unsigned dev_id;
    int fd;
    unsigned source_log_addr;
    unsigned source_phys_addr;
    bool active;
};

struct CecBusMonitorRef {
    int fd;
    fd_set rd_fds;
	fd_set ex_fds;
    bool success;
};

struct CecBusMsg {
    bool has_event;
    bool has_message;
    bool initial_state;
    bool lost_events;
    bool disconnected;
    bool state_change;
    unsigned state_change_phys_addr;
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
CecNetworkDevice create_net_device(CecRef *cec, __u8 log_addr);
std::vector<CecNetworkDevice> detect_devices(CecRef *cec);
__u16 get_net_dev_physical_addr(CecNetworkDevice *dev);
__u32 get_net_device_vendor_id(CecNetworkDevice *dev);
std::string get_net_device_osd_name(CecNetworkDevice *dev);
CecPowerState get_net_device_pwr_state(CecNetworkDevice *dev);
__u16 get_net_dev_active_source_phys_addr(CecNetworkDevice *dev);
bool set_net_dev_active_source(CecNetworkDevice *dev, __u16 phys_addr);
bool ping_net_dev(CecNetworkDevice *dev);
bool set_logical_address(CecRef *cec, CecDeviceType type);
bool report_net_device_pwr_on(CecNetworkDevice *dev);
CecBusMonitorRef start_msg_monitor(CecRef *cec);
CecBusMsg deque_msg(CecBusMonitorRef *ref);

#endif