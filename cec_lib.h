#include <pybind11/pybind11.h>

struct CecInfo {
	std::string device_path;
    std::string adapter;
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

// struct CancellationToken {
//     bool cancelled;
//     void cancel() const {
//         cancelled = true;
//     }
// };

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
