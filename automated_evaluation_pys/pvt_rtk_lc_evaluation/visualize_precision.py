#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精度指标可视化工具：将融合定位精度统计结果可视化展示

设计原则：
- 单个数据集：直接定位 position_precision.txt
- X轴 = 场景（7个场景分组）
- 分组柱状图：每个场景下3根柱子（pvtlc / rtklc / GNSS）
- 4行x4列布局：行=维度(H/L/F/V)，列=指标类型(rms/CEP95/CEP99/max)
- 每个方案各自生成独立图表
- 美观简洁，支持中文字体

使用方法：
    python visualize_precision.py <配置文件路径>
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    import toml
except ImportError:
    print("错误: 需要安装 toml 库，请运行: pip install toml")
    sys.exit(1)

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    import numpy as np
    from matplotlib.font_manager import FontManager
except ImportError:
    print("错误: 需要安装 matplotlib 和 numpy 库")
    print("请运行: pip install matplotlib numpy")
    sys.exit(1)


# ---- 中文字体设置 ----
def setup_chinese_font():
    chinese_fonts = [
        'PingFang SC', 'STHeiti', 'Heiti SC', 'Hiragino Sans GB',
        'Microsoft YaHei', 'SimHei', 'WenQuanYi Micro Hei',
        'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'Noto Sans CJK',
        'Source Han Sans CN', 'Droid Sans Fallback', 'Arial Unicode MS',
    ]
    fm = FontManager()
    available = set(f.name for f in fm.ttflist)
    for font in chinese_fonts:
        if font in available:
            plt.rcParams['font.sans-serif'] = [font, 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            print(f"[信息] 使用中文字体: {font}")
            return True
    print("[警告] 未找到中文字体，将使用英文标签")
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    return False


# ---- 标签映射 ----
SCENE_EN_MAP = {
    '全部': 'All', '正常': 'Normal', '开阔场景': 'Open Area',
    '半遮挡': 'Half-block', '双边遮挡': 'Double-block',
    '隧道': 'Tunnel', '转发器': 'Repeater', '难点场景': 'Complex',
    '高速': 'Highway', '常规城市': 'Urban', '林荫道': 'Tree-road',
    '高架': 'Overpass', '城市峡谷': 'Urban Canyon', '长隧道': 'Long Tunnel',
}

HAS_CHINESE_FONT = False


def get_label(text: str) -> str:
    return text if HAS_CHINESE_FONT else SCENE_EN_MAP.get(text, text)


# ---- 维度与配色配置 ----
METRIC_DISPLAY_NAMES = {
    # Horizontal
    'H-rms': 'RMS_Horizontal',
    'H-CEP95': 'CEP95_Horizontal',
    'H-CEP99': 'CEP99_Horizontal',
    'H-max': 'Max_Horizontal',
    # Lateral
    'L-rms': 'RMS_Lateral',
    'L-CEP95': 'CEP95_Lateral',
    'L-CEP99': 'CEP99_Lateral',
    'L-max': 'Max_Lateral',
    # Forward
    'F-rms': 'RMS_Forward',
    'F-CEP95': 'CEP95_Forward',
    'F-CEP99': 'CEP99_Forward',
    'F-max': 'Max_Forward',
    # Vertical
    'V-rms': 'RMS_Vertical',
    'V-CEP95': 'CEP95_Vertical',
    'V-CEP99': 'CEP99_Vertical',
    'V-max': 'Max_Vertical',
}

# 场景的标准顺序（用于图表标签排序）
SCENE_ORDER = ['全部', '正常', '开阔场景', '半遮挡', '双边遮挡', '隧道', '转发器']

DIMENSION_CONFIGS = {
    'H': {
        'metrics': ['H-rms', 'H-CEP95', 'H-CEP99', 'H-max'],
        'label_cn': '水平',
        'label_en': 'Horizontal',
        'colors': ['#2196F3', '#4CAF50', '#FF9800'],
    },
    'L': {
        'metrics': ['L-rms', 'L-CEP95', 'L-CEP99', 'L-max'],
        'label_cn': '横向',
        'label_en': 'Lateral',
        'colors': ['#2196F3', '#4CAF50', '#FF9800'],
    },
    'F': {
        'metrics': ['F-rms', 'F-CEP95', 'F-CEP99', 'F-max'],
        'label_cn': '前进方向',
        'label_en': 'Forward',
        'colors': ['#2196F3', '#4CAF50', '#FF9800'],
    },
    'V': {
        'metrics': ['V-rms', 'V-CEP95', 'V-CEP99', 'V-max'],
        'label_cn': '高程',
        'label_en': 'Vertical',
        'colors': ['#2196F3', '#4CAF50', '#FF9800'],
    },
}


# ---- 数据结构 ----
class MetricsData:
    """位置精度数据"""
    METRICS_FULL = [
        'H-rms', 'H-CEP95', 'H-CEP99', 'H-max',
        'L-rms', 'L-CEP95', 'L-CEP99', 'L-max',
        'F-rms', 'F-CEP95', 'F-CEP99', 'F-max',
        'V-rms', 'V-CEP95', 'V-CEP99', 'V-max',
    ]

    def __init__(self, odom: float = 0.0):
        self.odom = odom  # 里程 (km)
        self.metrics: Dict[str, float] = {m: 0.0 for m in self.METRICS_FULL}


class VelocityMetricsData:
    """速度精度数据"""
    METRICS_VELOCITY = ['RMS', 'CEP50', 'CEP95', 'CEP99', 'Max']

    def __init__(self):
        self.metrics: Dict[str, float] = {m: 0.0 for m in self.METRICS_VELOCITY}


class SchemeData:
    """单个方案的位置精度统计数据：{scene_name: MetricsData}"""
    def __init__(self, name: str, version: str):
        self.name = name    # scheme key: 'lc', 'tc', 'gnss'
        self.version = version  # e.g. 'pvtlc_c80c32da'
        self.scenes: Dict[str, MetricsData] = {}

    def add_scene(self, scene_name: str, data: MetricsData):
        self.scenes[scene_name] = data


class VelocitySchemeData:
    """单个方案的速度精度统计数据：{scene_name: VelocityMetricsData}"""
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.scenes: Dict[str, VelocityMetricsData] = {}

    def add_scene(self, scene_name: str, data: VelocityMetricsData):
        self.scenes[scene_name] = data


# ---- 解析逻辑 ----
def parse_precision_file(filepath: str) -> Tuple[str, List[SchemeData]]:
    """
    解析单个精度统计文件。
    返回: (dataset_name, [SchemeData, ...])
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    lc_version = None
    tc_version = None
    for line in lines:
        m = re.search(r'LC版本:\s*(\S+)', line)
        if m:
            lc_version = m.group(1)
        m = re.search(r'TC版本:\s*(\S+)', line)
        if m:
            tc_version = m.group(1)

    dataset_name = Path(filepath).parent.parent.name
    result: List[SchemeData] = []

    # ---- 找所有方案块的起止行号 ----
    section_headers = []
    for i, line in enumerate(lines):
        # 方案块的标题行格式: "pvtlc_c80c32da Statistics ..."
        # 必须是一行的开始（排除行中间的版本名引用）
        stripped = line.rstrip()
        if not stripped:
            continue
        # 检查是否匹配方案版本 + " Statistics"
        for ver in [lc_version, tc_version, 'GNSS']:
            if ver and re.match(rf'^{re.escape(ver)}\s+Statistics', stripped):
                section_headers.append((i, ver))
                break

    # 按行号排序
    section_headers.sort(key=lambda x: x[0])

    # ---- 提取每个方案块 ----
    for idx, (start_line, version) in enumerate(section_headers):
        end_line = len(lines)
        if idx + 1 < len(section_headers):
            end_line = section_headers[idx + 1][0]

        # 跳过标题行，从分隔线之后开始，到下一个section之前结束
        block_lines = lines[start_line + 1:end_line]
        skip = True
        sd = SchemeData(version, version)

        for line in block_lines:
            stripped = line.strip()
            if not stripped:
                continue
            if set(stripped) == {'-'}:
                skip = False
                continue
            if skip:
                continue

            nums = re.findall(r'[\d.]+', stripped)
            has_vertical = any('V-rms' in stripped for _ in [1]) or 'V-rms' in ''.join(block_lines)
            expected = 17 if has_vertical else 13
            if len(nums) < expected:
                continue

            m = re.match(r'^(.+?)\s*[\d.]+\s+', stripped)
            if not m:
                continue
            scene = m.group(1).strip()

            METRICS_FULL = [
                'H-rms', 'H-CEP95', 'H-CEP99', 'H-max',
                'L-rms', 'L-CEP95', 'L-CEP99', 'L-max',
                'F-rms', 'F-CEP95', 'F-CEP99', 'F-max',
                'V-rms', 'V-CEP95', 'V-CEP99', 'V-max',
            ]
            valid_metrics = METRICS_FULL[:16] if has_vertical else METRICS_FULL[:12]
            values = [float(n) for n in nums]
            odom = values[0]  # 第一个数值是里程
            data = MetricsData(odom)
            for i_m, metric in enumerate(valid_metrics):
                if i_m + 1 < len(values):
                    data.metrics[metric] = values[i_m + 1]

            sd.add_scene(scene, data)

        if sd.scenes:
            # scheme key
            if version == lc_version:
                sd.name = 'lc'
            elif version == tc_version:
                sd.name = 'tc'
            else:
                sd.name = 'gnss'
            result.append(sd)

    return dataset_name, result


def _parse_scheme_block(scheme_key: str, version: str, block: str) -> Optional[SchemeData]:
    """解析一个方案的统计块"""
    sd = SchemeData(scheme_key, version)
    lines = block.split('\n')

    has_vertical = 'V-rms' in block
    valid_metrics = MetricsData.METRICS_FULL[:16] if has_vertical else MetricsData.METRICS_FULL[:12]

    skip = True
    for line in lines:
        ls = line.strip()
        if not ls:
            continue
        # 跳过分隔线
        if set(ls) == {'-'}:
            skip = False
            continue
        if skip:
            continue

        nums = re.findall(r'[\d.]+', ls)
        expected = 17 if has_vertical else 13
        if len(nums) < expected:
            continue

        # 提取场景名
        m = re.match(r'^(.+?)\s*[\d.]+\s+', ls)
        if not m:
            continue
        scene = m.group(1).strip()

        values = [float(n) for n in nums]
        odom = values[0]  # 第一个数值是里程
        data = MetricsData(odom)
        for i, metric in enumerate(valid_metrics):
            if i + 1 < len(values):
                data.metrics[metric] = values[i + 1]

        sd.add_scene(scene, data)

    return sd


def parse_velocity_file(filepath: str) -> Tuple[str, List[VelocitySchemeData]]:
    """
    解析速度精度文件。
    返回: (dataset_name, [VelocitySchemeData, ...])
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    lc_version = None
    tc_version = None
    for line in lines:
        m = re.search(r'LC版本:\s*(\S+)', line)
        if m:
            lc_version = m.group(1)
        m = re.search(r'TC版本:\s*(\S+)', line)
        if m:
            tc_version = m.group(1)

    dataset_name = Path(filepath).parent.parent.name
    result: List[VelocitySchemeData] = []

    # 找所有方案块的起止行号（速度文件格式: "xxx Velocity Statistics"）
    section_headers = []
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if not stripped:
            continue
        for ver in [lc_version, tc_version, 'GNSS']:
            if ver and re.match(rf'^{re.escape(ver)}\s+Velocity\s+Statistics', stripped):
                section_headers.append((i, ver))
                break

    section_headers.sort(key=lambda x: x[0])

    for idx, (start_line, version) in enumerate(section_headers):
        end_line = len(lines)
        if idx + 1 < len(section_headers):
            end_line = section_headers[idx + 1][0]

        block_lines = lines[start_line + 1:end_line]
        skip = True

        # scheme key
        if version == lc_version:
            scheme_key = 'lc'
        elif version == tc_version:
            scheme_key = 'tc'
        else:
            scheme_key = 'gnss'

        sd = VelocitySchemeData(scheme_key, version)
        valid_metrics = VelocityMetricsData.METRICS_VELOCITY

        for line in block_lines:
            ls = line.strip()
            if not ls:
                continue
            if set(ls) == {'-'}:
                skip = False
                continue
            if skip:
                continue

            nums = re.findall(r'[\d.]+', ls)
            if len(nums) < 5:  # 速度精度有5个指标
                continue

            m = re.match(r'^(.+?)\s*[\d.]+\s+', ls)
            if not m:
                continue
            scene = m.group(1).strip()

            values = [float(n) for n in nums]
            data = VelocityMetricsData()
            for i, metric in enumerate(valid_metrics):
                if i < len(values):
                    data.metrics[metric] = values[i]

            sd.add_scene(scene, data)

        if sd.scenes:
            result.append(sd)

    return dataset_name, result


# ---- 查找精度文件 ----
def find_precision_file(input_dir: Path) -> Optional[Path]:
    """在目录树下查找 position_precision.txt"""
    if not input_dir.exists():
        return None
    # 优先查找 results/ 子目录下
    results_dir = input_dir / 'results'
    pfile = results_dir / 'position_precision.txt'
    if pfile.exists():
        return pfile
    # 递归查找
    for root, _, files in os.walk(input_dir):
        if 'position_precision.txt' in files:
            return Path(root) / 'position_precision.txt'
    return None


def find_velocity_file(input_dir: Path) -> Optional[Path]:
    """在目录树下查找 velocity_precision.txt"""
    if not input_dir.exists():
        return None
    results_dir = input_dir / 'results'
    vfile = results_dir / 'velocity_precision.txt'
    if vfile.exists():
        return vfile
    for root, _, files in os.walk(input_dir):
        if 'velocity_precision.txt' in files:
            return Path(root) / 'velocity_precision.txt'
    return None


def _nice_step(y_max: float) -> float:
    if y_max <= 0:
        return 1.0
    raw = y_max / 6
    mag = 10 ** np.floor(np.log10(raw) if raw > 0 else 0)
    norm = raw / mag if mag > 0 else raw
    if norm <= 1:
        step = 1
    elif norm <= 2:
        step = 2
    elif norm <= 5:
        step = 5
    else:
        step = 10
    return step * mag


def _make_safe_filename(name: str) -> str:
    """将标题转为安全的文件名"""
    return name.replace(' ', '_').replace('-', '_').replace('__', '_')


def plot_single_metric(
    metric_key: str,
    schemes: List[SchemeData],
    scenes_ordered: List[str],
    output_dir: Path,
    version_label: str,
) -> None:
    """
    为单个指标生成一张条形图。
    X轴: 各场景
    每组 N 根柱子 (N=方案数)
    """
    scheme_labels: Dict[str, str] = {
        'lc': 'pvtlc',
        'tc': 'rtklc',
        'gnss': 'GNSS',
    }
    scheme_names = [scheme_labels.get(s.name, s.name) for s in schemes]
    n_schemes = len(schemes)

    dim_key = metric_key.split('-')[0]
    dim_cfg = DIMENSION_CONFIGS[dim_key]
    colors = dim_cfg['colors']
    display_name = METRIC_DISPLAY_NAMES.get(metric_key, metric_key)

    # 文件名用英文全称
    fname = f"{_make_safe_filename(display_name)}.png"

    n_scenes = len(scenes_ordered)
    bar_width = 0.20
    group_gap = 0.30
    total_bar_w = bar_width * n_schemes
    scene_gap = group_gap

    # 计算每个场景的X中心
    x_centers = []
    cx = total_bar_w / 2
    for _ in scenes_ordered:
        x_centers.append(cx)
        cx += total_bar_w + scene_gap

    fig, ax = plt.subplots(figsize=(max(10, n_scenes * 1.6), 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#F8F9FA')

    all_vals = []
    for si, scheme in enumerate(schemes):
        xs = [x_centers[di] - total_bar_w / 2 + si * bar_width
              for di in range(n_scenes)]
        vals = []
        for scene in scenes_ordered:
            v = scheme.scenes.get(scene, MetricsData()).metrics.get(metric_key, 0.0)
            vals.append(v)
            all_vals.append(v)

        color = colors[si % len(colors)]
        bars = ax.bar(xs, vals, bar_width * 0.88,
                     color=color, edgecolor='white',
                     linewidth=0.6, zorder=3,
                     label=scheme_names[si])

        for bar, val in zip(bars, vals):
            if val > 0:
                y_offset = val * 0.015
                ax.text(bar.get_x() + bar.get_width() / 2,
                       val + y_offset,
                       f'{val:.2f}',
                       ha='center', va='bottom',
                       fontsize=9, color='#333333', zorder=4)

    # X轴
    ax.set_xticks(x_centers)
    scene_labels = [get_label(s) for s in scenes_ordered]
    ax.set_xticklabels(scene_labels, rotation=25, ha='right', fontsize=10)

    # Y轴
    valid = [v for v in all_vals if v > 0]
    if valid:
        y_max = max(valid)
        ax.set_ylim(0, y_max * 1.30)
        y_step = _nice_step(y_max * 1.30)
        ax.set_yticks(np.arange(0, y_max * 1.30 + y_step, y_step))
    ax.set_ylabel('Error (m)', fontsize=10)
    ax.tick_params(axis='y', labelsize=9)
    ax.grid(axis='y', linestyle='--', linewidth=0.7, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)

    # 美化边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')

    # 标题和图例
    ax.set_title(display_name, fontsize=14, fontweight='bold',
                color='#2C3E50', pad=10)
    ax.legend(loc='upper right', fontsize=10,
             frameon=True, edgecolor='#CCCCCC')

    fig.suptitle(
        f'{display_name} | {version_label}',
        fontsize=12, color='#555555', y=1.01,
    )

    fig.tight_layout()
    out_path = output_dir / fname
    fig.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  [生成] {fname}")


def plot_all_metrics(
    schemes: List[SchemeData],
    scenes_ordered: List[str],
    output_dir: Path,
    version_label: str,
) -> int:
    """为每个指标分别生成一张独立的图"""
    for metric in MetricsData.METRICS_FULL:
        plot_single_metric(
            metric, schemes, scenes_ordered,
            output_dir, version_label,
        )
    return len(MetricsData.METRICS_FULL)


def plot_velocity_metrics(
    schemes: List[VelocitySchemeData],
    scenes_ordered: List[str],
    output_dir: Path,
    version_label: str,
) -> int:
    """为速度精度每个指标生成一张图"""
    scheme_labels: Dict[str, str] = {
        'lc': 'pvtlc',
        'tc': 'rtklc',
        'gnss': 'GNSS',
    }
    scheme_names = [scheme_labels.get(s.name, s.name) for s in schemes]
    colors = ['#2196F3', '#4CAF50', '#FF9800']

    for metric in VelocityMetricsData.METRICS_VELOCITY:
        display_name = METRIC_DISPLAY_NAMES.get(metric, metric)
        fname = f'{display_name}_Velocity.png'

        n_schemes = len(schemes)
        n_scenes = len(scenes_ordered)
        bar_width = 0.25
        scene_gap = 0.15
        total_bar_w = n_schemes * bar_width

        x_centers = []
        cx = total_bar_w / 2
        for _ in scenes_ordered:
            x_centers.append(cx)
            cx += total_bar_w + scene_gap

        fig, ax = plt.subplots(figsize=(max(10, n_scenes * 1.6), 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#F8F9FA')

        all_vals = []
        for si, scheme in enumerate(schemes):
            xs = [x_centers[di] - total_bar_w / 2 + si * bar_width
                  for di in range(n_scenes)]
            vals = []
            for scene in scenes_ordered:
                v = scheme.scenes.get(scene, VelocityMetricsData()).metrics.get(metric, 0.0)
                vals.append(v)
                all_vals.append(v)

            color = colors[si % len(colors)]
            bars = ax.bar(xs, vals, bar_width * 0.88,
                         color=color, edgecolor='white',
                         linewidth=0.6, zorder=3,
                         label=scheme_names[si])

            for bar, val in zip(bars, vals):
                if val > 0:
                    y_offset = val * 0.015
                    ax.text(bar.get_x() + bar.get_width() / 2,
                           val + y_offset,
                           f'{val:.2f}',
                           ha='center', va='bottom',
                           fontsize=9, color='#333333', zorder=4)

        ax.set_xticks(x_centers)
        scene_labels = [get_label(s) for s in scenes_ordered]
        ax.set_xticklabels(scene_labels, rotation=25, ha='right', fontsize=10)

        valid = [v for v in all_vals if v > 0]
        if valid:
            y_max = max(valid)
            ax.set_ylim(0, y_max * 1.30)
            y_step = _nice_step(y_max * 1.30)
            ax.set_yticks(np.arange(0, y_max * 1.30 + y_step, y_step))
        ax.set_ylabel('Velocity Error (m/s)', fontsize=10)
        ax.tick_params(axis='y', labelsize=9)
        ax.grid(axis='y', linestyle='--', linewidth=0.7, alpha=0.5, zorder=0)
        ax.set_axisbelow(True)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')

        ax.set_title(f'{display_name} (Velocity)', fontsize=14, fontweight='bold',
                    color='#2C3E50', pad=10)
        ax.legend(loc='upper right', fontsize=10,
                 frameon=True, edgecolor='#CCCCCC')

        fig.suptitle(
            f'{display_name} (Velocity) | {version_label}',
            fontsize=12, color='#555555', y=1.01,
        )

        fig.tight_layout()
        out_path = output_dir / fname
        fig.savefig(out_path, dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        print(f"  [生成] {fname}")

    return len(VelocityMetricsData.METRICS_VELOCITY)


def write_text_summary(
    schemes: List[SchemeData],
    scenes_ordered: List[str],
    output_dir: Path,
    version_label: str,
) -> None:
    """输出文本格式汇总表"""
    scheme_labels: Dict[str, str] = {
        'lc': 'pvtlc',
        'tc': 'rtklc',
        'gnss': 'GNSS',
    }

    lines = []
    lines.append("=" * 90)
    lines.append(f"精度指标汇总  |  版本: {version_label}  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 90)
    lines.append("")

    scheme_names = [scheme_labels.get(s.name, s.name) for s in schemes]
    sc_col_w = 14
    val_col_w = 10

    for dim_key in ['H', 'L', 'F', 'V']:
        dim_cfg = DIMENSION_CONFIGS[dim_key]
        metrics = dim_cfg['metrics']
        dim_title = f"{dim_cfg['label_cn']} ({dim_cfg['label_en']})"

        lines.append(f"\n{'─' * 90}")
        lines.append(f"  {dim_title}")
        lines.append(f"{'─' * 90}")

        # 表头
        header = f"{'场景':^{sc_col_w}}" + "".join([f"{sn:^{val_col_w}}" for sn in scheme_names])
        lines.append(header)
        lines.append("─" * len(header))

        for metric in metrics:
            lines.append(f"\n{'  ' + metric}")
            for scene in scenes_ordered:
                row = f"{scene:<{sc_col_w}}"
                for scheme in schemes:
                    if scene in scheme.scenes:
                        v = scheme.scenes[scene].metrics.get(metric, 0.0)
                        val_str = f"{v:>{val_col_w}.3f}" if v > 0 else f"{'--':>{val_col_w}}"
                    else:
                        val_str = f"{'--':>{val_col_w}}"
                    row += val_str
                lines.append(row)

    lines.append("\n" + "=" * 90)

    txt = "\n".join(lines)
    out_path = output_dir / 'summary_table.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(txt)
    print(f"  [生成] {out_path.name}")


def write_velocity_summary(
    schemes: List[VelocitySchemeData],
    scenes_ordered: List[str],
    output_dir: Path,
    version_label: str,
) -> None:
    """输出速度精度文本格式汇总表"""
    scheme_labels: Dict[str, str] = {
        'lc': 'pvtlc',
        'tc': 'rtklc',
        'gnss': 'GNSS',
    }

    lines = []
    lines.append("=" * 90)
    lines.append(f"速度精度汇总  |  版本: {version_label}  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 90)
    lines.append("单位: m/s")
    lines.append("")

    scheme_names = [scheme_labels.get(s.name, s.name) for s in schemes]
    sc_col_w = 14
    val_col_w = 10

    # 表头
    header = f"{'场景':^{sc_col_w}}" + "".join([f"{sn:^{val_col_w}}" for sn in scheme_names])
    lines.append(header)
    lines.append("─" * len(header))

    for metric in VelocityMetricsData.METRICS_VELOCITY:
        lines.append(f"\n{'  ' + metric}")
        for scene in scenes_ordered:
            row = f"{scene:<{sc_col_w}}"
            for scheme in schemes:
                if scene in scheme.scenes:
                    v = scheme.scenes[scene].metrics.get(metric, 0.0)
                    val_str = f"{v:>{val_col_w}.3f}" if v > 0 else f"{'--':>{val_col_w}}"
                else:
                    val_str = f"{'--':>{val_col_w}}"
                row += val_str
            lines.append(row)

    lines.append("\n" + "=" * 90)

    txt = "\n".join(lines)
    out_path = output_dir / 'velocity_summary_table.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(txt)
    print(f"  [生成] {out_path.name}")


def create_output_directory(output_base_dir: Path, version_label: str) -> Path:
    visualize_dir = output_base_dir / "visualize_precision"
    visualize_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir = visualize_dir / f"{timestamp}_{version_label}"
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir


# ---- 主函数 ----
def main():
    global HAS_CHINESE_FONT
    HAS_CHINESE_FONT = setup_chinese_font()

    parser = argparse.ArgumentParser(description="精度指标可视化工具")
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
        print("[错误] 配置文件中缺少 input_dir")
        sys.exit(1)

    input_dir = Path(input_dir_str)
    if not input_dir.exists():
        print(f"[错误] 输入目录不存在: {input_dir}")
        sys.exit(1)

    version_label = config.get('version_label', input_dir.name)
    visualize_types = config.get('visualize_types', ['bar', 'table'])
    visualize_schemes_cfg = config.get('visualize_schemes', [])  # 可选：['lc', 'tc', 'gnss']
    visualize_scenes_cfg = config.get('visualize_scenes', [])

    output_base_dir_str = config.get('output_base_dir', '').strip()
    output_base_dir = Path(output_base_dir_str) if output_base_dir_str else input_dir.parent

    output_dir = create_output_directory(output_base_dir, version_label)
    print(f"[信息] 输出目录: {output_dir}")

    # ---- 查找精度文件 ----
    pfile = find_precision_file(input_dir)
    if not pfile:
        print(f"[错误] 未找到 position_precision.txt 文件于: {input_dir}")
        sys.exit(1)
    print(f"[信息] 使用精度文件: {pfile}")

    # ---- 解析 ----
    dataset_name, schemes = parse_precision_file(str(pfile))
    print(f"[信息] 数据集: {dataset_name}")
    print(f"[信息] 方案数量: {len(schemes)}")
    for s in schemes:
        print(f"  - {s.name}: {s.version} ({len(s.scenes)} 个场景)")

    if not schemes:
        print("[错误] 未能解析任何方案数据")
        sys.exit(1)

    # ---- 按配置过滤方案 ----
    if visualize_schemes_cfg:
        schemes = [s for s in schemes if s.name in visualize_schemes_cfg]
    print(f"[信息] 可视化方案: {[s.name for s in schemes]}")

    # ---- 确定场景列表 ----
    all_scenes = set()
    for s in schemes:
        all_scenes.update(s.scenes.keys())

    if visualize_scenes_cfg:
        # 按配置过滤，并按SCENE_ORDER排序
        scenes = [sc for sc in SCENE_ORDER if sc in visualize_scenes_cfg and sc in all_scenes]
    else:
        # 自动检测，按SCENE_ORDER排序（包含里程为0的场景）
        scenes = [sc for sc in SCENE_ORDER if sc in all_scenes]

    print(f"[信息] 场景列表: {scenes}")

    # ---- 生成位置精度图表 ----
    count = 0

    if 'bar' in visualize_types:
        print("\n[生成] 位置精度条形图（每个指标独立一张图）...")
        count += plot_all_metrics(schemes, scenes, output_dir, version_label)

    if 'table' in visualize_types:
        print("\n[生成] 位置精度文本汇总表...")
        write_text_summary(schemes, scenes, output_dir, version_label)
        count += 1

    # ---- 处理速度精度 ----
    vfile = find_velocity_file(input_dir)
    if vfile:
        print(f"\n[信息] 发现速度精度文件: {vfile}")
        v_dataset_name, v_schemes = parse_velocity_file(str(vfile))
        print(f"[信息] 速度方案数量: {len(v_schemes)}")

        if visualize_schemes_cfg:
            v_schemes = [s for s in v_schemes if s.name in visualize_schemes_cfg]

        if v_schemes:
            if 'bar' in visualize_types:
                print("\n[生成] 速度精度条形图...")
                count += plot_velocity_metrics(v_schemes, scenes, output_dir, version_label)

            if 'table' in visualize_types:
                print("\n[生成] 速度精度文本汇总表...")
                write_velocity_summary(v_schemes, scenes, output_dir, version_label)
                count += 1

    print(f"\n[完成] 共生成 {count} 个图表/文件，保存至: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
