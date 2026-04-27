import numpy as np
import os
import csv
from pathlib import Path
import math
from datetime import datetime
import fnmatch
from typing import Tuple, List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.interpolate import interp1d


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


def compare_tc_lc_ref_100c_with_plots(lcpath, tcpath, rtspath, save_dir):
    """
    比较TC、LC和RTS数据与参考数据，并绘制7副图，同时保存特定时间段的数据
    """
    # 导入所需的模块
    from readmsf_debug_state import readmsf_debug_state
    from read_rts_file import read_rts_file
    
    # 读取数据
    lcs = readmsf_debug_state(lcpath, 0)
    tcs = readmsf_debug_state(tcpath, 0)
    rts0 = read_rts_file(rtspath, 1)

    # 坐标转换参数
    pi = 3.14159265358979
    d2r = pi / 180
    r2m = d2r * 6378137
    
    # 检查数据维度是否足够进行坐标转换
    if lcs.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        lcs[:, 7:9] = (lcs[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if tcs.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        tcs[:, 7:9] = (tcs[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if rts0.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        rts0[:, 7:9] = (rts0[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    
    # RTS 插值
    tref = tcs[:,0]
    print(tref[0])
    print(tref[1])
    print(tref[2])
    rts = InterpState(rts0, rts0[:,0], tref)

    # 数据对齐
    aligned_data1, aligned_data2, common_timelc = alignDataByTimeTcSol(
        lcs, lcs[:, 0], rts, rts[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datalc = calculateDifferenceTcSol(aligned_data1, aligned_data2)
    diff_datalc = att_diff_adjust(diff_datalc)

    print(lcs[0, 0])
    print(rts[0, 0])
    
    aligned_data1, aligned_data2, common_timetc = alignDataByTimeTcSol(
        tcs, tcs[:, 0], rts, rts[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datatc = calculateDifferenceTcSol(aligned_data1, aligned_data2)
    diff_datatc = att_diff_adjust(diff_datatc)

    t0 = tcs[0, 0]  # 第1列 (Python索引0对应MATLAB的1)

    plt.close('all')
    tilestr = ['att', 'vel', 'pos','eb ','db ','kod','mpe']
    
    # 读取数据长度
    ltc = tcs[-1, 0] - t0
    llc = lcs[-1, 0] - t0
    readlen = max([ltc, llc])
    xranges = [0, readlen * 1.1]
    
    # 存储超过阈值的时间段
    lc_high_norm_times = []
    tc_high_norm_times = []
    
    for si in range(1, 8):  # 1:7 对应Python中的range(1, 8)，总共7个子图
        plt.figure(si, figsize=(12, 8))
        plt.suptitle(tilestr[si-1])  # tilestr(si,) 对应Python中的tilestr[si-1]

        for i in range(1, 4):  # 1:3 对应Python中的range(1, 4)
            pi = 3 * (si - 1) + 1 + i  # pi=3*(si-1)+1+i
            pi_idx = pi - 1  # 转换为Python的0基索引

            plt.subplot(2, 3, i)
            # 检查数据维度是否足够
            if si < 4:
                if rts.shape[1] > pi_idx:  # 改为 > 以确保索引有效
                    plt.plot(rts[:, 0] - t0, rts[:, pi_idx], "-o", linewidth=1, color='magenta', markersize=1, label='RTS')
            if lcs.shape[1] > pi_idx:  # 改为 > 以确保索引有效
                plt.plot(lcs[:, 0] - t0, lcs[:, pi_idx], "-o", linewidth=1, color='red', markersize=1, label='LC')
            if tcs.shape[1] > pi_idx:  # 改为 > 以确保索引有效
                plt.plot(tcs[:, 0] - t0, tcs[:, pi_idx], "-o", linewidth=1, color='blue', markersize=1, label='TC')
            plt.xlim(xranges)
            plt.grid(True)
            plt.legend()
            
            # 绘制差值图
            if si < 4:
                plt.subplot(2, 3, i + 3)
                # 检查数据维度是否足够
                if diff_datalc.shape[1] > pi_idx - 1:
                    lc_diff_data = diff_datalc[:, pi_idx - 1]
                    plt.plot(common_timelc - t0, lc_diff_data, "-o", linewidth=1, color='red', markersize=1, label='LC Diff')
                    
                    # 检查si=3时的norm是否大于2.0
                    if si == 3:  # 当si=3时，检查第3列
                        # 计算norm（假设是向量的模长）
                        if pi_idx - 1 == 2:  # 第3列（索引2）
                            norm_values = np.abs(lc_diff_data)
                            high_norm_mask = norm_values > 2.0
                            if np.any(high_norm_mask):
                                high_norm_times = common_timelc[high_norm_mask] - t0
                                lc_high_norm_times.extend(high_norm_times.tolist())
                
                if diff_datatc.shape[1] > pi_idx - 1:
                    tc_diff_data = diff_datatc[:, pi_idx - 1]
                    plt.plot(common_timetc - t0, tc_diff_data, "-o", linewidth=1, color='blue', markersize=1, label='TC Diff')
                    
                    # 检查si=3时的norm是否大于2.0
                    if si == 3:  # 当si=3时，检查第3列
                        # 计算norm（假设是向量的模长）
                        if pi_idx - 1 == 2:  # 第3列（索引2）
                            norm_values = np.abs(tc_diff_data)
                            high_norm_mask = norm_values > 2.0
                            if np.any(high_norm_mask):
                                high_norm_times = common_timetc[high_norm_mask] - t0
                                tc_high_norm_times.extend(high_norm_times.tolist())

                plt.grid(True)
                plt.xlim(xranges)
                plt.legend()
        
        # 保存图像
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f'{tilestr[si-1]}_comparison.png'))
        plt.close()
    
    # 保存超过阈值的时间段到文件
    if lc_high_norm_times:
        with open(os.path.join(save_dir, 'lc_high_norm_times.txt'), 'w') as f:
            for time in lc_high_norm_times:
                f.write(f"{time}\n")
    
    if tc_high_norm_times:
        with open(os.path.join(save_dir, 'tc_high_norm_times.txt'), 'w') as f:
            for time in tc_high_norm_times:
                f.write(f"{time}\n")


def matchAllDirectories(foldobjbase: str, foldrefbase: str, verstr: str, resultfile: str, reffilePattern: str) -> Tuple[List[str], List[str]]:
    """
    匹配所有目录的函数，移除了日期格式筛选
    """
    # 获取所有对象目录
    objBasePaths = getAllSubdirectories(foldobjbase)
    # 获取所有参考目录
    refBasePaths = getAllSubdirectories(foldrefbase)
    
    # 空数组保护
    if len(refBasePaths) == 0 or len(objBasePaths) == 0:
        raise ValueError('未找到有效目录')
    
    # 初始化匹配路径列表
    objMatchedPaths = []
    refMatchedPaths = []
    
    # 简单匹配：按顺序匹配对象目录和参考目录
    min_len = min(len(objBasePaths), len(refBasePaths))
    
    for i in range(min_len):
        # 构建目标文件路径
        objFilePath = os.path.join(objBasePaths[i], verstr, resultfile)
        # 构建参考文件路径 - 在对应的参考目录中查找匹配的文件
        refFilePath = buildResultPath(refBasePaths[i], 'postprocessresult', reffilePattern)
        
        # 保存到输出列表
        objMatchedPaths.append(objFilePath)
        refMatchedPaths.append(refFilePath)
    
    return objMatchedPaths, refMatchedPaths


def getAllSubdirectories(baseDir: str) -> List[str]:
    """
    获取所有子目录，移除了日期格式筛选
    """
    pathList = []
    
    # 获取目录下的所有子目录
    for item in os.listdir(baseDir):
        itemPath = os.path.join(baseDir, item)
        if os.path.isdir(itemPath) and not item.startswith('.'):
            pathList.append(itemPath)
    
    return pathList


def buildResultPath(basePath: str, subDir: str, filePattern: str) -> str:
    """
    构建目标文件路径
    规则：若 basePath/subDir 下匹配 filePattern 的文件数量 ≠ 1，则报错
    """
    # 拼接目标目录路径
    targetDir = os.path.join(basePath, subDir)
    
    # 检查目录是否存在
    if not os.path.isdir(targetDir):
        raise ValueError(f'目录不存在: {targetDir}')
    
    # 获取匹配文件列表
    fileList = []
    for file in os.listdir(targetDir):
        filePath = os.path.join(targetDir, file)
        if os.path.isfile(filePath) and fnmatch.fnmatch(file, filePattern):
            fileList.append(file)
    
    # 验证文件数量
    if len(fileList) == 0:
        raise ValueError(f'目录中未找到匹配文件: {os.path.join(targetDir, filePattern)}')
    elif len(fileList) > 1:
        raise ValueError(f'目录中存在多个匹配文件: {targetDir}')
    
    # 返回唯一文件的完整路径
    return os.path.join(targetDir, fileList[0])


def getParentDirectory(path: str) -> str:
    """
    获取父目录
    """
    return os.path.dirname(os.path.dirname(path))


def result_statistics(diff_datalc: np.ndarray, diff_datatc: np.ndarray, tcstart: int) -> Dict[str, Any]:
    """
    计算结果统计信息
    """
    # 初始化统计结构体
    stats = {}
    
    # ===== 合并列并重组数据 =====
    # LC数据处理
    lc_merged, lc_last2 = merge_columns(diff_datalc)
    
    # TC数据处理
    tc_data = diff_datatc[tcstart-1:, :]  # MATLAB索引从1开始，Python从0开始
    tc_merged, tc_last2 = merge_columns(tc_data)
    
    # ===== LC部分统计 =====
    stats['LC'] = {}
    stats['LC']['rms'] = np.sqrt(np.mean(lc_merged**2, axis=0))
    stats['LC']['max_abs'] = np.max(np.abs(lc_merged), axis=0)
    stats['LC']['interval_percent'] = calc_interval_percent(lc_last2)
    
    # ===== TC部分统计 =====
    stats['TC'] = {}
    stats['TC']['rms'] = np.sqrt(np.mean(tc_merged**2, axis=0))
    stats['TC']['max_abs'] = np.max(np.abs(tc_merged), axis=0)
    stats['TC']['interval_percent'] = calc_interval_percent(tc_last2)
    
    return stats


def merge_columns(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    合并列的辅助函数
    """
    # 1-3列: 姿态误差 (pitch, roll, yaw)
    attitude = np.abs(data[:, 0:3])
    
    # 4-5列合并为水平速度误差: sqrt(ve^2 + vn^2)
    hor_velocity = np.sqrt(data[:, 3]**2 + data[:, 4]**2)
    
    # 6列: 垂直速度误差 (vu)
    ver_velocity = np.abs(data[:, 5])
    
    # 7-8列合并为水平位置误差: sqrt(dlat^2 + dlon^2)
    hor_position = np.sqrt(data[:, 6]**2 + data[:, 7]**2)
    
    # 9列: 高程误差 (dalt)
    altitude = np.abs(data[:, 8])
    
    # 合并后的数据矩阵 (7列)
    merged_data = np.column_stack((attitude, hor_velocity, ver_velocity, hor_position, altitude))
    
    # 最后2列用于区间统计
    last2 = np.column_stack((hor_position, altitude))
    
    return merged_data, last2


def calc_interval_percent(data: np.ndarray) -> np.ndarray:
    """
    计算区间百分比的辅助函数
    """
    ranges = [0.2, 0.5, 1.0, float('inf')]
    num_rows, num_cols = data.shape
    percent_matrix = np.zeros((num_cols, len(ranges)))
    
    for col in range(num_cols):
        col_data = data[:, col]
        # 计算每个区间的计数
        for idx, range_val in enumerate(ranges):
            if idx == 0:
                count = np.sum((col_data >= 0) & (col_data < range_val))
            elif idx == len(ranges) - 1:  # 最后一个范围是 > 1
                count = np.sum(col_data >= ranges[idx-1])
            else:
                count = np.sum((col_data >= ranges[idx-1]) & (col_data < range_val))
            percent_matrix[col, idx] = (count / num_rows) * 100
    
    return percent_matrix


def load100ccsv(file_path: str, gpst0: float, gpste: float) -> np.ndarray:
    """
    加载CSV文件
    """
    data = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            # 转换每行数据为浮点数
            try:
                numeric_row = [float(x) for x in row]
                data.append(numeric_row)
            except ValueError:
                # 如果某行无法转换为数字，则跳过
                continue
    return np.array(data)


def readSensorDataTcSol(file_path: str, dt: float) -> np.ndarray:
    """
    读取传感器数据
    """
    # 这里需要根据实际的数据格式来实现
    # 假设是CSV格式的数据
    if file_path.endswith('.csv'):
        data = load100ccsv(file_path, 0, 0)
    else:
        # 其他格式的处理
        data = np.loadtxt(file_path)
    return data


def alignDataByTimeTcSol(data1i: np.ndarray, time1i: np.ndarray, data2: np.ndarray, time2: np.ndarray, tol: float, x: int = 1) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    根据时间对齐数据
    """
    # 时间对齐的实现
    # 找到共同的时间范围
    min_time = max(np.min(time1i), np.min(time2))
    max_time = min(np.max(time1i), np.max(time2))
    
    # 筛选在共同时间范围内的数据
    mask1 = (time1i >= min_time) & (time1i <= max_time)
    mask2 = (time2 >= min_time) & (time2 <= max_time)
    
    filtered_time1 = time1i[mask1]
    filtered_time2 = time2[mask2]
    filtered_data1 = data1i[mask1]
    filtered_data2 = data2[mask2]
    
    # 使用插值方法对齐数据
    if len(filtered_time1) > 0 and len(filtered_time2) > 0:
        # 创建共同时间轴
        common_time = np.intersect1d(filtered_time1, filtered_time2)
        
        if len(common_time) == 0:
            # 如果没有完全相同的时间点，使用容差范围内的最近邻
            common_time = np.sort(np.unique(np.concatenate([filtered_time1, filtered_time2])))
            # 应用容差
            common_time = common_time[::x]  # 按x间隔采样
        
        # 插值对齐数据
        aligned_data1 = np.zeros((len(common_time), data1i.shape[1]))
        aligned_data2 = np.zeros((len(common_time), data2.shape[1]))
        
        for col in range(data1i.shape[1]):
            if len(filtered_time1) > 1:
                f1 = interp1d(filtered_time1, filtered_data1[:, col], kind='linear', bounds_error=False, fill_value=np.nan)
                aligned_data1[:, col] = f1(common_time)
            else:
                aligned_data1[:, col] = filtered_data1[0, col] if len(filtered_data1) > 0 else np.nan
                
        for col in range(data2.shape[1]):
            if len(filtered_time2) > 1:
                f2 = interp1d(filtered_time2, filtered_data2[:, col], kind='linear', bounds_error=False, fill_value=np.nan)
                aligned_data2[:, col] = f2(common_time)
            else:
                aligned_data2[:, col] = filtered_data2[0, col] if len(filtered_data2) > 0 else np.nan
        
        # 处理NaN值
        valid_mask = ~(np.isnan(aligned_data1).any(axis=1) | np.isnan(aligned_data2).any(axis=1))
        common_time = common_time[valid_mask]
        aligned_data1 = aligned_data1[valid_mask]
        aligned_data2 = aligned_data2[valid_mask]
        
        return aligned_data1, aligned_data2, common_time
    else:
        return np.array([]), np.array([]), np.array([])


def calculateDifferenceTcSol(data1: np.ndarray, data2: np.ndarray) -> np.ndarray:
    """
    计算两个数据集之间的差异
    """
    # 确保两个数据集有相同的维度
    min_len = min(len(data1), len(data2))
    diff_data = data1[:min_len] - data2[:min_len]
    
    # 特殊处理角度差异（第1-3列），确保在[-π, π]范围内
    for i in range(min(3, diff_data.shape[1])):
        diff_data[:, i] = ((diff_data[:, i] + np.pi) % (2 * np.pi)) - np.pi
    
    return diff_data


def att_diff_adjust(att: np.ndarray) -> np.ndarray:
    """
    调整姿态差异
    """
    # 对于姿态角（前几列），调整到合适的范围
    if att.size == 0:
        return att
    
    adjusted_att = att.copy()
    
    # 假设前3列是姿态角（pitch, roll, yaw），调整到[-π, π]范围
    for i in range(min(3, att.shape[1])):
        adjusted_att[:, i] = ((att[:, i] + np.pi) % (2 * np.pi)) - np.pi
    
    return adjusted_att


def plot_stats_comparison(stats: Dict[str, Any], save_dir: str):
    """
    绘制统计比较图
    """
    os.makedirs(save_dir, exist_ok=True)
    
    # 创建图形
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # RMS比较
    lc_rms = stats['LC']['rms']
    tc_rms = stats['TC']['rms']
    labels = ['Pitch', 'Roll', 'Yaw', 'Hor Vel', 'Ver Vel', 'Hor Pos', 'Alt']
    
    x = np.arange(len(labels))
    width = 0.35
    
    axes[0, 0].bar(x - width/2, lc_rms, width, label='LC', alpha=0.8)
    axes[0, 0].bar(x + width/2, tc_rms, width, label='TC', alpha=0.8)
    axes[0, 0].set_xlabel('Parameter')
    axes[0, 0].set_ylabel('RMS Error')
    axes[0, 0].set_title('RMS Comparison')
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(labels, rotation=45)
    axes[0, 0].legend()
    
    # 最大绝对值比较
    lc_max = stats['LC']['max_abs']
    tc_max = stats['TC']['max_abs']
    
    axes[0, 1].bar(x - width/2, lc_max, width, label='LC', alpha=0.8)
    axes[0, 1].bar(x + width/2, tc_max, width, label='TC', alpha=0.8)
    axes[0, 1].set_xlabel('Parameter')
    axes[0, 1].set_ylabel('Max Absolute Error')
    axes[0, 1].set_title('Max Absolute Error Comparison')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(labels, rotation=45)
    axes[0, 1].legend()
    
    # 区间百分比比较
    lc_intervals = stats['LC']['interval_percent']
    tc_intervals = stats['TC']['interval_percent']
    
    interval_labels = ['0-0.2', '0.2-0.5', '0.5-1.0', '>1']
    
    ax_idx = 1
    for i in range(lc_intervals.shape[0]):  # 遍历不同类型的误差（水平位置、高程）
        ax = axes[ax_idx // 2, ax_idx % 2] if ax_idx < 4 else axes[1, 1]
        
        x_int = np.arange(len(interval_labels))
        ax.bar(x_int - width/2, lc_intervals[i, :], width, label='LC', alpha=0.8)
        ax.bar(x_int + width/2, tc_intervals[i, :], width, label='TC', alpha=0.8)
        ax.set_xlabel('Interval')
        ax.set_ylabel('Percentage (%)')
        ax.set_title(f'Interval Distribution - {"Hor Pos" if i==0 else "Alt"}')
        ax.set_xticks(x_int)
        ax.set_xticklabels(interval_labels)
        ax.legend()
        
        ax_idx += 1
        if ax_idx > 3:  # 只显示前几个子图
            break
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'stats_comparison.png'))
    plt.close()


def plotStatsComparisonaAll(statsall: List[Dict[str, Any]], save_dir: str):
    """
    绘制所有数据集的统计比较图
    """
    os.makedirs(save_dir, exist_ok=True)
    
    if not statsall:
        return
    
    n_datasets = len(statsall)
    datasets = [getattr(stat, 'dataset', f'Dataset_{i}') for i, stat in enumerate(statsall)]
    
    # 创建图形
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 准备数据
    lc_rms_all = np.array([stat['LC']['rms'] for stat in statsall])
    tc_rms_all = np.array([stat['TC']['rms'] for stat in statsall])
    
    labels = ['Pitch', 'Roll', 'Yaw', 'Hor Vel', 'Ver Vel', 'Hor Pos', 'Alt']
    x = np.arange(len(labels))
    width = 0.35
    
    # RMS比较
    axes[0, 0].plot(lc_rms_all, label='LC', marker='o')
    axes[0, 0].plot(tc_rms_all, label='TC', marker='s')
    axes[0, 0].set_xlabel('Dataset Index')
    axes[0, 0].set_ylabel('RMS Error')
    axes[0, 0].set_title('RMS Error Across Datasets')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # 平均RMS比较
    avg_lc_rms = np.mean(lc_rms_all, axis=0)
    avg_tc_rms = np.mean(tc_rms_all, axis=0)
    
    axes[0, 1].bar(x - width/2, avg_lc_rms, width, label='LC Avg', alpha=0.8)
    axes[0, 1].bar(x + width/2, avg_tc_rms, width, label='TC Avg', alpha=0.8)
    axes[0, 1].set_xlabel('Parameter')
    axes[0, 1].set_ylabel('Average RMS Error')
    axes[0, 1].set_title('Average RMS Error Comparison')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(labels, rotation=45)
    axes[0, 1].legend()
    
    # 最大值比较
    lc_max_all = np.array([stat['LC']['max_abs'] for stat in statsall])
    tc_max_all = np.array([stat['TC']['max_abs'] for stat in statsall])
    
    avg_lc_max = np.mean(lc_max_all, axis=0)
    avg_tc_max = np.mean(tc_max_all, axis=0)
    
    axes[1, 0].bar(x - width/2, avg_lc_max, width, label='LC Max', alpha=0.8)
    axes[1, 0].bar(x + width/2, avg_tc_max, width, label='TC Max', alpha=0.8)
    axes[1, 0].set_xlabel('Parameter')
    axes[1, 0].set_ylabel('Average Max Absolute Error')
    axes[1, 0].set_title('Average Max Absolute Error Comparison')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(labels, rotation=45)
    axes[1, 0].legend()
    
    # 显示第一个数据集的区间分布
    if hasattr(statsall[0]['LC'], 'interval_percent'):
        lc_intervals = statsall[0]['LC']['interval_percent']
        tc_intervals = statsall[0]['TC']['interval_percent']
        
        interval_labels = ['0-0.2', '0.2-0.5', '0.5-1.0', '>1']
        x_int = np.arange(len(interval_labels))
        
        axes[1, 1].bar(x_int - width/2, lc_intervals[0, :], width, label='LC Hor Pos', alpha=0.8)
        axes[1, 1].bar(x_int + width/2, tc_intervals[0, :], width, label='TC Hor Pos', alpha=0.8)
        axes[1, 1].set_xlabel('Interval')
        axes[1, 1].set_ylabel('Percentage (%)')
        axes[1, 1].set_title('Interval Distribution (First Dataset)')
        axes[1, 1].set_xticks(x_int)
        axes[1, 1].set_xticklabels(interval_labels)
        axes[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'all_stats_comparison.png'))
    plt.close()


def StatsComparisonAll(statsall: List[Dict[str, Any]], save_dir: str):
    """
    生成所有统计比较报告
    """
    os.makedirs(save_dir, exist_ok=True)
    
    if not statsall:
        return
    
    # 输出汇总统计信息
    with open(os.path.join(save_dir, 'summary_stats.txt'), 'w') as f:
        f.write("Summary Statistics Across All Datasets\n")
        f.write("="*50 + "\n\n")
        
        # 计算平均值
        lc_rms_all = np.array([stat['LC']['rms'] for stat in statsall])
        tc_rms_all = np.array([stat['TC']['rms'] for stat in statsall])
        
        avg_lc_rms = np.mean(lc_rms_all, axis=0)
        avg_tc_rms = np.mean(tc_rms_all, axis=0)
        
        f.write("Average RMS Errors:\n")
        f.write("Parameter\tLC\t\tTC\n")
        params = ['Pitch', 'Roll', 'Yaw', 'Hor Vel', 'Ver Vel', 'Hor Pos', 'Alt']
        for i, param in enumerate(params):
            f.write(f"{param}\t\t{avg_lc_rms[i]:.4f}\t\t{avg_tc_rms[i]:.4f}\n")
        
        f.write("\n" + "-"*30 + "\n")
        
        # 计算最大值
        lc_max_all = np.array([stat['LC']['max_abs'] for stat in statsall])
        tc_max_all = np.array([stat['TC']['max_abs'] for stat in statsall])
        
        max_lc_max = np.max(lc_max_all, axis=0)
        max_tc_max = np.max(tc_max_all, axis=0)
        
        f.write("Maximum Max Absolute Errors:\n")
        f.write("Parameter\tLC\t\tTC\n")
        for i, param in enumerate(params):
            f.write(f"{param}\t\t{max_lc_max[i]:.4f}\t\t{max_tc_max[i]:.4f}\n")


def bppaps(foldobjbase_lc: str = 'D:/dockers/huiguan_res/TCMSF_interface_0909_c652cb3',
           foldobjbase_tc: str = None,
           foldrefbase: str = 'D:/dockers/datas/202504/',
           resultfile: str = 'tcmsf_sol.csv'):
    """
    BPPAPS算法实现 - 批量处理精度和图片保存（移除日期筛选版本）
    需要真值文件
    """
    if foldobjbase_tc is None:
        foldobjbase_tc = foldobjbase_lc
    
    pi = 3.14159265358979
    d2r = pi / 180  # 度转弧度
    r2m = d2r * 6378137  # 弧度转米（地球半径）

    verstr = 'tcmsf_18f4b35'  # tcmsf_7487d05 lc_829d9fb   tcmsf_ebadc18_biased tcmsf_07006b2 tcmsf_504f4de9_v2
    objMatchedPathsLC, refMatchedPathsLC = matchAllDirectories(foldobjbase_lc, foldrefbase, verstr, resultfile, '*ref_02.csv')
    
    verstr = 'tcmsf_fed1d4c'  # lc_829d9fb   tcmsf_a0aec20 tcmsf_7a74f0a _abbeab0 tcmsf_cb245cc tcmsf_9032119 tcmsf_74d2b20
    objMatchedPathsTC, refMatchedPaths = matchAllDirectories(foldobjbase_tc, foldrefbase, verstr, resultfile, '*ref_02.csv')

    statsall = []
    
    for i in range(len(objMatchedPathsTC)):
        print(objMatchedPathsLC[i])
        refdataLC = load100ccsv(refMatchedPathsLC[i], 0, 0)
        refdata = load100ccsv(refMatchedPaths[i], 0, 0)
        lcs = readSensorDataTcSol(objMatchedPathsLC[i], 0)
        tcs = readSensorDataTcSol(objMatchedPathsTC[i], 0)

        # 转换经纬度为距离（以第一点为参考）
        lcs[:, 7:9] = (lcs[:, 7:9] - refdataLC[0, 7:9]) * r2m  # MATLAB索引从1开始，Python从0开始，所以是7:9对应8:9
        tcs[:, 7:9] = (tcs[:, 7:9] - refdata[0, 7:9]) * r2m
        refdataLC[:, 7:9] = (refdataLC[:, 7:9] - refdataLC[0, 7:9]) * r2m
        refdata[:, 7:9] = (refdata[:, 7:9] - refdata[0, 7:9]) * r2m

        # 数据对齐
        aligned_data1, aligned_data2, common_timelc = alignDataByTimeTcSol(
            lcs, lcs[:, 0], refdataLC, refdataLC[:, 0], 10e-3)
        diff_datalc = calculateDifferenceTcSol(aligned_data1, aligned_data2)
        diff_datalc = att_diff_adjust(diff_datalc)
        
        aligned_data1, aligned_data2, common_timetc = alignDataByTimeTcSol(
            tcs, tcs[:, 0], refdata, refdata[:, 0], 10e-3)
        diff_datatc = calculateDifferenceTcSol(aligned_data1, aligned_data2)
        diff_datatc = att_diff_adjust(diff_datatc)

        stats = result_statistics(diff_datalc, diff_datatc, 50)
        
        # 获取数据集名称
        parent_path = os.path.dirname(objMatchedPathsTC[i])
        parent_path = os.path.dirname(parent_path)
        last_folder = os.path.basename(parent_path)
        stats['dataset'] = last_folder[4:]  # 减少文字长度，去掉前4个字符
        statsall.append(stats)

        save_dir = os.path.join(os.path.dirname(objMatchedPathsTC[i]), verstr)
        os.makedirs(save_dir, exist_ok=True)
        
        # 调用新的绘图函数，绘制7副图并保存特定时间段的数据
        try:
            # 假设我们有RTS文件路径，这里使用refdata作为参考
            # 实际应用中可能需要根据具体文件结构调整路径
            compare_tc_lc_ref_100c_with_plots(
                objMatchedPathsLC[i],  # LC文件路径
                objMatchedPathsTC[i],  # TC文件路径
                refMatchedPaths[i],    # RTS文件路径（使用ref文件作为参考）
                save_dir               # 保存目录
            )
        except Exception as e:
            print(f"绘图过程中出现错误: {e}")

    # 保存汇总结果
    save_dir = os.path.join('D:/dockers/test_summary/', verstr)
    os.makedirs(save_dir, exist_ok=True)
    plotStatsComparisonaAll(statsall, save_dir)
    StatsComparisonAll(statsall, save_dir)

    # 保存统计结果到文本文件
    with open(os.path.join(save_dir, 'statistics_rms.txt'), 'w') as fidrms, \
         open(os.path.join(save_dir, 'statistics_max.txt'), 'w') as fidmax, \
         open(os.path.join(save_dir, 'statistics_his.txt'), 'w') as fidhis:
        
        # 写入标题
        fidrms.write(f"{'dataset':<20} {'type':<4} {'pitch':<10}{'roll':<10}{'yaw':<10}{'vh':<10}{'vu':<10}{'dh':<10}{'dalt':<10}\n")
        fidmax.write(f"{'dataset':<20} {'type':<4} {'pitch':<10}{'roll':<10}{'yaw':<10}{'vh':<10}{'vu':<10}{'dh':<10}{'dalt':<10}\n")
        fidhis.write(f"{'dataset':<20} {'type':<4} {'H:0-0.2':<10}{'H:0.2-0.5':<10}{'H:0.5-1.0':<10}{'H:>1':<10}{'V:0-0.2':<10}{'V:0.2-0.5':<10}{'V:0.5-1.0':<10}{'V:>1':<10}\n")
        
        for i in range(len(objMatchedPathsTC)):
            stats = statsall[i]
            # RMS统计
            fidrms.write(f"{stats['dataset']:<20}  LC ")
            for val in stats['LC']['rms']:
                fidrms.write(f"{val:<10.3f}")
            fidrms.write("\n")
            fidrms.write(f"{' ':<20}  TC ")
            for val in stats['TC']['rms']:
                fidrms.write(f"{val:<10.3f}")
            fidrms.write("\n")
            
            # 最大值统计
            fidmax.write(f"{stats['dataset']:<20}  LC ")
            for val in stats['LC']['max_abs']:
                fidmax.write(f"{val:<10.3f}")
            fidmax.write("\n")
            fidmax.write(f"{' ':<20}  TC ")
            for val in stats['TC']['max_abs']:
                fidmax.write(f"{val:<10.3f}")
            fidmax.write("\n")
            
            # 区间统计
            fidhis.write(f"{stats['dataset']:<20}  LC ")
            for val in stats['LC']['interval_percent'].flatten():
                fidhis.write(f"{val:<10.2f}")
            fidhis.write("\n")
            fidhis.write(f"{' ':<20}  TC ")
            for val in stats['TC']['interval_percent'].flatten():
                fidhis.write(f"{val:<10.2f}")
            fidhis.write("\n")

    return statsall


# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的路径）
    # result = bppaps()
    pass
