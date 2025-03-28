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
    unsigned phys_addr;
    CecInfo cec_info;
};

struct CecBusMonitorRef {
    int fd;
    fd_set rd_fds;
	fd_set ex_fds;
};

struct CecBusMsg {
    bool success = false;
    bool has_message = false;
    bool disconnected = false;
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
std::vector<CecNetworkDevice> detect_devices(CecRef *cec);
CecBusMonitorRef start_msg_monitor(CecRef *cec);
CecBusMsg deque_msg(CecBusMonitorRef *ref);
bool set_logical_address(CecRef *cec, CecDeviceType type);

#endif