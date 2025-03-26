
#include <vector>
#include <cstring>

#include <sys/ioctl.h>
#include <fcntl.h>
#include <stdio.h>
#include <glob.h>
#include <linux/cec.h>

#include <pybind11/stl.h>
#include <pybind11/pybind11.h>

struct CecInterface {
	std::string device_path;
    std::string adapter;
	unsigned caps;
	unsigned available_log_addrs;
    unsigned phys_addr;
    unsigned log_addrs;
	__u16 log_addr_mask;
    bool support_transmit;
};

struct CecDevice {
    unsigned phys_addr;
};

std::vector<std::string> find_cec_devices() {
    glob_t glob_result;
    std::vector<std::string> devices;
    int result = glob("/dev/cec*", GLOB_TILDE, nullptr, &glob_result);
    if (result == 0) {
        for (size_t i = 0; i < glob_result.gl_pathc; ++i) {
            devices.push_back(glob_result.gl_pathv[i]);
        }
    }
    globfree(&glob_result);
    return devices;
}

bool io_ctl_exec(int fd, unsigned long int req, void *parm) {
    bool ret_val = false;
    if (fd >= 0) {
        int err = ioctl(fd, req, parm);
        ret_val = err == 0;
    }
    return ret_val;
}

bool cec_info(const int fd, struct CecInterface *info) {
    __u16 phys_addr;
    struct cec_caps caps;
    struct cec_log_addrs laddrs;

    if (!io_ctl_exec(fd, CEC_ADAP_G_CAPS, &caps) ||
        !io_ctl_exec(fd, CEC_ADAP_G_PHYS_ADDR, &phys_addr) ||
        !io_ctl_exec(fd, CEC_ADAP_G_LOG_ADDRS, &laddrs)) {
        return false;
    }

    info->caps = caps.capabilities;
    info->available_log_addrs = caps.available_log_addrs;
    info->adapter = std::string(caps.driver) + " (" + caps.name + ")";
    info->phys_addr = phys_addr;
    info->log_addrs = laddrs.num_log_addrs;
    info->log_addr_mask = laddrs.log_addr_mask;
    info->support_transmit = (caps.capabilities & CEC_CAP_TRANSMIT) > 0;
    return true;
}

std::vector<CecInterface> ext_get_cec_interfaces() {
    std::vector<CecInterface> devices = {};
    std::vector<std::string> device_paths = find_cec_devices();
    for (const auto& device_path : device_paths) {
        CecInterface info;
        info.device_path = device_path;

        int fd = open(device_path.c_str(), O_RDWR);
        bool is_valid = cec_info(fd, &info);
        close(fd);
        if (is_valid) {
            devices.push_back(info);
        }
    }
    
    return devices;
}


std::vector<CecDevice> ext_get_devices(CecInterface *info) {
    std::vector<CecDevice> devices = {};
    if (info->support_transmit) {
        struct cec_msg msg;
        int fd = open(info->device_path.c_str(), O_RDWR);
        // ping all 14 addresses (15 is broadcast)
        for (unsigned i = 0; i < 15; i++) {
            cec_msg_init(&msg, info->log_addrs, i);
            if (!io_ctl_exec(fd, CEC_TRANSMIT, &msg)) {
                continue;
            }
    
            if (msg.tx_status & CEC_TX_STATUS_OK) {
                CecDevice device = {};
                device.phys_addr = i;
                devices.push_back(device);
            }
        }
        close(fd);
    }
    return devices;
}

// void wait_for_msgs(const struct node &node, __u32 monitor_time) {
// 	fd_set rd_fds;
// 	fd_set ex_fds;
// 	int fd = node.fd;
// 	time_t t;

// 	fcntl(fd, F_SETFL, fcntl(fd, F_GETFL) | O_NONBLOCK);
// 	t = time(nullptr) + monitor_time;

// 	while (!monitor_time || time(nullptr) < t) {
// 		struct timeval tv = { 1, 0 };
// 		int res;

// 		fflush(stdout);
// 		FD_ZERO(&rd_fds);
// 		FD_ZERO(&ex_fds);
// 		FD_SET(fd, &rd_fds);
// 		FD_SET(fd, &ex_fds);
// 		res = select(fd + 1, &rd_fds, nullptr, &ex_fds, &tv);
// 		if (res < 0)
// 			break;
// 		if (FD_ISSET(fd, &ex_fds)) {
// 			struct cec_event ev;

// 			if (doioctl(&node, CEC_DQEVENT, &ev))
// 				continue;
// 			log_event(ev, true);
// 		}
// 		if (FD_ISSET(fd, &rd_fds)) {
// 			struct cec_msg msg = { };

// 			res = doioctl(&node, CEC_RECEIVE, &msg);
// 			if (res == ENODEV) {
// 				fprintf(stderr, "Device was disconnected.\n");
// 				break;
// 			}
// 			if (!res)
// 				show_msg(msg);
// 		}
// 	}
// }


PYBIND11_MODULE(cec_lib, m) {
    pybind11::class_<CecInterface>(m, "CecInterface")
        //.def(py::init<std::string, int>())
        .def_readonly("path", &CecInterface::device_path)
        .def_readonly("adapter", &CecInterface::adapter)
        .def_readonly("caps", &CecInterface::caps)
        .def_readonly("available_logical_address", &CecInterface::available_log_addrs)
        .def_readonly("physical_address", &CecInterface::phys_addr)
        .def_readonly("logical_address", &CecInterface::log_addrs)
        .def_readonly("logical_address_mask", &CecInterface::log_addr_mask)
        .def_readonly("support_transmit", &CecInterface::support_transmit);
    
    pybind11::class_<CecDevice>(m, "CecDevice")
        //.def(py::init<std::string, int>())
        .def_readonly("physical_address", &CecDevice::phys_addr);

    m.def("get_cec_interfaces", &ext_get_cec_interfaces, "A function that gets all CEC interfaces");
    m.def("get_devices", &ext_get_devices, "A function that gets network devices");
}
