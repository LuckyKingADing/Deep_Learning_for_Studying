#pragma once

#include "modules/common/topic/topic_gflags.h"
#include "modules/localization/src/TCMSF/tcmsf/sensor/rtcm/include/rtcm_interface.h"

#include "modules/msg/drivers_msgs/rtcm.pb.h"
// #include "tcmsf_config.h"
#include "tcmsf_interface.h"
// #include "tcmsf_interface_impl.h"
#include "tcmsf_timer.h"

#include "cyber/record/record_reader.h"
#include "cyber/record/record_writer.h"

#include <algorithm>
#include <atomic>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

// #define _TCMSF_WRITE_RESULT_TO_RECORD_

class TCMSF_ {
private:
    std::unique_ptr<byd::tcmsf::TCMSF> tcmsf_ = nullptr;

public:
    TCMSF_(const std::string &);

public:
    int run(const std::string &, const std::string &);
};
