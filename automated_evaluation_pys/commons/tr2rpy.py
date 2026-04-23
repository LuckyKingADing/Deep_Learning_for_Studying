import numpy as np

def tr2rpy(R, *args):
    """
    TR2RPY 旋转矩阵转 RPY 角（Z-Y-X顺序）
    :param R: 3x3 旋转矩阵或 4x4 齐次变换矩阵
    :param args: 'deg' 返回角度值（默认弧度）
    :return: angles: [roll, pitch, yaw] 对应绕 X-Y-Z 轴的旋转角
    """
    # 解析输入参数
    deg = False
    if len(args) > 0 and isinstance(args[0], str) and args[0].lower() == 'deg':
        deg = True

    # 提取旋转矩阵部分（兼容齐次变换矩阵）
    R = np.array(R)
    if R.shape[0] >= 3 and R.shape[1] >= 3:
        R = R[:3, :3]
    else:
        raise ValueError("输入矩阵必须至少是3x3的")

    # 计算俯仰角（pitch）
    pitch = np.arctan2(-R[2, 0], np.sqrt(R[0, 0]**2 + R[1, 0]**2))

    # 处理奇异性（pitch接近±90°时）
    if abs(abs(pitch) - np.pi/2) < np.finfo(float).eps:
        roll = 0
        yaw = np.arctan2(R[1, 2], R[0, 2])
    else:
        # 计算横滚角（roll）和偏航角（yaw）
        roll = np.arctan2(R[2, 1]/np.cos(pitch), R[2, 2]/np.cos(pitch))
        yaw = np.arctan2(R[1, 0]/np.cos(pitch), R[0, 0]/np.cos(pitch))

    angles = np.array([roll, pitch, yaw])

    # 转换为角度值（若需要）
    if deg:
        angles = np.rad2deg(angles)

    return angles
