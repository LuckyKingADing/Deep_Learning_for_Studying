"""
This script is available and ready to use.

Functionality:
- Batch evaluates localization accuracy by comparing TC (Tightly Coupled) and LC (Loosely Coupled) 
  solutions against RTS (Reference Trajectory System) ground truth data
- Generates comprehensive visualization including:
  * 9 detailed comparison plots per dataset (attitude, velocity, position, errors, etc.)
  * Statistical comparison charts across all datasets (RMS, MAX, error distribution)
  * Text-based statistical reports (RMS, MAX, interval percentages)
- Saves all outputs organized by dataset names in separate directories
- Identifies and logs high-norm time periods for quality analysis
- Removes TC2 plotting as per requirements (all TC2 references changed to TC)

Main Function: bppaps_enhanced()
Usage: 
    from bppaps_msfdebg_rts_enhanced import bppaps_enhanced
    result = bppaps_enhanced(
        foldobjbase_lc='/path/to/lc/data',
        foldobjbase_tc='/path/to/tc/data',
        foldrefbase='/path/to/rts/data',
        resultfile='msf_debug_state.csv'
    )
"""

import numpy as np
import os

from pathlib import Path
import fnmatch
from typing import Tuple, List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.interpolate import interp1d
from readmsf_debug_state import readmsf_debug_state
from read_rts_file import read_rts_file
from readSensorDataTcXkPk import readSensorDataTcXkPk
import utils

def matchAllDirectories(foldobjbase: str, foldrefbase: str, verstr: str, verstr_ref: str, resultfile: str, reffilePattern: str) -> Tuple[List[str], List[str]]:
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
        refFilePath = buildResultPath(refBasePaths[i], verstr_ref, reffilePattern)
        
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
    # RMS是均方根，对于真误差，应计算为 sqrt(sum(x^2)/n)，其中n为样本数
    n_lc = lc_merged.shape[0]  # 样本数
    stats['LC']['rms'] = np.sqrt(np.sum(lc_merged**2, axis=0) / n_lc)
    stats['LC']['max_abs'] = np.max(np.abs(lc_merged), axis=0)
    stats['LC']['interval_percent'] = calc_interval_percent(lc_last2)
    
    # ===== TC部分统计 =====
    stats['TC'] = {}
    # RMS是均方根，对于真误差，应计算为 sqrt(sum(x^2)/n)，其中n为样本数
    n_tc = tc_merged.shape[0]  # 样本数
    stats['TC']['rms'] = np.sqrt(np.sum(tc_merged**2, axis=0) / n_tc)
    stats['TC']['max_abs'] = np.max(np.abs(tc_merged), axis=0)
    stats['TC']['interval_percent'] = calc_interval_percent(tc_last2)
    
    return stats


def merge_columns(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    合并列的辅助函数
    """
    # 1-3列: 姿态误差 (pitch, roll, yaw)
    attitude = np.abs(data[:, 1:4])
    
    # 4-5列合并为水平速度误差: sqrt(ve^2 + vn^2)
    hor_velocity = np.sqrt(data[:, 4]**2 + data[:, 5]**2)
    
    # 6列: 垂直速度误差 (vu)
    ver_velocity = np.abs(data[:, 6])
    
    # 7-8列合并为水平位置误差: sqrt(dlat^2 + dlon^2)
    hor_position = np.sqrt(data[:, 7]**2 + data[:, 8]**2)
    
    # 9列: 高程误差 (dalt)
    altitude = np.abs(data[:, 9])
    
    # 合并后的数据矩阵 (7列)
    merged_data = np.column_stack((attitude, hor_velocity, ver_velocity, hor_position, altitude))
    
    # 最后2列用于区间统计
    last2 = np.column_stack((hor_position, altitude))
    
    return merged_data, last2


def calc_interval_percent(data: np.ndarray) -> np.ndarray:
    """
    计算区间百分比的辅助函数
    """
    ranges = [0.3, 1.0, float('inf')]
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
    
    axes[0, 0].bar(x - width/2, lc_rms, width, label='LC', color='red', alpha=0.8)
    axes[0, 0].bar(x + width/2, tc_rms, width, label='TC', color='blue', alpha=0.8)
    axes[0, 0].set_xlabel('Parameter')
    axes[0, 0].set_ylabel('RMS Error')
    axes[0, 0].set_title('RMS Comparison')
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(labels, rotation=45)
    axes[0, 0].legend()
    
    # 最大绝对值比较
    lc_max = stats['LC']['max_abs']
    tc_max = stats['TC']['max_abs']
    
    axes[0, 1].bar(x - width/2, lc_max, width, label='LC', color='red', alpha=0.8)
    axes[0, 1].bar(x + width/2, tc_max, width, label='TC', color='blue', alpha=0.8)
    axes[0, 1].set_xlabel('Parameter')
    axes[0, 1].set_ylabel('Max Absolute Error')
    axes[0, 1].set_title('Max Absolute Error Comparison')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(labels, rotation=45)
    axes[0, 1].legend()
    
    # 区间百分比比较
    lc_intervals = stats['LC']['interval_percent']
    tc_intervals = stats['TC']['interval_percent']
    
    interval_labels = ['0-0.3', '0.3-1.0', '>1']
    
    ax_idx = 1
    for i in range(lc_intervals.shape[0]):  # 遍历不同类型的误差（水平位置、高程）
        ax = axes[ax_idx // 2, ax_idx % 2] if ax_idx < 4 else axes[1, 1]
        
        x_int = np.arange(len(interval_labels))
        ax.bar(x_int - width/2, lc_intervals[i, :], width, label='LC', color='red', alpha=0.8)
        ax.bar(x_int + width/2, tc_intervals[i, :], width, label='TC', color='blue', alpha=0.8)
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


def plotStatsComparisonaAll(statsall: List[Dict[str, Any]], save_dir: str, max_dataset_labels: int = 13):
    """
    绘制所有数据集的统计比较图 - 每个参数(label)一个图，包含RMS和MAX两个子图，
    对于'Hor Pos'和'Alt'额外绘制误差分布图
    
    Args:
        statsall: 所有数据集的统计信息
        save_dir: 保存目录
        max_dataset_labels: 最大数据集标签数，超过此值时使用序号而非数据集名称
    """
    os.makedirs(save_dir, exist_ok=True)
    
    if not statsall:
        return
    
    n_datasets = len(statsall)
    if n_datasets == 0:
        return
    
    # 准备数据
    lc_rms_all = []
    tc_rms_all = []
    lc_max_all = []
    tc_max_all = []
    lc_interval_all = []
    tc_interval_all = []
    
    for stat in statsall:
        lc_rms_all.append(stat['LC']['rms'])
        tc_rms_all.append(stat['TC']['rms'])
        lc_max_all.append(stat['LC']['max_abs'])
        tc_max_all.append(stat['TC']['max_abs'])
        if 'interval_percent' in stat['LC']:
            lc_interval_all.append(stat['LC']['interval_percent'])
        if 'interval_percent' in stat['TC']:
            tc_interval_all.append(stat['TC']['interval_percent'])
    
    lc_rms_all = np.array(lc_rms_all)
    tc_rms_all = np.array(tc_rms_all)
    lc_max_all = np.array(lc_max_all)
    tc_max_all = np.array(tc_max_all)
    
    labels = ['Pitch', 'Roll', 'Yaw', 'Hor Vel', 'Ver Vel', 'Hor Pos', 'Alt']
    dataset_names = [stat.get('dataset', f'Dataset_{i}') for i, stat in enumerate(statsall)]
    
    # 判断是否使用序号标签
    use_index_labels = n_datasets > max_dataset_labels
    
    # 如果使用序号标签，生成映射文件
    if use_index_labels:
        with open(os.path.join(save_dir, 'dataset_name_mapping.txt'), 'w') as f:
            f.write("Index\tDataset Name\n")
            f.write("="*50 + "\n")
            for i, name in enumerate(dataset_names, 1):
                f.write(f"{i}\t{name}\n")
    
    # 为每个参数创建一个包含RMS和MAX两个子图的图
    for param_idx, param_label in enumerate(labels):
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle(f'Statistics Comparison for {param_label}', fontsize=16)
        
        # 第一个子图：RMS值对比
        lc_values = lc_rms_all[:, param_idx]
        tc_values = tc_rms_all[:, param_idx]
        
        x_pos = np.arange(n_datasets)
        width = 0.35
        
        bars_lc = axes[0].bar(x_pos - width/2, lc_values, width, label='LC', color='red', alpha=0.8)
        bars_tc = axes[0].bar(x_pos + width/2, tc_values, width, label='TC', color='blue', alpha=0.8)
        
        # 在柱子上显示数值
        for bar, value in zip(bars_lc, lc_values):
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.4f}',
                        ha='center', va='bottom', fontsize=9)
        
        for bar, value in zip(bars_tc, tc_values):
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.4f}',
                        ha='center', va='bottom', fontsize=9)
        
        axes[0].set_xlabel('Dataset')
        axes[0].set_ylabel('RMS Error')
        axes[0].set_title(f'RMS Error for {param_label}')
        axes[0].set_xticks(x_pos)
        # 根据数据集数量决定使用序号还是名称
        xticklabels = [str(i+1) for i in range(n_datasets)] if use_index_labels else dataset_names
        axes[0].set_xticklabels(xticklabels, rotation=45)
        axes[0].legend()
        
        # 第二个子图：MAX值对比
        lc_max_values = lc_max_all[:, param_idx]
        tc_max_values = tc_max_all[:, param_idx]
        
        bars_lc_max = axes[1].bar(x_pos - width/2, lc_max_values, width, label='LC', color='red', alpha=0.8)
        bars_tc_max = axes[1].bar(x_pos + width/2, tc_max_values, width, label='TC', color='blue', alpha=0.8)
        
        # 在柱子上显示数值
        for bar, value in zip(bars_lc_max, lc_max_values):
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.4f}',
                        ha='center', va='bottom', fontsize=9)
        
        for bar, value in zip(bars_tc_max, tc_max_values):
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.4f}',
                        ha='center', va='bottom', fontsize=9)
        
        axes[1].set_xlabel('Dataset')
        axes[1].set_ylabel('Max Absolute Error')
        axes[1].set_title(f'Max Absolute Error for {param_label}')
        axes[1].set_xticks(x_pos)
        axes[1].set_xticklabels(xticklabels, rotation=45)
        axes[1].legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f'{param_label.lower().replace(" ", "_")}_rms_max_comparison.png'), 
                   bbox_inches='tight')
        plt.close()
    
    # 为'Hor Pos'和'Alt'额外绘制误差分布图
    if len(lc_interval_all) > 0 and len(tc_interval_all) > 0:
        for param_idx, param_label in enumerate(['Hor Pos', 'Alt']):
            if param_idx == 0:  # 'Hor Pos' 对应索引5
                interval_dim = 0  # 水平位置对应区间数据的第一个维度
            else:  # 'Alt' 对应索引6
                interval_dim = 1  # 高程对应区间数据的第二个维度
            
            # 提取对应维度的区间数据
            lc_intervals_data = [lc_interval[interval_dim] for lc_interval in lc_interval_all]
            tc_intervals_data = [tc_interval[interval_dim] for tc_interval in tc_interval_all]
            
            # 定义区间标签，合并中间区间
            interval_labels = ['0-0.3', '0.3-1.0', '>1']
            x_int = np.arange(len(interval_labels))
            
            # 创建包含三个子图的图，每个子图对应一个区间
            fig, axes = plt.subplots(3, 1, figsize=(12, 15))
            fig.suptitle(f'Error Distribution for {param_label}', fontsize=16)
            
            # 为每个区间创建一个子图
            for interval_idx, interval_name in enumerate(interval_labels):
                # 为每个数据集绘制LC和TC的值
                x_pos = np.arange(n_datasets)
                width = 0.35
                
                # 提取当前区间的LC和TC数据
                lc_interval_values = [lc_intervals_data[i][interval_idx] for i in range(n_datasets)]
                tc_interval_values = [tc_intervals_data[i][interval_idx] for i in range(n_datasets)]
                
                # 绘制柱状图
                bars1 = axes[interval_idx].bar(x_pos - width/2, lc_interval_values, width, label='LC', color='red', alpha=0.8)
                bars2 = axes[interval_idx].bar(x_pos + width/2, tc_interval_values, width, label='TC', color='blue', alpha=0.8)
                
                # 在柱子上显示数值
                for bar, value in zip(bars1, lc_interval_values):
                    height = bar.get_height()
                    axes[interval_idx].text(bar.get_x() + bar.get_width()/2., height,
                                            f'{value:.1f}',
                                            ha='center', va='bottom', fontsize=9)
                
                for bar, value in zip(bars2, tc_interval_values):
                    height = bar.get_height()
                    axes[interval_idx].text(bar.get_x() + bar.get_width()/2., height,
                                            f'{value:.1f}',
                                            ha='center', va='bottom', fontsize=9)
                
                axes[interval_idx].set_xlabel('Dataset')
                axes[interval_idx].set_ylabel('Percentage (%)')
                axes[interval_idx].set_title(f'{interval_name} for {param_label}')
                axes[interval_idx].set_xticks(x_pos)
                # 根据数据集数量决定使用序号还是名称
                xticklabels = [str(i+1) for i in range(n_datasets)] if use_index_labels else dataset_names
                axes[interval_idx].set_xticklabels(xticklabels, rotation=45)
                axes[interval_idx].legend()
            
            plt.tight_layout()
            plt.savefig(os.path.join(save_dir, f'{param_label.lower().replace(" ", "_")}_error_distribution.png'), 
                       bbox_inches='tight')
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


def compare_tc_lc_ref_rts_with_plots_enhanced(lcpath, tcpath, rtspath, save_dir, dataset_name):
    """
    比较TC、LC和RTS数据与参考数据，并绘制7副图，同时保存特定时间段的数据
    这是增强版本，去除了tc2的绘制，所有tc2相关内容都改为tc
    """
    os.makedirs(save_dir, exist_ok=True)
    
    # 读取数据
    lcs = readmsf_debug_state(lcpath, 0)
    tcs = readmsf_debug_state(tcpath, 0)
    rts0 = read_rts_file(rtspath, 1)
    
    lcs0 = lcs[:,7:9].copy()
    tcs0 = tcs[:,7:9].copy()

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
    rts = utils.InterpState(rts0, rts0[:,0], tref)

    # 数据对齐
    aligned_lc, aligned_data2, common_timelc,idlc = utils.alignDataByTimeTcSol(
        lcs, lcs[:, 0], rts, rts[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datalc = utils.calculateDifference(aligned_lc, aligned_data2)

    aligned_tc, aligned_data2, common_timetc,idtc = utils.alignDataByTimeTcSol(
        tcs, tcs[:, 0], rts, rts[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datatc = utils.calculateDifference(aligned_tc, aligned_data2)

    lcs_cmn = lcs0[idlc,:]
    tcs_cmn = tcs0[idtc,:]
    
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
    
    figlen = 8
    for si in range(1, figlen):  # 1:7 对应Python中的range(1, 8)，总共7个子图
        plt.figure(si, figsize=(12, 8))
        plt.suptitle(tilestr[si-1])  # tilestr(si,) 对应Python中的tilestr[si-1]

        for i in range(1, 4):  # 1:3 对应Python中的range(1, 4)
            pi = 3 * (si - 1) + i  # 

            plt.subplot(2, 3, i)
            # 检查数据维度是否足够
            if si < 4:
                if rts.shape[1] > pi:  # 改为 > 以确保索引有效
                    plt.plot(rts[:, 0] - t0, rts[:, pi], "-o", linewidth=1, color='magenta', markersize=1, label='RTS')
            if lcs.shape[1] > pi:  # 改为 > 以确保索引有效
                plt.plot(lcs[:, 0] - t0, lcs[:, pi], "-o", linewidth=1, color='red', markersize=1, label='LC')
            if tcs.shape[1] > pi:  # 改为 > 以确保索引有效
                plt.plot(tcs[:, 0] - t0, tcs[:, pi], "-o", linewidth=1, color='blue', markersize=1, label='TC')
            plt.xlim(xranges)
            plt.grid(True)
            plt.legend()
            
            # 绘制差值图
            if si < 4:
                plt.subplot(2, 3, i + 3)
                pi_idx = 3 * (si - 1) + 1  # 
                pie_idx = 3 * (si - 1) + 3  # 
                # 检查数据维度是否足够
                if diff_datalc.shape[1] > pi:
                    lc_diff_data = diff_datalc[:, pi]
                    plt.plot(common_timelc - t0, lc_diff_data, "-o", linewidth=1, color='red', markersize=1, label='LC Diff')
                    
                    # 检查si=3时的norm是否大于2.0
                    if si == 3:  # 当si=3时，检查第3列
                        # 计算norm（假设是向量的模长）
                        norm_values = np.sqrt(np.sum(diff_datalc[:, pi_idx:pie_idx]**2, axis=1))
                        high_norm_mask = norm_values > 2.0
                        if np.any(high_norm_mask):
                            # 分别处理时间和数据
                            high_norm_times_list = (common_timelc[high_norm_mask] - t0).tolist()
                            high_norm_data_list = lcs_cmn[high_norm_mask,:].tolist()
                            
                            # 将时间和数据扁平化为单一列表
                            for time, data in zip(high_norm_times_list, high_norm_data_list):
                                flat_entry = [time] + (data if isinstance(data, list) else [data])
                                lc_high_norm_times.append(flat_entry)
                
                if diff_datatc.shape[1] > pi:
                    tc_diff_data = diff_datatc[:, pi]
                    plt.plot(common_timetc - t0, tc_diff_data, "-o", linewidth=1, color='blue', markersize=1, label='TC Diff')
                    
                    # 检查si=3时的norm是否大于2.0
                    if si == 3:  # 当si=3时，检查第3列
                        # 计算norm（假设是向量的模长）
                        norm_values = np.sqrt(np.sum(diff_datatc[:, pi_idx:pie_idx]**2, axis=1))
                        high_norm_mask = norm_values > 2.0
                        if np.any(high_norm_mask):
                            # 分别处理时间和数据
                            high_norm_times_list = (common_timetc[high_norm_mask] - t0).tolist()
                            high_norm_data_list = tcs_cmn[high_norm_mask, :].tolist()
                            
                            # 将时间和数据扁平化为单一列表
                            for time, data in zip(high_norm_times_list, high_norm_data_list):
                                flat_entry = [time] + (data if isinstance(data, list) else [data])
                                tc_high_norm_times.append(flat_entry)

                plt.grid(True)
                plt.xlim(xranges)
                plt.legend()
        
        # 保存图像
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f'{tilestr[si-1]}_comparison.png'))
        plt.close()
    
    plt.figure(figlen + 1)
    si = 3
    pi_idx = 3 * (si - 1) + 1  # 
    pie_idx = 3 * (si - 1) + 3  # 
    if diff_datalc.shape[1] >= pie_idx:
        p3dlc = np.sqrt(np.sum(diff_datalc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(common_timelc - t0, p3dlc, "-o", linewidth=1, color='red', markersize=1, label='LC Diff')
    if diff_datatc.shape[1] >= pie_idx:
        p3dtc = np.sqrt(np.sum(diff_datatc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(common_timetc - t0, p3dtc, "-o", linewidth=1, color='blue', markersize=1, label='TC Diff')
        
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f'hor_comparison.png'))
    plt.close()
    
    # 保存超过阈值的时间段到文件
    if lc_high_norm_times:
        with open(os.path.join(save_dir, 'lc_high_norm_times.txt'), 'w') as f:
            for entry in lc_high_norm_times:
                f.write(','.join(map(str, entry)) + '\n')
    
    if tc_high_norm_times:
        with open(os.path.join(save_dir, 'tc_high_norm_times.txt'), 'w') as f:
            for entry in tc_high_norm_times:
                f.write(','.join(map(str, entry)) + '\n')


#函数入口
def bppaps_enhanced(foldobjbase_lc: str = '/mnt/d/dockers/test/rts',
                   foldobjbase_tc: str = '/mnt/d/dockers/test/rts',
                   foldrefbase: str = '/mnt/d/dockers/test/rts',
                   resultfile: str = 'msf_debug_state.csv'):
    """
    BPPAPS算法实现 - 批量处理精度和图片保存（增强版本）
    需要真值文件
    加入了更多细节图，去除tc2的绘制
    """
    if foldobjbase_tc is None:
        foldobjbase_tc = foldobjbase_lc
    
    pi = 3.14159265358979
    d2r = pi / 180  # 度转弧度
    r2m = d2r * 6378137  # 弧度转米（地球半径）

    verstr = 'TC_968e3ff7_v3' #TC
    verstr_ref = 'LC_968e3ff7'  # rts与LC同版本，结果同目录
    refname = 'rts_result.csv'
    objMatchedPathsLC, refMatchedPathsLC = matchAllDirectories(foldobjbase_lc, foldrefbase, verstr_ref, verstr_ref, resultfile, refname)
    
    objMatchedPathsTC, refMatchedPaths = matchAllDirectories(foldobjbase_tc, foldrefbase, verstr, verstr_ref, resultfile, refname)

    statsall = []
    
    for i in range(len(objMatchedPathsTC)):
        print(objMatchedPathsLC[i])
        rts = read_rts_file(refMatchedPathsLC[i],1)
        lcs = readmsf_debug_state(objMatchedPathsLC[i], 0) 
        tcs = readmsf_debug_state(objMatchedPathsTC[i], 0)
        tref = tcs[:,0]
        refdataLC = utils.InterpState(rts, rts[:,0], tref)
        refdata = refdataLC

        # 转换经纬度为距离（以第一点为参考）
        lcs[:, 7:9] = (lcs[:, 7:9] - refdataLC[0, 7:9]) * r2m  # MATLAB索引从1开始，Python从0开始，所以是7:9对应8:9
        tcs[:, 7:9] = (tcs[:, 7:9] - refdata[0, 7:9]) * r2m
        refdataLC[:, 7:9] = (refdataLC[:, 7:9] - refdataLC[0, 7:9]) * r2m

        # 数据对齐
        aligned_data1, aligned_data2, common_timelc,idxlc = utils.alignDataByTimeTcSol(
            lcs, lcs[:, 0], refdataLC, refdataLC[:, 0], 10e-3)
        diff_datalc = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)
        
        aligned_data1, aligned_data2, common_timetc,idxtc = utils.alignDataByTimeTcSol(
            tcs, tcs[:, 0], refdata, refdata[:, 0], 10e-3)
        diff_datatc = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)

        stats = result_statistics(diff_datalc, diff_datatc, 50)
        
        # 获取数据集名称
        parent_path = os.path.dirname(objMatchedPathsTC[i])
        parent_path = os.path.dirname(parent_path)
        last_folder = os.path.basename(parent_path)
        stats['dataset'] = last_folder[4:]  # 减少文字长度，去掉前4个字符
        statsall.append(stats)

        # 详细图表保存在以数据集命名的文件夹中
        save_dir = os.path.join('/mnt/d/dockers/rts_test_summary', verstr, stats['dataset'])
        os.makedirs(save_dir, exist_ok=True)
        
        # 调用增强的绘图函数，绘制10副图并保存特定时间段的数据
        try:
            compare_tc_lc_ref_rts_with_plots_enhanced(
                objMatchedPathsLC[i],  # LC文件路径
                objMatchedPathsTC[i],  # TC文件路径
                refMatchedPaths[i],    # RTS文件路径
                save_dir,              # 保存目录
                stats['dataset']       # 数据集名称
            )
        except Exception as e:
            print(f"绘图过程中出现错误: {e}")

    # 保存汇总结果
    save_dir = os.path.join('/mnt/d/dockers/rts_test_summary', verstr)
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
    result = bppaps_enhanced('/mnt/d/dockers/test/rts','/mnt/d/dockers/test/rts','/mnt/d/dockers/test/rts','msf_debug_state.csv')
    pass
