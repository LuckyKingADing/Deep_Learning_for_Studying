import numpy as np
from itertools import combinations

def find_discontinuous_indices(a, b):
    """
    查找子集b的所有可能索引组合（不连续）
    返回所有使得a[indices[i]] == b[i]的索引组合
    """
    from collections import defaultdict
    
    # 首先建立元素到索引的映射
    element_positions = defaultdict(list)
    for idx, element in enumerate(a):
        element_positions[element].append(idx)
    
    # 对于子集b的每个元素，获取它在a中的所有可能位置
    position_lists = [element_positions.get(elem, []) for elem in b]
    
    # 如果某个元素不在a中，返回空
    if any(len(pos_list) == 0 for pos_list in position_lists):
        return []
    
    # 生成所有可能的组合
    result = []
    from itertools import product
    for combo in product(*position_lists):
        # 检查索引是否严格递增（保持顺序）
        if all(combo[i] < combo[i+1] for i in range(len(combo)-1)):
            result.append(list(combo))
    
    return result


def calculate_errors(diff_data, heading):
    """
    CALCULATE_ERRORS 计算水平误差、横向误差、前进方向误差和垂直误差
    :param diff_data: 差值数据，包含dlat(第8列), dlon(第9列), dalt(第10列)
    :param heading: 航向角信息（度）
    :return: horizontal_error: 水平误差 sqrt(dlat^2 + dlon^2)
             lateral_error: 横向误差（垂直于车辆前进方向）
             vertical_error: 垂直误差 dalt
             forward_error: 前进方向误差（沿着车辆前进方向）
    """
    # 检查输入参数
    if diff_data.shape[1] < 10:
        raise ValueError('差值数据列数不足，至少需要10列')

    # 提取位置误差
    dlat = diff_data[:, 7]   # 纬度误差 (Python索引从0开始，所以第8列是索引7)
    dlon = diff_data[:, 8]   # 经度误差 (第9列是索引8)
    dalt = diff_data[:, 9]   # 高程误差 (第10列是索引9)

    # 计算水平误差
    horizontal_error = np.sqrt(dlat**2 + dlon**2)

    # 首先将航向角从度转换为弧度
    ind = find_discontinuous_indices(heading[:,0],diff_data[:,0])
    heading_rad = (np.deg2rad(heading[ind,1]))[0]

    # 计算横向误差（垂直于车辆前进方向）和前进方向误差（沿着车辆前进方向）
    # 根据用户定义的航向角（北偏西为正，逆时针为正，范围-180到180）
    # 我们使用直接投影的方法计算
    #
    # 在ENU坐标系中：
    # - dlat 是北向误差（y轴分量）
    # - dlon 是东向误差（x轴分量）
    #
    # 航向角是从北向逆时针测量的角度（北偏西为正）
    # 要将ENU坐标系中的误差向量投影到车辆坐标系中：
    # - 车辆前进方向（x轴）：与ENU坐标系的角度为 (pi/2 - heading_rad)
    # - 车辆右侧方向（y轴）：与ENU坐标系的角度为 (-heading_rad)
    #
    # 因此：
    # 前进方向误差 = -dlon * sin(heading_rad) + dlat * cos(heading_rad)
    # 横向误差 = dlon * cos(heading_rad) + dlat * sin(heading_rad)
    #
    # 注意：这里我们假设航向角heading_rad已经正确转换为弧度单位
    # 并且按照用户要求，横向误差相对于车辆右侧为正
    forward_error = -dlon * np.sin(heading_rad) + dlat * np.cos(heading_rad)
    lateral_error = dlon * np.cos(heading_rad) + dlat * np.sin(heading_rad)

    # 垂直误差就是高程误差
    vertical_error = dalt

    return horizontal_error, lateral_error, vertical_error, forward_error
