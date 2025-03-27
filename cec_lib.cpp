
#include <vector>
#include <cstring>

#include <sys/ioctl.h>
#include <fcntl.h>
#include <stdio.h>
#include <glob.h>
#include <linux/cec.h>

#include <pybind11/stl.h>
#include <pybind11/pybind11.h>

#include "cec_lib.h"

#define CEC_EVENT_FL_INITIAL_STATE	(1 << 0)
#define CEC_EVENT_FL_DROPPED_EVENTS	(1 << 1)
#define VENDOR_ID_HTNG 0x00d38d

bool _io_ctl(const int fd, unsigned long int req, void *parm) {
    bool ret_val = false;
    if (fd >= 0) {
        int err = ioctl(fd, req, parm);
        ret_val = err == 0;
    }
    return ret_val;
}

bool _cec_info(const int fd, struct CecInfo *info) {
    __u16 phys_addr;
    struct cec_caps caps;
    struct cec_log_addrs laddrs;

    if (!_io_ctl(fd, CEC_ADAP_G_CAPS, &caps) ||
        !_io_ctl(fd, CEC_ADAP_G_PHYS_ADDR, &phys_addr) ||
        !_io_ctl(fd, CEC_ADAP_G_LOG_ADDRS, &laddrs)) {
        return false;
    }

    info->caps = caps.capabilities;
    info->available_log_addrs = caps.available_log_addrs;
    info->adapter = std::string(caps.driver) + " (" + caps.name + ")";
    info->phys_addr = phys_addr;
    info->log_addrs = laddrs.num_log_addrs;
    info->log_addr_mask = laddrs.log_addr_mask;
    return true;
}

static bool _send_msg(CecRef *cec, unsigned char dest, cec_msg *msg) {
    cec_msg_init(msg, cec->info.phys_addr, dest);
    return _io_ctl(cec->fd, CEC_TRANSMIT, msg);
}

static inline bool _cec_msg_is_ok(const struct cec_msg *msg) {
    return
        (msg->tx_status & CEC_TX_STATUS_OK) ||
        (msg->rx_status & CEC_RX_STATUS_OK);
}

// TEST

#define cec_phys_addr_exp(pa) \
        ((pa) >> 12), ((pa) >> 8) & 0xf, ((pa) >> 4) & 0xf, (pa) & 0xf

const char *cec_la2s(unsigned la) {
    switch (la & 0xf) {
    case 0:
        return "TV";
    case 1:
        return "Recording Device 1";
    case 2:
        return "Recording Device 2";
    case 3:
        return "Tuner 1";
    case 4:
        return "Playback Device 1";
    case 5:
        return "Audio System";
    case 6:
        return "Tuner 2";
    case 7:
        return "Tuner 3";
    case 8:
        return "Playback Device 2";
    case 9:
        return "Recording Device 3";
    case 10:
        return "Tuner 4";
    case 11:
        return "Playback Device 3";
    case 12:
        return "Backup 1";
    case 13:
        return "Backup 2";
    case 14:
        return "Specific";
    case 15:
    default:
        return "Unregistered";
    }
}

static inline void cec_log_msg(const struct cec_msg *msg)
{
	__u32 vendor_id;
	__u16 phys_addr;
	const __u8 *bytes;
	__u8 size;
	unsigned i;

	switch (msg->msg[1]) {
	case CEC_MSG_VENDOR_COMMAND:
		printf("VENDOR_COMMAND (0x%02x):\n",
		       CEC_MSG_VENDOR_COMMAND);
		//cec_ops_vendor_command(msg, &size, &bytes);
		printf("\tvendor-specific-data:");
		for (i = 0; i < size; i++)
			printf(" 0x%02x", bytes[i]);
		printf("\n");
		break;
	case CEC_MSG_VENDOR_COMMAND_WITH_ID:
		//cec_ops_vendor_command_with_id(msg, &vendor_id, &size, &bytes);
		switch (vendor_id) {
		case VENDOR_ID_HTNG:
            printf("VENDOR_ID_HTNG");
			//log_htng_msg(msg);
			break;
		default:
			printf("VENDOR_COMMAND_WITH_ID (0x%02x):\n",
			       CEC_MSG_VENDOR_COMMAND_WITH_ID);
			//log_vendor_id("vendor-id", vendor_id);
			printf("\tvendor-specific-data:");
			for (i = 0; i < size; i++)
				printf(" 0x%02x", bytes[i]);
			printf("\n");
			break;
		}
		break;
	case CEC_MSG_VENDOR_REMOTE_BUTTON_DOWN:
		printf("VENDOR_REMOTE_BUTTON_DOWN (0x%02x):\n",
		       CEC_MSG_VENDOR_REMOTE_BUTTON_DOWN);
		// cec_ops_vendor_remote_button_down(msg, &size, &bytes);
		printf("\tvendor-specific-rc-code:");
		for (i = 0; i < size; i++)
			printf(" 0x%02x", bytes[i]);
		printf("\n");
		break;
	case CEC_MSG_CDC_MESSAGE:
		phys_addr = (msg->msg[2] << 8) | msg->msg[3];

		printf("CDC_MESSAGE (0x%02x): 0x%02x:\n",
		       CEC_MSG_CDC_MESSAGE, msg->msg[4]);
		//log_arg(&arg_u16, "phys-addr", phys_addr);
		printf("\tpayload:");
		for (i = 5; i < msg->len; i++)
			printf(" 0x%02x", msg->msg[i]);
		printf("\n");
		break;
	default:
		printf("UNKNOWN (0x%02x)%s", msg->msg[1], msg->len > 2 ? ":\n\tpayload:" : "");
		for (i = 2; i < msg->len; i++)
			printf(" 0x%02x", msg->msg[i]);
		printf("\n");
		break;
	}
}

// ----------------------------
// Externally exposed function

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

void close_cec(CecRef *ref) {
    if (ref != nullptr && ref->isOpen()) {
        close(ref->fd);
        ref->fd = -1;
    }
}

CecRef open_cec(std::string device_path) {
    struct CecRef ref;
    ref.fd = open(device_path.c_str(), O_RDWR);
    if (ref.isOpen()) {
        if (_cec_info(ref.fd, &ref.info)) {
            ref.can_transmit = (ref.info.caps & CEC_CAP_TRANSMIT) > 0;
            ref.can_set_log_addr = (ref.info.caps & CEC_CAP_LOG_ADDRS) > 0;
        }
        else {
            close_cec(&ref);
        }
    }

    return ref;
}


// std::vector<CecInfo> ext_get_cec_interfaces() {
//     std::vector<CecInterface> devices = {};
//     std::vector<std::string> device_paths = find_cec_devices();
//     for (const auto& device_path : device_paths) {
//         CecInterface info;
//         info.device_path = device_path;

//         int fd = open(device_path.c_str(), O_RDWR);
//         bool is_valid = cec_info(fd, &info);
//         close(fd);
//         if (is_valid) {
//             devices.push_back(info);
//         }
//     }
    
//     return devices;
// }

std::vector<CecNetworkDevice> detect_devices(CecRef *cec) {
    std::vector<CecNetworkDevice> devices = {};
    if (cec != nullptr &&
        cec->isOpen() &&
        cec->can_transmit) {
        struct cec_msg msg;

        // ping all 14 addresses (15 is broadcast)
        for (unsigned i = 0; i < 15; i++) {
            if (!_send_msg(cec, i, &msg)) {
                continue;
            }

            if (_cec_msg_is_ok(&msg)) {
                CecNetworkDevice device = {};
                device.phys_addr = i;
                device.cec_info = cec->info;
                devices.push_back(device);
            }
        }
    }

    return devices;
}


CecBusMonitorRef start_msg_monitor(CecRef *cec) {
    CecBusMonitorRef ref;
    ref.fd = cec->fd;
    fcntl(ref.fd, F_SETFL, fcntl(ref.fd, F_GETFL) | O_NONBLOCK);
    return ref;
}

CecBusMsg deque_msg(CecBusMonitorRef *ref) {
    CecBusMsg cec_msg;
    int res;
    struct timeval tv = { 1, 0 };
    FD_ZERO(&ref->rd_fds);
    FD_ZERO(&ref->ex_fds);
    FD_SET(ref->fd, &ref->rd_fds);
    FD_SET(ref->fd, &ref->ex_fds);
    res = select(ref->fd + 1, &ref->rd_fds, nullptr, &ref->ex_fds, &tv);
    if (res < 0)
		return cec_msg;

    if (FD_ISSET(ref->fd, &ref->ex_fds)) {
        struct cec_event ev;
        if (_io_ctl(ref->fd, CEC_DQEVENT, &ev)) {
            // no event pending
            return cec_msg;
        }
        
        if (ev.flags & CEC_EVENT_FL_DROPPED_EVENTS) {
            printf("warn: events were lost \n");
        }
        if (ev.flags & CEC_EVENT_FL_INITIAL_STATE) {
            printf("event: Initial state \n");
        }

        switch (ev.event) {
            case CEC_EVENT_STATE_CHANGE:
                printf("Event: State Change: PA: %x.%x.%x.%x, LA mask: 0x%04x, Conn Info: %s\n",
                        cec_phys_addr_exp(ev.state_change.phys_addr),
                        ev.state_change.log_addr_mask,
                        ev.state_change.have_conn_info ? "yes" : "no");
                break;
            case CEC_EVENT_LOST_MSGS:
                printf("Event: Lost %d messages\n",
                           ev.lost_msgs.lost_msgs);
                break;
            case CEC_EVENT_PIN_CEC_LOW:
            case CEC_EVENT_PIN_CEC_HIGH:
                if (ev.flags & CEC_EVENT_FL_INITIAL_STATE)
                    printf("Event: CEC Pin %s\n", ev.event == CEC_EVENT_PIN_CEC_HIGH ? "High" : "Low");
                break;
            case CEC_EVENT_PIN_HPD_LOW:
            case CEC_EVENT_PIN_HPD_HIGH:
                printf("Event: HPD Pin %s\n",
                           ev.event == CEC_EVENT_PIN_HPD_HIGH ? "High" : "Low");
                break;
            case CEC_EVENT_PIN_5V_LOW:
            case CEC_EVENT_PIN_5V_HIGH:
                    printf("Event: 5V Pin %s\n",
                           ev.event == CEC_EVENT_PIN_5V_HIGH ? "High" : "Low");
                break;
            default:
                    printf("Event: Unknown (0x%x)\n", ev.event);
                break;
        }
    }

    if (FD_ISSET(ref->fd, &ref->rd_fds)) {
        struct cec_msg msg = { };
        res = _io_ctl(ref->fd, CEC_RECEIVE, &msg);
        if (res == ENODEV) {
            cec_msg.disconnected = true;
        }
        else if (!res) {
            __u8 from = cec_msg_initiator(&msg);
            __u8 to = cec_msg_destination(&msg);

            bool transmitted = msg.tx_status != 0;
            printf("%s %s to %s (%d to %d): ",
                transmitted ? "Transmitted by" : "Received from",
                cec_la2s(from), to == 0xf ? "all" : cec_la2s(to), from, to);
            cec_log_msg(&msg);
            // std::string status;
            // if ((msg.tx_status & ~CEC_TX_STATUS_OK) ||
            //     (msg.rx_status & ~CEC_RX_STATUS_OK)) {
            //     status = std::string(" ") + cec_status2s(msg);
            //     if (verbose)
            //         printf("\tTimestamp: %s\n", ts2s(current_ts()).c_str());
            // }
            // if (verbose && transmitted)
            //     printf("\tSequence: %u Tx Timestamp: %s%s\n",
            //         msg.sequence, ts2s(msg.tx_ts).c_str(),
            //         status.c_str());
            // else if (verbose && !transmitted)
            //     printf("\tSequence: %u Rx Timestamp: %s%s\n",
            //         msg.sequence, ts2s(msg.rx_ts).c_str(),
            //         status.c_str());
        }
    }
    return cec_msg;
}

/*
void wait_for_msgs(const int fd, __u32 monitor_time) {
	fd_set rd_fds;
	fd_set ex_fds;
	int fd = node.fd;
	time_t t;

	fcntl(fd, F_SETFL, fcntl(fd, F_GETFL) | O_NONBLOCK);
	t = time(nullptr) + monitor_time;

	while (!monitor_time || time(nullptr) < t) {
		struct timeval tv = { 1, 0 };
		int res;

		fflush(stdout);
		FD_ZERO(&rd_fds);
		FD_ZERO(&ex_fds);
		FD_SET(fd, &rd_fds);
		FD_SET(fd, &ex_fds);
		res = select(fd + 1, &rd_fds, nullptr, &ex_fds, &tv);
		if (res < 0)
			break;
		if (FD_ISSET(fd, &ex_fds)) {
			struct cec_event ev;

			if (doioctl(&node, CEC_DQEVENT, &ev))
				continue;
			log_event(ev, true);
		}
		if (FD_ISSET(fd, &rd_fds)) {
			struct cec_msg msg = { };

			res = doioctl(&node, CEC_RECEIVE, &msg);
			if (res == ENODEV) {
				fprintf(stderr, "Device was disconnected.\n");
				break;
			}
			if (!res)
				show_msg(msg);
		}
	}
}

// void monitor(CancellationToken *token, std:function<void()> on_disconnect) {
//   while (1) {
    
//   }
// }

*/

PYBIND11_MODULE(cec_lib, m) {
    pybind11::class_<CecInfo>(m, "CecInfo")
        .def_readonly("path", &CecInfo::device_path)
        .def_readonly("adapter", &CecInfo::adapter)
        .def_readonly("caps", &CecInfo::caps)
        .def_readonly("available_logical_address", &CecInfo::available_log_addrs)
        .def_readonly("physical_address", &CecInfo::phys_addr)
        .def_readonly("logical_address", &CecInfo::log_addrs)
        .def_readonly("logical_address_mask", &CecInfo::log_addr_mask);
    
    pybind11::class_<CecNetworkDevice>(m, "CecNetworkDevice")
        .def_readonly("physical_address", &CecNetworkDevice::phys_addr);

    pybind11::class_<CecRef>(m, "CecRef")
        .def_readonly("info", &CecRef::info)
        .def_readonly("can_transmit", &CecRef::can_transmit)
        .def_readonly("can_set_logical_address", &CecRef::can_set_log_addr)
        .def("isOpen", &CecRef::isOpen)
        .def("hasInfo", &CecRef::hasInfo);

    pybind11::class_<CecBusMonitorRef>(m, "CecBusMonitorRef");

    pybind11::class_<CecBusMsg>(m, "CecBusMsg")
        .def_readonly("success", &CecBusMsg::success)
        .def_readonly("disconnected", &CecBusMsg::disconnected);

    m.def("find_cec_devices", &find_cec_devices, "Find CEC devices in /dev/cec*");
    m.def("open_cec", &open_cec, "Open CEC device for read");
    m.def("close_cec", &close_cec, "Closes CEC device for read");
    m.def("detect_devices", &detect_devices, "Detects network devices by a CEC ref");
    m.def("start_msg_monitor", &start_msg_monitor, "Start listening to a CEC ref");
    m.def("deque_msg", &deque_msg, "Get a CEC message");
}
