#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融合定位结果连续性检测脚本

功能：
1. 从 pvt.csv / gnss.csv 建立 Unix秒 → GPS秒 的时间映射
2. 给 imu.csv / vehicle.csv 追加 GPS秒列
3. 与 msf_debug_state.csv 的 GPS秒列对比，检测大段缺失
4. 输出 gap_intervals.toml 供绘图和统计使用

使用方法：
    python gap_detection.py <子数据集目录> [配置文件.toml]
    python gap_detection.py /path/to/subdataset_dir
    python gap_detection.py /path/to/subdataset_dir /path/to/config.toml

示例：
    python gap_detection.py /data/2026-04-10_14-58-57
    python gap_detection.py /data/2026-04-10_14-58-57 custom_config.toml
"""

import os
import sys
import argparse
import toml
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional


# GPS 常数：Unix时间起点到GPS时间起点的秒数差
GPS_EPOCH_OFFSET = 315964800.0


class GapDetector:
    """融合定位结果连续性检测器"""

    def __init__(self, subdataset_dir: str, config: Optional[Dict] = None):
        """
        初始化检测器

        Args:
            subdataset_dir: 子数据集目录（包含 topic_parse/ 和 pvtlc_*/、rtklc_*/ 等）
            config: 可选配置字典
        """
        self.subdataset_dir = Path(subdataset_dir)
        self.topic_parse_dir = self.subdataset_dir / "topic_parse"
        self.config = config if config else {}

        # 默认配置
        self.pvt_file = self.topic_parse_dir / "pvt.csv"
        self.gnss_file = self.topic_parse_dir / "gnss.csv"
        self.imu_file = self.topic_parse_dir / "imu.csv"
        self.vehicle_file = self.topic_parse_dir / "vehicle.csv"
        self.fusion_patterns = ["pvtlc", "rtklc", "pvttc", "rtktc"]

        # 可配置参数
        self.gap_threshold_sec = self.config.get("gap_threshold_sec", 5.0)
        self.min_consecutive_missing = self.config.get("min_consecutive_missing", 3)
        self.imu_freq_hz = self.config.get("imu_freq_hz", 100)
        self.fusion_freq_hz = self.config.get("fusion_freq_hz", 5)
        self.time_tolerance = self.config.get("time_tolerance", 0.5)

        self.verbose = self.config.get("verbose", False)

        # 数据
        self.unix_to_gps_map: Dict[float, float] = {}
        self.imu_times_gps: np.ndarray = None
        self.vehicle_times_gps: np.ndarray = None
        self.fusion_times_gps: Dict[str, np.ndarray] = {}
        self.gap_intervals: Dict[str, List[Tuple[float, float]]] = {}

    def _load_time_mapping(self) -> bool:
        """
        从 pvt.csv（或 gnss.csv）加载 Unix秒 → GPS秒 时间映射

        pvt.csv 格式：
            pub_time,measure_time,lat,lon,...
            1775804339.6288,457155.9000,22.54403602,...
        - pub_time: Unix时间戳（秒）
        - measure_time: GPS周内秒（= pub_time - 315964800）
        """
        src_file = self.pvt_file if self.pvt_file.exists() else self.gnss_file

        if not src_file.exists():
            print(f"[警告] 未找到时间映射源文件: {src_file}")
            return False

        if self.verbose:
            print(f"[信息] 从 {src_file.name} 加载时间映射...")

        unix_times = []
        gps_times = []

        try:
            with open(src_file, 'r', encoding='utf-8') as f:
                header = f.readline().strip()
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(',')
                    if len(parts) < 2:
                        continue
                    try:
                        unix_sec = float(parts[0])
                        gps_sec = float(parts[1])
                        unix_times.append(unix_sec)
                        gps_times.append(gps_sec)
                    except ValueError:
                        continue
        except Exception as e:
            print(f"[错误] 读取时间映射文件失败: {e}")
            return False

        if len(unix_times) == 0:
            print(f"[错误] 时间映射文件为空: {src_file}")
            return False

        self.unix_to_gps_map = dict(zip(unix_times, gps_times))

        if self.verbose:
            print(f"  加载映射点数: {len(self.unix_to_gps_map)}")
            print(f"  GPS秒范围: {min(gps_times):.3f} ~ {max(gps_times):.3f}")
            print(f"  Unix秒范围: {min(unix_times):.3f} ~ {max(unix_times):.3f}")

        return True

    def _unix_to_gps(self, unix_sec: float) -> Optional[float]:
        """
        将 Unix 秒转换为 GPS 秒（通过最近邻插值）

        注意：pvt.csv 的 measure_time 是 GPS 秒（10Hz，精度 0.1s），
        而 imu/vehicle 的 measure_time 是 Unix 秒（10Hz/100Hz，精度 0.1s/0.01s）。
        两者精度不同，不能用精确查表，必须找最近的 Unix 时间点。
        """
        if not self.unix_to_gps_map:
            return None

        # 用最近邻查找：找与 unix_sec 差距最小的键
        unix_keys = np.array(sorted(self.unix_to_gps_map.keys()))
        if len(unix_keys) == 0:
            return None

        # 二分查找最近邻
        idx = np.searchsorted(unix_keys, unix_sec)
        if idx == 0:
            nearest_key = unix_keys[0]
        elif idx == len(unix_keys):
            nearest_key = unix_keys[-1]
        else:
            # 比较前后两个键，选更近的
            before = unix_keys[idx - 1]
            after = unix_keys[idx]
            nearest_key = before if abs(before - unix_sec) <= abs(after - unix_sec) else after

        return self.unix_to_gps_map[nearest_key]

    def _load_sensor_gps_times(self) -> bool:
        """
        加载 IMU 和 vehicle 的 GPS 秒时间数组

        imu.csv 格式：
            pub_time,measure_time,acc_x,acc_y,...
            1775804339.5645,1775804339.5611,...

        vehicle.csv 格式：
            pub_time,measure_time,spd_rl,spd_rr,...
            1775804339.5629,1775804339.5620,...

        注意：这里的 measure_time 也是 Unix 秒，不是 GPS 秒
        """
        if self.verbose:
            print("[信息] 加载传感器 GPS 秒时间数组...")

        # ---- 加载 IMU ----
        if self.imu_file.exists():
            try:
                imu_times = []
                with open(self.imu_file, 'r', encoding='utf-8') as f:
                    header = f.readline()  # 跳过表头
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split(',')
                        if len(parts) < 2:
                            continue
                        try:
                            # measure_time 是 Unix 秒
                            unix_sec = float(parts[1])
                            gps_sec = self._unix_to_gps(unix_sec)
                            if gps_sec is not None:
                                imu_times.append(gps_sec)
                        except ValueError:
                            continue

                if imu_times:
                    self.imu_times_gps = np.array(sorted(imu_times))
                    if self.verbose:
                        print(f"  IMU: 加载 {len(self.imu_times_gps)} 个 GPS 秒时间点")
                        print(f"    GPS秒范围: {self.imu_times_gps[0]:.3f} ~ {self.imu_times_gps[-1]:.3f}")
                        print(f"    估计频率: {len(self.imu_times_gps) / (self.imu_times_gps[-1] - self.imu_times_gps[0]):.1f} Hz")
            except Exception as e:
                print(f"[错误] 加载 IMU 文件失败: {e}")
                self.imu_times_gps = None
        else:
            print(f"[警告] IMU 文件不存在: {self.imu_file}")
            self.imu_times_gps = None

        # ---- 加载 Vehicle ----
        if self.vehicle_file.exists():
            try:
                vehicle_times = []
                with open(self.vehicle_file, 'r', encoding='utf-8') as f:
                    header = f.readline()  # 跳过表头
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split(',')
                        if len(parts) < 2:
                            continue
                        try:
                            unix_sec = float(parts[1])
                            gps_sec = self._unix_to_gps(unix_sec)
                            if gps_sec is not None:
                                vehicle_times.append(gps_sec)
                        except ValueError:
                            continue

                if vehicle_times:
                    self.vehicle_times_gps = np.array(sorted(vehicle_times))
                    if self.verbose:
                        print(f"  Vehicle: 加载 {len(self.vehicle_times_gps)} 个 GPS 秒时间点")
                        print(f"    GPS秒范围: {self.vehicle_times_gps[0]:.3f} ~ {self.vehicle_times_gps[-1]:.3f}")
                        print(f"    估计频率: {len(self.vehicle_times_gps) / (self.vehicle_times_gps[-1] - self.vehicle_times_gps[0]):.1f} Hz")
            except Exception as e:
                print(f"[错误] 加载 Vehicle 文件失败: {e}")
                self.vehicle_times_gps = None
        else:
            print(f"[警告] Vehicle 文件不存在: {self.vehicle_file}")
            self.vehicle_times_gps = None

        return (self.imu_times_gps is not None or self.vehicle_times_gps is not None)

    def _find_fusion_dirs(self) -> List[Tuple[str, Path]]:
        """查找所有融合结果目录（pvtlc_*, rtklc_*, ...）"""
        fusion_dirs = []
        for item in self.subdataset_dir.iterdir():
            if not item.is_dir():
                continue
            name_lower = item.name.lower()
            for pattern in self.fusion_patterns:
                if pattern in name_lower:
                    fusion_dirs.append((item.name, item))
                    break
        return fusion_dirs

    def _load_fusion_gps_times(self, fusion_dir: Path) -> Optional[np.ndarray]:
        """
        从 msf_debug_state.csv 加载 GPS 秒时间数组

        msf_debug_state.csv 格式（无表头，最后一列是GPS秒）：
            1775804341.332, ..., 457157.66
            1775804341.532, ..., 457157.86
            ...
        """
        msf_file = fusion_dir / "msf_debug_state.csv"
        if not msf_file.exists():
            return None

        try:
            gps_times = []
            with open(msf_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(',')
                    if len(parts) < 2:
                        continue
                    try:
                        # 最后一列是 GPS 秒
                        gps_sec = float(parts[-1].strip())
                        gps_times.append(gps_sec)
                    except ValueError:
                        continue

            if gps_times:
                times = np.array(sorted(gps_times))
                if self.verbose:
                    print(f"  {fusion_dir.name}: 加载 {len(times)} 个 GPS 秒时间点")
                    print(f"    GPS秒范围: {times[0]:.3f} ~ {times[-1]:.3f}")
                    print(f"    估计频率: {len(times) / (times[-1] - times[0]):.1f} Hz")
                return times
            return None
        except Exception as e:
            print(f"[错误] 加载融合结果文件失败: {msf_file}, {e}")
            return None

    def _has_sensor_data(self, fusion_gps_time: float) -> bool:
        """
        判断融合帧对应的时刻，IMU 或 Vehicle 是否有原始数据

        Args:
            fusion_gps_time: 融合结果的 GPS 秒时间

        Returns:
            True 表示 IMU 或 Vehicle 至少有一个在该时刻附近有数据
        """
        tolerance = self.time_tolerance

        # 检查 IMU
        if self.imu_times_gps is not None and len(self.imu_times_gps) > 0:
            closest_imu = self.imu_times_gps[np.argmin(np.abs(self.imu_times_gps - fusion_gps_time))]
            if abs(closest_imu - fusion_gps_time) <= tolerance:
                return True

        # 检查 Vehicle
        if self.vehicle_times_gps is not None and len(self.vehicle_times_gps) > 0:
            closest_veh = self.vehicle_times_gps[np.argmin(np.abs(self.vehicle_times_gps - fusion_gps_time))]
            if abs(closest_veh - fusion_gps_time) <= tolerance:
                return True

        return False

    def _detect_gaps(self, fusion_times: np.ndarray) -> List[Tuple[float, float]]:
        """
        检测大段缺失

        Args:
            fusion_times: 融合结果的 GPS 秒时间数组（有序）

        Returns:
            List of (gap_start_gps, gap_end_gps) 元组，GPS秒为单位
        """
        if fusion_times is None or len(fusion_times) < 2:
            return []

        gaps = []
        consecutive_missing = 0
        gap_start = None

        # 理论帧间隔
        expected_interval = 1.0 / self.fusion_freq_hz  # 5Hz → 0.2s

        for i in range(len(fusion_times)):
            gps_time = fusion_times[i]
            has_data = self._has_sensor_data(gps_time)

            if has_data:
                # 有数据
                if consecutive_missing >= self.min_consecutive_missing:
                    # 刚才有一段 gap，现在找到了正常帧，说明 gap 结束
                    gap_end = fusion_times[i - consecutive_missing // 2]
                    gap_start_gps = fusion_times[i - consecutive_missing]
                    gap_end_gps = gap_end
                    gap_duration = gap_end_gps - gap_start_gps
                    if gap_duration >= self.gap_threshold_sec:
                        gaps.append((gap_start_gps, gap_end_gps))
                        if self.verbose:
                            print(f"  [Gap] GPS秒 {gap_start_gps:.3f} ~ {gap_end_gps:.3f} "
                                  f"(持续 {gap_duration:.2f}s, {consecutive_missing}帧)")
                consecutive_missing = 0
                gap_start = None
            else:
                # 缺失
                consecutive_missing += 1

        return gaps

    def _merge_overlapping_gaps(self, gaps: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """合并重叠或相邻的 gap 区间"""
        if not gaps:
            return []

        gaps = sorted(gaps, key=lambda x: x[0])
        merged = [gaps[0]]

        for start, end in gaps[1:]:
            last_start, last_end = merged[-1]
            # 重叠或相邻（间隔 < 1s）
            if start <= last_end + 1.0:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))

        return merged

    def run(self) -> Dict[str, List[Tuple[float, float]]]:
        """
        执行连续性检测

        Returns:
            Dict[str, List[Tuple[float, float]]]: 以融合版本名为key的gap区间列表
        """
        print(f"\n{'='*60}")
        print(f"[连续性检测] 子数据集: {self.subdataset_dir.name}")
        print(f"[配置] 缺失阈值: {self.gap_threshold_sec}s, 最小连续缺失帧: {self.min_consecutive_missing}")
        print(f"[配置] IMU频率: {self.imu_freq_hz}Hz, Fusion频率: {self.fusion_freq_hz}Hz, 容差: {self.time_tolerance}s")
        print(f"{'='*60}")

        # Step 1: 加载时间映射
        if not self._load_time_mapping():
            print("[错误] 时间映射加载失败，退出")
            return {}

        # Step 2: 加载传感器 GPS 秒时间
        if not self._load_sensor_gps_times():
            print("[错误] 传感器时间加载失败，退出")
            return {}

        # Step 3: 查找并处理每个融合结果目录
        fusion_dirs = self._find_fusion_dirs()
        if not fusion_dirs:
            print("[警告] 未找到任何融合结果目录（pvtlc_*, rtklc_*, ...）")
            return {}

        print(f"\n[信息] 找到 {len(fusion_dirs)} 个融合结果目录")

        all_gaps = {}

        for fusion_name, fusion_dir in fusion_dirs:
            print(f"\n--- 处理: {fusion_name} ---")

            fusion_times = self._load_fusion_gps_times(fusion_dir)
            if fusion_times is None or len(fusion_times) == 0:
                print(f"  [跳过] 无有效 GPS 秒数据")
                continue

            gaps = self._detect_gaps(fusion_times)
            gaps = self._merge_overlapping_gaps(gaps)

            if gaps:
                all_gaps[fusion_name] = gaps
                print(f"  检测到大段缺失: {len(gaps)} 段")
                for start, end in gaps:
                    print(f"    GPS秒 {start:.3f} ~ {end:.3f} (持续 {end - start:.2f}s)")
            else:
                all_gaps[fusion_name] = []
                print(f"  未检测到大段缺失")

        self.gap_intervals = all_gaps

        print(f"\n{'='*60}")
        print(f"[汇总]")
        for name, gaps in all_gaps.items():
            if gaps:
                print(f"  {name}: {len(gaps)} 段大段缺失")
                for start, end in gaps:
                    print(f"    {start:.3f} ~ {end:.3f} ({end - start:.2f}s)")
            else:
                print(f"  {name}: 无大段缺失")
        print(f"{'='*60}")

        return all_gaps

    def save_results(self, output_dir: Optional[Path] = None) -> bool:
        """
        保存检测结果

        Args:
            output_dir: 输出目录（默认为子数据集目录）

        Returns:
            是否保存成功
        """
        if output_dir is None:
            output_dir = self.subdataset_dir

        output_dir = Path(output_dir)
        results_dir = output_dir / "gap_detection"
        results_dir.mkdir(parents=True, exist_ok=True)

        # ---- 保存 gap_intervals.toml ----
        toml_path = results_dir / "gap_intervals.toml"
        self._save_toml(toml_path)

        # ---- 保存 gap_intervals.txt（人类可读）----
        txt_path = results_dir / "gap_intervals.txt"
        self._save_txt(txt_path)

        # ---- 保存带 GPS 秒的 imu / vehicle CSV ----
        self._save_sensor_csv_with_gps(results_dir)

        print(f"\n[结果] 已保存到 {results_dir}/")
        print(f"  - gap_intervals.toml (供脚本读取)")
        print(f"  - gap_intervals.txt  (人工查看)")

        return True

    def _save_toml(self, toml_path: Path):
        """保存为 TOML 格式"""
        gap_config = {
            "gap_detection": {
                "gap_threshold_sec": self.gap_threshold_sec,
                "min_consecutive_missing": self.min_consecutive_missing,
                "fusion_freq_hz": self.fusion_freq_hz,
                "time_tolerance_sec": self.time_tolerance,
            }
        }

        for fusion_name, intervals in self.gap_intervals.items():
            safe_name = fusion_name.replace("-", "_").replace(".", "_")
            gap_config[f"gap_intervals_{safe_name}"] = {
                "fusion_type": fusion_name,
                "gps_ranges": [[float(start), float(end)] for start, end in intervals],
                "count": len(intervals),
            }

        try:
            with open(toml_path, 'w', encoding='utf-8') as f:
                toml.dump(gap_config, f)
            print(f"  ✓ gap_intervals.toml 已保存")
        except Exception as e:
            print(f"  ✗ gap_intervals.toml 保存失败: {e}")

    def _save_txt(self, txt_path: Path):
        """保存为文本格式"""
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("融合定位结果连续性检测报告\n")
                f.write("=" * 60 + "\n")
                f.write(f"子数据集: {self.subdataset_dir.name}\n")
                f.write(f"检测阈值: >= {self.gap_threshold_sec}s 判定为大段缺失\n")
                f.write(f"IMU频率: {self.imu_freq_hz}Hz  Fusion频率: {self.fusion_freq_hz}Hz  容差: {self.time_tolerance}s\n")
                f.write("=" * 60 + "\n\n")

                total_gaps = 0
                for fusion_name, intervals in self.gap_intervals.items():
                    f.write(f"[{fusion_name}]\n")
                    if intervals:
                        f.write(f"  大段缺失段数: {len(intervals)}\n")
                        total_gaps += len(intervals)
                        for i, (start, end) in enumerate(intervals, 1):
                            f.write(f"  段{i}: GPS秒 {start:.3f} ~ {end:.3f}  "
                                    f"持续 {end - start:.2f}s\n")
                    else:
                        f.write("  无大段缺失\n")
                    f.write("\n")

                f.write("=" * 60 + "\n")
                f.write(f"总计: {total_gaps} 段大段缺失\n")
                f.write("说明: GPS秒为GPS周内秒（从每周日0点开始的秒数）\n")
                f.write("      转换为Unix时间戳: Unix = GPS + 315964800\n")

            print(f"  ✓ gap_intervals.txt 已保存")
        except Exception as e:
            print(f"  ✗ gap_intervals.txt 保存失败: {e}")

    def _save_sensor_csv_with_gps(self, results_dir: Path):
        """保存带 GPS 秒的传感器 CSV（供后续调试）"""
        # 保存 IMU
        if self.imu_times_gps is not None and self.imu_file.exists():
            imu_out = results_dir / "imu_with_gps.csv"
            try:
                gps_set = set(self.imu_times_gps)
                with open(self.imu_file, 'r', encoding='utf-8') as fin:
                    header = fin.readline().strip()
                    with open(imu_out, 'w', encoding='utf-8') as fout:
                        fout.write(header + ",gps_time\n")
                        for line in fin:
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split(',')
                            if len(parts) < 2:
                                continue
                            try:
                                unix_sec = float(parts[1])
                                gps_sec = self._unix_to_gps(unix_sec)
                                if gps_sec is not None:
                                    fout.write(line + f",{gps_sec:.6f}\n")
                            except ValueError:
                                continue
                print(f"  ✓ imu_with_gps.csv 已保存 ({len(self.imu_times_gps)} 行)")
            except Exception as e:
                print(f"  ✗ imu_with_gps.csv 保存失败: {e}")

        # 保存 Vehicle
        if self.vehicle_times_gps is not None and self.vehicle_file.exists():
            veh_out = results_dir / "vehicle_with_gps.csv"
            try:
                with open(self.vehicle_file, 'r', encoding='utf-8') as fin:
                    header = fin.readline().strip()
                    with open(veh_out, 'w', encoding='utf-8') as fout:
                        fout.write(header + ",gps_time\n")
                        for line in fin:
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split(',')
                            if len(parts) < 2:
                                continue
                            try:
                                unix_sec = float(parts[1])
                                gps_sec = self._unix_to_gps(unix_sec)
                                if gps_sec is not None:
                                    fout.write(line + f",{gps_sec:.6f}\n")
                            except ValueError:
                                continue
                print(f"  ✓ vehicle_with_gps.csv 已保存 ({len(self.vehicle_times_gps)} 行)")
            except Exception as e:
                print(f"  ✗ vehicle_with_gps.csv 保存失败: {e}")


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except Exception as e:
        print(f"[警告] 配置文件读取失败: {e}，使用默认配置")
        return {}


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="融合定位结果连续性检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    python gap_detection.py /path/to/subdataset_dir
    python gap_detection.py /path/to/subdataset_dir --threshold 3.0
    python gap_detection.py /path/to/subdataset_dir /path/to/config.toml

配置文件示例 (config.toml):
    [gap_detection]
    gap_threshold_sec = 5.0    # 连续缺失多少秒算大段缺失
    min_consecutive_missing = 3  # 最小连续缺失帧数
    fusion_freq_hz = 5         # 融合结果频率
    time_tolerance = 0.5      # 时间容差（秒）
    verbose = true
"""
    )

    parser.add_argument(
        "subdataset_dir",
        type=str,
        help="子数据集目录（包含 topic_parse/ 和 pvtlc_*/rtklc_*/ 等融合结果目录）"
    )

    parser.add_argument(
        "config_file",
        type=str,
        nargs='?',
        default=None,
        help="配置文件路径（可选，会覆盖命令行参数）"
    )

    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=None,
        dest="gap_threshold_sec",
        help=f"连续缺失多少秒判定为大段缺失（默认: 5.0）"
    )

    parser.add_argument(
        "--tolerance",
        type=float,
        default=None,
        dest="time_tolerance",
        help=f"时间容差，秒（默认: 0.5）"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=None,
        help="详细输出"
    )

    args = parser.parse_args()

    # 加载配置
    config = {}
    if args.config_file and os.path.exists(args.config_file):
        config = load_config(args.config_file)
        # 配置文件中可能用 gap_detection 子表
        if "gap_detection" in config:
            config = config["gap_detection"]

    # 命令行参数覆盖配置文件
    if args.gap_threshold_sec is not None:
        config["gap_threshold_sec"] = args.gap_threshold_sec
    if args.time_tolerance is not None:
        config["time_tolerance"] = args.time_tolerance
    if args.verbose is not None:
        config["verbose"] = args.verbose

    # 设置默认值
    config.setdefault("gap_threshold_sec", 5.0)
    config.setdefault("min_consecutive_missing", 3)
    config.setdefault("fusion_freq_hz", 5)
    config.setdefault("time_tolerance", 0.5)
    config.setdefault("verbose", False)

    # 检查目录
    subdataset_dir = Path(args.subdataset_dir)
    if not subdataset_dir.exists():
        print(f"[错误] 目录不存在: {subdataset_dir}")
        sys.exit(1)

    topic_parse = subdataset_dir / "topic_parse"
    if not topic_parse.exists():
        print(f"[错误] topic_parse 目录不存在: {topic_parse}")
        sys.exit(1)

    # 执行检测
    detector = GapDetector(str(subdataset_dir), config)
    gaps = detector.run()

    if gaps:
        detector.save_results()

    print("\n[完成]")


if __name__ == "__main__":
    main()
