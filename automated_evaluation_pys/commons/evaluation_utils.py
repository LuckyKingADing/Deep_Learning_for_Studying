"""
评估工具公共模块
包含precision评估脚本中可复用的函数
"""

import numpy as np
import os
import sys
import toml

# 导入现有的数据读取函数
from readSensorDataTcXkPk import readSensorDataTcXkPk
from readmsf_debug_state import readmsf_debug_state
import utils


def load_config_from_toml(config_path):
    """
    从TOML配置文件加载配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        config: 配置字典
    """
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        sys.exit(1)
    
    try:
        config = toml.load(config_path)
        print(f"已加载配置文件: {config_path}")
        return config
    except Exception as e:
        print(f"错误: 无法解析配置文件 - {e}")
        sys.exit(1)


def process_sensor_data(filepath, refdata, pos0, tthreshod, statetype, dt, data_type):
    """
    处理传感器数据(LC或TC)
    
    Args:
        filepath: 数据文件路径
        refdata: 参考数据
        tthreshod: 时间阈值
        statetype: 状态文件类型 0-tcmsf_sol.csv 1-msf_debug_state.csv
        dt: 时间偏移
        data_type: 数据类型名称('LC'或'TC'),用于打印信息
        
    Returns:
        data: 处理后的数据
        diff_data: 差值数据
        common_time: 公共时间点
    """
    print(f"\n读取{data_type}数据: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"  警告: {data_type}文件不存在: {filepath}")
        return None, None, None
    
    # 读取数据
    if statetype == 0:
        data = readSensorDataTcXkPk(filepath, 0)
    else:
        data0 = readmsf_debug_state(filepath, dt)
        # 赋值tref: data0[:,0]起点和终点范围内的refdata[:, 0]元素
        tref = refdata[(refdata[:, 0] >= data0[0, 0]) & (refdata[:, 0] <= data0[-1, 0]), 0]
        if tref is None or len(tref) == 0:
            print(f"  警告: 参考数据与输入数据时间无交集")
            return None, None, None
        data = utils.InterpState(data0, data0[:,0], tref)
    
    print(f"  数据维度: {data.shape}")
    print(f"  时间范围: {data[0, 0]:.2f}s ~ {data[-1, 0]:.2f}s")
    
    # 坐标转换：将经纬度转换为米
    data[:, 7:9] = utils.dpos2den(data[:, 7:9],pos0)
    
    # 时间对齐
    print(f"\n进行{data_type}时间对齐...")
    aligned_data1, aligned_data2, common_time, _ = utils.alignDataByTimeTcSol(
        data, data[:, 0], refdata, refdata[:, 0], tthreshod)
    diff_data = utils.calculateDifference(aligned_data1, aligned_data2)
    print(f"  对齐后数据点数: {len(common_time)}")
    
    return data, diff_data, common_time


def calculate_normal_scene_time_ranges(all_time_ranges, excluded_ranges):
    """
    计算正常场景的时间范围（去除特殊场景后的剩余时段）
    
    Args:
        all_time_ranges: 所有的时间范围 [[start1, end1], [start2, end2], ...]
        excluded_ranges: 需要排除的时间范围 [[ex_start1, ex_end1], [ex_start2, ex_end2], ...]
        
    Returns:
        normal_ranges: 正常场景的时间范围列表
    """
    if not all_time_ranges or len(all_time_ranges) == 0:
        return []
    
    # 展开 all_time_ranges 为连续的时间区间集
    time_segments = []
    for start, end in all_time_ranges:
        time_segments.append((start, end))
    
    # 按起始时间排序
    time_segments.sort(key=lambda x: x[0])
    
    # 合并相邻或重叠的时间段
    merged_segments = []
    for segment in time_segments:
        if not merged_segments:
            merged_segments.append(segment)
        else:
            last_start, last_end = merged_segments[-1]
            current_start, current_end = segment
            if current_start <= last_end:
                # 有重叠或相邻，合并
                merged_segments[-1] = (last_start, max(last_end, current_end))
            else:
                merged_segments.append(segment)
    
    if not excluded_ranges or len(excluded_ranges) == 0:
        # 没有需要排除的范围，返回所有时间范围
        return [[s, e] for s, e in merged_segments]
    
    # 处理需要排除的时间范围
    normal_ranges = []
    for segment_start, segment_end in merged_segments:
        current_start = segment_start
        
        # 将排除范围也排序
        sorted_excluded = sorted(excluded_ranges, key=lambda x: x[0])
        
        for ex_start, ex_end in sorted_excluded:
            if ex_end <= current_start:
                # 排除范围在当前起始点之前，跳过
                continue
            elif ex_start >= segment_end:
                # 排除范围在当前段之后，不再处理
                break
            else:
                # 有重叠
                if ex_start > current_start:
                    # 保留排除范围之前的部分
                    normal_ranges.append([current_start, ex_start])
                current_start = max(current_start, ex_end)
        
        # 保留最后一段
        if current_start < segment_end:
            normal_ranges.append([current_start, segment_end])
    
    return normal_ranges


def calculate_horizontal_velocity_stats(diff_datalc, diff_datatc, diff_datagnss, 
                                        common_timelc, common_timetc, common_timegnss,
                                        t_start, t_end, type_label, lcver='LC', tcver='TC'):
    """
    计算水平速度误差统计（使用已对齐的差值数据）
    
    Args:
        diff_datalc: LC差值数据（已对齐，索引4=ve, 5=vn, 6=vu）
        diff_datatc: TC差值数据（已对齐，索引4=ve, 5=vn, 6=vu）
        diff_datagnss: GNSS差值数据（已对齐，索引4=ve, 5=vn, 6=vu）
        common_timelc: LC公共时间点
        common_timetc: TC公共时间点
        common_timegnss: GNSS公共时间点
        t_start: 时间范围起始点
        t_end: 时间范围结束点
        type_label: 场景类型标签
        lcver: LC版本标识
        tcver: TC版本标识
        
    Returns:
        velocity_stats: 速度误差统计字典
    """
    velocity_stats = {
        'lc': {'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0, 'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0},
        'tc': {'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0, 'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0},
        'gnss': {'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0, 'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0}
    }
    
    # 辅助函数：计算单个数据源的速度误差统计
    def calc_velocity_error_stats(diff_data, common_time, data_name):
        stats = {'rms': 0, 'mean': 0, 'std': 0, 'max': 0, 'min': 0, 'cep50': 0, 'cep68': 0, 'cep95': 0, 'cep99': 0}
        
        if diff_data is None or common_time is None or len(common_time) == 0:
            print(f"  {data_name}: 无数据，速度误差统计置0")
            return stats
        
        # 根据时间范围筛选已对齐的差值数据
        try:
            original_count = len(common_time)
            
            if t_start is not None and t_end is not None and len(t_start) > 0:
                # 多个时间范围：筛选在指定时间范围内的数据点
                mask = np.zeros(len(common_time), dtype=bool)
                for i in range(len(t_start)):
                    range_start = t_start[i]
                    range_end = t_end[i]
                    mask |= (common_time >= range_start) & (common_time <= range_end)
                diff_data_filtered = diff_data[mask, :]
                common_time_filtered = common_time[mask]
                filtered_count = len(common_time_filtered)
                # 只在非All场景或数据点数有变化时打印
                if type_label.lower() != 'all' or filtered_count != original_count:
                    print(f"  {data_name}: 原始{original_count}点 -> 筛选{filtered_count}点 (时间范围筛选)")
            else:
                # 使用全部数据
                diff_data_filtered = diff_data
                common_time_filtered = common_time
                filtered_count = original_count
                # 只在All场景时打印
                if type_label.lower() == 'all':
                    print(f"  {data_name}: 使用全部数据 {filtered_count}点")
            
            if len(diff_data_filtered) == 0:
                print(f"  {data_name}: 筛选后无数据，速度误差统计置0")
                return stats
            
            # 检查数据列数（需要至少7列：时间+位置+速度）
            if diff_data_filtered.shape[1] < 7:
                print(f"  {data_name}: 数据列数不足（{diff_data_filtered.shape[1]}），跳过速度误差计算")
                return stats
            
            # 提取速度误差（索引4=ve, 5=vn, 6=vu）
            error_ve = diff_data_filtered[:, 4]  # 东向速度误差
            error_vn = diff_data_filtered[:, 5]  # 北向速度误差
            error_vu = diff_data_filtered[:, 6]  # 垂向速度误差（本函数不使用）
            
            # 计算水平速度误差（东向和北向速度误差的合成）
            velocity_error = np.sqrt(error_ve**2 + error_vn**2)
            
            # 计算统计指标
            stats['rms'] = np.sqrt(np.mean(velocity_error**2))
            stats['mean'] = np.mean(velocity_error)
            stats['std'] = np.std(velocity_error)
            stats['max'] = np.max(velocity_error)
            stats['min'] = np.min(velocity_error)
            stats['cep50'] = np.percentile(velocity_error, 50)
            stats['cep68'] = np.percentile(velocity_error, 68)
            stats['cep95'] = np.percentile(velocity_error, 95)
            stats['cep99'] = np.percentile(velocity_error, 99)
            
            print(f"  {data_name}速度误差: RMS={stats['rms']:.6f}, Max={stats['max']:.6f}, 点数={len(velocity_error)}")
            
        except Exception as e:
            print(f"  {data_name}: 速度误差计算出错 - {e}")
            import traceback
            traceback.print_exc()
        
        return stats
    
    # 计算LC速度误差
    velocity_stats['lc'] = calc_velocity_error_stats(diff_datalc, common_timelc, lcver)
    
    # 计算TC速度误差
    velocity_stats['tc'] = calc_velocity_error_stats(diff_datatc, common_timetc, tcver)
    
    # 计算GNSS速度误差
    velocity_stats['gnss'] = calc_velocity_error_stats(diff_datagnss, common_timegnss, 'GNSS')
    
    return velocity_stats


# 固定的场景输出顺序（不含Normal，Normal根据表格类型动态添加）
SCENE_ORDER_BASE = ['All', '开阔场景', '半遮挡', '双边遮挡', '隧道', '转发器']


def get_scene_order_for_table(table_type):
    """根据表格类型获取场景顺序"""
    normal_key = f'Normal_{table_type}'
    return ['All', normal_key] + SCENE_ORDER_BASE[1:]


def convert_label_to_chinese(label):
    """
    将英文标签转换为中文
    """
    if label.lower() == 'all':
        return '全部'
    if 'Normal' in label:
        return '正常'
    return label


def save_horizontal_velocity_stats(outfile, all_type_stats, lcver='LC', tcver='TC'):
    """
    保存水平速度误差统计到TXT文件（参考位置误差的输出格式）

    Args:
        outfile: 输出文件路径
        all_type_stats: 所有场景的统计结果列表
        lcver: LC版本标识
        tcver: TC版本标识
    """
    # 将统计列表转换为字典，方便查找
    stats_dict = {stats.get('type_label', 'Unknown'): stats for stats in all_type_stats}

    with open(outfile, 'w', encoding='utf-8') as fid:
        fid.write('='*100 + '\n')
        fid.write('所有场景水平速度误差统计结果汇总 (Horizontal Velocity Error Statistics Summary)\n')
        fid.write('='*100 + '\n\n')
        fid.write(f'LC版本: {lcver}\n')
        fid.write(f'TC版本: {tcver}\n')
        fid.write('注：速度误差单位为 m/s\n\n')

        # 写入LC速度统计表格
        fid.write(f'{lcver} Velocity Statistics ({lcver}水平速度误差统计)\n')
        fid.write('-'*100 + '\n')

        # 表头 - 场景类型左对齐，数值列右对齐
        header = f"{'场景类型':<12}{'RMS':>10}{'CEP50':>10}{'CEP95':>10}{'CEP99':>10}{'Max':>10}"
        fid.write(header + '\n')
        fid.write('-'*100 + '\n')

        # LC表格只输出Normal_LC
        scene_order_lc = get_scene_order_for_table('LC')
        for scene_label in scene_order_lc:
            stats = stats_dict.get(scene_label)
            if stats:
                lc_vel = stats.get('velocity', {}).get('lc', {})
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}"
                row += f"{lc_vel.get('rms', 0):>10.2f}"
                row += f"{lc_vel.get('cep50', 0):>10.2f}"
                row += f"{lc_vel.get('cep95', 0):>10.2f}"
                row += f"{lc_vel.get('cep99', 0):>10.2f}"
                row += f"{lc_vel.get('max', 0):>10.2f}"
                fid.write(row + '\n')
            else:
                # 该场景不存在，输出0值
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}"
                row += f"{'0.00':>10}{'0.00':>10}{'0.00':>10}{'0.00':>10}{'0.00':>10}"
                fid.write(row + '\n')

        fid.write('\n')

        # 写入TC速度统计表格
        fid.write(f'{tcver} Velocity Statistics ({tcver}水平速度误差统计)\n')
        fid.write('-'*100 + '\n')

        fid.write(header + '\n')
        fid.write('-'*100 + '\n')

        # TC表格只输出Normal_TC
        scene_order_tc = get_scene_order_for_table('TC')
        for scene_label in scene_order_tc:
            stats = stats_dict.get(scene_label)
            if stats:
                tc_vel = stats.get('velocity', {}).get('tc', {})
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}"
                row += f"{tc_vel.get('rms', 0):>10.2f}"
                row += f"{tc_vel.get('cep50', 0):>10.2f}"
                row += f"{tc_vel.get('cep95', 0):>10.2f}"
                row += f"{tc_vel.get('cep99', 0):>10.2f}"
                row += f"{tc_vel.get('max', 0):>10.2f}"
                fid.write(row + '\n')
            else:
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}"
                row += f"{'0.00':>10}{'0.00':>10}{'0.00':>10}{'0.00':>10}{'0.00':>10}"
                fid.write(row + '\n')

        fid.write('\n')

        # 写入GNSS速度统计表格
        fid.write('GNSS Velocity Statistics (GNSS水平速度误差统计)\n')
        fid.write('-'*100 + '\n')

        fid.write(header + '\n')
        fid.write('-'*100 + '\n')

        # GNSS表格只输出Normal_GNSS
        scene_order_gnss = get_scene_order_for_table('GNSS')
        for scene_label in scene_order_gnss:
            stats = stats_dict.get(scene_label)
            if stats:
                gnss_vel = stats.get('velocity', {}).get('gnss', {})
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}"
                row += f"{gnss_vel.get('rms', 0):>10.2f}"
                row += f"{gnss_vel.get('cep50', 0):>10.2f}"
                row += f"{gnss_vel.get('cep95', 0):>10.2f}"
                row += f"{gnss_vel.get('cep99', 0):>10.2f}"
                row += f"{gnss_vel.get('max', 0):>10.2f}"
                fid.write(row + '\n')
            else:
                display_label = convert_label_to_chinese(scene_label)
                row = f"{display_label:<12}"
                row += f"{'0.00':>10}{'0.00':>10}{'0.00':>10}{'0.00':>10}{'0.00':>10}"
                fid.write(row + '\n')

        fid.write('\n')
        fid.write('='*100 + '\n')
        fid.write('说明 (Notes):\n')
        fid.write('  RMS = Root Mean Square (均方根)\n')
        fid.write('  CEP50 = 50% Circular Error Probable (50%圆误差概率)\n')
        fid.write('  CEP95 = 95% Circular Error Probable (95%圆误差概率)\n')
        fid.write('  CEP99 = 99% Circular Error Probable (99%圆误差概率)\n')
        fid.write('  Max = Maximum Error (最大误差)\n')
        fid.write('  速度误差单位: m/s\n')
        fid.write('='*100 + '\n')

    print(f"水平速度误差统计已保存到: {outfile}")