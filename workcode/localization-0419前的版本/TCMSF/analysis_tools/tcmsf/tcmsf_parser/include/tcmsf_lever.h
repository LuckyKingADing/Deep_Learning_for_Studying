#include "Eigen/Dense"
#include <string>

namespace VehicleInfo {

class Lever {
public:
    Eigen::Vector3d antenna = Eigen::Vector3d::Zero();
    Eigen::Vector3d imu     = Eigen::Vector3d::Zero();
    Lever(Eigen::Vector3d antenna_, Eigen::Vector3d imu_) {
        antenna = antenna_;
        imu     = imu_;
    }
};

// 以下坐标系定义均与杆臂配置文档保持一致，使用FLU坐标系

namespace VCPB_ORINX {
Lever hchpc34({0.178, 0.000, 1.456}, {2.30375, -0.54512, 0.32152});
Lever hchpc34_acu({0.1779969, 0.00001245, 1.456017}, {1.85228, 0.008, 0.46628});
} // namespace VCPB_ORINX

namespace ORINN {
Lever MC({-0.873, 0.463, 1.711}, {1.830, 0.356, 0.435});
Lever SA6({-0.51212, 0.44077, 1.56847}, {1.32968, 0.34142, 0.39857});
Lever EK({-0.85588, -0.28301, 1.02325}, {0.54639, -0.27942, 0.31621});
Lever HC25({0.6573, -0.00036, 1.4632}, {-0.7213, 0.2848, 0.4501});
Lever ST25({-0.60947, -0.37274, 1.57512}, {-0.6384, 0.70679, 0.65882});
Lever SH25({-0.40014, 0.47663, 1.5177}, {1.47494, 0.2776, 0.35893});
Lever SF25({-0.10374, 0.0009, 1.86215}, {-0.40883, 0.53716, 0.73415});
Lever HK24({0.11229, 0.0, 1.45168}, {-0.50362, 0.31213, 0.45476});
Lever MR25({-0.85628, 0.24186, 1.79508}, {-0.73733, -0.08238, 0.47627});
} // namespace ORINN

namespace J6M {
Lever SC3({-0.39842, -0.37362, 1.5263}, {1.48687, 0.44136, 0.34796});
Lever HA6({0.18035, 0.0, 1.48246}, {-0.71775, 0.00891, 0.46608});
Lever HA5({0.1802, 0.0, 1.48637}, {-0.53472, 0.08255, 0.45971});
} // namespace J6M

} // namespace VehicleInfo