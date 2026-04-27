#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本对比工具：对比两个融合定位版本的精度差异

功能说明：
1. 对比两个版本共同存在的数据集（支持多层子目录结构）
2. 对比相同方案（pvtlc vs pvtlc, rtklc vs rtklc）
3. 对比精度指标，较大值（较差）标粗显示
4. 缺失的数据集/方案在报告中说明
5. 自动生成带时间戳的输出目录
6. 指标和场景从精度文件中自动检测，不自行扩展

使用方法：
    python compare_fusion_versions.py <配置文件路径>

示例：
    python compare_fusion_versions.py conf/compare_versions_config.toml
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
try:
    import toml
except ImportError:
    print("错误: 需要安装 toml 库，请运行: pip install toml")
    sys.exit(1)


class StatisticsData:
    """单个场景的统计数据"""

    METRICS_FULL = ['H-rms', 'H-CEP95', 'H-CEP99', 'H-max',
                    'L-rms', 'L-CEP95', 'L-CEP99', 'L-max',
                    'F-rms', 'F-CEP95', 'F-CEP99', 'F-max',
                    'V-rms', 'V-CEP95', 'V-CEP99', 'V-max']

    METRICS_HORIZONTAL = ['H-rms', 'H-CEP95', 'H-CEP99', 'H-max',
                          'L-rms', 'L-CEP95', 'L-CEP99', 'L-max',
                          'F-rms', 'F-CEP95', 'F-CEP99', 'F-max']

    def __init__(self, odom: float = 0.0, has_vertical: bool = True):
        self.odom = odom
        self.has_vertical = has_vertical
        self.METRICS = self.METRICS_FULL if has_vertical else self.METRICS_HORIZONTAL
        self.metrics = {metric: 0.0 for metric in self.METRICS}


class PrecisionStatistics:
    """存储精度统计数据"""

    def __init__(self, version: str = ""):
        self.version = version
        self.scenes = {}  # scene_type -> StatisticsData


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
        start_match = re.search(rf'{pattern}', content)
        if not start_match:
            continue

        start_pos = start_match.end()

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

        stat_block = content[start_pos:end_pos]
        lines = stat_block.split('\n')
        stats = PrecisionStatistics(version)

        has_vertical = 'V-rms' in stat_block

        skip_line = True

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if set(line.strip()) == {'-'} or line.startswith('Scene Type') or line.startswith('场景类型'):
                skip_line = False
                continue

            if skip_line:
                continue

            numbers = re.findall(r'[\d.]+', line)
            expected_count = 17 if has_vertical else 13
            if len(numbers) == expected_count:
                values = [float(n) for n in numbers]
                odom = values[0]
                metrics_values = values[1:]

                match = re.match(r'^(.+?)\s*[\d.]+\s+', line)
                if match:
                    scene_type = match.group(1).strip()
                else:
                    scene_type = 'Unknown'

                data = StatisticsData(odom, has_vertical=has_vertical)
                data.metrics = dict(zip(data.METRICS, metrics_values))

                stats.scenes[scene_type] = data

        if stats.scenes:
            result[stat_key] = stats

    return result


def discover_datasets_recursive(version_dir: Path) -> Dict[str, Path]:
    """
    递归发现版本目录下的所有数据集及其精度文件路径
    支持多层子目录结构

    Args:
        version_dir: 版本目录路径

    Returns:
        数据集相对路径 -> 精度文件路径 的字典
        例如: "20260410/dataset1" -> Path("/path/to/20260410/dataset1/results/position_precision.txt")
    """
    datasets = {}
    if not version_dir.exists():
        return datasets

    # 递归查找所有 position_precision.txt 文件
    for root, dirs, files in os.walk(version_dir):
        for filename in files:
            if filename == 'position_precision.txt':
                full_path = Path(root) / filename
                # 计算相对于版本目录的路径
                rel_path = full_path.parent.parent  # 去掉 results/position_precision.txt
                try:
                    relative_name = rel_path.relative_to(version_dir)
                    datasets[str(relative_name)] = full_path
                except ValueError:
                    # 如果无法计算相对路径，使用绝对路径名
                    datasets[rel_path.name] = full_path

    return datasets


def get_scheme_stats(precision_file: Path, scheme: str) -> Optional[PrecisionStatistics]:
    """
    从精度文件中提取特定方案的统计数据

    Args:
        precision_file: 精度文件路径
        scheme: 方案名称 (pvtlc, rtklc, pvttc, rtktc)

    Returns:
        统计数据，如果不存在返回None
    """
    try:
        all_stats = parse_precision_file(str(precision_file))
        # 根据方案类型选择 lc 或 tc
        stat_key = 'lc' if 'pvtlc' in scheme or 'pvttc' in scheme else 'tc'
        if stat_key in all_stats:
            return all_stats[stat_key]
        return None
    except Exception as e:
        print(f"  [警告] 解析文件失败 {precision_file}: {e}")
        return None


def format_bold(value: float, is_worse: bool, use_terminal: bool = True) -> str:
    """
    格式化数值，如果较差则加粗

    Args:
        value: 数值
        is_worse: 是否较差（较大的值）
        use_terminal: 是否使用终端ANSI代码（False时使用Markdown格式）

    Returns:
        格式化的字符串
    """
    formatted = f"{value:.2f}"
    if is_worse:
        if use_terminal:
            return f"\033[1m{formatted}\033[0m"
        else:
            return f"**{formatted}**"
    return formatted


def get_available_schemes_from_files(datasets: Dict[str, Path]) -> List[str]:
    """
    从数据集文件中检测可用的方案

    Args:
        datasets: 数据集字典

    Returns:
        可用方案列表（从精度文件中检测）
    """
    available = set()
    for precision_file in datasets.values():
        try:
            all_stats = parse_precision_file(str(precision_file))
            if 'lc' in all_stats:
                version = all_stats['lc'].version
                # 从版本字符串中提取方案类型
                if 'pvtlc' in version:
                    available.add('pvtlc')
                elif 'pvttc' in version:
                    available.add('pvttc')
            if 'tc' in all_stats:
                version = all_stats['tc'].version
                if 'rtklc' in version:
                    available.add('rtklc')
                elif 'rtktc' in version:
                    available.add('rtktc')
        except:
            pass

    return sorted(list(available))


def get_available_scenes_from_files(datasets: Dict[str, Path], scheme: str) -> List[str]:
    """
    从数据集文件中检测可用的场景

    Args:
        datasets: 数据集字典
        scheme: 方案名称

    Returns:
        可用场景列表（从精度文件中检测）
    """
    available = set()
    stat_key = 'lc' if 'pvtlc' in scheme or 'pvttc' in scheme else 'tc'

    for precision_file in datasets.values():
        try:
            all_stats = parse_precision_file(str(precision_file))
            if stat_key in all_stats:
                available.update(all_stats[stat_key].scenes.keys())
        except:
            pass

    return sorted(list(available))


def get_available_metrics_from_files(datasets: Dict[str, Path], scheme: str) -> List[str]:
    """
    从数据集文件中检测可用的精度指标

    Args:
        datasets: 数据集字典
        scheme: 方案名称

    Returns:
        可用指标列表（从精度文件中检测）
    """
    available = set()
    stat_key = 'lc' if 'pvtlc' in scheme or 'pvttc' in scheme else 'tc'

    for precision_file in datasets.values():
        try:
            all_stats = parse_precision_file(str(precision_file))
            if stat_key in all_stats:
                for scene_data in all_stats[stat_key].scenes.values():
                    available.update(scene_data.metrics.keys())
        except:
            pass

    return sorted(list(available))


def create_output_directory(output_base_dir: Path, version_a_label: str, version_b_label: str) -> Path:
    """
    创建输出目录

    Args:
        output_base_dir: 输出基础目录
        version_a_label: 版本A标签
        version_b_label: 版本B标签

    Returns:
        创建的输出目录路径
    """
    # 创建 compare_versions 主目录
    compare_dir = output_base_dir / "compare_versions"
    compare_dir.mkdir(parents=True, exist_ok=True)

    # 生成带时间戳的子目录名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir_name = f"{timestamp}_{version_a_label}_vs_{version_b_label}"
    output_dir = compare_dir / subdir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def compare_versions(
    version_a_dir: Path,
    version_b_dir: Path,
    version_a_label: str,
    version_b_label: str,
    compare_schemes: List[str],
    compare_metrics: List[str],
    compare_scenes: List[str],
    verbose: bool
) -> Tuple[str, str]:
    """
    对比两个版本的精度

    Args:
        version_a_dir: 版本A目录
        version_b_dir: 版本B目录
        version_a_label: 版本A标签
        version_b_label: 版本B标签
        compare_schemes: 要对比的方案列表（空列表表示全部）
        compare_metrics: 要对比的指标列表（空列表表示全部）
        compare_scenes: 要对比的场景列表（空列表表示全部）
        verbose: 是否显示详细输出

    Returns:
        (终端输出报告, 文件输出报告)
    """
    terminal_output = []
    file_output = []

    # 发现数据集（递归）
    datasets_a = discover_datasets_recursive(version_a_dir)
    datasets_b = discover_datasets_recursive(version_b_dir)

    # 找出共同数据集
    common_datasets = sorted(set(datasets_a.keys()) & set(datasets_b.keys()))
    only_a_datasets = sorted(set(datasets_a.keys()) - set(datasets_b.keys()))
    only_b_datasets = sorted(set(datasets_b.keys()) - set(datasets_a.keys()))

    # 如果没有指定方案，从共同数据集中检测可用方案
    if not compare_schemes:
        # 合并两个版本的数据集来检测方案
        all_datasets = {**datasets_a, **datasets_b}
        compare_schemes = get_available_schemes_from_files(all_datasets)
        if not compare_schemes:
            compare_schemes = ['pvtlc', 'rtklc']  # 默认值

    # 输出基本信息
    header_lines = []
    header_lines.append("=" * 120)
    header_lines.append("融合定位版本对比报告")
    header_lines.append("=" * 120)
    header_lines.append("")
    header_lines.append(f"版本A: {version_a_label} ({version_a_dir})")
    header_lines.append(f"版本B: {version_b_label} ({version_b_dir})")
    header_lines.append(f"对比方案: {', '.join(compare_schemes)}")
    header_lines.append(f"对比指标: {', '.join(compare_metrics) if compare_metrics else '全部指标'}")
    header_lines.append("")
    header_lines.append(f"共同数据集 ({len(common_datasets)}个):")
    for ds in common_datasets[:10]:  # 只显示前10个
        header_lines.append(f"  - {ds}")
    if len(common_datasets) > 10:
        header_lines.append(f"  ... 等共 {len(common_datasets)} 个数据集")
    if only_a_datasets:
        header_lines.append(f"")
        header_lines.append(f"版本A独有 ({len(only_a_datasets)}个):")
        for ds in only_a_datasets[:5]:
            header_lines.append(f"  - {ds}")
        if len(only_a_datasets) > 5:
            header_lines.append(f"  ... 等共 {len(only_a_datasets)} 个")
    if only_b_datasets:
        header_lines.append(f"")
        header_lines.append(f"版本B独有 ({len(only_b_datasets)}个):")
        for ds in only_b_datasets[:5]:
            header_lines.append(f"  - {ds}")
        if len(only_b_datasets) > 5:
            header_lines.append(f"  ... 等共 {len(only_b_datasets)} 个")
    header_lines.append("")
    header_lines.append("=" * 120)
    header_lines.append("")

    terminal_output.extend(header_lines)
    file_output.extend(header_lines)

    # 缺失说明收集
    missing_notes = []

    # 对比每个方案
    for scheme in compare_schemes:
        scheme_header = []
        scheme_header.append("=" * 120)
        scheme_header.append(f"{scheme} 方案对比")
        scheme_header.append("=" * 120)
        scheme_header.append("")
        scheme_header.append("注: 较小的数值（较好性能）以粗体显示")
        scheme_header.append("")

        terminal_output.extend(scheme_header)
        file_output.extend(scheme_header)

        # 获取共同数据集字典
        common_datasets_dict = {k: datasets_a[k] for k in common_datasets if k in datasets_a}

        # 使用局部变量，避免覆盖传入参数
        # 如果没有指定场景，从共同数据集中检测可用场景
        scenes_to_compare = compare_scenes if compare_scenes else get_available_scenes_from_files(common_datasets_dict, scheme)
        if not scenes_to_compare:
            scenes_to_compare = ['全部', '正常']  # 默认值

        # 如果没有指定指标，从共同数据集中检测可用指标
        metrics_to_compare = compare_metrics if compare_metrics else get_available_metrics_from_files(common_datasets_dict, scheme)
        if not metrics_to_compare:
            metrics_to_compare = ['H-rms', 'H-CEP95', 'H-CEP99', 'H-max']  # 默认值

        # 对比每个场景
        for scene in scenes_to_compare:
            scene_header = []
            scene_header.append(f"--- {scene} 场景 ---")
            scene_header.append("")
            # 动态调整列宽以适应较长的数据集路径
            max_dataset_len = max(len(ds) for ds in common_datasets) if common_datasets else 15
            dataset_col_width = max(max_dataset_len, 15)
            header_fmt = f"{{dataset:<{dataset_col_width}}} | {{metric:<10}} | {{version_a:>12}} | {{version_b:>12}}"
            scene_header.append(header_fmt.format(dataset='数据集', metric='指标',
                                                  version_a=version_a_label, version_b=version_b_label))
            scene_header.append("-" * (dataset_col_width + 35))

            terminal_output.extend(scene_header)
            file_output.extend(scene_header)

            for dataset in common_datasets:
                precision_file_a = datasets_a[dataset]
                precision_file_b = datasets_b[dataset]

                stats_a = get_scheme_stats(precision_file_a, scheme)
                stats_b = get_scheme_stats(precision_file_b, scheme)

                if not stats_a or not stats_b:
                    missing_notes.append(f"{dataset}/{scheme}: 缺少{scheme}方案结果")
                    continue

                # 获取场景数据
                scene_data_a = stats_a.scenes.get(scene)
                scene_data_b = stats_b.scenes.get(scene)

                if not scene_data_a or not scene_data_b:
                    missing_notes.append(f"{dataset}/{scheme}/{scene}: 缺少场景数据")
                    continue

                # 对比每个指标（使用已检测或配置的指标列表）
                for metric in metrics_to_compare:
                    value_a = scene_data_a.metrics.get(metric, 0.0)
                    value_b = scene_data_b.metrics.get(metric, 0.0)

                    # 较小的值为较好（加粗显示）
                    is_a_better = value_a < value_b
                    is_b_better = value_b < value_a

                    # 格式化输出 - 较小的数值（较好的性能）用粗体
                    formatted_a_terminal = format_bold(value_a, is_a_better, use_terminal=True)
                    formatted_b_terminal = format_bold(value_b, is_b_better, use_terminal=True)
                    formatted_a_file = format_bold(value_a, is_a_better, use_terminal=False)
                    formatted_b_file = format_bold(value_b, is_b_better, use_terminal=False)

                    row_fmt_terminal = f"{{dataset:<{dataset_col_width}}} | {{metric:<10}} | {{value_a:>12}} | {{value_b:>12}}"
                    row_fmt_file = f"{{dataset:<{dataset_col_width}}} | {{metric:<10}} | {{value_a:>16}} | {{value_b:>16}}"

                    terminal_output.append(row_fmt_terminal.format(
                        dataset=dataset, metric=metric,
                        value_a=formatted_a_terminal, value_b=formatted_b_terminal))
                    file_output.append(row_fmt_file.format(
                        dataset=dataset, metric=metric,
                        value_a=formatted_a_file, value_b=formatted_b_file))

            terminal_output.append("")
            file_output.append("")
            terminal_output.append("-" * 120)
            file_output.append("-" * 120)
            terminal_output.append("")
            file_output.append("")

    # 输出缺失说明
    if missing_notes:
        missing_section = []
        missing_section.append("=" * 120)
        missing_section.append("缺失说明")
        missing_section.append("=" * 120)
        missing_section.append("")
        for note in missing_notes[:50]:  # 限制显示数量
            missing_section.append(f"  - {note}")
        if len(missing_notes) > 50:
            missing_section.append(f"  ... 等共 {len(missing_notes)} 条缺失说明")
        missing_section.append("")
        terminal_output.extend(missing_section)
        file_output.extend(missing_section)

    footer = []
    footer.append("=" * 120)
    footer.append("对比完成")
    footer.append("=" * 120)
    terminal_output.extend(footer)
    file_output.extend(footer)

    return "\n".join(terminal_output), "\n".join(file_output)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="对比两个融合定位版本的精度差异",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python compare_fusion_versions.py conf/compare_versions_config.toml

对比说明:
  1. 支持多层子目录结构，自动递归查找精度文件
  2. 只对比两个版本共同存在的数据集
  3. 对比相同方案（pvtlc vs pvtlc, rtklc vs rtklc）
  4. 较大的精度值（较差性能）以粗体显示
  5. 缺失的数据集/方案在报告中说明
  6. compare_schemes/metrics/scenes 为空时自动对比全部
  7. 输出目录自动生成: compare_versions/<时间戳>_<版本A>_vs_<版本B>/
        """
    )

    parser.add_argument(
        "config_file",
        type=str,
        help="配置文件路径"
    )

    args = parser.parse_args()

    # 验证配置文件
    config_file = Path(args.config_file)
    if not config_file.exists():
        print(f"[错误] 配置文件不存在: {config_file}")
        sys.exit(1)

    # 读取配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = toml.load(f)
    except Exception as e:
        print(f"[错误] 读取配置文件失败: {e}")
        sys.exit(1)

    # 读取配置项
    version_a_dir_str = config.get('version_a_dir', '').strip()
    version_b_dir_str = config.get('version_b_dir', '').strip()

    if not version_a_dir_str or not version_b_dir_str:
        print(f"[错误] 配置文件中缺少 version_a_dir 或 version_b_dir")
        sys.exit(1)

    version_a_dir = Path(version_a_dir_str)
    version_b_dir = Path(version_b_dir_str)

    if not version_a_dir.exists():
        print(f"[错误] 版本A目录不存在: {version_a_dir}")
        sys.exit(1)

    if not version_b_dir.exists():
        print(f"[错误] 版本B目录不存在: {version_b_dir}")
        sys.exit(1)

    version_a_label = config.get('version_a_label', 'VersionA')
    version_b_label = config.get('version_b_label', 'VersionB')

    # 获取对比配置（空列表表示全部）
    compare_schemes = config.get('compare_schemes', [])
    compare_metrics = config.get('compare_metrics', [])
    compare_scenes = config.get('compare_scenes', [])

    verbose = config.get('verbose', True)

    # 确定输出目录
    output_base_dir_str = config.get('output_base_dir', '').strip()
    if not output_base_dir_str:
        # 使用版本目录的父目录
        output_base_dir = version_a_dir.parent
    else:
        output_base_dir = Path(output_base_dir_str)

    # 创建输出目录
    output_dir = create_output_directory(output_base_dir, version_a_label, version_b_label)
    output_file = output_dir / "version_comparison_report.txt"

    print(f"[信息] 输出目录: {output_dir}")

    # 执行对比
    terminal_report, file_report = compare_versions(
        version_a_dir,
        version_b_dir,
        version_a_label,
        version_b_label,
        compare_schemes,
        compare_metrics,
        compare_scenes,
        verbose
    )

    # 输出报告（终端）
    print(terminal_report)

    # 保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(file_report)
    print(f"\n报告已保存到: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())