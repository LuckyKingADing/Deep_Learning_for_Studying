#pragma once

#include "Eigen/Eigen"

#include "base_type.h"
#include "gps_processor.h"
#include "gps_single_processor.h"
#include "imu_processor.h"
#include "kalman_filter.h"
#include "map_processor.h"
#include "vehicle_processor.h"
#include "vision_processor.h"
#include "zupt_processor.h"

#include "geo_trans.h"
#include "processor_interface.h"
#include "traj_logger.h"

namespace MSF {

class TrajAnalysis {
public:
    TrajAnalysis();

private:
    Parameters &parameters_sgt = Parameters::getInstance(TCMSF_CONFIG_FILE_DIR_);

private:
    struct POS_INFO {
        // INS的位置需要投影到天线上，这样在与RTK位置进行对比的时候，才能够避免杆臂的影响。
        double          measurement_timestamp;
        Eigen::Vector3d ins_blh, rtk_blh, delta_blh_in_meters;
        double          ins_heading, ins_traj_heading, rtk_traj_heading;
        double          dp_ins;
        uint64_t        rtk_status;
        POS_INFO() {
            measurement_timestamp = 0.0;
            ins_blh               = Eigen::Vector3d::Zero();
            rtk_blh               = Eigen::Vector3d::Zero();
            delta_blh_in_meters   = Eigen::Vector3d::Zero();
            ins_heading           = 0.0;
            ins_traj_heading      = 0.0;
            rtk_traj_heading      = 0.0;
            dp_ins                = 0.0;
            rtk_status            = 0;
        }
        POS_INFO(
            double                 measurement_timestamp_, //
            const Eigen::Vector3d &ins_blh_,               //
            const Eigen::Vector3d &rtk_blh_,               //
            const Eigen::Vector3d &delta_blh_in_meters_,   //
            double                 ins_heading_,           //
            double                 ins_traj_heading_,      //
            double                 rtk_traj_heading_,      //
            double                 dp_ins_,                //
            uint64_t               rtk_status_             //
        ) {
            measurement_timestamp = measurement_timestamp_;
            ins_blh               = ins_blh_;
            rtk_blh               = rtk_blh_;
            delta_blh_in_meters   = delta_blh_in_meters_;
            ins_heading           = ins_heading_;
            ins_traj_heading      = ins_traj_heading_;
            rtk_traj_heading      = rtk_traj_heading_;
            dp_ins                = dp_ins_;
            rtk_status            = rtk_status_;
        }
    };

    POS_INFO init_pos;
    POS_INFO pre_pos;

private:
    constexpr static size_t MAX_QUEUE_SIZE = 10;

private:
    std::deque<POS_INFO> traj_queue;

private:
    bool FirstTimeInitializationReady;

public:
    void Analysis(double m_time_, const Eigen::Vector3d &ins_blh_antenna_, const Eigen::Vector3d &rtk_blh_, const Eigen::Quaterniond &att, uint64_t rtk_status_, double ins_heading_, double long_acc_);
    bool isFirstTimeInitializationReady();
    void resetFirstTimeInitialization();
    void setFirstTimeInitialization();

private:
    byd::geo::LocalTrans local_trans;
};

class GnssFusionModeAdaption {

    // 做一个卫星定位融合模式的自适应
    // 如果单点解持续一定里程，就切换到单点解融合模式
    // 如果固定解持续一定里程，就切换到固定解融合模式

public:
    GnssFusionModeAdaption();

private:
    Parameters::GnssFusionMode recommend_fusion_mode;

private:
    constexpr static double MILEAGE_SWITCH_TO_GNSS_LC_MODE = 1000.0;
    constexpr static double MILEAGE_SWITCH_TO_RTK_LC_MODE  = 50.0;

private:
    uint64_t pre_gnss_status;
    double   pre_gnss_timestamp;
    double   continuous_gnss_mileage;
    double   continuous_rtk_mileage;

private:
    void clear_mileage();

public:
    void                       update(const GnssDataPtr gps_data_ptr_, const StatePtr state_ptr_);
    Parameters::GnssFusionMode recommend_mode();
};

class ProcessorImpl : public byd::tcmsf::processor::Processor {

public:
    ProcessorImpl();
    ~ProcessorImpl();

    virtual bool ProcessImuData(const ImuDataPtr imu_data_ptr, double dt_, StatePtr state_ptr) override final;
    virtual bool ProcessGnssData(const GnssDataPtr gps_data_ptr, StatePtr state_ptr, const KinematicDataPtr delta_ptr, const KinematicDataPtr dr_ptr) override final;
    virtual bool ProcessVehicleData(const VehicleDataPtr vehicle_data_ptr, StatePtr state_ptr, const KinematicDataPtr delta_ptr) override final;
    virtual bool ProcessVisionData(const VisionFusionDataPtr vis_data_ptr, StatePtr state_ptr, const KinematicDataPtr delta_ptr) override final;
    virtual bool ProcessMapData(const MapPosDataPtr map_data_ptr, StatePtr state_ptr, const KinematicDataPtr delta_ptr) override final;
    virtual void AttitudeReference(const MSF::ImuData &, const MSF::VehicleData &, double dt_, StatePtr state_ptr, const KinematicDataPtr inner_motion_state_ptr) override final;

private:
    Parameters &parameters_sgt = Parameters::getInstance(TCMSF_CONFIG_FILE_DIR_);

private:
    std::unique_ptr<Initializer>      initializer_       = nullptr;
    std::unique_ptr<ImuProcessor>     imu_processor_     = nullptr;
    std::unique_ptr<GpsProcessor>     gps_processor_     = nullptr;
    std::unique_ptr<VehicleProcessor> vehicle_processor_ = nullptr;
    std::unique_ptr<VisionProcessor>  vision_processor_  = nullptr;
    std::unique_ptr<MapProcessor>     map_processor_     = nullptr;
    std::unique_ptr<ZuptProcessor>    zupt_processor_    = nullptr;
    std::unique_ptr<AttReference>     att_referencer_    = nullptr;

    std::unique_ptr<GpsSingleProcessor> gps_single_processor_ = nullptr;

    // public:
    //     KfPtr<21, 3> kf_ptr_ = nullptr;

private:
    byd::geo::Trans geotrans;
    void            BacktrackState(StatePtr state_ptr, const KinematicDataPtr delta_ptr, bool enable_vel_compesation);
    void            AdvanceState(StatePtr state_ptr, const KinematicDataPtr delta_ptr, bool enable_vel_compesation);

private:
    ImuDataPtr pre_imu_data_ptr_ = nullptr;

private:
    uint64_t zupt_damper_count = 0;

private:
    VehicleDataPtr pre_veh_data_ptr_ = nullptr;
    uint64_t       zupt_count_by_pls = 0;
    bool           judge_zupt_by_pls_count(const VehicleDataPtr pre_msg_, const VehicleDataPtr cur_msg_);

private:
    TrajAnalysis init_traj_analysis_ = TrajAnalysis();

private:
    bool isStateReasonable(const StatePtr state_ptr);

private:
    std::string state_debug_info(const StatePtr state_ptr);

private:
    GnssDataPtr pre_gnss_data_ptr_ = nullptr;

private:
    StateSwitchInfo zspd_switch_info;

private:
    byd::traj_logger::BatchDeltaLocLogger loc_logger{20};

private:
    GnssFusionModeAdaption gnss_fusion_mode_adaption;

private:
    void calcPosInnoRangeNorm(StatePtr state_ptr, const Eigen::Vector3d &pos_std_);
};

} // namespace MSF