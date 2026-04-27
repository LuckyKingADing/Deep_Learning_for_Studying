#include "tcmsf_component.h"
// #include "Coord.h"

// #define __TCMSF__ENABLE_TIGHT_COUPLE

#include "processor_debug.h"

namespace byd {
namespace tcmsf {

// 坐标脱敏需求，使用加偏后的坐标
// #define GPS_TPC "/drivers/gnss/raw"
#define GPS_TPC "/drivers/gnss/packet"

#define IMU_TPC "/drivers/imu/raw"
#define INS_TPC "/drivers/ins/raw"
#define VEH_TPC "/drivers/canbus/vehicle_info"
#define TCMSF_TPC "/localization/tcmsf"
#define DR_TPC "/localization/dr"
#define VF_TPC "/localization/vf/vf_result"
#define ROVER_TPC "/drivers/rover_rtcm/raw"
#define BASE_TPC "/drivers/base_rtcm/raw"
#define MSF_TPC "/localization/ld_loc_result"
#define SDMM_TPC "/localization/sd_mapmatch_result"

using apollo::cyber::ReaderConfig;

TCMSFComponent::TCMSFComponent() :
    gps_dispose_(false), imu_dispose_(false), ins_dispose_(false), veh_dispose_(false), rover_dispose_(false), base_dispose_(false), tcmsf_dispose_(false), dr_dispose_(false), vision_dispose_(false), sdmm_dispose_(false) {
    init_timing_.component_start = std::chrono::steady_clock::now();
}

TCMSFComponent::~TCMSFComponent() { AINFO << "TCMSFComponent exit"; }

bool TCMSFComponent::Init() {

    iif_ptr_ = MSF::IIF::ImuIssueFallbackInterface::create();
    init_timing_.iif_created = std::chrono::steady_clock::now();
    init_timing_.iif_created_ok = (iif_ptr_ != nullptr);
    ACHECK(iif_ptr_ != nullptr);

    tcmsf_result_msg_ = std::make_shared<Pose>();
    resolve_          = rtcm::Resolve::create();
    init_timing_.resolve_created = std::chrono::steady_clock::now();
    init_timing_.resolve_created_ok = (resolve_ != nullptr);
    tcmsf_            = TCMSF::create(ConfigFilePath());
    init_timing_.tcmsf_created = std::chrono::steady_clock::now();
    init_timing_.tcmsf_created_ok = (tcmsf_ != nullptr);

    RegisterCallbackFunctions();
    init_timing_.callbacks_registered = std::chrono::steady_clock::now();

    // set receive topics
    ReaderConfig veh_cfg, gps_cfg, imu_cfg, ins_cfg, rover_cfg, base_cfg, dr_cfg, vision_cfg, sdmm_cfg;
    veh_cfg.channel_name    = VEH_TPC;
    gps_cfg.channel_name    = GPS_TPC;
    imu_cfg.channel_name    = IMU_TPC;
    ins_cfg.channel_name    = INS_TPC;
    rover_cfg.channel_name  = ROVER_TPC;
    base_cfg.channel_name   = BASE_TPC;
    dr_cfg.channel_name     = DR_TPC;
    vision_cfg.channel_name = VF_TPC;
    sdmm_cfg.channel_name   = SDMM_TPC;

    veh_cfg.pending_queue_size    = 3;
    gps_cfg.pending_queue_size    = 2;
    imu_cfg.pending_queue_size    = 3;
    ins_cfg.pending_queue_size    = 3;
    rover_cfg.pending_queue_size  = 2;
    base_cfg.pending_queue_size   = 2;
    dr_cfg.pending_queue_size     = 3;
    vision_cfg.pending_queue_size = 2;
    sdmm_cfg.pending_queue_size   = 2;

    veh_reader_    = node_->CreateReader<VehInfo>(veh_cfg, veh_reader_cb_);
    gps_reader_    = node_->CreateReader<Gps>(gps_cfg, gps_reader_cb_);
    imu_reader_    = node_->CreateReader<Imu>(imu_cfg, imu_reader_cb_);
    ins_reader_    = node_->CreateReader<Ins>(ins_cfg, ins_reader_cb_);
    dr_reader_     = node_->CreateReader<LocalizationEstimate>(dr_cfg, dr_reader_cb_);
    vision_reader_ = node_->CreateReader<VFResult>(vision_cfg, vision_reader_cb_);
    sdmm_reader_   = node_->CreateReader<SDMapMatchResult>(sdmm_cfg, sdmm_reader_cb_);
    ACHECK(veh_reader_ != nullptr);
    ACHECK(gps_reader_ != nullptr);
    ACHECK(imu_reader_ != nullptr);
    ACHECK(ins_reader_ != nullptr);
    ACHECK(dr_reader_ != nullptr);
    ACHECK(vision_reader_ != nullptr);
    ACHECK(sdmm_reader_ != nullptr);

#ifdef __TCMSF__ENABLE_TIGHT_COUPLE
    rover_reader_ = node_->CreateReader<Rtcm>(rover_cfg, rover_reader_cb_);
    base_reader_  = node_->CreateReader<Rtcm>(base_cfg, base_reader_cb_);
    ACHECK(rover_reader_ != nullptr);
    ACHECK(base_reader_ != nullptr);
#endif
    init_timing_.readers_created = std::chrono::steady_clock::now();
    // set publish topics
    tcmsf_result_writer_ = node_->CreateWriter<Pose>(TCMSF_TPC);
    ACHECK(tcmsf_result_writer_ != nullptr);

    msf_result_msg_    = std::make_shared<LocResult>();
    msf_result_writer_ = node_->CreateWriter<LocResult>(MSF_TPC);
    ACHECK(msf_result_writer_ != nullptr);

    init_timing_.writers_created = std::chrono::steady_clock::now();

    tcmsf_->start_fusion_daemon(result_cb_);
    init_timing_.fusion_started = std::chrono::steady_clock::now();
    init_timing_.fusion_started_ok = true;

    return true;
}

void TCMSFComponent::RegisterCallbackFunctions() {
    gps_reader_cb_ = [this](const std::shared_ptr<Gps> &gps_msg_) {
        RETURN_IF_MSG_INVALID(gps_msg_);
        PERFORMANCE_TRACE_START(TCMSF, gps);
        if (gps_dispose_.exchange(true)) {
            AINFO << "new message arrived while gps_reader_cb_ not finished yet!";
            return;
        }
        if (!init_timing_.first_gps_received) {
            init_timing_.first_gps_time = std::chrono::steady_clock::now();
            init_timing_.first_gps_received = true;
            if (gps_msg_->has_position_status() && gps_msg_->position_status() != 0) {
                init_timing_.first_valid_gps_time = std::chrono::steady_clock::now();
                init_timing_.first_valid_gps_ok = true;
            }
        }
        if (!init_timing_.first_valid_rtk_ok && gps_msg_->has_position_status() && gps_msg_->position_status() == 6) {
            init_timing_.first_valid_rtk_time = std::chrono::steady_clock::now();
            init_timing_.first_valid_rtk_ok = true;
        }
        tcmsf_->insert_msg(gps_msg_);

        gps_dispose_.exchange(false);
    };
    imu_reader_cb_ = [this](const std::shared_ptr<Imu> &imu_msg_) {
        RETURN_IF_MSG_INVALID(imu_msg_);
        PERFORMANCE_TRACE_START(TCMSF, imu);
        if (imu_dispose_.exchange(true)) {
            AINFO << "new message arrived while imu_reader_cb_ not finished yet!";
            return;
        }
        if (!init_timing_.first_imu_received) {
            init_timing_.first_imu_time = std::chrono::steady_clock::now();
            init_timing_.first_imu_received = true;
        }
        auto imu_msg_mod_ = iif_ptr_->insert_imu(imu_msg_);
        if (imu_msg_mod_->has_header() && imu_msg_mod_->has_imu_status() && imu_msg_mod_->imu_status() == 1) {
            if (!init_timing_.first_valid_imu_ok) {
                init_timing_.first_valid_imu_time = std::chrono::steady_clock::now();
                init_timing_.first_valid_imu_ok = true;
            }
        }
        tcmsf_->insert_msg(imu_msg_mod_);

        imu_dispose_.exchange(false);
    };
    veh_reader_cb_ = [this](const std::shared_ptr<VehInfo> &veh_msg_) {
        RETURN_IF_MSG_INVALID(veh_msg_);
        PERFORMANCE_TRACE_START(TCMSF, veh);
        if (veh_dispose_.exchange(true)) {
            AINFO << "new message arrived while veh_reader_cb_ not finished yet!";
            return;
        }
        if (!init_timing_.first_veh_received) {
            init_timing_.first_veh_time = std::chrono::steady_clock::now();
            init_timing_.first_veh_received = true;
        }
        iif_ptr_->insert_veh(veh_msg_);
        tcmsf_->insert_msg(veh_msg_);

        veh_dispose_.exchange(false);
    };
    ins_reader_cb_ = [this](const std::shared_ptr<Ins> &ins_msg_) {
        RETURN_IF_MSG_INVALID(ins_msg_);
        PERFORMANCE_TRACE_START(TCMSF, ins);
        if (ins_dispose_.exchange(true)) {
            AINFO << "new message arrived while ins_reader_cb_ not finished yet!";
            return;
        }

        ins_dispose_.exchange(false);
    };
    rover_reader_cb_ = [this](const std::shared_ptr<Rtcm> &rover_msg_) {
        RETURN_IF_MSG_INVALID(rover_msg_);
        PERFORMANCE_TRACE_START(TCMSF, rover);
        if (rover_dispose_.exchange(true)) {
            AINFO << "new message arrived while rover_reader_cb_ not finished yet!";
            return;
        }

        AINFO << "get rover rtcm msg";
        // get rover rtcm msg
        for (int i = 0; i < rover_msg_->value_size(); i++)
            resolve_->write_rover(rover_msg_->value(i));

        rover_dispose_.exchange(false);
    };
    base_reader_cb_ = [this](const std::shared_ptr<Rtcm> &base_msg_) {
        RETURN_IF_MSG_INVALID(base_msg_);
        PERFORMANCE_TRACE_START(TCMSF, base);
        if (base_dispose_.exchange(true)) {
            AINFO << "new message arrived while base_reader_cb_ not finished yet!";
            return;
        }

        AINFO << "get base rtcm msg";
        // get base rtcm msg
        for (int i = 0; i < base_msg_->value_size(); i++)
            resolve_->write_base(base_msg_->value(i));

        base_dispose_.exchange(false);
    };

    dr_reader_cb_ = [this](const std::shared_ptr<LocalizationEstimate> &dr_msg_) {
        RETURN_IF_MSG_INVALID(dr_msg_);
        PERFORMANCE_TRACE_START(TCMSF, dr);
        if (dr_dispose_.exchange(true)) {
            AINFO << "new message arrived while dr_reader_cb_ not finished yet!";
            return;
        }
        tcmsf_->insert_msg(dr_msg_);

        dr_dispose_.exchange(false);
    };

    vision_reader_cb_ = [this](const std::shared_ptr<VFResult> &vis_msg_) {
        RETURN_IF_MSG_INVALID(vis_msg_);
        PERFORMANCE_TRACE_START(TCMSF, vf);
        if (vision_dispose_.exchange(true)) {
            AINFO << "new message arrived while vision_reader_cb_ not finished yet!";
            return;
        }
        tcmsf_->insert_msg(vis_msg_);

        vision_dispose_.exchange(false);
    };

    sdmm_reader_cb_ = [this](const std::shared_ptr<SDMapMatchResult> &sdmm_msg_) {
        RETURN_IF_MSG_INVALID(sdmm_msg_);
        PERFORMANCE_TRACE_START(TCMSF, sdmm);
        if (sdmm_dispose_.exchange(true)) {
            AINFO << "new message arrived while sdmm_reader_cb_ not finished yet!";
            return;
        }
        tcmsf_->insert_msg(sdmm_msg_);

        sdmm_dispose_.exchange(false);
    };

    result_cb_ = [this]() {
        PERFORMANCE_TRACE_START(TCMSF, msf);
        tcmsf_->output_msg(tcmsf_result_msg_);
        auto now = std::chrono::steady_clock::now();
        if (!init_timing_.first_msf_output_ok) {
            init_timing_.first_msf_output_time = now;
            init_timing_.first_msf_output_ok = true;
            auto iif_ms = std::chrono::duration<double, std::milli>(now - init_timing_.component_start).count();
            auto imu_ms = init_timing_.first_imu_received ?
                std::chrono::duration<double, std::milli>(now - init_timing_.first_imu_time).count() : -1.0;
            auto gps_ms = init_timing_.first_gps_received ?
                std::chrono::duration<double, std::milli>(now - init_timing_.first_gps_time).count() : -1.0;
            auto fuse_ms = init_timing_.fusion_started_ok ?
                std::chrono::duration<double, std::milli>(now - init_timing_.fusion_started).count() : -1.0;
            AINFO << "[INIT-TIMING] First MSF output at " << fmt::format("{:8.2f}", iif_ms) << "ms from start"
                  << " | imu_to_out:" << fmt::format("{:8.2f}", imu_ms) << "ms"
                  << " | gps_to_out:" << fmt::format("{:8.2f}", gps_ms) << "ms"
                  << " | fuse_start_to_out:" << fmt::format("{:8.2f}", fuse_ms) << "ms"
                  << " | fusion_status:" << (int)tcmsf_result_msg_->fusion_status()
                  << " | align_status:" << (int)tcmsf_result_msg_->align_status();
        }
        if (!init_timing_.msf_ready &&
            (tcmsf_result_msg_->fusion_status() == byd::modules::tcmsf::Pose::FusionStatus::Pose_FusionStatus_FULLSTATE ||
             tcmsf_result_msg_->fusion_status() == byd::modules::tcmsf::Pose::FusionStatus::Pose_FusionStatus_GPSONLY)) {
            init_timing_.msf_ready = true;
            init_timing_.msf_ready_duration_ms = std::chrono::duration<double, std::milli>(now - init_timing_.component_start).count();
            AINFO << "[INIT-TIMING] MSF Ready! duration:" << init_timing_.msf_ready_duration_ms << "ms from start";
        }
        if (!init_timing_.msf_aligned_ok &&
            tcmsf_result_msg_->align_status() == byd::modules::tcmsf::Pose_AlignType::TCMSF_Pose_AlignType_ALIGNED) {
            init_timing_.msf_aligned_ok = true;
            init_timing_.align_complete_duration_ms = std::chrono::duration<double, std::milli>(now - init_timing_.component_start).count();
            AINFO << "[INIT-TIMING] MSF ALIGNED! duration:" << init_timing_.align_complete_duration_ms << "ms from start";
        }
        tcmsf_result_msg_->mutable_header()->set_publish_timestamp(apollo::cyber::Time::Now().ToSecond());
        update_msf_from_tcmsf();
        auto tcmsf_output_msg_ = std::make_shared<byd::modules::tcmsf::Pose>(*tcmsf_result_msg_);
        tcmsf_result_writer_->Write(tcmsf_output_msg_);
        auto msf_output_msg_ = std::make_shared<byd::modules::localization::LocResult>(*msf_result_msg_);
        msf_result_writer_->Write(msf_output_msg_);
    };
}

void TCMSFComponent::update_msf_from_tcmsf() {
    constexpr double DEG2RAD = 3.141592653589793 / 180.0;
    if (tcmsf_result_msg_ && msf_result_msg_) {
        auto &tcmsf_header_      = tcmsf_result_msg_->header();
        auto &tcmsf_att_         = tcmsf_result_msg_->attitude();
        auto &tcmsf_vel_         = tcmsf_result_msg_->velocity();
        auto &tcmsf_pos_         = tcmsf_result_msg_->position();
        auto &tcmsf_gyro_bias_   = tcmsf_result_msg_->gyro_bias();
        auto &tcmsf_acc_bias_    = tcmsf_result_msg_->acc_bias();
        auto &tcmsf_map_bias_    = tcmsf_result_msg_->map_bias();
        auto &tcmsf_att_std_     = tcmsf_result_msg_->attitude_std();
        auto &tcmsf_vel_std_     = tcmsf_result_msg_->velocity_std();
        auto &tcmsf_pos_std_     = tcmsf_result_msg_->position_std();
        auto  msf_header_ptr_    = msf_result_msg_->mutable_header();
        auto  msf_att_ptr_       = msf_result_msg_->mutable_orientation();
        auto  msf_vel_ptr_       = msf_result_msg_->mutable_linear_velocity();
        auto  msf_pos_ptr_       = msf_result_msg_->mutable_position();
        auto  msf_gyro_bias_ptr_ = msf_result_msg_->mutable_gyro_bias();
        auto  msf_acc_bias_ptr_  = msf_result_msg_->mutable_acc_bias();
        auto  msf_att_std_ptr_   = msf_result_msg_->mutable_quat_std();
        auto  msf_vel_std_ptr_   = msf_result_msg_->mutable_speed_std();
        auto  msf_pos_std_ptr_   = msf_result_msg_->mutable_pos_std();
        auto  msf_map_bias_ptr_  = msf_result_msg_->mutable_map_bias();

        double lat_mars = 0.0, lon_mars = 0.0;
        // 坐标脱敏，此处不必再加偏
        // wgtochina_lb(0, tcmsf_pos_.lon(), tcmsf_pos_.lat(), tcmsf_pos_.height(), 0, 0, &lon_mars, &lat_mars);
        lon_mars = tcmsf_pos_.lon();
        lat_mars = tcmsf_pos_.lat();

        msf_header_ptr_->set_sequence_num(tcmsf_header_.sequence_num());
        msf_header_ptr_->set_publish_timestamp(tcmsf_header_.publish_timestamp());
        msf_header_ptr_->set_measurement_timestamp(tcmsf_header_.measurement_timestamp());
        msf_att_ptr_->set_qw(tcmsf_att_.qw());
        msf_att_ptr_->set_qx(tcmsf_att_.qx());
        msf_att_ptr_->set_qy(tcmsf_att_.qy());
        msf_att_ptr_->set_qz(tcmsf_att_.qz());
        msf_vel_ptr_->set_x(tcmsf_vel_.x());
        msf_vel_ptr_->set_y(tcmsf_vel_.y());
        msf_vel_ptr_->set_z(tcmsf_vel_.z());
        msf_pos_ptr_->set_lat(lat_mars * DEG2RAD);
        msf_pos_ptr_->set_lon(lon_mars * DEG2RAD);
        msf_pos_ptr_->set_height(tcmsf_pos_.height());
        msf_gyro_bias_ptr_->set_x(tcmsf_gyro_bias_.x());
        msf_gyro_bias_ptr_->set_y(tcmsf_gyro_bias_.y());
        msf_gyro_bias_ptr_->set_z(tcmsf_gyro_bias_.z());
        msf_acc_bias_ptr_->set_x(tcmsf_acc_bias_.x());
        msf_acc_bias_ptr_->set_y(tcmsf_acc_bias_.y());
        msf_acc_bias_ptr_->set_z(tcmsf_acc_bias_.z());
        msf_att_std_ptr_->set_x(tcmsf_att_std_.x());
        msf_att_std_ptr_->set_y(tcmsf_att_std_.y());
        msf_att_std_ptr_->set_z(tcmsf_att_std_.z());
        msf_vel_std_ptr_->set_x(tcmsf_vel_std_.x());
        msf_vel_std_ptr_->set_y(tcmsf_vel_std_.y());
        msf_vel_std_ptr_->set_z(tcmsf_vel_std_.z());
        msf_pos_std_ptr_->set_x(tcmsf_pos_std_.x());
        msf_pos_std_ptr_->set_y(tcmsf_pos_std_.y());
        msf_pos_std_ptr_->set_z(tcmsf_pos_std_.z());

        msf_map_bias_ptr_->set_x(tcmsf_map_bias_.x());
        msf_map_bias_ptr_->set_y(tcmsf_map_bias_.y());
        msf_map_bias_ptr_->set_z(tcmsf_map_bias_.z());

        msf_result_msg_->set_heading(tcmsf_result_msg_->heading());
        msf_result_msg_->set_fusion_status((LocResult::FusionStatus)tcmsf_result_msg_->fusion_status());

        msf_result_msg_->set_ins_status(LocResult::Type::LocResult_Type_GOOD);
    }
}

} // namespace tcmsf
} // namespace byd
