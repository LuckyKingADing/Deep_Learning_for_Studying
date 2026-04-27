#include "base_type.h"
#include "fmt/format.h"
#include "rigid_transform.h"

#include <iomanip>

namespace MSF {
// 定义了输出打印方式，主要用于调试
std::ostream &operator<<(std::ostream &out, const KinematicData &motion) {
    Eigen::Vector3d eulr_ = INS::quaternion2euler(motion.att) * 180 / M_PI;

    auto s_ = fmt::format(
        "t {: >6.4f} │ p {: >6.3f} {: >6.3f} {: >6.3f} │ v {: >6.3f} {: >6.3f} {: >6.3f} │ eulr_ {:6.3f} {:6.3f} {:6.3f} │ {:6.3f}",
        motion.measurement_timestamp,
        motion.pos.x(),
        motion.pos.y(),
        motion.pos.z(),
        motion.vel.x(),
        motion.vel.y(),
        motion.vel.z(),
        eulr_.x(),
        eulr_.y(),
        eulr_.z(),
        motion.ego_longitude_vel);
    out << s_;
    return out;
}

} // namespace MSF