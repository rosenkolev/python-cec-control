
#include <pybind11/stl.h>
#include <pybind11/pybind11.h>
#include "cec_lib.h"

PYBIND11_MODULE(cec_lib, m) {
    pybind11::enum_<CecDeviceType>(m, "CecDeviceType")
        .value("Unregistered", CecDeviceType::Unregistered)
        .value("TV", CecDeviceType::TV)
        .value("Playback", CecDeviceType::Playback)
        .value("Processor", CecDeviceType::Processor)
        .value("Record", CecDeviceType::Record)
        .value("Audio", CecDeviceType::Audio)
        .value("Tuner", CecDeviceType::Tuner)
        .export_values();
    
    pybind11::enum_<CecPowerState>(m, "CecPowerState")
        .value("UNKNOWN", CecPowerState::UNKNOWN)
        .value("ON", CecPowerState::ON)
        .value("OFF", CecPowerState::OFF)
        .value("TRANSITION", CecPowerState::TRANSITION)
        .export_values(); 

    pybind11::class_<CecInfo>(m, "CecInfo")
        .def_readonly("path", &CecInfo::device_path)
        .def_readonly("adapter", &CecInfo::adapter)
        .def_readonly("caps", &CecInfo::caps)
        .def_readonly("available_logical_address", &CecInfo::available_log_addrs)
        .def_readonly("physical_address", &CecInfo::phys_addr)
        .def_readonly("physical_address_text", &CecInfo::phys_addr_txt)
        .def_readonly("osd_name", &CecInfo::osd_name)
        .def_readonly("logical_address", &CecInfo::log_addr)
        .def_readonly("logical_address_count", &CecInfo::log_addrs)
        .def_readonly("logical_address_mask", &CecInfo::log_addr_mask);
    
    pybind11::class_<CecNetworkDevice>(m, "CecNetworkDevice")
        .def_readonly("device_id", &CecNetworkDevice::dev_id)
        .def_readonly("source_phys_addr", &CecNetworkDevice::source_phys_addr);

    pybind11::class_<CecRef>(m, "CecRef")
        .def_readonly("info", &CecRef::info)
        .def_readonly("can_transmit", &CecRef::can_transmit)
        .def_readonly("can_set_logical_address", &CecRef::can_set_log_addr)
        .def("isOpen", &CecRef::isOpen);

    pybind11::class_<CecBusMonitorRef>(m, "CecBusMonitorRef");

    pybind11::class_<CecBusMsg>(m, "CecBusMsg")
        .def_readonly("has_event", &CecBusMsg::has_event)
        .def_readonly("has_message", &CecBusMsg::has_message)
        .def_readonly("initial_state", &CecBusMsg::initial_state)
        .def_readonly("lost_events", &CecBusMsg::lost_events)
        .def_readonly("state_change", &CecBusMsg::state_change)
        .def_readonly("state_change_phys_addr", &CecBusMsg::state_change_phys_addr)
        .def_readonly("disconnected", &CecBusMsg::disconnected);

    m.def("find_cec_devices", &find_cec_devices, "Find CEC devices in /dev/cec*");
    m.def("open_cec", &open_cec, "Open CEC device for read");
    m.def("close_cec", &close_cec, "Closes CEC device for read");
    m.def("set_logical_address", &set_logical_address, "Set logical address to the current device");
    m.def("detect_devices", &detect_devices, "Detects network devices by a CEC ref");
    m.def("create_net_device", &create_net_device, "Create a network device");
    m.def("ping_net_dev", &ping_net_dev, "Ping a network device.");
    m.def("get_net_dev_physical_addr", &get_net_dev_physical_addr, "Get network device physical address.");
    m.def("get_net_device_vendor_id", &get_net_device_vendor_id, "Get network device vendor id.");
    m.def("get_net_device_osd_name", &get_net_device_osd_name, "Get network device OSD name.");
    m.def("get_net_dev_pwr_state", &get_net_device_pwr_state, "Get network device power state.");
    m.def("get_net_dev_active_source_phys_addr", &get_net_dev_active_source_phys_addr, "Get network device active source physical address.");
    m.def("set_net_dev_active_source", &set_net_dev_active_source, "Get network device active source physical address.");
    m.def("report_net_device_pwr_on", &report_net_device_pwr_on, "Reprot power on state to device.");
    m.def("start_msg_monitor", &start_msg_monitor, "Start listening to a CEC ref");
    m.def("deque_msg", &deque_msg, "Get a CEC message");
}