#!/usr/bin/env python3
"""
聚合多个精度统计文件，按里程加权平均计算总体评估结果

功能：
1. 从指定目录递归查找所有 position_precision.txt 文件（位置精度）
2. 从指定目录递归查找所有 velocity_precision.txt 文件（速度精度）
3. 提取每个文件中的 LC、TC、GNSS 统计数据
4. 对同类场景按里程占总里程占比取加权均值
5. odo取和
6. 完全为0的场景不参与加权平均
7. 输出分 lc、tc、gnss 的位置精度和速度精度总体评估结果
"""

import os
import re
import tarfile
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple


class PrecisionStatistics:
    """存储精度统计数据"""
    
    def __init__(self, version: str = ""):
        self.version = version
        self.scenes = {}  # scene_type -> StatisticsData
        
    def __repr__(self):
        return f"PrecisionStatistics(version={self.version}, scenes={len(self.scenes)})"


class StatisticsData:
    """单个场景的统计数据（位置精度，支持完整模式和水平模式）"""

    # 完整模式指标（包含高程误差）
    METRICS_FULL = ['H-rms', 'H-CEP95', 'H-CEP99', 'H-max',
                    'L-rms', 'L-CEP95', 'L-CEP99', 'L-max',
                    'F-rms', 'F-CEP95', 'F-CEP99', 'F-max',
                    'V-rms', 'V-CEP95', 'V-CEP99', 'V-max']

    # 水平模式指标（不含高程误差）
    METRICS_HORIZONTAL = ['H-rms', 'H-CEP95', 'H-CEP99', 'H-max',
                          'L-rms', 'L-CEP95', 'L-CEP99', 'L-max',
                          'F-rms', 'F-CEP95', 'F-CEP99', 'F-max']

    def __init__(self, odom: float = 0.0, has_vertical: bool = True):
        self.odom = odom
        self.has_vertical = has_vertical
        # 根据是否包含高程误差选择指标
        self.METRICS = self.METRICS_FULL if has_vertical else self.METRICS_HORIZONTAL
        self.metrics = {metric: 0.0 for metric in self.METRICS}

    def is_zero(self) -> bool:
        """检查是否全为0"""
        return self.odom == 0.0 and all(v == 0.0 for v in self.metrics.values())

    def __repr__(self):
        return f"StatisticsData(odom={self.odom}, metrics={self.metrics})"


class VelocityStatisticsData:
    """单个场景的速度统计数据"""
    
    METRICS = ['RMS', 'CEP50', 'CEP95', 'CEP99', 'Max']
    
    def __init__(self, odom: float = 0.0):
        self.odom = odom
        self.metrics = {metric: 0.0 for metric in self.METRICS}
        
    def is_zero(self) -> bool:
        """检查是否全为0"""
        return self.odom == 0.0 and all(v == 0.0 for v in self.metrics.values())
        
    def __repr__(self):
        return f"VelocityStatisticsData(odom={self.odom}, metrics={self.metrics})"


def parse_precision_file(filepath: str) -> Dict[str, PrecisionStatistics]:
    """
    解析单个精度统计文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        包含 lc、tc、gnss 三种统计的字典
    """
    result = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取LC和TC版本号
    lc_version_match = re.search(r'LC版本:\s*(\S+)', content)
    tc_version_match = re.search(r'TC版本:\s*(\S+)', content)
    
    lc_version = lc_version_match.group(1) if lc_version_match else "unknown"
    tc_version = tc_version_match.group(1) if tc_version_match else "unknown"
    
    # 定义三种统计类型
    stats_types = [
        ('lc', rf'{re.escape(lc_version)} Statistics', lc_version),
        ('tc', rf'{re.escape(tc_version)} Statistics', tc_version),
        ('gnss', 'GNSS Statistics', 'GNSS')
    ]
    
    for stat_key, pattern, version in stats_types:
        # 查找对应的统计块开始位置
        start_match = re.search(rf'{pattern}', content)
        if not start_match:
            continue
            
        start_pos = start_match.end()
        
        # 查找统计块的结束位置（下一个统计块或文件结尾）
        end_patterns = [rf'{re.escape(lc_version)} Statistics', 
                       rf'{re.escape(tc_version)} Statistics', 
                       'GNSS Statistics', 
                       '说明', 'Notes', '============']
        
        end_pos = len(content)
        for end_pattern in end_patterns:
            end_match = re.search(end_pattern, content[start_pos:])
            if end_match:
                end_pos = start_pos + end_match.start()
                break
        
        # 提取统计块内容
        stat_block = content[start_pos:end_pos]

        # 提取所有数据行 - 使用更灵活的匹配
        lines = stat_block.split('\n')
        stats = PrecisionStatistics(version)

        # 检测是否包含高程误差（V-rms）- 通过检查表头
        has_vertical = 'V-rms' in stat_block

        skip_line = True  # 跳过分隔线行

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过分隔线（纯减号行）或表头行（支持中英文表头）
            if set(line.strip()) == {'-'} or line.startswith('Scene Type') or line.startswith('场景类型'):
                skip_line = False
                continue

            if skip_line:
                continue

            # 提取所有数字
            numbers = re.findall(r'[\d.]+', line)
            # 根据数字数量判断模式
            # 完整模式: 17个数字（odom + 16个指标：H/L/F/V各4个）
            # 水平模式: 13个数字（odom + 12个指标：H/L/F各4个）
            expected_count = 17 if has_vertical else 13
            if len(numbers) == expected_count:
                values = [float(n) for n in numbers]
                odom = values[0]
                metrics_values = values[1:]

                # 场景类型提取：从第一个数字之前提取所有非空白字符
                # 使用正则匹配行首到第一个数字之间的内容
                match = re.match(r'^(.+?)\s*[\d.]+\s+', line)
                if match:
                    scene_type = match.group(1).strip()
                else:
                    scene_type = 'Unknown'

                data = StatisticsData(odom, has_vertical=has_vertical)
                data.metrics = dict(zip(data.METRICS, metrics_values))

                stats.scenes[scene_type] = data

        if stats.scenes:  # 只有当找到场景数据时才添加到结果
            result[stat_key] = stats

    return result


def find_all_precision_files(base_dir: str) -> List[str]:
    """
    递归查找所有位置精度统计文件
    
    Args:
        base_dir: 基础目录
        
    Returns:
        文件路径列表
    """
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        for filename in filenames:
            if filename == 'position_precision.txt':
                files.append(os.path.join(root, filename))
    return files


def find_all_velocity_files(base_dir: str) -> List[str]:
    """
    递归查找所有速度精度统计文件
    
    Args:
        base_dir: 基础目录
        
    Returns:
        文件路径列表
    """
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        for filename in filenames:
            if filename == 'velocity_precision.txt':
                files.append(os.path.join(root, filename))
    return files


def parse_velocity_file(filepath: str) -> Dict[str, PrecisionStatistics]:
    """
    解析单个速度精度统计文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        包含 lc、tc、gnss 三种统计的字典
    """
    result = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取LC和TC版本号
    lc_version_match = re.search(r'LC版本:\s*(\S+)', content)
    tc_version_match = re.search(r'TC版本:\s*(\S+)', content)
    
    lc_version = lc_version_match.group(1) if lc_version_match else "unknown"
    tc_version = tc_version_match.group(1) if tc_version_match else "unknown"
    
    # 定义三种统计类型（速度统计）
    stats_types = [
        ('lc', rf'{re.escape(lc_version)} Velocity Statistics', lc_version),
        ('tc', rf'{re.escape(tc_version)} Velocity Statistics', tc_version),
        ('gnss', 'GNSS Velocity Statistics', 'GNSS')
    ]
    
    for stat_key, pattern, version in stats_types:
        # 查找对应的统计块开始位置
        start_match = re.search(rf'{pattern}', content)
        if not start_match:
            continue
            
        start_pos = start_match.end()
        
        # 查找统计块的结束位置（下一个统计块或文件结尾）
        end_patterns = [rf'{re.escape(lc_version)} Velocity Statistics', 
                       rf'{re.escape(tc_version)} Velocity Statistics', 
                       'GNSS Velocity Statistics', 
                       '说明', 'Notes', '============']
        
        end_pos = len(content)
        for end_pattern in end_patterns:
            end_match = re.search(end_pattern, content[start_pos:])
            if end_match:
                end_pos = start_pos + end_match.start()
                break
        
        # 提取统计块内容
        stat_block = content[start_pos:end_pos]

        # 提取所有数据行
        lines = stat_block.split('\n')
        stats = PrecisionStatistics(version)

        skip_line = True  # 跳过分隔线行

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过分隔线（支持中英文表头）
            if set(line.strip()) == {'-'} or line.startswith('Scene Type') or line.startswith('场景类型'):
                skip_line = False
                continue

            if skip_line:
                continue

            # 提取所有数字
            numbers = re.findall(r'[\d.]+', line)
            # 速度统计: 5个数字（RMS, CEP50, CEP95, CEP99, Max）
            if len(numbers) == 5:
                values = [float(n) for n in numbers]

                # 场景类型提取：从第一个数字之前提取所有非空白字符
                match = re.match(r'^(.+?)\s*[\d.]+\s+', line)
                if match:
                    scene_type = match.group(1).strip()
                else:
                    scene_type = 'Unknown'

                # 注意：速度文件中没有odom信息，我们使用统一的odom=1.0
                # 这样在聚合时会取简单的算术平均
                data = VelocityStatisticsData(odom=1.0)
                data.metrics = dict(zip(VelocityStatisticsData.METRICS, values))

                stats.scenes[scene_type] = data

        if stats.scenes:  # 只有当找到场景数据时才添加到结果
            result[stat_key] = stats

    return result


def aggregate_velocity_statistics(all_files_stats: List[Dict[str, PrecisionStatistics]],
                                   skip_zero_scenes: bool = True) -> Dict[str, PrecisionStatistics]:
    """
    聚合多个文件的速度统计数据

    Args:
        all_files_stats: 所有文件的统计数据列表
        skip_zero_scenes: 是否跳过全为0的场景（在聚合平均时跳过，但输出时保留0值场景）

    Returns:
        聚合后的统计结果
    """
    # 初始化结果结构
    result = {
        'lc': PrecisionStatistics("Aggregated LC Velocity"),
        'tc': PrecisionStatistics("Aggregated TC Velocity"),
        'gnss': PrecisionStatistics("Aggregated GNSS Velocity")
    }

    # 按统计类型和场景收集所有数据
    for stat_type in ['lc', 'tc', 'gnss']:
        scene_data_map = defaultdict(list)  # scene_type -> list of VelocityStatisticsData

        # 收集所有文件的数据
        for file_stats in all_files_stats:
            if stat_type not in file_stats:
                continue

            stats = file_stats[stat_type]
            result[stat_type].version = stats.version  # 使用第一个文件的版本号

            for scene_type, data in stats.scenes.items():
                # 跳过全为0的数据（不参与平均）
                if skip_zero_scenes and data.is_zero():
                    continue
                scene_data_map[scene_type].append(data)

        # 使用固定的场景顺序处理每个场景
        scene_order = get_scene_order_for_stat_type(stat_type)

        for scene_type in scene_order:
            data_list = scene_data_map.get(scene_type, [])

            if not data_list:
                # 如果该场景没有数据，输出0值
                aggregated = VelocityStatisticsData(odom=0)
                result[stat_type].scenes[scene_type] = aggregated
                continue

            # 初始化聚合数据（odom设为数据文件数量，用于统计）
            aggregated = VelocityStatisticsData(odom=len(data_list))

            # 简单平均每个指标
            for metric in VelocityStatisticsData.METRICS:
                metric_sum = sum(d.metrics[metric] for d in data_list)
                aggregated.metrics[metric] = metric_sum / len(data_list) if data_list else 0.0

            result[stat_type].scenes[scene_type] = aggregated

    return result


# 固定的场景输出顺序（使用中文标签，与分文件输出一致）
SCENE_ORDER_BASE = ['全部', '开阔场景', '半遮挡', '双边遮挡', '隧道', '转发器']


def get_scene_order_for_stat_type(stat_type):
    """
    根据stat_type获取对应的场景输出顺序（使用中文标签）
    LC表格只输出正常，TC表格只输出正常，GNSS表格只输出正常
    """
    # 正常场景的中文标签
    return ['全部', '正常'] + SCENE_ORDER_BASE[1:]


def convert_scene_label_to_chinese(label: str) -> str:
    """
    将英文场景标签转换为中文

    Args:
        label: 英文场景标签

    Returns:
        中文场景标签
    """
    # 替换 All → 全部
    if label.lower() == 'all':
        return '全部'
    # 替换 Normal → 正常
    if 'Normal' in label:
        return '正常'
    # 其他场景类型保持原样或使用常用翻译
    scene_map = {
        'Highway': '高速',
        'Conventional Urban Area': '常规城市',
        'Tree-lined Roads': '林荫道',
        'Elevated Structure': '高架',
        'Urban Canyon': '城市峡谷',
        'Satellite Repeater': '转发器',
        'Long Tunnel': '长隧道',
        '开阔场景': '开阔场景',
        '半遮挡': '半遮挡',
        '双边遮挡': '双边遮挡',
        '隧道': '隧道',
        '转发器': '转发器',
    }
    return scene_map.get(label, label)


def format_velocity_output(aggregated_stats: Dict[str, PrecisionStatistics]) -> str:
    """
    格式化输出速度统计结果

    Args:
        aggregated_stats: 聚合后的统计数据

    Returns:
        格式化的字符串
    """
    output = []
    output.append("=" * 100)
    output.append("所有场景水平速度误差统计结果汇总 (Horizontal Velocity Error Statistics Summary)")
    output.append("=" * 100)
    output.append("")
    output.append("聚合统计 (Aggregated Statistics)")
    output.append("注：同类场景统计值取简单平均，速度误差单位为 m/s")
    output.append("")

    # 输出每种统计类型
    for stat_type, stats in [('lc', aggregated_stats['lc']),
                             ('tc', aggregated_stats['tc']),
                             ('gnss', aggregated_stats['gnss'])]:
        stat_name = {
            'lc': f"{stats.version} Statistics ({stats.version}水平速度误差统计)",
            'tc': f"{stats.version} Statistics ({stats.version}水平速度误差统计)",
            'gnss': "GNSS Velocity Statistics (GNSS水平速度误差统计)"
        }[stat_type]

        output.append(stat_name)
        output.append("-" * 100)
        # 表头 - 场景类型左对齐，数值列右对齐
        header = f"{'场景类型':<12}{'RMS':>10}{'CEP50':>10}{'CEP95':>10}{'CEP99':>10}{'Max':>10}"
        output.append(header)
        output.append("-" * 100)

        # 根据stat_type获取场景顺序
        scene_order = get_scene_order_for_stat_type(stat_type)

        # 按固定顺序输出场景类型（标签已经是中文，无需转换）
        for scene in scene_order:
            data = stats.scenes.get(scene)
            if data:
                values = [data.metrics[m] for m in VelocityStatisticsData.METRICS]
                line = f"{scene:<12}" + " ".join(f"{v:>10.2f}" for v in values)
                output.append(line)
            else:
                # 该场景不存在，输出0值
                line = f"{scene:<12}" + " ".join(f"{0.00:>10.2f}" for _ in range(5))
                output.append(line)

        output.append("")

    output.append("=" * 100)
    output.append("说明 (Notes):")
    output.append("  RMS = Root Mean Square (均方根)")
    output.append("  CEP50 = 50% Circular Error Probable (50%圆误差概率)")
    output.append("  CEP95 = 95% Circular Error Probable (95%圆误差概率)")
    output.append("  CEP99 = 99% Circular Error Probable (99%圆误差概率)")
    output.append("  Max = Maximum Error (最大误差)")
    output.append("  速度误差单位: m/s")
    output.append("=" * 100)

    return "\n".join(output)


def aggregate_statistics(all_files_stats: List[Dict[str, PrecisionStatistics]],
                        skip_zero_scenes: bool = True) -> Dict[str, PrecisionStatistics]:
    """
    聚合多个文件的统计数据

    Args:
        all_files_stats: 所有文件的统计数据列表
        skip_zero_scenes: 是否跳过全为0的场景（在聚合加权平均时跳过，但输出时保留0值场景）

    Returns:
        聚合后的统计结果
    """
    # 初始化结果结构
    result = {
        'lc': PrecisionStatistics("Aggregated LC"),
        'tc': PrecisionStatistics("Aggregated TC"),
        'gnss': PrecisionStatistics("Aggregated GNSS")
    }

    # 按统计类型和场景收集所有数据
    for stat_type in ['lc', 'tc', 'gnss']:
        scene_data_map = defaultdict(list)  # scene_type -> list of (odom, StatisticsData)

        # 收集所有文件的数据
        for file_stats in all_files_stats:
            if stat_type not in file_stats:
                continue

            stats = file_stats[stat_type]
            result[stat_type].version = stats.version  # 使用第一个文件的版本号

            for scene_type, data in stats.scenes.items():
                # 跳过全为0的数据（不参与加权平均）
                if skip_zero_scenes and data.is_zero():
                    continue
                scene_data_map[scene_type].append(data)

        # 使用固定的场景顺序处理每个场景
        scene_order = get_scene_order_for_stat_type(stat_type)

        # 检测是否有高程误差（从已有的数据推断）
        all_have_vertical = True
        for d_list in scene_data_map.values():
            if d_list:
                all_have_vertical = d_list[0].has_vertical
                break

        for scene_type in scene_order:
            data_list = scene_data_map.get(scene_type, [])

            if not data_list:
                # 如果该场景没有数据，输出0值
                aggregated = StatisticsData(0.0, has_vertical=all_have_vertical)
                result[stat_type].scenes[scene_type] = aggregated
                continue

            # 计算总里程
            total_odom = sum(d.odom for d in data_list)

            if total_odom == 0:
                # 里程为0也输出0值
                aggregated = StatisticsData(0.0, has_vertical=all_have_vertical)
                result[stat_type].scenes[scene_type] = aggregated
                continue

            # 初始化聚合数据 - 检测数据模式
            aggregated = StatisticsData(total_odom, has_vertical=all_have_vertical)

            # 按里程加权平均每个指标（使用数据实际的METRICS）
            for metric in aggregated.METRICS:
                # 只聚合该数据存在的指标
                weighted_sum = sum(d.odom * d.metrics.get(metric, 0.0) for d in data_list if metric in d.metrics)
                odom_sum = sum(d.odom for d in data_list if metric in d.metrics)
                aggregated.metrics[metric] = weighted_sum / odom_sum if odom_sum > 0 else 0.0

            result[stat_type].scenes[scene_type] = aggregated

    return result


def format_output(aggregated_stats: Dict[str, PrecisionStatistics]) -> str:
    """
    格式化输出结果（支持完整模式和水平模式）

    Args:
        aggregated_stats: 聚合后的统计数据

    Returns:
        格式化的字符串
    """
    output = []
    output.append("=" * 120)

    # 检测是否有高程误差（通过检查第一个场景数据）
    has_vertical = False
    for stat_type in ['lc', 'tc', 'gnss']:
        if stat_type in aggregated_stats and aggregated_stats[stat_type].scenes:
            first_scene = list(aggregated_stats[stat_type].scenes.values())[0]
            has_vertical = first_scene.has_vertical
            break

    if has_vertical:
        output.append("所有场景精度统计结果汇总 (All Scene Types Statistics Summary)")
        output.append("=" * 120)
        output.append("")
        output.append("聚合统计 (Aggregated Statistics)")
        output.append("注：同类场景统计值按里程占总里程占比取加权均值，odo取和，完全为0的场景不参与加权平均")
        output.append("")
    else:
        output.append("所有场景水平精度统计结果汇总 (Horizontal Precision Statistics Summary)")
        output.append("=" * 100)
        output.append("")
        output.append("聚合统计 (Aggregated Statistics)")
        output.append("注：同类场景统计值按里程占总里程占比取加权均值，odo取和，完全为0的场景不参与加权平均")
        output.append("")
        output.append("⚠️  水平精度专用模式：仅统计和展示水平方向误差（包括横向、前进方向、水平位置误差），不包含高程误差")
        output.append("")

    # 输出每种统计类型
    for stat_type, stats in [('lc', aggregated_stats['lc']),
                             ('tc', aggregated_stats['tc']),
                             ('gnss', aggregated_stats['gnss'])]:
        stat_name = {
            'lc': f"{stats.version} Statistics ({stats.version}精度统计)",
            'tc': f"{stats.version} Statistics ({stats.version}精度统计)",
            'gnss': "GNSS Statistics (GNSS精度统计)"
        }[stat_type]

        output.append(stat_name)
        line_width = 120 if has_vertical else 100
        output.append("-" * line_width)

        # 根据模式生成表头 - 场景类型左对齐，数值列右对齐
        if has_vertical:
            header = f"{'场景类型':<12}{'里程km':>10}"
            header += f"{'H-rms':>8}{'H-CEP95':>8}{'H-CEP99':>8}{'H-max':>8}"
            header += f"{'L-rms':>8}{'L-CEP95':>8}{'L-CEP99':>8}{'L-max':>8}"
            header += f"{'F-rms':>8}{'F-CEP95':>8}{'F-CEP99':>8}{'F-max':>8}"
            header += f"{'V-rms':>8}{'V-CEP95':>8}{'V-CEP99':>8}{'V-max':>8}"
        else:
            header = f"{'场景类型':<12}{'里程km':>10}"
            header += f"{'H-rms':>8}{'H-CEP95':>8}{'H-CEP99':>8}{'H-max':>8}"
            header += f"{'L-rms':>8}{'L-CEP95':>8}{'L-CEP99':>8}{'L-max':>8}"
            header += f"{'F-rms':>8}{'F-CEP95':>8}{'F-CEP99':>8}{'F-max':>8}"
        output.append(header)
        output.append("-" * line_width)

        # 根据stat_type获取场景顺序
        scene_order = get_scene_order_for_stat_type(stat_type)

        # 按固定顺序输出场景类型（标签已经是中文，无需转换）
        for scene in scene_order:
            data = stats.scenes.get(scene)
            if data:
                values = [data.odom] + [data.metrics[m] for m in data.METRICS]
                line = f"{scene:<12}" + " ".join(f"{v:>8.2f}" for v in values)
                output.append(line)
            else:
                # 该场景不存在，输出0值
                num_cols = 1 + len(StatisticsData.METRICS_FULL if has_vertical else StatisticsData.METRICS_HORIZONTAL)
                line = f"{scene:<12}" + " ".join(f"{0.00:>8.2f}" for _ in range(num_cols))
                output.append(line)

        output.append("")

    line_width = 120 if has_vertical else 100
    output.append("=" * line_width)
    output.append("说明 (Notes):")
    output.append("  H = Horizontal (水平位置误差)")
    output.append("  L = Lateral (横向误差)")
    output.append("  F = Forward (前进方向误差)")
    if has_vertical:
        output.append("  V = Vertical (高程误差)")
    output.append("  rms = Root Mean Square (均方根)")
    output.append("  CEP95 = 95% Circular Error Probable (95%圆误差概率)")
    output.append("  CEP99 = 99% Circular Error Probable (99%圆误差概率)")
    output.append("  max = Maximum Error (最大误差)")
    if not has_vertical:
        output.append("  ⚠️  本模式为水平精度专用，不包含高程误差（Vertical）")
    output.append("=" * line_width)

    return "\n".join(output)


def load_config(config_file: str):
    """
    加载配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置字典
    """
    try:
        import toml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        return config
    except ImportError:
        print("警告: 未安装 toml 库，将使用默认配置")
        print("可以通过 pip install toml 安装")
        return None
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='聚合多个精度统计文件（位置精度和速度精度）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用配置文件（默认）
  %(prog)s
  
  # 使用指定的配置文件
  %(prog)s /path/to/config.toml
  
  # 完全通过命令行指定参数
  %(prog)s --config /path/to/config.toml --input-dir /data/results --output-file output.txt
  
  # 跳过配置文件，仅使用命令行参数
  %(prog)s --no-config --input-dir /data/results --output-file output.txt --velocity-output-file velocity.txt --skip-zero-scenes --verbose
        """)
    
    # 配置文件相关参数
    parser.add_argument('--config', type=str, 
                       default='aggregate_precision_statistics_config.toml',
                       help='配置文件路径（默认: aggregate_precision_statistics_config.toml）')
    parser.add_argument('--no-config', action='store_true',
                       help='不使用配置文件，仅使用命令行参数')
    
    # 通用参数
    parser.add_argument('--input-dir', type=str, 
                       help='输入目录，会递归查找所有精度统计文件')
    parser.add_argument('--output-file', type=str, 
                       help='位置精度输出文件路径')
    parser.add_argument('--velocity-output-file', type=str,
                       help='速度精度输出文件路径')
    
    # 选项参数
    parser.add_argument('--skip-zero-scenes', action='store_true', default=None,
                       help='跳过全为0的场景')
    parser.add_argument('--no-skip-zero-scenes', action='store_false', dest='skip_zero_scenes',
                       help='不跳过全为0的场景')
    parser.add_argument('--verbose', action='store_true', default=None,
                       help='在控制台打印详细信息')
    parser.add_argument('--quiet', '-q', action='store_false', dest='verbose',
                       help='静默模式，不打印详细信息')
    
    args = parser.parse_args()
    
    # 加载配置文件（如果不使用--no-config）
    config = None
    if not args.no_config:
        config = load_config(args.config)
        if config is None and not args.no_config:
            print(f"警告: 无法加载配置文件 '{args.config}'，将使用默认值和命令行参数")
    
    # 设置默认值
    default_config = {
        'general': {
            'input_dir': '/mnt/d/dockers/rt/rtk_pvt/2026',
            'output_file': 'position_precision_aggregated.txt',
            'velocity_output_file': 'velocity_precision_aggregated.txt'
        },
        'options': {
            'skip_zero_scenes': True,
            'verbose': True
        }
    }
    
    # 合并配置（配置文件 > 默认配置）
    if config:
        if 'general' in config:
            default_config['general'].update(config['general'])
        if 'options' in config:
            default_config['options'].update(config['options'])
    
    # 命令行参数覆盖配置文件
    if args.input_dir is not None:
        default_config['general']['input_dir'] = args.input_dir
    if args.output_file is not None:
        default_config['general']['output_file'] = args.output_file
    if args.velocity_output_file is not None:
        default_config['general']['velocity_output_file'] = args.velocity_output_file
    if args.skip_zero_scenes is not None:
        default_config['options']['skip_zero_scenes'] = args.skip_zero_scenes
    if args.verbose is not None:
        default_config['options']['verbose'] = args.verbose
    
    input_dir = default_config['general']['input_dir']
    output_file = default_config['general']['output_file']
    velocity_output_file = default_config['general']['velocity_output_file']
    skip_zero_scenes = default_config['options']['skip_zero_scenes']
    verbose = default_config['options']['verbose']
    
    # ==================== 处理位置精度统计 ====================
    if verbose:
        print("=" * 60)
        print("开始处理位置精度统计")
        print("=" * 60)
        print(f"正在查找目录 {input_dir} 中的位置精度统计文件...")
    
    all_files = find_all_precision_files(input_dir)
    
    if not all_files:
        print("未找到任何位置精度统计文件！")
    else:
        if verbose:
            print(f"找到 {len(all_files)} 个位置精度统计文件:")
            for filepath in all_files:
                print(f"  - {filepath}")
        
        # 解析所有文件
        if verbose:
            print("\n正在解析位置精度统计文件...")
        
        all_files_stats = []
        for filepath in all_files:
            try:
                stats = parse_precision_file(filepath)
                all_files_stats.append(stats)
                if verbose:
                    print(f"  已解析: {filepath}")
            except Exception as e:
                if verbose:
                    print(f"  解析失败 {filepath}: {e}")
        
        if all_files_stats:
            # 聚合统计
            if verbose:
                print("\n正在聚合位置精度统计数据...")
            
            aggregated_stats = aggregate_statistics(all_files_stats, skip_zero_scenes=skip_zero_scenes)
            
            # 格式化输出
            if verbose:
                print("正在生成位置精度输出...")
            
            output = format_output(aggregated_stats)
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            
            print(f"\n位置精度聚合结果已保存到: {output_file}")
            
            # 打印统计信息
            if verbose:
                print("\n位置精度聚合统计信息:")
                for stat_type in ['lc', 'tc', 'gnss']:
                    stats = aggregated_stats[stat_type]
                    print(f"\n{stat_type.upper()} ({stats.version}):")
                    print(f"  场景数量: {len(stats.scenes)}")
                    for scene_type, data in sorted(stats.scenes.items()):
                        print(f"    {scene_type}: odom={data.odom:.3f}km, H-rms={data.metrics['H-rms']:.3f}m")
    
    # ==================== 处理速度精度统计 ====================
    if verbose:
        print("\n" + "=" * 60)
        print("开始处理速度精度统计")
        print("=" * 60)
        print(f"正在查找目录 {input_dir} 中的速度精度统计文件...")
    
    all_velocity_files = find_all_velocity_files(input_dir)
    
    if not all_velocity_files:
        print("未找到任何速度精度统计文件！")
    else:
        if verbose:
            print(f"找到 {len(all_velocity_files)} 个速度精度统计文件:")
            for filepath in all_velocity_files:
                print(f"  - {filepath}")
        
        # 解析所有速度文件
        if verbose:
            print("\n正在解析速度精度统计文件...")
        
        all_velocity_files_stats = []
        for filepath in all_velocity_files:
            try:
                stats = parse_velocity_file(filepath)
                all_velocity_files_stats.append(stats)
                if verbose:
                    print(f"  已解析: {filepath}")
            except Exception as e:
                if verbose:
                    print(f"  解析失败 {filepath}: {e}")
        
        if all_velocity_files_stats:
            # 聚合速度统计
            if verbose:
                print("\n正在聚合速度精度统计数据...")
            
            aggregated_velocity_stats = aggregate_velocity_statistics(all_velocity_files_stats, skip_zero_scenes=skip_zero_scenes)
            
            # 格式化输出
            if verbose:
                print("正在生成速度精度输出...")
            
            velocity_output = format_velocity_output(aggregated_velocity_stats)
            
            # 保存到文件
            with open(velocity_output_file, 'w', encoding='utf-8') as f:
                f.write(velocity_output)
            
            print(f"\n速度精度聚合结果已保存到: {velocity_output_file}")
            
            # 打印统计信息
            if verbose:
                print("\n速度精度聚合统计信息:")
                for stat_type in ['lc', 'tc', 'gnss']:
                    stats = aggregated_velocity_stats[stat_type]
                    print(f"\n{stat_type.upper()} ({stats.version}):")
                    print(f"  场景数量: {len(stats.scenes)}")
                    for scene_type, data in sorted(stats.scenes.items()):
                        print(f"    {scene_type}: files={data.odom:.0f}, RMS={data.metrics['RMS']:.6f}m/s")
    
    # ==================== 打包 input_dir 内容 ====================
    if verbose:
        print("\n" + "=" * 60)
        print("开始打包输入目录")
        print("=" * 60)
    
    try:
        # 获取 input_dir 的 Path 对象
        input_path = Path(input_dir)
        
        # 检查 input_dir 是否存在
        if not input_path.exists():
            print(f"警告: 输入目录 {input_dir} 不存在，跳过打包")
        else:
            # 获取父目录
            parent_dir = input_path.parent
            dir_name = input_path.name
            
            # 生成带时间戳的压缩文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{dir_name}_{timestamp}.tar.gz"
            archive_path = parent_dir / archive_name
            
            if verbose:
                print(f"正在打包 {input_dir} ...")
                print(f"打包文件将保存到: {archive_path}")
            
            # 创建 tar.gz 压缩包
            with tarfile.open(archive_path, "w:gz") as tar:
                # 递归添加目录中的所有文件
                for item in input_path.iterdir():
                    if verbose:
                        print(f"  正在添加: {item.name}")
                    tar.add(item, arcname=item.name)
            
            print(f"\n✓ 打包完成！压缩文件已保存到: {archive_path}")
            
            # 获取压缩包大小
            archive_size = archive_path.stat().st_size
            size_mb = archive_size / (1024 * 1024)
            print(f"  压缩包大小: {size_mb:.2f} MB")
            
    except PermissionError as e:
        print(f"\n警告: 打包失败，权限错误: {e}")
    except Exception as e:
        print(f"\n警告: 打包失败: {e}")
    
    print("\n" + "=" * 60)
    print("所有处理完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()