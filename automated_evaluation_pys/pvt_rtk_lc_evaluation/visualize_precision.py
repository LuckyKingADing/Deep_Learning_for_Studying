#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精度指标可视化工具：将融合定位精度统计结果可视化展示

功能说明：
1. 支持多种可视化类型：柱状图、雷达图、热力图、表格
2. 支持多方案对比（pvtlc、rtklc）
3. 支持多场景、多指标可视化
4. 自动生成带时间戳的输出目录

使用方法：
    python visualize_precision.py <配置文件路径>

示例：
    python visualize_precision.py ../conf/visualize_precision_config.toml
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    import toml
except ImportError:
    print("错误: 需要安装 toml 库，请运行: pip install toml")
    sys.exit(1)

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    import numpy as np
    from matplotlib.font_manager import FontManager
except ImportError:
    print("错误: 需要安装 matplotlib 和 numpy 库")
    print("请运行: pip install matplotlib numpy")
    sys.exit(1)


def setup_chinese_font():
    """设置中文字体，尝试多种可用字体"""
    # 尝试的中文字体列表（按优先级）
    chinese_fonts = [
        'SimHei',        # Windows 黑体
        'WenQuanYi Micro Hei',  # Linux 常见中文字体
        'WenQuanYi Zen Hei',    # Linux 另一个常见中文字体
        'Noto Sans CJK SC',     # Google Noto 字体
        'Noto Sans CJK',        # Google Noto 字体简体
        'Source Han Sans CN',   # 思源黑体
        'Droid Sans Fallback',  # Android 字体
        'Microsoft YaHei',      # 微软雅黑
        'PingFang SC',          # macOS 苹方
        'Heiti SC',             # macOS 黑体
        'STHeiti',              # macOS 华文黑体
        'Arial Unicode MS',     # Unicode 字体
    ]

    # 获取系统可用字体
    fm = FontManager()
    available_fonts = set([f.name for f in fm.ttflist])

    # 找到可用的中文字体
    font_found = None
    for font in chinese_fonts:
        if font in available_fonts:
            font_found = font
            break

    if font_found:
        plt.rcParams['font.sans-serif'] = [font_found, 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        print(f"[信息] 使用中文字体: {font_found}")
        return True
    else:
        # 没有找到中文字体，使用默认字体
        print("[警告] 未找到中文字体，图表可能显示方框")
        print("[提示] 可安装中文字体: sudo apt install fonts-wqy-microhei fonts-wqy-zenhei")
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        return False


# 场景和指标的英文映射（用于无中文字体时）
SCENE_EN_MAP = {
    '全部': 'All',
    '正常': 'Normal',
    '开阔场景': 'Open',
    '半遮挡': 'Half-block',
    '双边遮挡': 'Double-block',
    '隧道': 'Tunnel',
    '转发器': 'Repeater',
    '难点场景': 'Complex',
    '高速': 'Highway',
    '常规城市': 'Urban',
    '林荫道': 'Tree-road',
    '高架': 'Overpass',
    '城市峡谷': 'Urban-canyon',
    '长隧道': 'Long-tunnel',
}

# 全局变量：是否找到中文字体
HAS_CHINESE_FONT = False


def get_label(text: str) -> str:
    """获取标签文本，如果有中文字体返回原文，否则返回英文"""
    if HAS_CHINESE_FONT:
        return text
    return SCENE_EN_MAP.get(text, text)


class StatisticsData:
    """单个场景的统计数据"""

    METRICS_FULL = ['H-rms', 'H-CEP95', 'H-CEP99', 'H-max',
                    'L-rms', 'L-CEP95', 'L-CEP99', 'L-max',
                    'F-rms', 'F-CEP95', 'F-CEP99', 'F-max',
                    'V-rms', 'V-CEP95', 'V-CEP99', 'V-max']

    def __init__(self, odom: float = 0.0, has_vertical: bool = True):
        self.odom = odom
        self.has_vertical = has_vertical
        self.METRICS = self.METRICS_FULL if has_vertical else self.METRICS_FULL[:12]
        self.metrics = {metric: 0.0 for metric in self.METRICS}


class PrecisionStatistics:
    """存储精度统计数据"""

    def __init__(self, version: str = ""):
        self.version = version
        self.scenes = {}  # scene_type -> StatisticsData


def parse_precision_file(filepath: str) -> Dict[str, PrecisionStatistics]:
    """解析单个精度统计文件"""
    result = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lc_version_match = re.search(r'LC版本:\s*(\S+)', content)
    tc_version_match = re.search(r'TC版本:\s*(\S+)', content)

    lc_version = lc_version_match.group(1) if lc_version_match else "unknown"
    tc_version = tc_version_match.group(1) if tc_version_match else "unknown"

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
                       'GNSS Statistics', '说明', 'Notes', '============']

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
                scene_type = match.group(1).strip() if match else 'Unknown'

                data = StatisticsData(odom, has_vertical=has_vertical)
                data.metrics = dict(zip(data.METRICS, metrics_values))
                stats.scenes[scene_type] = data

        if stats.scenes:
            result[stat_key] = stats

    return result


def discover_datasets_recursive(input_dir: Path) -> Dict[str, Path]:
    """递归发现所有数据集及其精度文件路径"""
    datasets = {}
    if not input_dir.exists():
        return datasets

    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename == 'position_precision.txt':
                full_path = Path(root) / filename
                rel_path = full_path.parent.parent
                try:
                    relative_name = rel_path.relative_to(input_dir)
                    datasets[str(relative_name)] = full_path
                except ValueError:
                    datasets[rel_path.name] = full_path

    return datasets


def get_scheme_stats(precision_file: Path, scheme: str) -> Optional[PrecisionStatistics]:
    """从精度文件中提取特定方案的统计数据"""
    try:
        all_stats = parse_precision_file(str(precision_file))
        stat_key = 'lc' if 'pvtlc' in scheme or 'pvttc' in scheme else 'tc'
        if stat_key in all_stats:
            return all_stats[stat_key]
        return None
    except Exception as e:
        print(f"  [警告] 解析文件失败 {precision_file}: {e}")
        return None


def create_bar_chart(stats: PrecisionStatistics, metrics: List[str], scenes: List[str],
                     output_path: Path, title: str, scheme: str):
    """创建柱状图：各场景指标对比"""
    if not stats or not stats.scenes:
        print(f"  [警告] 无数据，跳过柱状图生成")
        return

    available_scenes = [s for s in scenes if s in stats.scenes]
    if not available_scenes:
        print(f"  [警告] 无可用场景，跳过柱状图生成")
        return

    first_scene_data = stats.scenes[available_scenes[0]]
    available_metrics = [m for m in metrics if m in first_scene_data.metrics]
    if not available_metrics:
        print(f"  [警告] 无可用指标，跳过柱状图生成")
        return

    n_metrics = len(available_metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=(n_metrics * 3, 6))
    if n_metrics == 1:
        axes = [axes]

    # 转换标签
    scene_labels = [get_label(s) for s in available_scenes]
    xlabel_text = get_label('场景')
    ylabel_text = get_label('误差') + ' (m)'

    for i, metric in enumerate(available_metrics):
        values = [stats.scenes[s].metrics.get(metric, 0) for s in available_scenes]
        ax = axes[i]
        bars = ax.bar(range(len(available_scenes)), values, color='steelblue', alpha=0.8)
        ax.set_title(metric, fontsize=12)
        ax.set_xlabel(xlabel_text, fontsize=10)
        ax.set_ylabel(ylabel_text, fontsize=10)
        ax.set_xticks(range(len(available_scenes)))
        ax.set_xticklabels(scene_labels, rotation=45, ha='right', fontsize=9)

        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=8)

    title_text = f'{get_label(title)} - {scheme} {get_label("各场景指标对比")}'
    plt.suptitle(title_text, fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path / f'bar_chart_{scheme}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [生成] 柱状图: {output_path / f'bar_chart_{scheme}.png'}")


def create_radar_chart(stats: PrecisionStatistics, metrics: List[str], scenes: List[str],
                       output_path: Path, title: str, scheme: str):
    """创建雷达图：多维度指标展示"""
    if not stats or not stats.scenes:
        print(f"  [警告] 无数据，跳过雷达图生成")
        return

    available_scenes = [s for s in scenes if s in stats.scenes]
    if not available_scenes:
        print(f"  [警告] 无可用场景，跳过雷达图生成")
        return

    first_scene_data = stats.scenes[available_scenes[0]]
    available_metrics = [m for m in metrics if m in first_scene_data.metrics]
    if len(available_metrics) < 3:
        print(f"  [警告] 指标数量不足，跳过雷达图生成")
        return

    angles = np.linspace(0, 2*np.pi, len(available_metrics), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    colors = plt.cm.Set2.colors[:min(len(available_scenes), 8)]

    for i, scene in enumerate(available_scenes[:5]):
        values = [stats.scenes[scene].metrics.get(m, 0) for m in available_metrics]
        values += values[:1]

        scene_label = get_label(scene)
        ax.plot(angles, values, 'o-', linewidth=2, label=scene_label, color=colors[i % len(colors)])
        ax.fill(angles, values, alpha=0.25, color=colors[i % len(colors)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(available_metrics, fontsize=10)
    title_text = f'{get_label(title)} - {scheme} {get_label("多维度指标雷达图")}'
    ax.set_title(title_text, fontsize=14, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

    plt.savefig(output_path / f'radar_chart_{scheme}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [生成] 雷达图: {output_path / f'radar_chart_{scheme}.png'}")


def create_heatmap(stats: PrecisionStatistics, metrics: List[str], scenes: List[str],
                   output_path: Path, title: str, scheme: str):
    """创建热力图：场景-指标矩阵"""
    if not stats or not stats.scenes:
        print(f"  [警告] 无数据，跳过热力图生成")
        return

    available_scenes = [s for s in scenes if s in stats.scenes]
    if not available_scenes:
        print(f"  [警告] 无可用场景，跳过热力图生成")
        return

    first_scene_data = stats.scenes[available_scenes[0]]
    available_metrics = [m for m in metrics if m in first_scene_data.metrics]
    if not available_metrics:
        print(f"  [警告] 无可用指标，跳过热力图生成")
        return

    data_matrix = np.zeros((len(available_scenes), len(available_metrics)))
    for i, scene in enumerate(available_scenes):
        for j, metric in enumerate(available_metrics):
            data_matrix[i, j] = stats.scenes[scene].metrics.get(metric, 0)

    fig, ax = plt.subplots(figsize=(max(14, len(available_metrics) * 0.9),
                                    max(10, len(available_scenes) * 1.2)))

    im = ax.imshow(data_matrix, cmap='YlOrRd', aspect='auto')

    # 转换标签
    scene_labels = [get_label(s) for s in available_scenes]

    ax.set_xticks(np.arange(len(available_metrics)))
    ax.set_yticks(np.arange(len(available_scenes)))
    ax.set_xticklabels(available_metrics, fontsize=10, rotation=45, ha='right')
    ax.set_yticklabels(scene_labels, fontsize=10)

    for i in range(len(available_scenes)):
        for j in range(len(available_metrics)):
            val = data_matrix[i, j]
            color = 'white' if val > np.percentile(data_matrix, 70) else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center', color=color, fontsize=9)

    title_text = f'{get_label(title)} - {scheme} {get_label("场景-指标热力图")}'
    ax.set_title(title_text, fontsize=14)
    ax.set_xlabel(get_label('指标'), fontsize=12)
    ax.set_ylabel(get_label('场景'), fontsize=12)

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(get_label('误差') + ' (m)', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path / f'heatmap_{scheme}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [生成] 热力图: {output_path / f'heatmap_{scheme}.png'}")


def create_table(stats: PrecisionStatistics, metrics: List[str], scenes: List[str],
                 output_path: Path, title: str, scheme: str) -> str:
    """创建表格：文本格式汇总"""
    if not stats or not stats.scenes:
        return ""

    available_scenes = [s for s in scenes if s in stats.scenes]
    if not available_scenes:
        return ""

    first_scene_data = stats.scenes[available_scenes[0]]
    available_metrics = [m for m in metrics if m in first_scene_data.metrics]
    if not available_metrics:
        return ""

    lines = []
    col_width = max(12, len(title) + 10)
    lines.append("=" * (col_width + len(available_metrics) * 10))
    lines.append(f"{title} - {scheme} 精度指标汇总表")
    lines.append("=" * (col_width + len(available_metrics) * 10))
    lines.append("")

    header = f"{'场景':<12}" + "".join([f"{m:>10}" for m in available_metrics])
    lines.append(header)
    lines.append("-" * (col_width + len(available_metrics) * 10))

    for scene in available_scenes:
        values = [stats.scenes[scene].metrics.get(m, 0) for m in available_metrics]
        row = f"{scene:<12}" + "".join([f"{v:>10.2f}" for v in values])
        lines.append(row)

    lines.append("")
    lines.append("=" * (col_width + len(available_metrics) * 10))

    table_content = "\n".join(lines)

    with open(output_path / f'table_{scheme}.txt', 'w', encoding='utf-8') as f:
        f.write(table_content)
    print(f"  [生成] 表格: {output_path / f'table_{scheme}.txt'}")

    return table_content


def create_output_directory(output_base_dir: Path, version_label: str) -> Path:
    """创建输出目录"""
    visualize_dir = output_base_dir / "visualize_precision"
    visualize_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir_name = f"{timestamp}_{version_label}"
    output_dir = visualize_dir / subdir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def main():
    """主函数"""
    global HAS_CHINESE_FONT

    # 设置中文字体
    HAS_CHINESE_FONT = setup_chinese_font()

    parser = argparse.ArgumentParser(
        description="精度指标可视化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python visualize_precision.py ../conf/visualize_precision_config.toml

可视化类型:
  - bar: 柱状图（各场景指标对比）
  - radar: 雷达图（多维度指标展示）
  - heatmap: 热力图（场景-指标矩阵）
  - table: 表格（文本格式汇总）
        """
    )

    parser.add_argument("config_file", type=str, help="配置文件路径")
    args = parser.parse_args()

    config_file = Path(args.config_file)
    if not config_file.exists():
        print(f"[错误] 配置文件不存在: {config_file}")
        sys.exit(1)

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = toml.load(f)
    except Exception as e:
        print(f"[错误] 读取配置文件失败: {e}")
        sys.exit(1)

    input_dir_str = config.get('input_dir', '').strip()
    if not input_dir_str:
        print(f"[错误] 配置文件中缺少 input_dir")
        sys.exit(1)

    input_dir = Path(input_dir_str)
    if not input_dir.exists():
        print(f"[错误] 输入目录不存在: {input_dir}")
        sys.exit(1)

    version_label = config.get('version_label', 'Unknown')
    visualize_schemes = config.get('visualize_schemes', ['pvtlc', 'rtklc'])
    visualize_metrics = config.get('visualize_metrics', [])
    visualize_scenes = config.get('visualize_scenes', [])
    visualize_types = config.get('visualize_types', ['bar', 'radar', 'heatmap', 'table'])

    output_base_dir_str = config.get('output_base_dir', '').strip()
    output_base_dir = Path(output_base_dir_str) if output_base_dir_str else input_dir.parent

    output_dir = create_output_directory(output_base_dir, version_label)
    print(f"[信息] 输出目录: {output_dir}")

    datasets = discover_datasets_recursive(input_dir)
    print(f"[信息] 发现 {len(datasets)} 个数据集")

    if not datasets:
        print("[错误] 未找到任何精度文件")
        sys.exit(1)

    if not visualize_schemes:
        for precision_file in datasets.values():
            try:
                all_stats = parse_precision_file(str(precision_file))
                if 'lc' in all_stats:
                    version = all_stats['lc'].version
                    if 'pvtlc' in version:
                        visualize_schemes.append('pvtlc')
                    elif 'pvttc' in version:
                        visualize_schemes.append('pvttc')
                if 'tc' in all_stats:
                    version = all_stats['tc'].version
                    if 'rtklc' in version:
                        visualize_schemes.append('rtklc')
                    elif 'rtktc' in version:
                        visualize_schemes.append('rtktc')
            except:
                pass
        visualize_schemes = list(set(visualize_schemes))
        if not visualize_schemes:
            visualize_schemes = ['pvtlc', 'rtklc']

    for scheme in visualize_schemes:
        print(f"\n[处理] 方案: {scheme}")

        first_precision_file = list(datasets.values())[0]
        stats = get_scheme_stats(first_precision_file, scheme)

        if not stats:
            print(f"  [警告] 未找到 {scheme} 方案数据")
            continue

        scenes_to_use = visualize_scenes if visualize_scenes else sorted(list(stats.scenes.keys()))
        metrics_to_use = visualize_metrics if visualize_metrics else list(list(stats.scenes.values())[0].metrics.keys())

        title = f"{get_label('版本')}: {version_label}"

        if 'bar' in visualize_types:
            create_bar_chart(stats, metrics_to_use, scenes_to_use, output_dir, title, scheme)

        if 'radar' in visualize_types:
            create_radar_chart(stats, metrics_to_use, scenes_to_use, output_dir, title, scheme)

        if 'heatmap' in visualize_types:
            create_heatmap(stats, metrics_to_use, scenes_to_use, output_dir, title, scheme)

        if 'table' in visualize_types:
            create_table(stats, metrics_to_use, scenes_to_use, output_dir, title, scheme)

    print(f"\n[完成] 可视化结果已保存到: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())