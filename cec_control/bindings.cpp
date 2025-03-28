
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

    pybind11::class_<CecInfo>(m, "CecInfo")
        .def_readonly("path", &CecInfo::device_path)
        .def_readonly("adapter", &CecInfo::adapter)
        .def_readonly("caps", &CecInfo::caps)
        .def_readonly("available_logical_address", &CecInfo::available_log_addrs)
        .def_readonly("physical_address", &CecInfo::phys_addr)
        .def_readonly("physical_address_text", &CecInfo::phys_addr_txt)
        .def_readonly("osd_name", &CecInfo::osd_name)
        .def_readonly("logical_address", &CecInfo::log_addrs)
        .def_readonly("logical_address_mask", &CecInfo::log_addr_mask);
    
    pybind11::class_<CecNetworkDevice>(m, "CecNetworkDevice")
        .def_readonly("physical_address", &CecNetworkDevice::phys_addr);

    pybind11::class_<CecRef>(m, "CecRef")
        .def_readonly("info", &CecRef::info)
        .def_readonly("can_transmit", &CecRef::can_transmit)
        .def_readonly("can_set_logical_address", &CecRef::can_set_log_addr)
        .def("isOpen", &CecRef::isOpen);

    pybind11::class_<CecBusMonitorRef>(m, "CecBusMonitorRef");

    pybind11::class_<CecBusMsg>(m, "CecBusMsg")
        .def_readonly("success", &CecBusMsg::success)
        .def_readonly("disconnected", &CecBusMsg::disconnected);

    m.def("find_cec_devices", &find_cec_devices, "Find CEC devices in /dev/cec*");
    m.def("open_cec", &open_cec, "Open CEC device for read");
    m.def("close_cec", &close_cec, "Closes CEC device for read");
    m.def("detect_devices", &detect_devices, "Detects network devices by a CEC ref");
    m.def("set_logical_address", &set_logical_address, "Set logical address to the current device");
    m.def("start_msg_monitor", &start_msg_monitor, "Start listening to a CEC ref");
    m.def("deque_msg", &deque_msg, "Get a CEC message");
}