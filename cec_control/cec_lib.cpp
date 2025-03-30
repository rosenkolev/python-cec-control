
#include <vector>
#include <cstring>

#include <sys/ioctl.h>
#include <fcntl.h>
#include <stdio.h>
#include <glob.h>
#include <linux/cec.h>
#include <linux/cec-funcs.h>

#include <pybind11/stl.h>
#include <pybind11/pybind11.h>

#include "cec_lib.h"

#define VENDOR_ID_HTNG 0x00d38d
#define cec_phys_addr_exp(pa) \
        ((pa) >> 12), ((pa) >> 8) & 0xf, ((pa) >> 4) & 0xf, (pa) & 0xf

template<typename ... Args>
std::string string_format( const std::string& format, Args ... args )
{
    int size_s = std::snprintf( nullptr, 0, format.c_str(), args ... ) + 1; // Extra space for '\0'
    if( size_s <= 0 ){ throw std::runtime_error( "Error during formatting." ); }
    auto size = static_cast<size_t>( size_s );
    auto buf = std::make_unique<char[]>( size );
    std::snprintf( buf.get(), size, format.c_str(), args ... );
    return std::string( buf.get(), buf.get() + size - 1 ); // We don't want the '\0' inside
}

bool _io_ctl(const int fd, unsigned long int req, void *parm) {
    bool ret_val = false;
    if (fd >= 0) {
        int err = ioctl(fd, req, parm);
        ret_val = err == 0;
        if (!ret_val) {
            printf("error: %s\n", strerror(errno));
        }
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
    info->phys_addr_txt = string_format("%x.%x.%x.%x", cec_phys_addr_exp(phys_addr));
    info->osd_name = std::string(laddrs.osd_name);
    info->log_addrs = laddrs.num_log_addrs;
    info->log_addr = laddrs.log_addr[0];
    info->log_addr_mask = laddrs.log_addr_mask;
    return true;
}

static bool _send_msg(CecRef *cec, unsigned char dest, cec_msg *msg) {
    cec_msg_init(msg, cec->info.phys_addr, dest);
    return _io_ctl(cec->fd, CEC_TRANSMIT, msg);
}

static inline std::string _cec_type_to_string(CecDeviceType type) {
    switch (type) {
        case CecDeviceType::TV:
            return "TV";
        case CecDeviceType::Record:
            return "Record";
        case CecDeviceType::Playback:
            return "Playback";
        case CecDeviceType::Tuner:
            return "Tuner";
        case CecDeviceType::Audio:
            return "Audio System";
        case CecDeviceType::Processor:
            return "Processor";
        default:
            return "TV";
    }
}

static int transmit_msg_retry(const int fd, struct cec_msg &msg) {
	bool from_unreg = cec_msg_initiator(&msg) == CEC_LOG_ADDR_UNREGISTERED;
	unsigned cnt = 0;
	bool repeat;
	int ret;

	do {
		ret = _io_ctl(fd, CEC_TRANSMIT, &msg);
		repeat = ret == ENONET || (ret == EINVAL && from_unreg);
		if (repeat)
			usleep(100000);
	} while (repeat && cnt++ < 10);
	return ret;
}

// TEST

static inline void cec_log_msg(const struct cec_msg *msg) {
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

CecNetworkDevice create_net_device(CecRef *cec, __u8 log_addr) {
    CecNetworkDevice device = {};
    device.dev_id = log_addr;
    device.fd = cec->fd;
    device.source_log_addr = cec->info.log_addr;
    device.source_phys_addr = cec->info.phys_addr;
    return device;
}

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

            if (cec_msg_status_is_ok(&msg)) {
                devices.push_back(create_net_device(cec, i));
            }
        }
    }

    return devices;
}

bool ping_net_dev(CecNetworkDevice *dev) {
    struct cec_msg msg;
    cec_msg_init(&msg, dev->source_log_addr, dev->dev_id);
    return (
        _io_ctl(dev->fd, CEC_TRANSMIT, &msg) &&
        cec_msg_status_is_ok(&msg)
    );
}

__u16 get_net_dev_physical_addr(CecNetworkDevice *dev) {
    struct cec_msg msg;
    __u16 phys_addr;
    cec_msg_init(&msg, dev->source_log_addr, dev->dev_id);
	cec_msg_give_physical_addr(&msg, true);
    if (_io_ctl(dev->fd, CEC_TRANSMIT, &msg) &&
        cec_msg_status_is_ok(&msg)) {
        phys_addr = (msg.msg[2] << 8) | msg.msg[3];
    }

    return phys_addr;
}

__u32 get_net_device_vendor_id(CecNetworkDevice *dev) {
    struct cec_msg msg;
    __u32 vendor_id;
    cec_msg_init(&msg, dev->source_log_addr, dev->dev_id);
	cec_msg_give_device_vendor_id(&msg, true);
    if (_io_ctl(dev->fd, CEC_TRANSMIT, &msg) &&
        cec_msg_status_is_ok(&msg)) {
        vendor_id = msg.msg[2] << 16 | msg.msg[3] << 8 | msg.msg[4];
    }

    return vendor_id;
}

std::string get_net_device_osd_name(CecNetworkDevice *dev) {
    struct cec_msg msg;
    char osd_name[15];
    cec_msg_init(&msg, dev->source_log_addr, dev->dev_id);
	cec_msg_give_osd_name(&msg, true);
    _io_ctl(dev->fd, CEC_TRANSMIT, &msg);
    cec_ops_set_osd_name(&msg, osd_name);
    if (!cec_msg_status_is_ok(&msg)) {
        std::string err = "NO NAME";
        strcpy(osd_name, err.c_str());
    }

    return std::string(osd_name);
}

CecPowerState get_net_device_pwr_state(CecNetworkDevice *dev) {
    struct cec_msg msg;
    CecPowerState state = CecPowerState::UNKNOWN;
    __u8 pwr;
    cec_msg_init(&msg, dev->source_log_addr, dev->dev_id);
	cec_msg_give_device_power_status(&msg, true);
    if (_io_ctl(dev->fd, CEC_TRANSMIT, &msg) &&
        cec_msg_status_is_ok(&msg)) {
        cec_ops_report_power_status(&msg, &pwr);
        switch (pwr) {
            case CEC_OP_POWER_STATUS_ON:
                state = CecPowerState::ON;
                break;
            case CEC_OP_POWER_STATUS_STANDBY:
                state = CecPowerState::OFF;
                break;
            default:
                state = CecPowerState::TRANSITION;
        }
    }

    return state;
}

__u16 get_net_dev_active_source_phys_addr(CecNetworkDevice *dev) {
    __u16 pa;
    struct cec_msg msg;
    cec_msg_init(&msg, dev->source_log_addr, dev->dev_id);
    cec_msg_request_active_source(&msg, true);
    if (_io_ctl(dev->fd, CEC_TRANSMIT, &msg) &&
        cec_msg_status_is_ok(&msg)) {
        cec_ops_active_source(&msg, &pa);
    }

    return pa;
}

bool set_net_dev_active_source(CecNetworkDevice *dev, __u16 phys_addr) {
    struct cec_msg msg;
    cec_msg_init(&msg, dev->source_phys_addr, dev->dev_id);
    cec_msg_active_source(&msg, phys_addr);
    return !transmit_msg_retry(dev->fd, msg);
}

bool set_logical_address(CecRef *cec, CecDeviceType type) {
    __u8 all_dev_types = 0;
    __u8 prim_type = 0xff;
    unsigned la_type;
    struct cec_log_addrs laddrs = {};

    if (cec != nullptr && 
        cec->isOpen() &&
        cec->can_set_log_addr &&
        _io_ctl(cec->fd, CEC_ADAP_S_LOG_ADDRS, &laddrs)) {
        // unregister only
        if (type == CecDeviceType::Unregistered) {
            return true;
        }

        memset(&laddrs, 0, sizeof(laddrs));  // reset the struct
        
        // set name
        std::string osd_name = _cec_type_to_string(type);
        strncpy(laddrs.osd_name, osd_name.c_str(), sizeof(laddrs.osd_name));
        laddrs.osd_name[sizeof(laddrs.osd_name) - 1] = 0;

        laddrs.vendor_id = 0x000c03; // HDMI
        laddrs.cec_version = CEC_OP_CEC_VERSION_2_0; // CEC_OP_CEC_VERSION_1_4; CEC_OP_CEC_VERSION_2_0

        switch (type) {
            case CecDeviceType::TV:
                prim_type = CEC_OP_PRIM_DEVTYPE_TV;
                la_type = CEC_LOG_ADDR_TYPE_TV;
                all_dev_types |= CEC_OP_ALL_DEVTYPE_TV;
                break;
            case CecDeviceType::Record:
                prim_type = CEC_OP_PRIM_DEVTYPE_RECORD;
                la_type = CEC_LOG_ADDR_TYPE_RECORD;
                all_dev_types |= CEC_OP_ALL_DEVTYPE_RECORD;
                break;
            case CecDeviceType::Playback:
                prim_type = CEC_OP_PRIM_DEVTYPE_PLAYBACK;
                la_type = CEC_LOG_ADDR_TYPE_PLAYBACK;
                all_dev_types |= CEC_OP_ALL_DEVTYPE_PLAYBACK;
                break;
            case CecDeviceType::Tuner:
                prim_type = CEC_OP_PRIM_DEVTYPE_TUNER;
                la_type = CEC_LOG_ADDR_TYPE_TUNER;
                all_dev_types |= CEC_OP_ALL_DEVTYPE_TUNER;
                break;
            case CecDeviceType::Audio:
                prim_type = CEC_OP_PRIM_DEVTYPE_AUDIOSYSTEM;
                la_type = CEC_LOG_ADDR_TYPE_AUDIOSYSTEM;
                all_dev_types |= CEC_OP_ALL_DEVTYPE_AUDIOSYSTEM;
                break;
            case CecDeviceType::Processor:
                prim_type = CEC_OP_PRIM_DEVTYPE_PROCESSOR;
                la_type = CEC_LOG_ADDR_TYPE_SPECIFIC;
                all_dev_types |= CEC_OP_ALL_DEVTYPE_SWITCH;
                break;
            default:
                la_type = CEC_LOG_ADDR_TYPE_UNREGISTERED;
                all_dev_types |= CEC_OP_ALL_DEVTYPE_SWITCH;
                break;
        }

        laddrs.log_addr_type[0] = la_type;
        laddrs.primary_device_type[0] = prim_type;
        laddrs.all_device_types[0] = all_dev_types;
        laddrs.features[0][0] = 0; // rc_tv | rc_src;
        laddrs.num_log_addrs = 1;

        bool isSet = _io_ctl(cec->fd, CEC_ADAP_S_LOG_ADDRS, &laddrs);
        return isSet;
    }

    return false;
}

bool report_net_device_pwr_on(CecNetworkDevice *dev) {
    struct cec_msg msg;
    cec_msg_init(&msg, dev->source_log_addr, dev->dev_id);
    cec_msg_report_power_status(&msg, CEC_OP_POWER_STATUS_ON);
    return (
        _io_ctl(dev->fd, CEC_TRANSMIT, &msg) &&
        cec_msg_status_is_ok(&msg)
    );
}

CecBusMonitorRef start_msg_monitor(CecRef *cec) {
    CecBusMonitorRef ref;
    __u32 monitor = CEC_MODE_MONITOR;
    ref.fd = cec->fd;
    if (_io_ctl(cec->fd, CEC_S_MODE, &monitor)) {
        fcntl(ref.fd, F_SETFL, fcntl(ref.fd, F_GETFL) | O_NONBLOCK);
        ref.success = true;
	}
    else {
        fprintf(stderr, "Selecting monitor mode failed, you may have to run this as root.\n");
    }

    return ref;
}

CecBusMsg deque_msg(CecBusMonitorRef *ref) {
    fd_set rd_fds;
    fd_set ex_fds;
    CecBusMsg cec_msg;
    int res;
    struct timeval tv = { 1, 0 };

    FD_ZERO(&rd_fds);
    FD_ZERO(&ex_fds);
    FD_SET(ref->fd, &rd_fds);
    FD_SET(ref->fd, &ex_fds);
    res = select(ref->fd + 1, &rd_fds, nullptr, &ex_fds, &tv);
    if (res < 0)
		return cec_msg;

    if (FD_ISSET(ref->fd, &ex_fds)) {
        struct cec_event ev;
        if (!_io_ctl(ref->fd, CEC_DQEVENT, &ev)) {
            // no event pending
            return cec_msg;
        }
        
        cec_msg.has_event = true;
        cec_msg.lost_events = (ev.flags & CEC_EVENT_FL_DROPPED_EVENTS);
        cec_msg.initial_state = (ev.flags & CEC_EVENT_FL_INITIAL_STATE);

        switch (ev.event) {
            case CEC_EVENT_STATE_CHANGE:
                cec_msg.state_change = true;
                cec_msg.state_change_phys_addr = ev.state_change.phys_addr;
                break;
            // case CEC_EVENT_LOST_MSGS:
            //     printf("Event: Lost %d messages\n", ev.lost_msgs.lost_msgs);
            //     break;
            // case CEC_EVENT_PIN_CEC_LOW:
            // case CEC_EVENT_PIN_CEC_HIGH:
            //     if (ev.flags & CEC_EVENT_FL_INITIAL_STATE)
            //         printf("Event: CEC Pin %s\n", ev.event == CEC_EVENT_PIN_CEC_HIGH ? "High" : "Low");
            //     break;
            // case CEC_EVENT_PIN_HPD_LOW:
            // case CEC_EVENT_PIN_HPD_HIGH:
            //     printf("Event: HPD Pin %s\n",
            //                ev.event == CEC_EVENT_PIN_HPD_HIGH ? "High" : "Low");
            //     break;
            // case CEC_EVENT_PIN_5V_LOW:
            // case CEC_EVENT_PIN_5V_HIGH:
            //         printf("Event: 5V Pin %s\n",
            //                ev.event == CEC_EVENT_PIN_5V_HIGH ? "High" : "Low");
            //     break;
            default:
                    printf("Event: Unknown (0x%x)\n", ev.event);
                break;
        }
    }

    if (FD_ISSET(ref->fd, &rd_fds)) {
        struct cec_msg msg = { };
        if (_io_ctl(ref->fd, CEC_RECEIVE, &msg)) {
            __u8 from = cec_msg_initiator(&msg);
            __u8 to = cec_msg_destination(&msg);

            cec_msg.has_message = true;
            bool transmitted = msg.tx_status != 0;
            printf("%s %s to %s (%d to %d): ",
                transmitted ? "Transmitted by" : "Received from",
                "X", to == 0xf ? "all" : "Y", from, to);
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
            // cec_msg.success = true;
        }
        else if (errno == ENODEV) {
            cec_msg.disconnected = true;
        }
    }
    return cec_msg;
}
