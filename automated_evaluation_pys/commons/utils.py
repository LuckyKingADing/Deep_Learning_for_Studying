
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

# 处理常用的完全对齐的两个矩阵差值
# 首列为时间，不做差值
# 第一列为time，接下来的前21维为pry，vn，lat lon alt，eb，db，dp kod dy，map
# 数据必须列含义一致，不要求维度必须完整
def calculateDifference(data1: np.ndarray, data2: np.ndarray,radtag = 0) -> np.ndarray:
    """
    计算两个数据集之间的差异
    """
    # 确保两个数据集有相同的维度,行一一对应
    min_col = min(data1.shape[1],data2.shape[1])
    mlen = data1.shape[0]
    diff_data = np.zeros((mlen,min_col))
    diff_data[:,0] = data1[:,0]
    diff_data[:,1:min_col] = data1[:,1:min_col] - data2[:,1:min_col]
    
    if data1.shape[0] != data2.shape[0]:
        print("data not matched.")
        exit(1)
        
    if radtag == 1:
        angle = np.pi
    else:
        angle = 180
    # 特殊处理角度差异，不同索引使用不同的范围限制
    for j in range(3):
        i = j + 1
        if j == 0:  # 第1列（索引0），限制在[-π/2, π/2]范围内
            # 先将角度归一化到[0, π]范围
            diff_data[:, i] = diff_data[:, i] % angle
            
            # 将超过π/2的角度映射到[-π/2, π/2]范围
            mask = diff_data[:, i] > angle/2
            diff_data[mask, i] = diff_data[mask, i] - angle
            
        else:  # 第2、3列（索引1和2），限制在[-π, π]范围内
            # 使用取模运算将角度映射到[-π, π]范围内
            diff_data[:, i] = ((diff_data[:, i] + angle) % (2 * angle)) - angle
    
    return diff_data

def alignDataByTimeTcSol(data1i, time1i, data2, time2, tol, x=1):
    """
    时间对齐函数（带容差）
    :param data1i: 第一个数据集
    :param time1i: 第一个时间序列
    :param data2: 第二个数据集
    :param time2: 第二个时间序列
    :param tol: 时间容差
    :param x: 归化倍数，默认为1
    :return: data1_aligned: 对齐后的第一个数据集
             data2_aligned: 对齐后的第二个数据集
             common_time: 共同时间序列
    """
    # 根据条件选择数据（这里采用else分支，即直接使用输入数据）
    data1 = data1i
    time1 = time1i

    # 计算时间的容差化整
    temp_rounded_time1 = np.round(time1 / tol)
    temp_rounded_time2 = np.round(time2 / tol)

    # 将时间按照x的整数倍进行归化
    rounded_time1 = np.round(temp_rounded_time1 / x) * x
    rounded_time2 = np.round(temp_rounded_time2 / x) * x

    # 寻找交集
    # 使用numpy的intersect1d来找到共同元素及其索引
    common_vals, idx1, idx2 = np.intersect1d(rounded_time1, rounded_time2, return_indices=True)

    # 根据找到的索引提取对齐的数据
    data1_aligned = data1[idx1, :]
    data2_aligned = data2[idx2, :]
    common_time = time1[idx1]

    return data1_aligned, data2_aligned, common_time,idx1

def InterpState(state, t, t_ref):
    """
    插值函数，支持时间非单调递增的情况
    :param state: 待插值的状态数据
    :param t: 原始时间序列
    :param t_ref: 参考时间序列
    :return: 插值后的状态数据
    """
    # 检查时间是否单调递增
    if not np.all(t[1:] >= t[:-1]):
        # 如果时间不是单调递增的，先排序
        sorted_indices = np.argsort(t)
        t_sorted = t[sorted_indices]
        state_sorted = state[sorted_indices, :]
    else:
        # 时间已经是单调递增的
        t_sorted = t
        state_sorted = state
    
    # 检查时间范围是否重叠
    t_min, t_max = np.min(t_sorted), np.max(t_sorted)
    t_ref_min, t_ref_max = np.min(t_ref), np.max(t_ref)
    
    print(f"Original time range: [{t_min}, {t_max}]")
    print(f"Reference time range: [{t_ref_min}, {t_ref_max}]")
    
    # 创建插值函数，对于超出范围的值使用边界值
    state_ = np.zeros([t_ref.shape[0], state.shape[1]])
    for i in range(state.shape[1]):
        # 使用scipy的interp1d，设置fill_value为'extrapolate'或使用边界值
        f = interp1d(t_sorted, state_sorted[:, i], kind='linear', bounds_error=False, fill_value='extrapolate')
        state_[:, i] = f(t_ref)
    
    return state_

def filter_rows_by_column_value(data, col_index, value):
    """
    筛选 numpy 数组中指定列等于某个值的行
    
    :param data: numpy 数组
    :param col_index: 要筛选的列索引
    :param value: 筛选值
    :return: 筛选后的数组
    """
    mask = data[:, col_index] == value
    return data[mask]


def set_y_lim_to_x_range(xlim_range):
    """
    手动设置y轴范围以适应当前x轴范围内的数据
    """
    ax = plt.gca()
    all_y_data = []
    
    # 获取所有绘制的数据线
    for line in ax.get_lines():
        xdata, ydata = line.get_data()
        if len(xdata) > 0 and len(ydata) > 0:
            # 筛选在 xlim 范围内的数据点
            mask = (xdata >= xlim_range[0]) & (xdata <= xlim_range[1])
            if np.any(mask):
                all_y_data.extend(ydata[mask])
    
    if all_y_data:
        y_min, y_max = min(all_y_data), max(all_y_data)
        # 添加10%的边距
        if y_max != y_min:
            margin = (y_max - y_min) * 0.1
        else:
            margin = 1.0
        plt.ylim(y_min - margin, y_max + margin)
        
def dpos2den(data,pos0):
    d2r = np.pi / 180
    d2m = d2r * 6378137
    d2mlon = d2r * (6378137 * np.cos(pos0[0] * d2r))
    data[:, 0] = (data[:, 0] - pos0[0]) * d2m
    data[:, 1] = (data[:, 1] - pos0[1]) * d2mlon
    return data