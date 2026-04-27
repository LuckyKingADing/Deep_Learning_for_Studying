"""
基于head topic和参考数据的精度评估脚本
对应MATLAB文件: precision_head_topic_ref_100c_wdh.m

功能:
- 读取LC数据 (tcmsf_sol.csv)
- 读取TC数据 (tcmsf_sol_msf.csv)
- 读取GNSS数据 (gnss.csv)
- 读取参考数据 (ref_02.txt)
- 进行时间对齐
- 计算误差
- 输出统计结果
- 绘制误差曲线
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import sys
import toml
import warnings
from pathlib import Path
warnings.filterwarnings('ignore')


# 导入现有的数据读取函数
import sys
import os

# 添加父目录到Python路径，以便导入commons模块
current_dir = os.path.dirname(os.path.abspath(__file__))
commons_dir = os.path.join(os.path.dirname(current_dir), 'commons')
if commons_dir not in sys.path:
    sys.path.insert(0, commons_dir)

# 从commons模块导入
import utils
import fileutils
from outpre_new import outpre_new
from plot_errors import plot_errors
from calculate_errors import calculate_errors
from evaluation_utils import (
    load_config_from_toml,
    process_sensor_data,
    calculate_normal_scene_time_ranges,
    calculate_horizontal_velocity_stats,
    save_horizontal_velocity_stats
)

def plot_detail_subplots(
    common_timelc, diff_datalc, common_timetc, diff_datatc,
    common_timegnss, diff_datagnss, t0, yaw,
    horizontal_threshold_meters, vertical_threshold_meters,
    detail_window_seconds, output_dir, type_label, lcver='LC', tcver='TC',
    plotlc=True, plottc=True, gap_intervals=None
):
    """
    绘制误差大于阈值的详细子图（水平误差或高程误差任一超过阈值）
    
    Args:
        common_timelc: LC时间向量
        diff_datalc: LC差值数据
        common_timetc: TC时间向量
        diff_datatc: TC差值数据
        common_timegnss: GNSS时间向量
        diff_datagnss: GNSS差值数据
        t0: 时间基准点
        yaw: 航向角数据
        horizontal_threshold_meters: 水平误差阈值（米）
        vertical_threshold_meters: 高程误差阈值（米）
        detail_window_seconds: 子图时间窗口（秒）
        output_dir: 输出目录
        type_label: 类型标签
        lcver: LC版本标识
        tcver: TC版本标识
    """
    print(f"\n开始绘制详细子图...")
    print(f"  水平误差阈值: {horizontal_threshold_meters}米")
    print(f"  高程误差阈值: {vertical_threshold_meters}米")
    print(f"  时间窗口: ±{detail_window_seconds}秒")
    
    # 创建details目录
    details_dir = os.path.join(output_dir, 'details')
    os.makedirs(details_dir, exist_ok=True)
    print(f"  详细子图保存目录: {details_dir}")
    
    # 收集所有数据的时间点和误差
    all_times = []
    all_horizontal_errors = []
    all_vertical_errors = []
    
    # 处理LC数据
    if common_timelc is not None and diff_datalc is not None and len(common_timelc) > 0:
        lc_horizontal, lc_lateral, lc_vertical, _ = calculate_errors(diff_datalc, yaw)
        lc_horizontal_error = np.sqrt(lc_horizontal**2 + lc_lateral**2)
        all_times.extend(common_timelc)
        all_horizontal_errors.extend(lc_horizontal_error)
        all_vertical_errors.extend(np.abs(lc_vertical))
    
    # 处理TC数据
    if common_timetc is not None and diff_datatc is not None and len(common_timetc) > 0:
        tc_horizontal, tc_lateral, tc_vertical, _ = calculate_errors(diff_datatc, yaw)
        tc_horizontal_error = np.sqrt(tc_horizontal**2 + tc_lateral**2)
        all_times.extend(common_timetc)
        all_horizontal_errors.extend(tc_horizontal_error)
        all_vertical_errors.extend(np.abs(tc_vertical))
    
    # 处理GNSS数据
    if common_timegnss is not None and diff_datagnss is not None and len(common_timegnss) > 0:
        gnss_horizontal, gnss_lateral, gnss_vertical, _ = calculate_errors(diff_datagnss, yaw)
        gnss_horizontal_error = np.sqrt(gnss_horizontal**2 + gnss_lateral**2)
        all_times.extend(common_timegnss)
        all_horizontal_errors.extend(gnss_horizontal_error)
        all_vertical_errors.extend(np.abs(gnss_vertical))
    
    if len(all_times) == 0:
        print("  没有可用的数据，跳过子图绘制")
        return
    
    # 转换为numpy数组
    all_times = np.array(all_times)
    all_horizontal_errors = np.array(all_horizontal_errors)
    all_vertical_errors = np.array(all_vertical_errors)
    
    # 循环查找超过阈值的极值点
    excluded_ranges = []  # 已处理的范围
    subplot_count = 0
    
    while True:
        # 在已处理范围外的数据中查找误差最大值
        mask = np.ones(len(all_times), dtype=bool)
        
        # 排除已处理的范围
        for (range_start, range_end) in excluded_ranges:
            mask &= ((all_times < range_start) | (all_times > range_end))
        
        # 筛选出范围外的数据
        filtered_times = all_times[mask]
        filtered_horizontal_errors = all_horizontal_errors[mask]
        filtered_vertical_errors = all_vertical_errors[mask]
        
        if len(filtered_times) == 0:
            break  # 没有更多数据需要处理
        
        # 找到水平误差最大值和高程误差最大值
        max_horizontal_error = np.max(filtered_horizontal_errors)
        max_vertical_error = np.max(filtered_vertical_errors)
        
        # 判断是否超过任一阈值
        max_horizontal_idx = np.argmax(filtered_horizontal_errors)
        max_vertical_idx = np.argmax(filtered_vertical_errors)
        
        # 检查是否超过阈值
        horizontal_exceeds = max_horizontal_error > horizontal_threshold_meters
        vertical_exceeds = max_vertical_error > vertical_threshold_meters
        
        if not horizontal_exceeds and not vertical_exceeds:
            print(f"  剩余数据: 水平误差{max_horizontal_error:.2f}米, 高程误差{max_vertical_error:.2f}米")
            print(f"  未超过阈值（水平{horizontal_threshold_meters}米或高程{vertical_threshold_meters}米），停止绘制子图")
            break
        
        # 选择超过阈值较大的那个点
        if horizontal_exceeds and vertical_exceeds:
            # 两个都超过，选择相对超值较大的
            horizontal_ratio = max_horizontal_error / horizontal_threshold_meters
            vertical_ratio = max_vertical_error / vertical_threshold_meters
            if horizontal_ratio >= vertical_ratio:
                max_error_idx = max_horizontal_idx
                error_type = 'horizontal'
                error_value = max_horizontal_error
            else:
                max_error_idx = max_vertical_idx
                error_type = 'vertical'
                error_value = max_vertical_error
        elif horizontal_exceeds:
            max_error_idx = max_horizontal_idx
            error_type = 'horizontal'
            error_value = max_horizontal_error
        else:
            max_error_idx = max_vertical_idx
            error_type = 'vertical'
            error_value = max_vertical_error
        
        max_error_time = filtered_times[max_error_idx]
        
        error_text = '水平误差' if error_type == 'horizontal' else '高程误差'
        print(f"  发现超过阈值的极值点: 时间={max_error_time:.2f}s, {error_text}={error_value:.2f}米")
        
        # 确定子图的时间范围
        subplot_start = max_error_time - detail_window_seconds
        subplot_end = max_error_time + detail_window_seconds
        
        # 将此范围添加到已处理列表
        excluded_ranges.append((subplot_start, subplot_end))
        
        # 绘制子图
        subplot_count += 1
        save_path = os.path.join(
            details_dir, 
            f'detail_subplot_type_{type_label}_peak_{subplot_count}_t{max_error_time:.0f}_{error_type}_{error_value:.1f}m.png'
        )
        
        # 调用plot_errors函数，但只绘制这个时间范围内的数据
        plot_errors(
            common_timelc, diff_datalc, 
            common_timetc, diff_datatc, 
            common_timegnss, diff_datagnss, 
            t0, save_path, yaw, 
            t_start=[subplot_start], t_end=[subplot_end],
            lcver=lcver, tcver=tcver, is_detail=True,
            plotlc=plotlc, plottc=plottc, gap_intervals=gap_intervals
        )
        
        print(f"  已保存子图 {subplot_count}: {os.path.basename(save_path)}")
    
    print(f"  共绘制 {subplot_count} 个详细子图")


def outpre_unified_table(outfile, all_type_stats, t0=0, lcver='LC', tcver='TC'):
    """
    输出统一表格格式的统计结果
    :param outfile: 输出文件路径
    :param all_type_stats: 所有场景的统计结果列表
    :param t0: 绘图的时间基准点（绘图的时间起点值）
    :param lcver: LC版本标识
    :param tcver: TC版本标识
    """
    # 固定的场景输出顺序（不含Normal，Normal根据表格类型动态添加）
    SCENE_ORDER_BASE = ['All', '开阔场景', '半遮挡', '双边遮挡', '隧道', '转发器']

    # 标签转换函数：将英文标签转换为中文
    def convert_label_to_chinese(label):
        if label.lower() == 'all':
            return '全部'
        if 'Normal' in label:
            return '正常'
        return label

    # 根据表格类型获取场景顺序
    def get_scene_order_for_table(table_type):
        normal_key = f'Normal_{table_type}'
        return ['All', normal_key] + SCENE_ORDER_BASE[1:]

    # 将统计列表转换为字典，方便查找
    stats_dict = {stats.get('type_label', 'Unknown'): stats for stats in all_type_stats}

    with open(outfile, 'w', encoding='utf-8') as fid:
        fid.write('='*120 + '\n')
        fid.write('所有场景精度统计结果汇总 (All Scene Types Statistics Summary)\n')
        fid.write('='*120 + '\n\n')
        fid.write(f'LC版本: {lcver}\n')
        fid.write(f'TC版本: {tcver}\n')
        fid.write(f'绘图时间基准点 (Plot Time Reference Point): t0 = {t0:.2f} 秒\n')
        fid.write('注：所有误差曲线图的时间轴均以t0为起点，即图中的0秒对应实际时间的{:.2f}秒\n\n'.format(t0))

        # 写入LC统计表格
        fid.write(f'{lcver} Statistics ({lcver}精度统计)\n')
        fid.write('-'*120 + '\n')

        # 表头 - 场景类型左对齐，数值右对齐，固定宽度
        header = f"{'场景类型':<12}{'里程km':>10}"
        header += f"{'H-rms':>8}{'H-CEP95':>8}{'H-CEP99':>8}{'H-max':>8}"
        header += f"{'L-rms':>8}{'L-CEP95':>8}{'L-CEP99':>8}{'L-max':>8}"
        header += f"{'F-rms':>8}{'F-CEP95':>8}{'F-CEP99':>8}{'F-max':>8}"
        header += f"{'V-rms':>8}{'V-CEP95':>8}{'V-CEP99':>8}{'V-max':>8}"
        fid.write(header + '\n')
        fid.write('-'*120 + '\n')

        # LC表格只输出Normal_LC
        scene_order_lc = get_scene_order_for_table('LC')
        for scene_label in scene_order_lc:
            stats = stats_dict.get(scene_label)
            if stats:
                lc = stats.get('lc', {})
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}{lc.get('odom', 0):>10.2f}"
                row += f"{lc.get('horizontal_rms', 0):>8.2f}{lc.get('horizontal_cep95', 0):>8.2f}{lc.get('horizontal_cep99', 0):>8.2f}{lc.get('horizontal_max', 0):>8.2f}"
                row += f"{lc.get('lateral_rms', 0):>8.2f}{lc.get('lateral_cep95', 0):>8.2f}{lc.get('lateral_cep99', 0):>8.2f}{lc.get('lateral_max', 0):>8.2f}"
                row += f"{lc.get('forward_rms', 0):>8.2f}{lc.get('forward_cep95', 0):>8.2f}{lc.get('forward_cep99', 0):>8.2f}{lc.get('forward_max', 0):>8.2f}"
                row += f"{lc.get('vertical_rms', 0):>8.2f}{lc.get('vertical_cep95', 0):>8.2f}{lc.get('vertical_cep99', 0):>8.2f}{lc.get('vertical_max', 0):>8.2f}"
                fid.write(row + '\n')
            else:
                # 该场景不存在，输出0值
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}{'0.00':>10}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                fid.write(row + '\n')

        fid.write('\n')

        # 写入TC统计表格
        fid.write(f'{tcver} Statistics ({tcver}精度统计)\n')
        fid.write('-'*120 + '\n')
        fid.write(header + '\n')
        fid.write('-'*120 + '\n')

        # TC表格只输出Normal_TC
        scene_order_tc = get_scene_order_for_table('TC')
        for scene_label in scene_order_tc:
            stats = stats_dict.get(scene_label)
            if stats:
                tc = stats.get('tc', {})
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}{tc.get('odom', 0):>10.2f}"
                row += f"{tc.get('horizontal_rms', 0):>8.2f}{tc.get('horizontal_cep95', 0):>8.2f}{tc.get('horizontal_cep99', 0):>8.2f}{tc.get('horizontal_max', 0):>8.2f}"
                row += f"{tc.get('lateral_rms', 0):>8.2f}{tc.get('lateral_cep95', 0):>8.2f}{tc.get('lateral_cep99', 0):>8.2f}{tc.get('lateral_max', 0):>8.2f}"
                row += f"{tc.get('forward_rms', 0):>8.2f}{tc.get('forward_cep95', 0):>8.2f}{tc.get('forward_cep99', 0):>8.2f}{tc.get('forward_max', 0):>8.2f}"
                row += f"{tc.get('vertical_rms', 0):>8.2f}{tc.get('vertical_cep95', 0):>8.2f}{tc.get('vertical_cep99', 0):>8.2f}{tc.get('vertical_max', 0):>8.2f}"
                fid.write(row + '\n')
            else:
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}{'0.00':>10}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                fid.write(row + '\n')

        fid.write('\n')

        # 写入GNSS统计表格
        fid.write('GNSS Statistics (GNSS精度统计)\n')
        fid.write('-'*120 + '\n')
        fid.write(header + '\n')
        fid.write('-'*120 + '\n')

        # GNSS表格只输出Normal_GNSS
        scene_order_gnss = get_scene_order_for_table('GNSS')
        for scene_label in scene_order_gnss:
            stats = stats_dict.get(scene_label)
            if stats:
                gnss = stats.get('gnss', {})
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}{gnss.get('odom', 0):>10.2f}"
                row += f"{gnss.get('horizontal_rms', 0):>8.2f}{gnss.get('horizontal_cep95', 0):>8.2f}{gnss.get('horizontal_cep99', 0):>8.2f}{gnss.get('horizontal_max', 0):>8.2f}"
                row += f"{gnss.get('lateral_rms', 0):>8.2f}{gnss.get('lateral_cep95', 0):>8.2f}{gnss.get('lateral_cep99', 0):>8.2f}{gnss.get('lateral_max', 0):>8.2f}"
                row += f"{gnss.get('forward_rms', 0):>8.2f}{gnss.get('forward_cep95', 0):>8.2f}{gnss.get('forward_cep99', 0):>8.2f}{gnss.get('forward_max', 0):>8.2f}"
                row += f"{gnss.get('vertical_rms', 0):>8.2f}{gnss.get('vertical_cep95', 0):>8.2f}{gnss.get('vertical_cep99', 0):>8.2f}{gnss.get('vertical_max', 0):>8.2f}"
                fid.write(row + '\n')
            else:
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}{'0.00':>10}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                row += f"{'0.00':>8}{'0.00':>8}{'0.00':>8}{'0.00':>8}"
                fid.write(row + '\n')

        fid.write('\n')
        fid.write('='*120 + '\n')
        fid.write('说明 (Notes):\n')
        fid.write('  H = Horizontal (水平误差)\n')
        fid.write('  L = Lateral (横向误差)\n')
        fid.write('  F = Forward (前进方向误差)\n')
        fid.write('  V = Vertical (高程误差)\n')
        fid.write('  rms = Root Mean Square (均方根)\n')
        fid.write('  CEP95 = 95% Circular Error Probable (95%圆误差概率)\n')
        fid.write('  CEP99 = 99% Circular Error Probable (99%圆误差概率)\n')
        fid.write('  max = Maximum Error (最大误差)\n')
        fid.write('='*120 + '\n')

    print(f"统一表格格式的统计结果已保存到: {outfile}")


def precision_head_topic_ref_100c_wdh(
    basefold, 
    reffile, 
    lcver='', 
    tcver='', 
    dataset='', 
    dt=0,
    plotlc=True,
    plottc=False,
    plotgnssstat=True,
    tthreshod=5e-3,
    output_dir=None,
    reftype=0,
    statetype=0,
    config=None
):
    """
    主评估函数
    
    Args:
        basefold: 基础目录
        reffile: 参考数据文件路径
        lcver: LC版本
        tcver: TC版本
        dataset: 数据集名称
        dt: 时间偏移
        plotlc: 是否绘制LC数据
        plottc: 是否绘制TC数据
        plotgnssstat: 是否绘制GNSS数据
        tthreshod: 时间阈值
        output_dir: 输出目录（默认为basefold）
        reftype: 参考真值的数据类型 0-2504月采集的真值 1-后续wdh处理的真值
        statetype: 状态文件的类型 0-tcmsf_sol.csv 1-msf_debug_state.csv
        config: TOML配置文件加载的配置字典（可选）
    """
    print(f"\n{'='*60}")
    print("Head Topic 精度评估")
    print(f"{'='*60}\n")
    
    # 设置输出目录
    if output_dir is None:
        output_dir = basefold
    
    # 创建结果目录，如果seldataset不为空，则使用seldataset作为子目录
    if dataset and dataset != "":
        result_dir = os.path.join(output_dir, 'results', dataset)
    else:
        result_dir = os.path.join(output_dir, 'results')
    os.makedirs(result_dir, exist_ok=True)
    print(f"结果目录: {result_dir}")
        
    tcmsfname = 'tcmsf_sol.csv'
    if statetype:
        tcmsfname = 'msf_debug_state.csv'
    
    # 设置文件路径
    tcmsffold = basefold
    lcpath = os.path.join(tcmsffold, dataset, lcver, tcmsfname)
    tcpath = os.path.join(tcmsffold, dataset, tcver, tcmsfname)
    
    # 从配置文件读取GNSS路径配置
    gnss_subdir = config.get('data', {}).get('gnss_subdir', 'topic_parse') if config else 'topic_parse'
    gnss_filename = config.get('data', {}).get('gnss_filename', 'pvt.csv') if config else 'pvt.csv'
    gnsspath = os.path.join(basefold, dataset, gnss_subdir, gnss_filename)
    
    # 从配置文件读取数据源标识符
    lc_label = config.get('data', {}).get('lc_label', 'LC') if config else 'LC'
    tc_label = config.get('data', {}).get('tc_label', 'TC') if config else 'TC'
    gnss_label = config.get('data', {}).get('gnss_label', 'GNSS') if config else 'GNSS'
    
    outfile = os.path.join(tcmsffold, 'precison_statistics.txt')
    
    # 读取参考数据
    print(f"读取参考数据: {reffile}")
    if reftype:
        # 读取列: [0:time, 6:lat, 7:lon, 5:height, 15:vn, 14:ve, 16:vu, 2:roll, 3:pitch, 4:yaw, -1:quality]
        # ref数据中14,15,16对应NEU速度，调整为15,14后存储后的索引4,5,6对应ENU速度
        refdata = fileutils.readfullcsv(reffile,[0,6,7,5,15,14,16,2,3,4,-1])
        #航向角 北偏东为正，相当于 真北方位角
    else:
        refdata = []
        
    pos0 = refdata[0, 7:9].copy()
    refdata[:, 7:9] = utils.dpos2den(refdata[:, 7:9],pos0)
    
    print(f"  数据维度: {refdata.shape}")
    print(f"  时间范围: {refdata[0, 0]:.2f}s ~ {refdata[-1, 0]:.2f}s")
    
    # 新增：为 LC 和 TC 分别准备参考数据
    refdata_lc = refdata.copy()  # 默认使用原始参考数据
    refdata_tc = refdata.copy()  # 默认使用原始参考数据
    ref_filename = os.path.basename(reffile)
    
    # 只有当 reffile 是 *_84.txt 格式时，才考虑使用 *_02.txt
    if ref_filename.endswith('_84.txt'):
        ref_dir = os.path.dirname(reffile)
        ref_filename_02 = ref_filename.replace('_84.txt', '_02.txt')
        reffile_02 = os.path.join(ref_dir, ref_filename_02)
        
        # 检查 *_02.txt 是否存在
        if os.path.exists(reffile_02):
            print(f"\n检测到 WGS84 参考文件: {reffile}")
            print(f"找到对应的 GCJ-02 参考文件: {reffile_02}")
            
            # 读取 GCJ-02 参考数据
            refdata_02 = fileutils.readfullcsv(reffile_02, [0,6,7,5,15,14,16,2,3,4,-1])
            refdata_02[:, 7:9] = utils.dpos2den(refdata_02[:, 7:9], pos0)
            print(f"  GCJ-02 参考数据维度: {refdata_02.shape}")
            print(f"  GCJ-02 参考数据时间范围: {refdata_02[0, 0]:.2f}s ~ {refdata_02[-1, 0]:.2f}s")
            
            # 判断 LC 是否使用 GCJ-02 参考数据
            lc_use_gcj02 = lcver and 'pvt' not in lcver.lower()
            if lc_use_gcj02:
                print(f"\nLC 评估:")
                print(f"  lcver = '{lcver}' (不包含 'pvt')")
                print(f"  将使用 GCJ-02 参考数据评估 LC")
                refdata_lc = refdata_02
            else:
                print(f"\nLC 评估:")
                print(f"  lcver = '{lcver}' (包含 'pvt' 或为空)")
                print(f"  将使用 WGS84 参考数据评估 LC")
            
            # 判断 TC 是否使用 GCJ-02 参考数据
            tc_use_gcj02 = tcver and 'pvt' not in tcver.lower()
            if tc_use_gcj02:
                print(f"\nTC 评估:")
                print(f"  tcver = '{tcver}' (不包含 'pvt')")
                print(f"  将使用 GCJ-02 参考数据评估 TC")
                refdata_tc = refdata_02
            else:
                print(f"\nTC 评估:")
                print(f"  tcver = '{tcver}' (包含 'pvt' 或为空)")
                print(f"  将使用 WGS84 参考数据评估 TC")
            
            print(f"\nGNSS 评估:")
            print(f"  将使用 WGS84 参考数据评估 GNSS\n")
        else:
            print(f"\n检测到 WGS84 参考文件: {reffile}")
            print(f"警告: 未找到对应的 GCJ-02 参考文件: {reffile_02}")
            print(f"LC、TC 和 GNSS 都将使用 WGS84 参考数据\n")
    else:
        print(f"\n参考文件: {reffile}（非 WGS84 格式）")
        print(f"LC、TC 和 GNSS 都将使用该参考数据\n")
    
    # 读取LC数据
    lcs = None
    diff_datalc = None
    common_timelc = None
    if plotlc:
        lcs, diff_datalc, common_timelc = process_sensor_data(
            lcpath, refdata_lc, pos0, tthreshod, statetype, dt, lcver)
    
    # 读取TC数据
    tcs = None
    diff_datatc = None
    common_timetc = None
    if plottc:
        tcs, diff_datatc, common_timetc = process_sensor_data(
            tcpath, refdata_tc, pos0, tthreshod, statetype, dt, tcver)
    
    # 读取GNSS数据
    gnss = None
    gnss0 = None  # 原始GNSS数据（未筛选）
    gnss_raw_time = None  # 原始时间列（从gnsspath文件首列）
    diff_datagnss = None
    common_timegnss = None
    
    if plotgnssstat:
        print(f"\n读取GNSS数据: {gnsspath}")
        if os.path.exists(gnsspath):
            
            # 首先读取原始时间列（gnsspath文件的首列：Unix时间戳）
            # 同时读取第1列（GPS周内秒），用于建立映射关系
            gnss_raw_data = fileutils.readfullcsv(gnsspath, [0, 1], [])
            gnss_unix_time = gnss_raw_data[:, 0]  # Unix时间戳
            gnss_week_seconds = gnss_raw_data[:, 1]  # GPS周内秒
            print(f"  原始时间列点数: {len(gnss_unix_time)}")
            print(f"  Unix时间范围: {gnss_unix_time[0]:.2f} ~ {gnss_unix_time[-1]:.2f}")
            print(f"  GPS周内秒范围: {gnss_week_seconds[0]:.2f}s ~ {gnss_week_seconds[-1]:.2f}s")
            
            # 建立GPS周内秒到Unix时间戳的映射
            gnss_time_mapping = {}
            for i in range(len(gnss_week_seconds)):
                gnss_time_mapping[gnss_week_seconds[i]] = gnss_unix_time[i]
            
            # 从配置文件读取GNSS位置索引
            gnss_pos_index_1 = config.get('data', {}).get('gnss_pos_index_1', 2) if config else 2
            gnss_pos_index_2 = config.get('data', {}).get('gnss_pos_index_2', 3) if config else 3
            gnss_pos_index_3 = config.get('data', {}).get('gnss_pos_index_3', 4) if config else 4
            
            # 构建gnssindex数组，使用配置文件中的位置索引
            gnssindex = [1,-1,-1,8,5,6,7,gnss_pos_index_1,gnss_pos_index_2,gnss_pos_index_3,10]
            extindex = [14,15,16,9,10]  # 最后一列对应status
            gnssstdindex0 = len(gnssindex)  # 计算std数据的起始索引
            gnss0 = fileutils.readfullcsv(gnsspath,gnssindex,extindex)
            mask_negative = gnss0[:,3] > 180
            gnss0[mask_negative, 3] = gnss0[mask_negative, 3] - 360
            
            # 筛选GNSS数据：只保留状态大于0的数据
            if gnss0.shape[1] >= 12:
                ind = np.where(gnss0[:, -1] > 0)[0]  # rtk模式备用
                gnss = gnss0[ind, :]
                print(f"  筛选后数据维度: {gnss.shape}")
                print(f"  时间范围: {gnss[0, 0]:.2f}s ~ {gnss[-1, 0]:.2f}s")
                
                # 坐标转换
                gnss[:, 7:9] = utils.dpos2den(gnss[:, 7:9],pos0)
                
                # 时间对齐
                print("\n进行GNSS时间对齐...")
                
                aligned_data1, aligned_data2, common_timegnss,idxgnss = utils.alignDataByTimeTcSol(
                    gnss, gnss[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
                diff_datagnss = utils.calculateDifference(aligned_data1, aligned_data2)
                
                print(f"  对齐后数据点数: {len(common_timegnss)}")
                
                # 筛选位置误差小于10000的数据
                # if diff_datagnss is not None:
                #     c = np.sum(diff_datagnss[:, 7:9]**2, axis=1)
                #     indb = np.where(c < 10000)[0]
                #     common_timegnss = common_timegnss[indb]
                #     diff_datagnss = diff_datagnss[indb, :]
                #     gnss = gnss[indb, :]
                #     print(f"  筛选后数据点数: {len(common_timegnss)}")
            else:
                print(f"  警告: GNSS数据列数不足")
        else:
            print(f"  警告: GNSS文件不存在: {gnsspath}")
    
    # 计算时间基准点
    t0 = 0
    if plottc and tcs is not None:
        t0 = tcs[0, 0]
    elif lcs is not None:
        t0 = lcs[0, 0]
    
    # 提取航向角数据
    yaw = refdata[:, [0, 3]] 
    yaw[:,1] = -yaw[:,1] # 真北方位角转换为 航向角（北偏西为正）
    
    # 从配置文件读取时间范围配置
    if config is None:
        config = {}
    time_ranges_config = config.get('time_ranges', {}).get('type_config', [])

    # 收集需要完全排除的场景的时间范围（如"卫导异常排除"）
    # 这些时间段的数据不参与统计、不参与绘图、不输出
    exclude_time_ranges = []
    exclude_scene_labels = []
    for type_config in time_ranges_config:
        type_label = type_config.get('type_label', '')
        type_time_range = type_config.get('type_time_range', [])
        # 检查场景标签是否包含"排除"关键字
        if '排除' in type_label or '异常' in type_label:
            # 处理-1值
            for start, end in type_time_range:
                if start == -1:
                    start = refdata[0, 0] if refdata is not None and len(refdata) > 0 else 0
                if end == -1:
                    end = refdata[-1, 0] if refdata is not None and len(refdata) > 0 else 0
                exclude_time_ranges.append([start, end])
            exclude_scene_labels.append(type_label)
            print(f"识别排除场景: '{type_label}'，时间段 {len(type_time_range)} 个，数据将完全跳过处理")

    # ---- 任务1：加载 gap_intervals，统计时排除 gap 区间 ----
    gap_intervals = []
    gap_dir = Path(basefold) / "gap_detection"
    gap_toml = gap_dir / "gap_intervals.toml"
    if gap_toml.exists():
        try:
            gap_config_all = toml.load(str(gap_toml))
            # 查找与当前 lcver / tcver 匹配的 gap 配置
            for key, val in gap_config_all.items():
                if not isinstance(val, dict):
                    continue
                fusion_type = val.get("fusion_type", "")
                gps_ranges = val.get("gps_ranges", [])
                if not fusion_type or not gps_ranges:
                    continue
                # 用融合类型的前缀匹配（pvtlc_xxx / rtklc_xxx）
                fusion_prefix = fusion_type.split('_')[0] if '_' in fusion_type else fusion_type
                lcver_prefix = lcver.split('_')[0] if '_' in lcver else lcver
                tcver_prefix = tcver.split('_')[0] if '_' in tcver else tcver
                if fusion_prefix == lcver_prefix or fusion_prefix == tcver_prefix:
                    gap_intervals = [tuple(r) for r in gps_ranges]
                    print(f"\n[Gap] 加载 gap_intervals (from {fusion_type}): {len(gap_intervals)} 段")
                    for s, e in gap_intervals:
                        print(f"  GPS {s:.3f} ~ {e:.3f} ({e - s:.2f}s)")
                    break
            if not gap_intervals:
                print(f"[Gap] 未匹配到 {lcver_prefix} 或 {tcver_prefix} 的gap配置，跳过 gap 处理")
        except Exception as e:
            print(f"[Gap] 读取 gap_intervals.toml 失败: {e}")
    else:
        print(f"[Gap] gap_intervals.toml 不存在: {gap_toml}，跳过 gap 处理")

    # 将 gap 区间加入排除列表（统计时不计入有效里程）
    if gap_intervals:
        exclude_time_ranges.extend([[s, e] for s, e in gap_intervals])
        print(f"[Gap] 已将 {len(gap_intervals)} 段 gap 加入统计排除列表")

    # 函数：从时间序列中排除指定时间段
    def filter_excluded_time_ranges(time_data, diff_data, exclude_ranges):
        """从数据中排除指定时间段"""
        if len(exclude_ranges) == 0 or time_data is None or len(time_data) == 0:
            return time_data, diff_data, np.ones(len(time_data), dtype=bool)  # 返回全True的mask表示无排除

        mask = np.ones(len(time_data), dtype=bool)
        for start, end in exclude_ranges:
            mask &= ((time_data < start) | (time_data > end))

        filtered_time = time_data[mask] if time_data is not None else None
        filtered_diff = diff_data[mask] if diff_data is not None else None

        return filtered_time, filtered_diff, mask

    # 函数：从原始数据数组中排除指定时间段（根据时间列过滤）
    def filter_raw_data_by_time(raw_data, exclude_ranges):
        """从原始数据数组中排除指定时间段（时间列在索引0）"""
        if len(exclude_ranges) == 0 or raw_data is None or len(raw_data) == 0:
            return raw_data, np.ones(len(raw_data), dtype=bool)

        mask = np.ones(len(raw_data), dtype=bool)
        time_col = raw_data[:, 0]  # 时间列在第一列
        for start, end in exclude_ranges:
            mask &= ((time_col < start) | (time_col > end))

        filtered_data = raw_data[mask] if raw_data is not None else None
        return filtered_data, mask

    # 如果有排除时间段，应用过滤
    if len(exclude_time_ranges) > 0:
        print(f"\n应用排除时间段过滤，共 {len(exclude_time_ranges)} 个时间段:")
        for start, end in exclude_time_ranges:
            print(f"  排除时间段: {start:.2f}s ~ {end:.2f}s")

        # 对原始LC数据应用排除过滤
        if lcs is not None and len(lcs) > 0:
            lcs, mask_lcs_raw = filter_raw_data_by_time(lcs, exclude_time_ranges)
            print(f"  原始LC数据排除后剩余点数: {len(lcs) if lcs is not None else 0}")

        # 对原始TC数据应用排除过滤
        if tcs is not None and len(tcs) > 0:
            tcs, mask_tcs_raw = filter_raw_data_by_time(tcs, exclude_time_ranges)
            print(f"  原始TC数据排除后剩余点数: {len(tcs) if tcs is not None else 0}")

        # 对原始GNSS数据应用排除过滤
        if gnss is not None and len(gnss) > 0:
            gnss, mask_gnss_raw = filter_raw_data_by_time(gnss, exclude_time_ranges)
            print(f"  原始GNSS数据排除后剩余点数: {len(gnss) if gnss is not None else 0}")

        # 对LC、TC、GNSS数据应用排除过滤
        if common_timelc is not None and diff_datalc is not None:
            common_timelc, diff_datalc, mask_lc = filter_excluded_time_ranges(common_timelc, diff_datalc, exclude_time_ranges)
            print(f"  LC对齐数据排除后剩余点数: {len(common_timelc) if common_timelc is not None else 0}")

        if common_timetc is not None and diff_datatc is not None:
            common_timetc, diff_datatc, mask_tc = filter_excluded_time_ranges(common_timetc, diff_datatc, exclude_time_ranges)
            print(f"  TC对齐数据排除后剩余点数: {len(common_timetc) if common_timetc is not None else 0}")

        if common_timegnss is not None and diff_datagnss is not None:
            common_timegnss, diff_datagnss, mask_gnss = filter_excluded_time_ranges(common_timegnss, diff_datagnss, exclude_time_ranges)
            print(f"  GNSS对齐数据排除后剩余点数: {len(common_timegnss) if common_timegnss is not None else 0}")

    # 如果配置文件中没有时间范围配置，则使用旧的seldataset逻辑
    if len(time_ranges_config) == 0:
        print("\n警告: 配置文件中没有时间范围配置")
    else:
        # 使用新的TOML配置，循环处理所有type
        print(f"\n从配置文件读取到 {len(time_ranges_config)} 个type的时间范围配置")
        
        # 创建统一的统计结果文件
        outfile_unified = os.path.join(result_dir, 'position_precision.txt')
        print(f"将创建统一统计结果文件: {outfile_unified}")

        # 收集所有场景的统计结果
        all_type_stats = []

        # 存储所有场景的时间范围（用于后续正常场景计算）
        # 格式: {场景标签: [[start1, end1], [start2, end2], ...]}
        all_scene_time_ranges = {}

        # 从配置文件读取正常场景需要排除的场景列表
        lc_tc_exclude = config.get('normal_scene_exclusions', {}).get('lc_tc_exclude', [])
        gnss_exclude = config.get('normal_scene_exclusions', {}).get('gnss_exclude', [])

        print(f"\n正常场景排除配置:")
        print(f"  LC/TC排除场景: {lc_tc_exclude}")
        print(f"  GNSS排除场景: {gnss_exclude}")

        for idx, type_config in enumerate(time_ranges_config):
            type_label = type_config.get('type_label', str(idx))
            type_time_range = type_config.get('type_time_range', [])

            # 获取参考数据的起始和结束时间（用于处理-1替换）
            if lcs is not None:
                ref_start = lcs[0, 0]
                ref_end = lcs[-1, 0]
            elif tcs is not None:
                ref_start = tcs[0, 0]
                ref_end = tcs[-1, 0]
            elif gnss is not None:
                ref_start = gnss[0, 0]
                ref_end = gnss[-1, 0]
            else:
                ref_start = 0
                ref_end = 0

            # 处理并保存当前场景的时间范围（将-1替换为实际值）
            scene_time_ranges_processed = []
            for start, end in type_time_range:
                if start == -1:
                    start = ref_start
                if end == -1:
                    end = ref_end
                scene_time_ranges_processed.append([start, end])

            # 保存到字典中（即使是被排除的场景也要保存，用于正常场景计算）
            all_scene_time_ranges[type_label] = scene_time_ranges_processed

            # 跳过排除场景（如"卫导异常排除"），不绘图、不统计、不输出
            if type_label in exclude_scene_labels:
                print(f"\n跳过排除场景: '{type_label}'（数据已过滤，不绘图、不统计、不输出）")
                continue

            # 如果该场景在排除列表中，打印提示
            if type_label in lc_tc_exclude or type_label in gnss_exclude:
                print(f"  场景 '{type_label}' 将在正常场景计算中被排除")
                print(f"    时间范围: {scene_time_ranges_processed}")

            print(f"\n{'='*60}")
            print(f"处理 Type {type_label}")
            print(f"{'='*60}")
            
            # 检查时间范围是否为空
            if len(type_time_range) == 0:
                print(f"  该场景无数据（type_time_range为空），统计值置0，跳过绘图")
                
                # 创建空统计结果
                empty_stats = {
                    'type_label': type_label,
                    'has_data': False,
                    'lc': {
                        'odom': 0,
                        'horizontal_rms': 0,
                        'horizontal_cep95': 0,
                        'horizontal_cep99': 0,
                        'horizontal_max': 0,
                        'lateral_rms': 0,
                        'lateral_cep95': 0,
                        'lateral_cep99': 0,
                        'lateral_max': 0,
                        'forward_rms': 0,
                        'forward_cep95': 0,
                        'forward_cep99': 0,
                        'forward_max': 0,
                        'vertical_rms': 0,
                        'vertical_cep95': 0,
                        'vertical_cep99': 0,
                        'vertical_max': 0
                    },
                    'tc': {
                        'odom': 0,
                        'horizontal_rms': 0,
                        'horizontal_cep95': 0,
                        'horizontal_cep99': 0,
                        'horizontal_max': 0,
                        'lateral_rms': 0,
                        'lateral_cep95': 0,
                        'lateral_cep99': 0,
                        'lateral_max': 0,
                        'forward_rms': 0,
                        'forward_cep95': 0,
                        'forward_cep99': 0,
                        'forward_max': 0,
                        'vertical_rms': 0,
                        'vertical_cep95': 0,
                        'vertical_cep99': 0,
                        'vertical_max': 0
                    },
                    'gnss': {
                        'odom': 0,
                        'horizontal_rms': 0,
                        'horizontal_cep95': 0,
                        'horizontal_cep99': 0,
                        'horizontal_max': 0,
                        'lateral_rms': 0,
                        'lateral_cep95': 0,
                        'lateral_cep99': 0,
                        'lateral_max': 0,
                        'forward_rms': 0,
                        'forward_cep95': 0,
                        'forward_cep99': 0,
                        'forward_max': 0,
                        'vertical_rms': 0,
                        'vertical_cep95': 0,
                        'vertical_cep99': 0,
                        'vertical_max': 0
                    }
                }
                all_type_stats.append(empty_stats)
                continue
            
            # 提取时间范围
            if len(type_time_range) > 0:
                # 获取参考数据的起始和结束时间
                # 优先使用lcs，如果lcs为None则使用tcs
                if lcs is not None:
                    ref_start = lcs[0, 0]
                    ref_end = lcs[-1, 0]
                elif tcs is not None:
                    ref_start = tcs[0, 0]
                    ref_end = tcs[-1, 0]
                elif gnss is not None:
                    ref_start = gnss[0, 0]
                    ref_end = gnss[-1, 0]
                else:
                    print("  警告: 没有可用的LC或TC或gnss数据，无法处理-1值")
                    ref_start = 0
                    ref_end = 0
                
                # 处理时间范围，将-1替换为实际数据的时间点
                t_start = []
                t_end = []
                print(f"时间范围数量: {len(type_time_range)}")
                for i, (start, end) in enumerate(type_time_range):
                    # 处理起点值
                    if start == -1:
                        start = ref_start
                        start_label = "lcs[0,0]" if lcs is not None else "tcs[0,0]"
                    else:
                        start_label = str(start)
                    
                    # 处理终点值
                    if end == -1:
                        end = ref_end
                        end_label = "lcs[-1,0]" if lcs is not None else "tcs[-1,0]"
                    else:
                        end_label = str(end)
                    
                    t_start.append(start)
                    t_end.append(end)
                    print(f"  范围 {i+1}: {start_label} ~ {end_label} (实际值: {start} ~ {end})")
            else:
                t_start = []
                t_end = []
                print("  无时间范围限制，使用全部数据")
            
            # 计算统计结果并收集
            print("\n计算统计结果...")
            stats = outpre_new(outfile_unified, diff_datalc, diff_datatc, diff_datagnss,
                               lcs, tcs, gnss, yaw, None, t_start, t_end, type_label,
                               append_mode=False, return_stats=True, lcver=lcver, tcver=tcver)
            stats['type_label'] = type_label

            # 检查该时间段内是否有实际数据（LC/TC/GNSS任意一个有数据即可）
            has_data_in_range = False
            if t_start and t_end:
                for start, end in zip(t_start, t_end):
                    # 检查LC数据
                    if common_timelc is not None and len(common_timelc) > 0:
                        mask_lc = (common_timelc >= start) & (common_timelc <= end)
                        if np.any(mask_lc):
                            has_data_in_range = True
                            break
                    # 检查TC数据
                    if common_timetc is not None and len(common_timetc) > 0:
                        mask_tc = (common_timetc >= start) & (common_timetc <= end)
                        if np.any(mask_tc):
                            has_data_in_range = True
                            break
                    # 检查GNSS数据
                    if common_timegnss is not None and len(common_timegnss) > 0:
                        mask_gnss = (common_timegnss >= start) & (common_timegnss <= end)
                        if np.any(mask_gnss):
                            has_data_in_range = True
                            break
            else:
                # 无时间范围限制时，检查是否有数据
                has_data_in_range = (common_timelc is not None and len(common_timelc) > 0) or \
                                    (common_timetc is not None and len(common_timetc) > 0) or \
                                    (common_timegnss is not None and len(common_timegnss) > 0)

            stats['has_data'] = has_data_in_range

            # 计算水平速度误差
            print("\n计算水平速度误差...")
            velocity_stats = calculate_horizontal_velocity_stats(
                diff_datalc, diff_datatc, diff_datagnss,
                common_timelc, common_timetc, common_timegnss,
                t_start, t_end, type_label, lcver, tcver
            )
            stats['velocity'] = velocity_stats

            all_type_stats.append(stats)

            # 绘制误差曲线（仅当该时间段内有数据时才绘图）
            if has_data_in_range:
                save_path = os.path.join(result_dir, f'{type_label}.png')
                print("\n绘制误差曲线...")
                plot_errors(common_timelc, diff_datalc, common_timetc, diff_datatc,
                            common_timegnss, diff_datagnss, t0, save_path, yaw, t_start, t_end,
                            lcver, tcver, plotlc=plotlc, plottc=plottc,
                            gap_intervals=gap_intervals)
            else:
                print(f"\n该时间段内无实际数据，跳过绘图（统计结果已输出到表格）")
            
            # 对于type为"All"的情况，绘制详细子图（仅当有数据时）
            if has_data_in_range and type_label.lower() == 'all':
                print(f"\nType '{type_label}' 为必须解算场景，开始绘制详细子图...")
                
                # 从配置文件读取子图绘制参数
                horizontal_threshold_meters = config.get('detail_plot', {}).get('horizontal_error_threshold_meters', 10.0)
                vertical_threshold_meters = config.get('detail_plot', {}).get('vertical_error_threshold_meters', 15.0)
                detail_window_seconds = config.get('detail_plot', {}).get('detail_window_seconds', 20.0)
                
                # 调用子图绘制函数
                plot_detail_subplots(
                    common_timelc, diff_datalc,
                    common_timetc, diff_datatc,
                    common_timegnss, diff_datagnss,
                    t0, yaw,
                    horizontal_threshold_meters, vertical_threshold_meters,
                    detail_window_seconds, result_dir, type_label, lcver, tcver,
                    plotlc=plotlc, plottc=plottc, gap_intervals=gap_intervals
                )
            else:
                print(f"\nType '{type_label}' 不需要绘制详细子图（仅All类型需要）")

        # 处理正常场景（去除特殊场景后的剩余时段）
        print(f"\n{'='*60}")
        print("处理正常场景")
        print(f"{'='*60}")

        # 获取All场景的时间范围作为总时间范围
        all_time_ranges = []
        for type_config in time_ranges_config:
            if type_config.get('type_label', '').lower() == 'all':
                all_time_ranges = type_config.get('type_time_range', [])
                break

        if len(all_time_ranges) > 0:
            # 处理All场景的时间范围（将-1替换为实际数据的时间点）
            if lcs is not None:
                ref_start = lcs[0, 0]
                ref_end = lcs[-1, 0]
            elif tcs is not None:
                ref_start = tcs[0, 0]
                ref_end = tcs[-1, 0]
            elif gnss is not None:
                ref_start = gnss[0, 0]
                ref_end = gnss[-1, 0]
            else:
                ref_start = 0
                ref_end = 0

            # 替换-1为实际时间点
            all_time_ranges_processed = []
            for start, end in all_time_ranges:
                if start == -1:
                    start = ref_start
                if end == -1:
                    end = ref_end
                all_time_ranges_processed.append([start, end])

            # 从配置的排除场景列表中收集需要排除的时间范围
            # GNSS正常场景：排除gnss_exclude列表中的场景 + 卫导异常排除等完全排除场景
            gnss_excluded_ranges = []
            for exclude_scene in gnss_exclude:
                if exclude_scene in all_scene_time_ranges:
                    gnss_excluded_ranges.extend(all_scene_time_ranges[exclude_scene])
                    print(f"  GNSS正常场景排除: {exclude_scene}")
            # 添加完全排除场景（如"卫导异常排除"）
            for exclude_scene in exclude_scene_labels:
                if exclude_scene in all_scene_time_ranges:
                    gnss_excluded_ranges.extend(all_scene_time_ranges[exclude_scene])
                    print(f"  GNSS正常场景排除（完全跳过）: {exclude_scene}")

            # LC/TC正常场景：排除lc_tc_exclude列表中的场景 + 卫导异常排除等完全排除场景
            lc_tc_excluded_ranges = []
            for exclude_scene in lc_tc_exclude:
                if exclude_scene in all_scene_time_ranges:
                    lc_tc_excluded_ranges.extend(all_scene_time_ranges[exclude_scene])
                    print(f"  LC/TC正常场景排除: {exclude_scene}")
            # 添加完全排除场景（如"卫导异常排除"）
            for exclude_scene in exclude_scene_labels:
                if exclude_scene in all_scene_time_ranges:
                    lc_tc_excluded_ranges.extend(all_scene_time_ranges[exclude_scene])
                    print(f"  LC/TC正常场景排除（完全跳过）: {exclude_scene}")

            # 计算正常场景的时间范围
            normal_time_ranges_gnss = calculate_normal_scene_time_ranges(
                all_time_ranges_processed, gnss_excluded_ranges
            )
            normal_time_ranges_lc_tc = calculate_normal_scene_time_ranges(
                all_time_ranges_processed, lc_tc_excluded_ranges
            )

            # 处理GNSS正常场景
            if len(normal_time_ranges_gnss) > 0:
                print(f"\nGNSS正常场景（排除: {gnss_exclude}）:")
                print(f"  排除的时间范围:")
                for ex_range in gnss_excluded_ranges:
                    print(f"    {ex_range[0]:.2f}s ~ {ex_range[1]:.2f}s")
                print(f"  正常场景的时间范围:")
                t_start_gnss = []
                t_end_gnss = []
                for i, (start, end) in enumerate(normal_time_ranges_gnss):
                    print(f"    {start:.2f}s ~ {end:.2f}s")
                    t_start_gnss.append(start)
                    t_end_gnss.append(end)

                # 生成GNSS正常场景的标签（使用简化格式，便于聚合脚本查找）
                type_label_gnss = 'Normal_GNSS'

                print(f"\n计算GNSS正常场景统计...")
                stats_gnss_normal = outpre_new(
                    outfile_unified, diff_datalc, diff_datatc, diff_datagnss,
                    lcs, tcs, gnss, yaw, None, t_start_gnss, t_end_gnss, type_label_gnss,
                    append_mode=False, return_stats=True, lcver=lcver, tcver=tcver
                )
                stats_gnss_normal['type_label'] = type_label_gnss
                stats_gnss_normal['has_data'] = True

                # 计算GNSS正常场景速度误差
                print(f"\n计算GNSS正常场景水平速度误差...")
                velocity_stats_gnss = calculate_horizontal_velocity_stats(
                    diff_datalc, diff_datatc, diff_datagnss,
                    common_timelc, common_timetc, common_timegnss,
                    t_start_gnss, t_end_gnss, type_label_gnss, lcver, tcver
                )
                stats_gnss_normal['velocity'] = velocity_stats_gnss

                # 只保留GNSS的统计，LC和TC置0
                stats_gnss_normal['lc'] = {
                    'odom': 0,
                    'horizontal_rms': 0, 'horizontal_cep95': 0, 'horizontal_cep99': 0, 'horizontal_max': 0,
                    'lateral_rms': 0, 'lateral_cep95': 0, 'lateral_cep99': 0, 'lateral_max': 0,
                    'forward_rms': 0, 'forward_cep95': 0, 'forward_cep99': 0, 'forward_max': 0,
                    'vertical_rms': 0, 'vertical_cep95': 0, 'vertical_cep99': 0, 'vertical_max': 0
                }
                stats_gnss_normal['tc'] = {
                    'odom': 0,
                    'horizontal_rms': 0, 'horizontal_cep95': 0, 'horizontal_cep99': 0, 'horizontal_max': 0,
                    'lateral_rms': 0, 'lateral_cep95': 0, 'lateral_cep99': 0, 'lateral_max': 0,
                    'forward_rms': 0, 'forward_cep95': 0, 'forward_cep99': 0, 'forward_max': 0,
                    'vertical_rms': 0, 'vertical_cep95': 0, 'vertical_cep99': 0, 'vertical_max': 0
                }
                stats_gnss_normal['velocity']['lc'] = {
                    'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0,
                    'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0
                }
                stats_gnss_normal['velocity']['tc'] = {
                    'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0,
                    'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0
                }

                # 绘制GNSS正常场景误差曲线
                save_path_gnss = os.path.join(result_dir, f'正常_GNSS.png')
                print(f"\n绘制GNSS正常场景误差曲线...")
                plot_errors(
                    common_timelc, diff_datalc, common_timetc, diff_datatc,
                    common_timegnss, diff_datagnss, t0, save_path_gnss, yaw,
                    t_start_gnss, t_end_gnss, lcver, tcver,
                    plotlc=False, plottc=False, gap_intervals=gap_intervals
                )

                all_type_stats.append(stats_gnss_normal)
            else:
                print(f"\n警告: GNSS正常场景时间范围为空，跳过GNSS正常场景处理")

            # 处理LC/TC正常场景
            if len(normal_time_ranges_lc_tc) > 0:
                # 生成LC/TC正常场景的标签
                if len(lc_tc_exclude) > 0:
                    exclude_str = ', '.join(lc_tc_exclude)
                    lc_tc_label_suffix = f'No {exclude_str}'
                else:
                    lc_tc_label_suffix = 'All Scenes'

                print(f"\nLC/TC正常场景（排除: {lc_tc_exclude}）:")
                print(f"  排除的时间范围:")
                for ex_range in lc_tc_excluded_ranges:
                    print(f"    {ex_range[0]:.2f}s ~ {ex_range[1]:.2f}s")
                print(f"  正常场景的时间范围:")
                t_start_lc_tc = []
                t_end_lc_tc = []
                for i, (start, end) in enumerate(normal_time_ranges_lc_tc):
                    print(f"    {start:.2f}s ~ {end:.2f}s")
                    t_start_lc_tc.append(start)
                    t_end_lc_tc.append(end)

                # 计算LC正常场景统计（使用简化格式，便于聚合脚本查找）
                type_label_lc = 'Normal_LC'
                print(f"\n计算LC正常场景统计...")
                stats_lc_normal = outpre_new(
                    outfile_unified, diff_datalc, diff_datatc, diff_datagnss,
                    lcs, tcs, gnss, yaw, None, t_start_lc_tc, t_end_lc_tc, type_label_lc,
                    append_mode=False, return_stats=True, lcver=lcver, tcver=tcver
                )
                stats_lc_normal['type_label'] = type_label_lc
                stats_lc_normal['has_data'] = True

                # 计算LC正常场景速度误差
                print(f"\n计算LC正常场景水平速度误差...")
                velocity_stats_lc = calculate_horizontal_velocity_stats(
                    diff_datalc, diff_datatc, diff_datagnss,
                    common_timelc, common_timetc, common_timegnss,
                    t_start_lc_tc, t_end_lc_tc, type_label_lc, lcver, tcver
                )
                stats_lc_normal['velocity'] = velocity_stats_lc

                # 只保留LC的统计，TC和GNSS置0
                stats_lc_normal['tc'] = {
                    'odom': 0,
                    'horizontal_rms': 0, 'horizontal_cep95': 0, 'horizontal_cep99': 0, 'horizontal_max': 0,
                    'lateral_rms': 0, 'lateral_cep95': 0, 'lateral_cep99': 0, 'lateral_max': 0,
                    'forward_rms': 0, 'forward_cep95': 0, 'forward_cep99': 0, 'forward_max': 0,
                    'vertical_rms': 0, 'vertical_cep95': 0, 'vertical_cep99': 0, 'vertical_max': 0
                }
                stats_lc_normal['gnss'] = {
                    'odom': 0,
                    'horizontal_rms': 0, 'horizontal_cep95': 0, 'horizontal_cep99': 0, 'horizontal_max': 0,
                    'lateral_rms': 0, 'lateral_cep95': 0, 'lateral_cep99': 0, 'lateral_max': 0,
                    'forward_rms': 0, 'forward_cep95': 0, 'forward_cep99': 0, 'forward_max': 0,
                    'vertical_rms': 0, 'vertical_cep95': 0, 'vertical_cep99': 0, 'vertical_max': 0
                }
                stats_lc_normal['velocity']['tc'] = {
                    'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0,
                    'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0
                }
                stats_lc_normal['velocity']['gnss'] = {
                    'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0,
                    'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0
                }

                # 绘制LC正常场景误差曲线
                save_path_lc = os.path.join(result_dir, f'正常_LC.png')
                print(f"\n绘制LC正常场景误差曲线...")
                plot_errors(
                    common_timelc, diff_datalc, common_timetc, diff_datatc,
                    common_timegnss, diff_datagnss, t0, save_path_lc, yaw,
                    t_start_lc_tc, t_end_lc_tc, lcver, tcver,
                    plotlc=True, plottc=False, gap_intervals=gap_intervals
                )

                all_type_stats.append(stats_lc_normal)

                # 计算TC正常场景统计（使用简化格式，便于聚合脚本查找）
                type_label_tc = 'Normal_TC'
                print(f"\n计算TC正常场景统计...")
                stats_tc_normal = outpre_new(
                    outfile_unified, diff_datalc, diff_datatc, diff_datagnss,
                    lcs, tcs, gnss, yaw, None, t_start_lc_tc, t_end_lc_tc, type_label_tc,
                    append_mode=False, return_stats=True, lcver=lcver, tcver=tcver
                )
                stats_tc_normal['type_label'] = type_label_tc
                stats_tc_normal['has_data'] = True

                # 计算TC正常场景速度误差
                print(f"\n计算TC正常场景水平速度误差...")
                velocity_stats_tc = calculate_horizontal_velocity_stats(
                    diff_datalc, diff_datatc, diff_datagnss,
                    common_timelc, common_timetc, common_timegnss,
                    t_start_lc_tc, t_end_lc_tc, type_label_tc, lcver, tcver
                )
                stats_tc_normal['velocity'] = velocity_stats_tc

                # 只保留TC的统计，LC和GNSS置0
                stats_tc_normal['lc'] = {
                    'odom': 0,
                    'horizontal_rms': 0, 'horizontal_cep95': 0, 'horizontal_cep99': 0, 'horizontal_max': 0,
                    'lateral_rms': 0, 'lateral_cep95': 0, 'lateral_cep99': 0, 'lateral_max': 0,
                    'forward_rms': 0, 'forward_cep95': 0, 'forward_cep99': 0, 'forward_max': 0,
                    'vertical_rms': 0, 'vertical_cep95': 0, 'vertical_cep99': 0, 'vertical_max': 0
                }
                stats_tc_normal['gnss'] = {
                    'odom': 0,
                    'horizontal_rms': 0, 'horizontal_cep95': 0, 'horizontal_cep99': 0, 'horizontal_max': 0,
                    'lateral_rms': 0, 'lateral_cep95': 0, 'lateral_cep99': 0, 'lateral_max': 0,
                    'forward_rms': 0, 'forward_cep95': 0, 'forward_cep99': 0, 'forward_max': 0,
                    'vertical_rms': 0, 'vertical_cep95': 0, 'vertical_cep99': 0, 'vertical_max': 0
                }
                stats_tc_normal['velocity']['lc'] = {
                    'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0,
                    'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0
                }
                stats_tc_normal['velocity']['gnss'] = {
                    'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0,
                    'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0
                }

                # 绘制TC正常场景误差曲线
                save_path_tc = os.path.join(result_dir, f'正常_TC.png')
                print(f"\n绘制TC正常场景误差曲线...")
                plot_errors(
                    common_timelc, diff_datalc, common_timetc, diff_datatc,
                    common_timegnss, diff_datagnss, t0, save_path_tc, yaw,
                    t_start_lc_tc, t_end_lc_tc, lcver, tcver,
                    plotlc=False, plottc=True, gap_intervals=gap_intervals
                )

                all_type_stats.append(stats_tc_normal)
            else:
                print(f"\n警告: LC/TC正常场景时间范围为空，跳过LC/TC正常场景处理")
        else:
            print(f"\n警告: 未找到'All'场景的时间范围配置，无法计算正常场景")

        # 所有场景处理完成后，统一输出表格格式的统计结果
        print("\n输出统一表格格式的统计结果...")
        outpre_unified_table(outfile_unified, all_type_stats, t0, lcver, tcver)

        # 输出水平速度误差统计文件
        print("\n输出水平速度误差统计文件...")
        velocity_stats_file = os.path.join(result_dir, 'velocity_precision.txt')
        save_horizontal_velocity_stats(velocity_stats_file, all_type_stats, lcver, tcver)
    
    # 处理GNSS clip数据（如果配置启用）
    saveclip = config.get('clip_plot', {}).get('saveclip', 0)
    if saveclip == 1 and gnss0 is not None and diff_datagnss is not None and common_timegnss is not None:
        print(f"\n配置启用GNSS Clip处理")
        horizontal_threshold_meters = config.get('clip_plot', {}).get('horizontal_error_threshold_meters', 10.0)
        vertical_threshold_meters = config.get('clip_plot', {}).get('vertical_error_threshold_meters', 15.0)
        clip_interval_seconds = config.get('clip_plot', {}).get('clip_plot_interval_seconds', 50.0)
        
        save_and_plot_clips(
            gnss0, diff_datagnss, common_timegnss, yaw,
            horizontal_threshold_meters, vertical_threshold_meters,
            clip_interval_seconds, result_dir, t0, gnss_time_mapping,
            gnssstdindex0  # 传递动态计算的std索引，修复std索引bug
        )
    
    print(f"\n{'='*60}")
    print("评估完成!")
    print(f"{'='*60}\n")
    
    return {
        'lcs': lcs,
        'tcs': tcs,
        'gnss': gnss,
        'refdata': refdata,
        'diff_datalc': diff_datalc,
        'diff_datatc': diff_datatc,
        'diff_datagnss': diff_datagnss,
        'common_timelc': common_timelc,
        'common_timetc': common_timetc,
        'common_timegnss': common_timegnss,
        't0': t0,
        't_start': t_start,
        't_end': t_end
    }


def save_and_plot_clips(
    gnss, diff_datagnss, common_timegnss, yaw, 
    horizontal_threshold_meters, vertical_threshold_meters, 
    clip_interval_seconds, output_dir, t0, gnss_time_mapping=None,
    gnssstdindex0=None
):
    """
    保存和绘制GNSS clip数据
    
    Args:
        gnss: GNSS原始数据（包含std数据列）
        diff_datagnss: GNSS差值数据
        common_timegnss: GNSS公共时间点
        yaw: 航向角数据
        horizontal_threshold_meters: 水平误差阈值（米）
        vertical_threshold_meters: 垂直误差阈值（米）
        clip_interval_seconds: clip子图时间间隔（秒）
        output_dir: 输出目录
        t0: 时间基准点
        gnss_time_mapping: GPS周内秒到Unix时间戳的映射字典
        gnssstdindex0: std数据的起始索引（动态计算，修复std索引bug）
    """
    print(f"\n{'='*60}")
    print("开始处理GNSS Clip数据")
    print(f"{'='*60}")
    print(f"  水平误差阈值: {horizontal_threshold_meters}米")
    print(f"  垂直误差阈值: {vertical_threshold_meters}米")
    print(f"  子图时间间隔: {clip_interval_seconds}秒")
    
    # 计算GNSS误差
    gnss_horizontal, gnss_lateral, gnss_vertical, _ = calculate_errors(diff_datagnss, yaw)
    gnss_horizontal_error = np.sqrt(gnss_horizontal**2 + gnss_lateral**2)
    
    # 筛选超过阈值的数据点
    horizontal_exceeds = gnss_horizontal_error > horizontal_threshold_meters
    vertical_exceeds = np.abs(gnss_vertical) > vertical_threshold_meters
    exceeds = horizontal_exceeds | vertical_exceeds
    
    exceed_indices = np.where(exceeds)[0]
    
    if len(exceed_indices) == 0:
        print("  没有数据超过阈值，跳过clip处理")
        return
    
    print(f"  超过阈值的数据点数: {len(exceed_indices)}")
    
    # 创建clip目录
    clip_dir = os.path.join(output_dir, 'clip')
    os.makedirs(clip_dir, exist_ok=True)
    print(f"  Clip数据保存目录: {clip_dir}")
    
    # 根据超过阈值的数据点，提取连续的数据段
    clip_segments = []
    current_segment = []
    
    for i in range(len(exceed_indices)):
        idx = exceed_indices[i]
        
        if len(current_segment) == 0:
            current_segment.append(idx)
        else:
            # 检查是否连续（时间间隔小于1秒）
            prev_idx = current_segment[-1]
            if common_timegnss[idx] - common_timegnss[prev_idx] < 1.0:
                current_segment.append(idx)
            else:
                # 保存当前段，开始新段
                if len(current_segment) > 0:
                    clip_segments.append(current_segment)
                current_segment = [idx]
    
    # 保存最后一段
    if len(current_segment) > 0:
        clip_segments.append(current_segment)
    
    print(f"  识别到 {len(clip_segments)} 个数据段")
    
    # 保存原始数据段
    clip_data_file = os.path.join(clip_dir, 'gnss_clip_raw_data.csv')
    
    # 收集所有clip段的原始数据
    all_clip_raw_data = []
    for seg_idx, segment in enumerate(clip_segments):
        # 获取这个段的时间范围
        seg_start_idx = segment[0]
        seg_end_idx = segment[-1]
        seg_start_time = common_timegnss[seg_start_idx]
        seg_end_time = common_timegnss[seg_end_idx]
        
        # 在原始gnss数据中找到对应的索引
        mask = (gnss[:, 0] >= seg_start_time) & (gnss[:, 0] <= seg_end_time)
        segment_raw_data = gnss[mask, :]
        
        # 添加段标识
        num_rows = segment_raw_data.shape[0]
        segment_col = np.full((num_rows, 1), seg_idx)
        
        # 添加时间列（使用GPS周内秒到Unix时间戳的映射）
        # segment_raw_data[i, 0]是GPS周内秒，需要映射到Unix时间戳
        original_times = []
        if gnss_time_mapping:
            for i in range(num_rows):
                gps_week_seconds = segment_raw_data[i, 0]  # GPS周内秒
                # 从映射字典中获取对应的Unix时间戳
                unix_timestamp = gnss_time_mapping.get(gps_week_seconds, gps_week_seconds)
                original_times.append([unix_timestamp])
        else:
            # 如果没有映射字典，直接使用GPS周内秒
            for i in range(num_rows):
                original_times.append([segment_raw_data[i, 0]])
        
        time_col = np.array(original_times)
        
        # 将段标识和时间列都添加到原始数据中
        segment_raw_data = np.hstack([segment_raw_data, segment_col, time_col])
        
        all_clip_raw_data.append(segment_raw_data)
        print(f"  段 {seg_idx}: 时间 {seg_start_time:.2f}s ~ {seg_end_time:.2f}s, 数据点数 {num_rows}")
    
    # 合并所有段并保存
    if len(all_clip_raw_data) > 0:
        all_clip_raw_data = np.vstack(all_clip_raw_data)
        
        # 定义每列的格式
        num_cols = all_clip_raw_data.shape[1]
        fmt_list = []
        for col_idx in range(num_cols):
            if col_idx == 0:  # 首列（时间列）保留3位小数
                fmt_list.append('%.3f')
            elif col_idx == 7 or col_idx == 8:  # 第8-9列（经纬度，索引7-8）保留8位小数
                fmt_list.append('%.8f')
            else:  # 其他列保留6位小数
                fmt_list.append('%.6f')
        
        np.savetxt(clip_data_file, all_clip_raw_data, delimiter=',', fmt=fmt_list)
        print(f"  原始数据已保存到: {clip_data_file}")
        print(f"  输出格式: 第1列和最后一列（原始时间）3位小数，第8-9列8位小数，其他列6位小数")
        print(f"  最后一列为原始时间，与原gnsspath对应文件的首列时间相同")
    
    # 绘制clip子图（50s间隔）
    print(f"\n开始绘制clip子图...")
    
    # 构建std索引数组（修复std索引bug）
    gnssstdindex = [gnssstdindex0, gnssstdindex0 + 1, gnssstdindex0 + 2] if gnssstdindex0 is not None else [14, 15, 16]
    
    clip_subplot_count = 0
    for seg_idx, segment in enumerate(clip_segments):
        seg_start_idx = segment[0]
        seg_end_idx = segment[-1]
        seg_start_time = common_timegnss[seg_start_idx]
        seg_end_time = common_timegnss[seg_end_idx] + 0.1
        
        # 计算这个段需要多少个子图（每个子图50s）
        seg_duration = seg_end_time - seg_start_time
        num_subplots = int(np.ceil(seg_duration / clip_interval_seconds))
        
        print(f"  段 {seg_idx}: 时长 {seg_duration:.2f}s, 需要绘制 {num_subplots} 个子图")
        
        # 为这个段绘制多个子图
        for subplot_idx in range(num_subplots):
            subplot_start = seg_start_time + subplot_idx * clip_interval_seconds
            subplot_end = min(subplot_start + clip_interval_seconds, seg_end_time)
            
            # 筛选这个子图范围内的数据
            mask = (common_timegnss >= subplot_start) & (common_timegnss < subplot_end)
            subplot_time = common_timegnss[mask]
            subplot_horizontal_error = gnss_horizontal_error[mask]
            subplot_vertical_error = np.abs(gnss_vertical[mask])
            subplot_3d_error = np.sqrt(subplot_horizontal_error**2 + subplot_vertical_error**2)
            
            # 获取std数据（使用动态计算的索引，修复std索引bug）
            # 首先找到对应的原始数据索引
            mask_raw = (gnss[:, 0] >= subplot_start) & (gnss[:, 0] < subplot_end)
            subplot_std_x = gnss[mask_raw, gnssstdindex[0]] if gnss.shape[1] > gnssstdindex[0] else np.zeros(len(subplot_time))
            subplot_std_y = gnss[mask_raw, gnssstdindex[1]] if gnss.shape[1] > gnssstdindex[1] else np.zeros(len(subplot_time))
            subplot_std_z = gnss[mask_raw, gnssstdindex[2]] if gnss.shape[1] > gnssstdindex[2] else np.zeros(len(subplot_time))
            subplot_3d_std = np.sqrt(subplot_std_x**2 + subplot_std_y**2 + subplot_std_z**2)
            
            if len(subplot_time) == 0:
                continue
            
            # 计算时长
            duration = subplot_end - subplot_start
            
            # 绘制子图（2行1列：第一行水平误差和std，第二行垂直误差和std）
            clip_subplot_count += 1
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            # 第一行：水平误差和std（添加点标记）
            axes[0].plot(subplot_time, subplot_horizontal_error, 'b-o', linewidth=2.0, markersize=4, 
                         label='Horizontal Position Error', alpha=0.8)
            axes[0].plot(subplot_time, subplot_3d_std, 'r-s', linewidth=2.0, markersize=4, 
                         label='Horizontal Position Std', alpha=0.8)
            axes[0].set_ylabel('Error/Std (m)', fontsize=13)
            axes[0].set_title(f'Clip Segment {seg_idx}, Window {subplot_idx+1}/{num_subplots} ({duration:.2f}s)', 
                             fontsize=15, fontweight='bold')
            axes[0].grid(True, alpha=0.3)
            axes[0].legend(fontsize=12, loc='upper right')
            
            # 第二行：垂直误差和std（添加点标记）
            axes[1].plot(subplot_time, subplot_vertical_error, 'b-o', linewidth=2.0, markersize=4, 
                         label='Vertical Position Error', alpha=0.8)
            axes[1].plot(subplot_time, subplot_std_z, 'r-s', linewidth=2.0, markersize=4, 
                         label='Vertical Position Std', alpha=0.8)
            axes[1].set_xlabel('Time (s)', fontsize=13)
            axes[1].set_ylabel('Error/Std (m)', fontsize=13)
            axes[1].grid(True, alpha=0.3)
            axes[1].legend(fontsize=12, loc='upper right')
            
            # 设置横轴显示完整时间，不使用科学计数法或缩写
            for ax in axes:
                ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=False, useMathText=False))
                ax.ticklabel_format(style='plain', axis='x')
            
            plt.tight_layout()
            
            save_path = os.path.join(clip_dir, f'clip_subplot_seg{seg_idx}_sub{subplot_idx}.png')
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"    已保存子图: {os.path.basename(save_path)}")
    
    print(f"  共绘制 {clip_subplot_count} 个clip子图")
    
    # 绘制总图（时间归一化）- 2行1列布局
    print(f"\n绘制GNSS总图（2行1列：水平误差+高程误差）...")
    
    # 计算水平误差和高程误差
    gnss_horizontal_error_final = gnss_horizontal_error  # 水平误差
    gnss_vertical_error_final = np.abs(gnss_vertical)    # 高程误差
    
    # 获取所有GNSS数据的std（使用动态计算的索引，修复std索引bug）
    gnss_std_x = np.zeros(len(common_timegnss))
    gnss_std_y = np.zeros(len(common_timegnss))
    gnss_std_z = np.zeros(len(common_timegnss))
    
    for i, t in enumerate(common_timegnss):
        # 在原始gnss数据中找到最接近的时间点
        idx = np.argmin(np.abs(gnss[:, 0] - t))
        if gnss.shape[1] > gnssstdindex[0]:
            gnss_std_x[i] = gnss[idx, gnssstdindex[0]]
        if gnss.shape[1] > gnssstdindex[1]:
            gnss_std_y[i] = gnss[idx, gnssstdindex[1]]
        if gnss.shape[1] > gnssstdindex[2]:
            gnss_std_z[i] = gnss[idx, gnssstdindex[2]]
    
    # 水平std和垂直std
    gnss_horizontal_std = np.sqrt(gnss_std_x**2 + gnss_std_y**2)
    gnss_vertical_std = gnss_std_z
    
    # 时间归一化（减去起点）
    normalized_time = common_timegnss - t0
    
    # 绘制总图（2行1列）
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    
    # 第一行：水平误差和std
    axes[0].plot(normalized_time, gnss_horizontal_error_final, 'b-', linewidth=1.5, 
                 label='Horizontal Position Error', alpha=0.8)
    axes[0].plot(normalized_time, gnss_horizontal_std, 'r-', linewidth=1.5, 
                 label='Horizontal Position Std', alpha=0.8)
    axes[0].axhline(y=horizontal_threshold_meters, color='orange', linestyle='--', 
                    label=f'Horizontal Threshold ({horizontal_threshold_meters}m)', alpha=0.6)
    axes[0].set_xlabel('Relative Time (s)', fontsize=14)
    axes[0].set_ylabel('Error (m)', fontsize=14)
    axes[0].set_title('GNSS Horizontal Position Error and Std', fontsize=16, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=12, loc='upper right')
    
    # 第二行：高程误差和std
    axes[1].plot(normalized_time, gnss_vertical_error_final, 'b-', linewidth=1.5, 
                 label='Vertical Position Error', alpha=0.8)
    axes[1].plot(normalized_time, gnss_vertical_std, 'r-', linewidth=1.5, 
                 label='Vertical Position Std', alpha=0.8)
    axes[1].axhline(y=vertical_threshold_meters, color='green', linestyle='--', 
                    label=f'Vertical Threshold ({vertical_threshold_meters}m)', alpha=0.6)
    axes[1].set_xlabel('Relative Time (s)', fontsize=14)
    axes[1].set_ylabel('Error (m)', fontsize=14)
    axes[1].set_title('GNSS Vertical Position Error and Std', fontsize=16, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=12, loc='upper right')
    
    # 添加时间起点备注
    for ax in axes:
        ax.text(0.02, 0.98, f'Time Axis Start (t0): {t0:.2f} s', 
                transform=ax.transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    save_path = os.path.join(clip_dir, 'gnss_error_and_std_overview.png')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  总图已保存到: {os.path.basename(save_path)}")
    
    # 绘制GNSS全部误差图（不包含std）
    print(f"\n绘制GNSS全部误差图（不包含std）...")
    
    # 时间归一化（减去起点）
    normalized_time = common_timegnss - t0
    
    # 绘制新图（只包含误差，不包含std）- 2行1列布局
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    
    # 第一行：水平位置误差（点和线）
    axes[0].plot(normalized_time, gnss_horizontal_error_final, 'b-o', linewidth=1.5, markersize=2, 
                label='Horizontal Position Error', alpha=0.8)
    axes[0].axhline(y=horizontal_threshold_meters, color='orange', linestyle='--', 
                   label=f'Horizontal Threshold ({horizontal_threshold_meters}m)', alpha=0.6)
    axes[0].set_xlabel('Relative Time (s)', fontsize=14)
    axes[0].set_ylabel('Error (m)', fontsize=14)
    axes[0].set_title('GNSS Horizontal Position Error (No Std)', fontsize=16, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=12, loc='upper right')
    
    # 第二行：高程位置误差（点和线）
    axes[1].plot(normalized_time, gnss_vertical_error_final, 'b-o', linewidth=1.5, markersize=2, 
                label='Vertical Position Error', alpha=0.8)
    axes[1].axhline(y=vertical_threshold_meters, color='green', linestyle='--', 
                   label=f'Vertical Threshold ({vertical_threshold_meters}m)', alpha=0.6)
    axes[1].set_xlabel('Relative Time (s)', fontsize=14)
    axes[1].set_ylabel('Error (m)', fontsize=14)
    axes[1].set_title('GNSS Vertical Position Error (No Std)', fontsize=16, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=12, loc='upper right')
    
    # 添加时间起点备注
    for ax in axes:
        ax.text(0.02, 0.98, f'Time Axis Start (t0): {t0:.2f} s', 
                transform=ax.transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    save_path_new = os.path.join(clip_dir, 'gnss_error_only_no_std.png')
    plt.savefig(save_path_new, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  全部误差图（无std）已保存到: {os.path.basename(save_path_new)}")
    print(f"\nClip处理完成!")


def main():
    """命令行入口"""
    # 支持两种模式：TOML配置文件和命令行参数
    if len(sys.argv) == 1:
        print("使用方法:")
        print("  方法1 (推荐): python precision_head_topic_ref_100c_wdh.py <config.toml>")
        print("  方法2 (已弃用): python precision_head_topic_ref_100c_wdh.py <basefold> <reffile> [lcver] [tcver] [dataset] [dt] [plotlc] [plottc] [plotgnssstat]")
        print("\n建议使用TOML配置文件，示例配置文件: precision_head_topic_ref_100c_wdh_config.toml")
        return
    
    # 初始化config变量
    config = None
    
    # 检查是否使用TOML配置文件
    if sys.argv[1].endswith('.toml'):
        # 使用TOML配置文件
        config_path = sys.argv[1]
        config = load_config_from_toml(config_path)
        
        # 从配置文件读取参数
        basefold = config.get('data', {}).get('basefold', '')
        reffile = config.get('data', {}).get('reffile', '')
        lcver = config.get('data', {}).get('lcver', '')
        tcver = config.get('data', {}).get('tcver', '')
        dataset = config.get('data', {}).get('dataset', '')
        dt = config.get('data', {}).get('dt', 0.0)
        
        plotlc = config.get('plot', {}).get('plotlc', True)
        plottc = config.get('plot', {}).get('plottc', False)
        plotgnssstat = config.get('plot', {}).get('plotgnssstat', True)
        
        tthreshod = config.get('evaluation', {}).get('tthreshod', 5e-3)
        
        output_dir = config.get('output', {}).get('output_dir', '')
        if output_dir == '':
            output_dir = None
        
        reftype = config.get('advanced', {}).get('reftype', 0)
        statetype = config.get('advanced', {}).get('statetype', 0)
        
        # 读取水平精度专用配置项（兼容配置，原始脚本默认不启用）
        horizontal_only = config.get('evaluation', {}).get('horizontal_only', 0)
        
        print(f"\n从配置文件读取参数:")
        print(f"  basefold = {basefold}")
        print(f"  reffile = {reffile}")
        print(f"  lcver = {lcver}")
        print(f"  tcver = {tcver}")
        print(f"  dataset = {dataset}")
        print(f"  dt = {dt}")
        print(f"  plotlc = {plotlc}")
        print(f"  plottc = {plottc}")
        print(f"  plotgnssstat = {plotgnssstat}")
        print(f"  tthreshod = {tthreshod}")
        print(f"  output_dir = {output_dir}")
        print(f"  reftype = {reftype}")
        print(f"  statetype = {statetype}")
        print(f"  horizontal_only = {horizontal_only}")
        
        # 如果配置项启用了水平精度专用模式，给出提示
        if horizontal_only == 1:
            print("\n注意：配置文件中启用了水平精度专用模式 (horizontal_only=1)")
            print("但当前脚本为完整精度评估版本，将包含所有误差项")
            print("如需仅评估水平精度，请使用专用脚本:")
            print("  precision_head_topic_ref_100c_wdh_horizontal_only.py")
        
    else:
        print('no config file.')
    
    # 执行评估
    precision_head_topic_ref_100c_wdh(
        basefold=basefold,
        reffile=reffile,
        lcver=lcver,
        tcver=tcver,
        dataset=dataset,
        dt=dt,
        plotlc=plotlc,
        plottc=plottc,
        plotgnssstat=plotgnssstat,
        tthreshod=tthreshod,
        output_dir=output_dir,
        reftype=reftype,
        statetype=statetype,
        config=config  # 传递config参数
    )


if __name__ == '__main__':
    main()
