import numpy as np

def calculate_odometry(position_data):
    """
    CALCULATE_ODOMETRY 计算里程数
    :param position_data: 位置数据，包含纬度(第8列), 经度(第9列), 高程(第10列)
    :return: odom: 累积里程数向量
    """
    # 检查输入参数
    if position_data.size == 0 or len(position_data) == 0:
        return np.array([])
    
    if position_data.shape[1] < 10:
        raise ValueError('位置数据列数不足，至少需要10列')

    # 提取位置数据
    lat = position_data[:, 7]  # 纬度 (Python索引从0开始，所以第8列是索引7)
    lon = position_data[:, 8]  # 经度 (第9列是索引8)
    alt = position_data[:, 9]  # 高程 (第10列是索引9)

    # 检查数据是否包含NaN或Inf
    if np.any(np.isnan(lat)) or np.any(np.isnan(lon)) or np.any(np.isnan(alt)) or \
       np.any(np.isinf(lat)) or np.any(np.isinf(lon)) or np.any(np.isinf(alt)):
        print('警告: 位置数据中包含NaN或Inf值，里程计算可能不准确')

    # 如果只有一行数据，返回[0]
    if position_data.shape[0] == 1:
        return np.array([0])

    # 计算相邻点之间的差值
    dlat = np.diff(lat)
    dlon = np.diff(lon)
    dalt = np.diff(alt)

    # 计算相邻点之间的3D距离
    position_diff = np.sqrt(dlat**2 + dlon**2 + dalt**2)

    # 检查计算结果是否包含NaN或Inf
    if np.any(np.isnan(position_diff)) or np.any(np.isinf(position_diff)):
        print('警告: 里程差值计算中出现NaN或Inf值')
        # 将NaN或Inf值替换为0
        mask = np.isnan(position_diff) | np.isinf(position_diff)
        position_diff[mask] = 0

    # 在开头添加0，使累积里程数向量与输入数据长度一致
    position_diff = np.concatenate(([0], position_diff))

    # 计算累积里程数
    odom = np.cumsum(position_diff)
    
    return odom
