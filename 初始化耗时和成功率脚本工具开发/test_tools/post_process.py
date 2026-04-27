#!/usr/bin/env python3
"""
Post-Processing Analysis for Localization Init Tests
================================================
直接分析 TCMSF/DR 二进制程序输出的 CSV 文件，以及日志文件，
提取初始化过程中的关键指标。

使用方式:
    python post_process.py --data-dir ./data/record_001/
    python post_process.py --data-dir ./data/record_001/ --module tcmsf
    python post_process.py --log-file ./data/record_001/test_output.log --module tcmsf
"""

import argparse
import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import glob

import pandas as pd
import numpy as np


ALIGN_TYPE_NAMES = {
    -1: "UNKNOWN",
    0: "UNALIGNED",
    1: "COARSE_ALIGN",
    2: "FINE_ALIGN",
    3: "ALIGNED",
}

FUSION_STATUS_NAMES = {
    -1: "UNKNOWN",
    0: "UNINIT",
    1: "INIT",
    2: "GPSONLY",
    3: "FULLSTATE",
    4: "VFMODE",
    5: "DRMODE",
}


@dataclass
class InitMetrics:
    """初始化过程的关键指标"""
    data_dir: str = ""

    # ===== 初始化阶段 =====
    init_start_time: float = -1.0
    init_end_time: float = -1.0
    init_duration_ms: float = -1.0

    # ===== 传感器数据就绪 =====
    first_imu_time: float = -1.0
    first_gps_time: float = -1.0
    first_veh_time: float = -1.0
    first_valid_imu_time: float = -1.0
    first_valid_gps_time: float = -1.0
    first_rtk_fix_time: float = -1.0

    # ===== MSF 状态转换 =====
    msf_ready_time: float = -1.0
    msf_aligned_time: float = -1.0
    msf_ready_reached: bool = False
    msf_aligned_reached: bool = False
    first_output_time: float = -1.0

    # ===== 融合状态统计 =====
    fusion_status_at_init: int = -1
    align_status_at_init: int = -1
    fusion_status_at_first_output: int = -1
    align_status_at_first_output: int = -1
    fusion_status_distribution: Dict[str, int] = None
    align_status_distribution: Dict[str, int] = None

    # ===== 传感器数据质量 =====
    imu_msg_count: int = 0
    gps_msg_count: int = 0
    veh_msg_count: int = 0
    valid_rtk_count: int = 0
    rtk_fix_rate: float = 0.0

    # ===== 耗时指标 =====
    sensor_ready_duration_ms: float = -1.0
    msf_ready_duration_ms: float = -1.0
    msf_aligned_duration_ms: float = -1.0
    first_output_duration_ms: float = -1.0
    imu_to_msf_ready_ms: float = -1.0
    rtk_fix_to_msf_ready_ms: float = -1.0

    # ===== 误差统计 (if debug CSV available) =====
    init_state_cols: List[str] = None
    init_state_has_data: bool = False

    def __post_init__(self):
        if self.fusion_status_distribution is None:
            self.fusion_status_distribution = {}
        if self.align_status_distribution is None:
            self.align_status_distribution = {}
        if self.init_state_cols is None:
            self.init_state_cols = []


def _parse_tcmsf_pose_csv(csv_path: str) -> Tuple[pd.DataFrame, InitMetrics]:
    """解析 TCMSF pose 输出 CSV"""
    metrics = InitMetrics(data_dir=os.path.dirname(csv_path))

    if not os.path.exists(csv_path):
        return pd.DataFrame(), metrics

    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(), metrics

    if df.empty:
        return df, metrics

    cols = df.columns.tolist()
    metrics.init_state_has_data = True

    time_col = None
    for c in ["measurement_timestamp", "publish_timestamp", "time", "pub_time", "header.measurement_timestamp"]:
        if c in cols:
            time_col = c
            break

    if time_col is None and len(cols) > 0:
        time_col = cols[0]

    if time_col:
        df = df.rename(columns={time_col: "timestamp"})
        metrics.init_start_time = float(df["timestamp"].iloc[0]) if len(df) > 0 else -1
        metrics.first_output_time = float(df["timestamp"].iloc[0]) if len(df) > 0 else -1
        metrics.init_end_time = float(df["timestamp"].iloc[-1]) if len(df) > 0 else -1
        metrics.first_output_duration_ms = 0.0

    fusion_cols = [c for c in cols if "fusion_status" in c.lower() or "fusionstatus" in c.lower()]
    if fusion_cols:
        df["fusion_status"] = df[fusion_cols[0]]
        metrics.fusion_status_at_first_output = int(df["fusion_status"].iloc[0])
        metrics.fusion_status_distribution = df["fusion_status"].value_counts().to_dict()
        status_reached = df[df["fusion_status"].isin([2, 3])]
        if not status_reached.empty:
            metrics.msf_ready_reached = True
            first_ready_idx = status_reached.index[0]
            metrics.msf_ready_time = float(df.loc[first_ready_idx, "timestamp"]) if "timestamp" in df.columns else -1
            metrics.first_output_duration_ms = (metrics.msf_ready_time - metrics.init_start_time) * 1000 if metrics.init_start_time > 0 else -1

    align_cols = [c for c in cols if "align_status" in c.lower() or "alignstatus" in c.lower()]
    if align_cols:
        df["align_status"] = df[align_cols[0]]
        metrics.align_status_at_first_output = int(df["align_status"].iloc[0])
        metrics.align_status_distribution = df["align_status"].value_counts().to_dict()
        aligned_rows = df[df["align_status"] == 3]
        if not aligned_rows.empty:
            metrics.msf_aligned_reached = True
            first_align_idx = aligned_rows.index[0]
            metrics.msf_aligned_time = float(df.loc[first_align_idx, "timestamp"]) if "timestamp" in df.columns else -1
            metrics.msf_aligned_duration_ms = (metrics.msf_aligned_time - metrics.init_start_time) * 1000 if metrics.init_start_time > 0 else -1

    metrics.init_state_cols = cols

    return df, metrics


def _parse_dr_csv(csv_path: str) -> Tuple[pd.DataFrame, InitMetrics]:
    """解析 DR 输出 CSV"""
    metrics = InitMetrics(data_dir=os.path.dirname(csv_path))

    if not os.path.exists(csv_path):
        return pd.DataFrame(), metrics

    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(), metrics

    if df.empty:
        return df, metrics

    metrics.init_state_has_data = True

    time_col = None
    cols = df.columns.tolist()
    for c in ["pub_time", "measure_time", "timestamp", "time"]:
        if c in cols and c in df.columns:
            time_col = c
            break

    if time_col is None and len(df.columns) > 0:
        time_col = df.columns[0]

    if time_col:
        df = df.rename(columns={time_col: "timestamp"})

    metrics.init_state_cols = df.columns.tolist()
    return df, metrics


def _parse_log_for_tcmsf(log_path: str) -> InitMetrics:
    """从日志文件中提取初始化耗时指标"""
    metrics = InitMetrics()

    if not os.path.exists(log_path):
        return metrics

    with open(log_path) as f:
        log_text = f.read()

    init_start_match = re.search(r"TCMSF daemon thread started!", log_text)
    if init_start_match:
        time_match = re.search(r"\[INIT-TIMING\] First MSF output at\s+([0-9.]+)\s*ms from start", log_text)
        if time_match:
            metrics.first_output_duration_ms = float(time_match.group(1))

    msf_ready_match = re.search(r"\[INIT-TIMING\] MSF Ready! duration:([0-9.]+)ms from start", log_text)
    if msf_ready_match:
        metrics.msf_ready_duration_ms = float(msf_ready_match.group(1))
        metrics.msf_ready_reached = True

    msf_aligned_match = re.search(r"\[INIT-TIMING\] MSF ALIGNED! duration:([0-9.]+)ms from start", log_text)
    if msf_aligned_match:
        metrics.msf_aligned_duration_ms = float(msf_aligned_match.group(1))
        metrics.msf_aligned_reached = True

    fusion_match = re.search(r"fusion_status:(\d+)", log_text)
    if fusion_match:
        metrics.fusion_status_at_first_output = int(fusion_match.group(1))

    align_match = re.search(r"align_status:(\d+)", log_text)
    if align_match:
        metrics.align_status_at_first_output = int(align_match.group(1))

    return metrics


def _parse_log_for_dr(log_path: str) -> InitMetrics:
    """从日志文件中提取 DR 初始化耗时指标"""
    metrics = InitMetrics()

    if not os.path.exists(log_path):
        return metrics

    with open(log_path) as f:
        log_text = f.read()

    init_complete_match = re.search(
        r"\[INIT-TIMING\] DR Init complete in\s+([0-9.]+)ms",
        log_text
    )
    if init_complete_match:
        metrics.init_duration_ms = float(init_complete_match.group(1))

    first_output_match = re.search(
        r"\[INIT-TIMING\] DR first output.*?"
        r"init:([0-9.]+)ms.*?"
        r"imu->out:([0-9.]+)ms",
        log_text, re.DOTALL
    )
    if first_output_match:
        metrics.init_duration_ms = float(first_output_match.group(1))
        metrics.first_output_duration_ms = float(first_output_match.group(2))
        metrics.dr_first_output_ms = float(first_output_match.group(2))

    return metrics


def analyze_tcmsf_data(data_dir: str) -> InitMetrics:
    """分析 TCMSF 数据目录"""
    metrics = InitMetrics(data_dir=data_dir)

    pose_csv = os.path.join(data_dir, "tcmsf_replay.csv")
    pose_csvs = glob.glob(os.path.join(data_dir, "**/tcmsf*.csv"), recursive=True)
    if pose_csvs:
        pose_csv = pose_csvs[0]

    df, csv_metrics = _parse_tcmsf_pose_csv(pose_csv)
    metrics = csv_metrics

    log_files = [
        os.path.join(data_dir, "test_output.log"),
        os.path.join(data_dir, "output.log"),
    ]
    log_files.extend(glob.glob(os.path.join(data_dir, "*.log")))
    log_path = None
    for lp in log_files:
        if os.path.exists(lp):
            log_path = lp
            break

    if log_path:
        log_metrics = _parse_log_for_tcmsf(log_path)
        for key in ["first_output_duration_ms", "msf_ready_duration_ms",
                     "msf_aligned_duration_ms", "msf_ready_reached",
                     "msf_aligned_reached"]:
            setattr(metrics, key, getattr(log_metrics, key))

    return metrics


def analyze_dr_data(data_dir: str) -> InitMetrics:
    """分析 DR 数据目录"""
    metrics = InitMetrics(data_dir=data_dir)

    dr_csv = os.path.join(data_dir, "dr_replay.csv")
    dr_csvs = glob.glob(os.path.join(data_dir, "**/dr*.csv"), recursive=True)
    if dr_csvs:
        dr_csv = dr_csvs[0]

    df, csv_metrics = _parse_dr_csv(dr_csv)
    metrics = csv_metrics

    log_files = [
        os.path.join(data_dir, "test_output.log"),
        os.path.join(data_dir, "output.log"),
    ]
    log_files.extend(glob.glob(os.path.join(data_dir, "*.log")))
    log_path = None
    for lp in log_files:
        if os.path.exists(lp):
            log_path = lp
            break

    if log_path:
        log_metrics = _parse_log_for_dr(log_path)
        for key in ["init_duration_ms", "first_output_duration_ms"]:
            val = getattr(log_metrics, key)
            if val >= 0:
                setattr(metrics, key, val)

    return metrics


def generate_summary(results: List[InitMetrics], output_dir: str, module: str):
    """生成汇总报告"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    records = []
    for r in results:
        d = asdict(r)
        d["fusion_status_distribution"] = json.dumps(d.get("fusion_status_distribution", {}))
        d["align_status_distribution"] = json.dumps(d.get("align_status_distribution", {}))
        d["init_state_cols"] = ",".join(d.get("init_state_cols", []))
        records.append(d)

    df = pd.DataFrame(records)
    csv_path = os.path.join(output_dir, f"init_metrics_{timestamp}.csv")
    df.to_csv(csv_path, index=False)
    print(f"  CSV saved: {csv_path}")

    summary = {"module": module, "total_cases": len(results), "timestamp": timestamp}

    success_count = sum(1 for r in results if r.msf_ready_reached or r.init_duration_ms >= 0)
    summary["success_count"] = success_count
    summary["success_rate"] = success_count / len(results) if results else 0

    ready_count = sum(1 for r in results if r.msf_ready_reached)
    aligned_count = sum(1 for r in results if r.msf_aligned_reached)
    summary["msf_ready_count"] = ready_count
    summary["msf_aligned_count"] = aligned_count

    numeric_keys = [
        "init_duration_ms", "first_output_duration_ms",
        "msf_ready_duration_ms", "msf_aligned_duration_ms",
    ]
    for key in numeric_keys:
        values = [getattr(r, key) for r in results if getattr(r, key) >= 0]
        if values:
            summary[f"{key}_mean"] = float(np.mean(values))
            summary[f"{key}_median"] = float(np.median(values))
            summary[f"{key}_std"] = float(np.std(values)) if len(values) > 1 else 0.0
            summary[f"{key}_min"] = float(np.min(values))
            summary[f"{key}_max"] = float(np.max(values))

    json_path = os.path.join(output_dir, f"init_summary_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  Summary saved: {json_path}")

    lines = []
    lines.append(f"# {module.upper()} Initialization Test Summary")
    lines.append(f"\nGenerated: {datetime.now().isoformat()}")
    lines.append(f"Test Cases: {len(results)}")
    lines.append(f"\n## Success Rate")
    lines.append(f"- Process Success: {success_count}/{len(results)} ({100*success_count/len(results):.1f}%)")
    if module == "tcmsf":
        lines.append(f"- MSF Ready: {ready_count}/{len(results)} ({100*ready_count/len(results):.1f}%)")
        lines.append(f"- MSF Aligned: {aligned_count}/{len(results)} ({100*aligned_count/len(results):.1f}%)")
    lines.append(f"\n## Timing Statistics (ms)")
    for key in numeric_keys:
        mean = summary.get(f"{key}_mean")
        median = summary.get(f"{key}_median")
        std = summary.get(f"{key}_std")
        min_v = summary.get(f"{key}_min")
        max_v = summary.get(f"{key}_max")
        if mean is not None:
            lines.append(f"- {key}:")
            lines.append(f"  - Mean: {mean:.2f} ms")
            lines.append(f"  - Median: {median:.2f} ms")
            lines.append(f"  - Std: {std:.2f} ms")
            lines.append(f"  - Range: [{min_v:.2f}, {max_v:.2f}] ms")

    md_path = os.path.join(output_dir, f"init_summary_{timestamp}.md")
    with open(md_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  Markdown saved: {md_path}")
    print("\n" + "\n".join(lines))

    return summary, csv_path, json_path, md_path


def main():
    parser = argparse.ArgumentParser(
        description="Post-processing analysis for localization init test results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python post_process.py --data-dir ./data/record_001/
    python post_process.py --data-dir ./data/record_001/ --module tcmsf
    python post_process.py --data-dirs ./data/record_001/ ./data/record_002/ --output ./analysis/
        """
    )
    parser.add_argument("--data-dir", help="Single data directory")
    parser.add_argument("--data-dirs", nargs="+", help="Multiple data directories")
    parser.add_argument("--output", "-o", default="./post_analysis", help="Output directory")
    parser.add_argument("--module", "-m", choices=["tcmsf", "dr", "auto"], default="auto")
    parser.add_argument("--log-file", help="Specific log file to analyze")

    args = parser.parse_args()

    data_dirs = []
    if args.data_dir:
        data_dirs = [args.data_dir]
    elif args.data_dirs:
        data_dirs = args.data_dirs
    else:
        print("Error: --data-dir or --data-dirs is required")
        sys.exit(1)

    for d in data_dirs:
        if not os.path.exists(d):
            print(f"Warning: Directory not found: {d}")

    data_dirs = [d for d in data_dirs if os.path.exists(d)]

    module = args.module
    if module == "auto":
        tcmsf_files = glob.glob(os.path.join(data_dirs[0], "**/tcmsf*.csv"), recursive=True) if data_dirs else []
        dr_files = glob.glob(os.path.join(data_dirs[0], "**/dr*.csv"), recursive=True) if data_dirs else []
        module = "tcmsf" if tcmsf_files else "dr"

    print(f"\n{'='*70}")
    print(f"Post-Processing: {module.upper()}")
    print(f"{'='*70}\n")

    results = []
    for d in data_dirs:
        print(f"  Analyzing: {d}")
        if module == "tcmsf":
            metrics = analyze_tcmsf_data(d)
        else:
            metrics = analyze_dr_data(d)
        results.append(metrics)

        if module == "tcmsf":
            status = "READY" if metrics.msf_ready_reached else "NOT_READY"
            aligned = "ALIGNED" if metrics.msf_aligned_reached else "NOT_ALIGNED"
            print(f"    first_output={metrics.first_output_duration_ms:.1f}ms "
                  f"msf_ready={metrics.msf_ready_duration_ms:.1f}ms ({status}) "
                  f"aligned={metrics.msf_aligned_duration_ms:.1f}ms ({aligned})")
        else:
            print(f"    init={metrics.init_duration_ms:.1f}ms "
                  f"first_output={metrics.first_output_duration_ms:.1f}ms")

    print(f"\n{'='*70}")
    summary, csv_path, json_path, md_path = generate_summary(results, args.output, module)
    print(f"{'='*70}\n")

    print(f"Output files:")
    print(f"  CSV: {csv_path}")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


if __name__ == "__main__":
    main()
