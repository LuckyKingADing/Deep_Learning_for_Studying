#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据压缩与归档工具

功能说明：
1. 根据原始数据路径自动创建TOML配置文件
2. 启动数据压缩脚本并监控执行状态
3. 将压缩后的数据集归档到指定目录

使用方法：
    python3 data_compression_archive.py

注意：
    - 在脚本开头配置参数后直接运行
    - 本脚本在云端环境执行（oss路径、mnt路径等均为云端路径）
"""

import os
import sys
import subprocess
import shutil
import re
import time
import threading
from collections import deque
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set

# ==================== 配置参数（用户在此设置）====================
# 原始数据路径（oss路径）
# 示例：oss-byd-wl-roadtest/BCNOA_ROADTEST/20260417/LC0C76C48S7033256/
RAW_DATA_URL = "oss-byd-wl-roadtest/BCNOA_ROADTEST/20260417/LC0C76C48S7033256/"

# 示例TOML文件名（位于脚本所在目录）
EXAMPLE_TOML_FILENAME = "20260324_hc25_pvt1_nc.toml"

# 压缩脚本路径
COMPRESSION_SCRIPT_PATH = "/mnt/workspace/user/lijianghua/scripts/oss/oss_data_split.py"

# TOML文件上传目录
TOML_UPLOAD_DIR = "/mnt/data/oss-byd-wl-roadtest/users/localization/split_data/split_data_url/"

# 压缩数据输出目录
COMPRESSION_OUTPUT_DIR = "/mnt/data/oss-byd-wl-roadtest/users/localization/split_data/split_data_dir/"

# 最终归档目录（子数据集将移动到此目录下的日期子目录）
ARCHIVE_BASE_DIR = "/mnt/data/oss-byd-wl-roadtest/users/localization/split_data/split_data_dir/pvtrtk_nocamera/"

# oss数据挂载前缀（用于从oss路径转换为本地路径）
OSS_MOUNT_PREFIX = "/mnt/data/"

# ==================== 配置参数结束 ====================


class DataCompressionArchive:
    """数据压缩与归档工具类"""

    def __init__(self):
        """初始化"""
        self.script_dir = Path(__file__).parent
        self.raw_data_url = RAW_DATA_URL.rstrip('/')  # 去除末尾的/
        self.example_toml = self.script_dir / EXAMPLE_TOML_FILENAME

        # 从oss路径提取关键信息
        self._parse_raw_data_url()

    def _parse_raw_data_url(self):
        """解析原始数据URL，提取日期等信息"""
        # oss路径格式：oss-byd-wl-roadtest/BCNOA_ROADTEST/20260417/LC0C76C48S7033256/
        parts = self.raw_data_url.split('/')
        self.date_str = None
        self.vehicle_id = None

        for part in parts:
            # 匹配日期格式 YYYYMMDD
            if re.match(r'^\d{8}$', part):
                self.date_str = part
            # 匹配车辆ID格式（以L开头的）
            elif re.match(r'^L[A-Z0-9]+$', part):
                self.vehicle_id = part

        if not self.date_str:
            raise ValueError(f"无法从路径中解析日期: {self.raw_data_url}")

        # 格式化日期为 YYYY-MM-DD 形式，用于匹配数据集名称
        self.formatted_date = f"{self.date_str[:4]}-{self.date_str[4:6]}-{self.date_str[6:8]}"

        # 构建本地挂载路径
        self.local_data_path = Path(OSS_MOUNT_PREFIX + self.raw_data_url)

    def run(self):
        """执行完整流程"""
        print("=" * 80)
        print("数据压缩与归档工具")
        print("=" * 80)
        print(f"[配置] 原始数据URL: {self.raw_data_url}")
        print(f"[配置] 本地数据路径: {self.local_data_path}")
        print(f"[配置] 日期: {self.date_str}")
        print(f"[配置] 车辆ID: {self.vehicle_id}")
        print("=" * 80)

        # Step 1.1: 列出子目录并创建TOML文件
        print("\n[Step 1.1] 列出子目录并创建TOML配置文件...")
        subdirs = self._list_subdirectories()
        toml_files = self._create_toml_files(subdirs)

        # 快照：记录压缩前输出目录中已有的数据集
        pre_existing = self._snapshot_existing_datasets()

        # Step 1.2: 启动压缩脚本
        print("\n[Step 1.2] 启动数据压缩脚本...")
        compression_process = self._start_compression_script()

        # 等待压缩脚本完成首次目录扫描（建立基线），再上传TOML文件
        # 否则脚本首次扫描就看到TOML文件，会将其视为"已有文件"而忽略
        print("[等待] 等待压缩脚本输出首次扫描完成...")
        self._wait_for_first_scan(compression_process)

        # Step 1.3: 上传TOML文件
        print("\n[Step 1.3] 上传TOML文件到指定目录...")
        self._upload_toml_files(toml_files)

        # Step 1.4: 监控压缩完成
        print("\n[Step 1.4] 监控数据压缩进度...")
        output_datasets = self._monitor_compression(subdirs, compression_process, pre_existing)

        # Step 1.5: 移动数据集到归档目录
        print("\n[Step 1.5] 移动数据集到归档目录...")
        archive_dir = self._move_datasets(output_datasets)

        # Step 1.6: 输出汇总信息
        print("\n[Step 1.6] 输出汇总信息...")
        self._print_summary(subdirs, output_datasets, archive_dir)

        print("\n" + "=" * 80)
        print("[完成] 数据压缩与归档流程执行完毕")
        print("=" * 80)

    def _list_subdirectories(self) -> List[str]:
        """列出原始数据目录下的所有子目录"""
        if not self.local_data_path.exists():
            raise FileNotFoundError(f"本地数据路径不存在: {self.local_data_path}")

        subdirs = []
        for item in self.local_data_path.iterdir():
            if item.is_dir():
                subdirs.append(item.name)

        if not subdirs:
            raise ValueError(f"未找到任何子目录: {self.local_data_path}")

        subdirs.sort()
        print(f"[信息] 找到 {len(subdirs)} 个子目录:")
        for i, subdir in enumerate(subdirs, 1):
            print(f"  {i}. {subdir}")

        return subdirs

    def _create_toml_files(self, subdirs: List[str]) -> List[Path]:
        """根据子目录创建TOML配置文件"""
        if not self.example_toml.exists():
            raise FileNotFoundError(f"示例TOML文件不存在: {self.example_toml}")

        # 读取示例TOML内容
        with open(self.example_toml, 'r', encoding='utf-8') as f:
            example_content = f.read()

        toml_files = []
        # 生成唯一时间戳，防止压缩脚本将同名文件视为"已处理"而忽略
        timestamp = datetime.now().strftime("%H%M%S")
        for i, subdir in enumerate(subdirs, 1):
            # 文件名带时间戳，保证每次运行都是全新的文件名
            new_filename = f"{self.date_str}_hc25_pvt1_nc_{i}_{timestamp}.toml"
            new_toml_path = self.script_dir / new_filename

            # 构建新的oss_data_url
            new_oss_url = f"oss://{self.raw_data_url}/{subdir}/"

            # 替换oss_data_url内容
            new_content = re.sub(
                r'oss_data_url\s*=\s*"[^"]*"',
                f'oss_data_url = "{new_oss_url}"',
                example_content
            )

            # 写入新TOML文件
            with open(new_toml_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            toml_files.append(new_toml_path)
            print(f"[创建] {new_filename} -> oss_data_url: {new_oss_url}")

        return toml_files

    def _start_compression_script(self) -> subprocess.Popen:
        """启动数据压缩脚本，使用行缓冲以支持实时输出"""
        if not Path(COMPRESSION_SCRIPT_PATH).exists():
            raise FileNotFoundError(f"压缩脚本不存在: {COMPRESSION_SCRIPT_PATH}")

        print(f"[启动] {COMPRESSION_SCRIPT_PATH}")
        process = subprocess.Popen(
            ['python3', '-u', COMPRESSION_SCRIPT_PATH],  # -u 禁用Python缓冲
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # 行缓冲
        )
        print(f"[信息] 压缩脚本已启动，PID: {process.pid}")

        # 启动后台线程读取stdout和stderr，防止PIPE缓冲区满导致阻塞
        self._script_output_lines = deque(maxlen=200)  # 保留最近200行输出
        self._stdout_thread = threading.Thread(
            target=self._stream_reader, args=(process.stdout, "脚本输出"), daemon=True
        )
        self._stderr_thread = threading.Thread(
            target=self._stream_reader, args=(process.stderr, "脚本错误"), daemon=True
        )
        self._stdout_thread.start()
        self._stderr_thread.start()

        return process

    def _stream_reader(self, stream, prefix: str):
        """后台线程：实时读取子进程输出流并打印"""
        try:
            for line in stream:
                line = line.rstrip('\n')
                if line:
                    msg = f"[{prefix}] {line}"
                    print(msg)
                    self._script_output_lines.append(msg)
        except Exception as e:
            print(f"[{prefix}] 读取流异常: {e}")

    def _cleanup_old_toml_files(self, toml_files: List[Path]):
        """清理上传目录中同名的旧TOML文件，确保压缩脚本能识别后续上传为新文件"""
        upload_dir = Path(TOML_UPLOAD_DIR)
        if not upload_dir.exists():
            return

        cleaned = 0
        for toml_file in toml_files:
            old_path = upload_dir / toml_file.name
            if old_path.exists():
                old_path.unlink()
                cleaned += 1
                print(f"[清理] 删除旧文件: {old_path}")

        if cleaned > 0:
            print(f"[清理] 共清理 {cleaned} 个旧TOML文件")
        else:
            print(f"[清理] 上传目录中无同名旧文件")

    def _wait_for_first_scan(self, process: subprocess.Popen):
        """等待压缩脚本输出首次扫描完成的标志，而不是盲等固定时间"""
        timeout = 60  # 最长等待 60 秒
        start = time.time()
        while time.time() - start < timeout:
            # 检查是否已看到首次扫描输出
            if hasattr(self, '_script_output_lines') and len(self._script_output_lines) > 0:
                # 看到了 "no new file uploaded!" 就说明首次扫描完成
                for line in self._script_output_lines:
                    if "no new file uploaded" in line.lower():
                        print(f"[等待] 压缩脚本已完成首次扫描，耗时 {time.time() - start:.1f} 秒")
                        # 再等 2 秒给脚本缓冲时间
                        time.sleep(2)
                        return
            time.sleep(1)
        print(f"[等待] 超时 {timeout} 秒，继续执行...")

    def _upload_toml_files(self, toml_files: List[Path]):
        """上传TOML文件到指定目录（不保留原始时间戳，确保为新文件）"""
        upload_dir = Path(TOML_UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        for toml_file in toml_files:
            dest_path = upload_dir / toml_file.name
            shutil.copy(toml_file, dest_path)  # copy而非copy2，不保留旧时间戳
            print(f"[上传] {toml_file.name} -> {dest_path}")

        print(f"[完成] 已上传 {len(toml_files)} 个TOML文件到 {TOML_UPLOAD_DIR}")

        # 删除本地临时生成的TOML文件
        for toml_file in toml_files:
            if toml_file.exists():
                toml_file.unlink()
                print(f"[清理] 已删除本地临时文件: {toml_file.name}")

    def _snapshot_existing_datasets(self) -> Set[str]:
        """快照当前输出目录中已有的数据集名称，用于排除旧数据"""
        output_dir = Path(COMPRESSION_OUTPUT_DIR)
        existing = set()
        if output_dir.exists():
            for item in output_dir.iterdir():
                if item.is_dir():
                    existing.add(item.name)
        print(f"[信息] 输出目录已有 {len(existing)} 个数据集（将排除）")
        return existing

    def _monitor_compression(self, subdirs: List[str], process: subprocess.Popen,
                              pre_existing: Set[str]) -> List[Path]:
        """监控压缩进度，返回生成的数据集路径"""
        output_dir = Path(COMPRESSION_OUTPUT_DIR)
        expected_datasets = len(subdirs)

        # 用格式化日期匹配数据集，只要文件夹名包含 YYYY-MM-DD 即可
        date_pattern = self.formatted_date  # 如 2026-04-17

        found_datasets = []
        found_names = set()  # 用名称去重
        last_count = 0
        check_count = 0

        print(f"[监控] 等待数据压缩完成，预期 {expected_datasets} 个数据集...")
        print(f"[监控] 输出目录: {COMPRESSION_OUTPUT_DIR}")
        print(f"[监控] 匹配日期: {date_pattern}")

        while True:
            # 检查进程状态
            if process.poll() is not None:
                print(f"\n[信息] 压缩脚本已结束，退出码: {process.returncode}")
                # 等待读取线程结束
                if hasattr(self, '_stdout_thread'):
                    self._stdout_thread.join(timeout=5)
                if hasattr(self, '_stderr_thread'):
                    self._stderr_thread.join(timeout=5)
                # 进程结束后做最终一次目录扫描
                self._scan_new_datasets(
                    output_dir, date_pattern, pre_existing, found_datasets, found_names
                )
                break

            # 检查输出目录中的新数据集
            self._scan_new_datasets(
                output_dir, date_pattern, pre_existing, found_datasets, found_names
            )

            if len(found_datasets) >= expected_datasets:
                print(f"\n[进度] 已找到所有 {expected_datasets} 个数据集文件夹，等待文件写入完毕...")
                self._wait_for_datasets_complete(found_datasets)
                print(f"[完成] 所有数据集文件写入稳定，终止压缩脚本")
                process.terminate()
                process.wait(timeout=10)
                print(f"[终止] 压缩脚本已终止")
                break

            # 打印进度
            if len(found_datasets) != last_count:
                last_count = len(found_datasets)
                print(f"[进度] 已找到 {len(found_datasets)}/{expected_datasets} 个数据集")

            # 定期打印心跳信息
            check_count += 1
            if check_count % 6 == 0:  # 每60秒打印一次
                elapsed = check_count * 10
                print(f"[心跳] 已等待 {elapsed} 秒，已找到 {len(found_datasets)}/{expected_datasets} 个数据集...")

            # 等待一段时间再检查
            time.sleep(10)

        # 确保找到所有数据集
        if len(found_datasets) < expected_datasets:
            print(f"[警告] 未找到全部数据集，预期 {expected_datasets}，实际 {len(found_datasets)}")
            if hasattr(self, '_script_output_lines') and self._script_output_lines:
                print(f"[警告] 压缩脚本最近输出：")
                for line in list(self._script_output_lines)[-20:]:
                    print(f"  {line}")

        return found_datasets

    def _wait_for_datasets_complete(self, datasets: List[Path],
                                     stable_seconds: int = 30,
                                     check_interval: int = 10):
        """等待数据集文件数量稳定，不再增长后认为写入完毕
        
        Args:
            datasets: 要监控的数据集路径列表
            stable_seconds: 文件数量连续稳定多少秒后认为完成（默认30秒）
            check_interval: 每次检查间隔秒数（默认10秒）
        """
        def count_files(path: Path) -> int:
            """递归统计目录下的文件数"""
            try:
                return sum(1 for f in path.rglob('*') if f.is_file())
            except Exception:
                return 0

        stable_count = 0
        required_stable_checks = stable_seconds // check_interval  # 需要连续稳定的次数
        last_counts = {d: -1 for d in datasets}

        print(f"[等待] 监控数据集文件数量，连续 {stable_seconds} 秒无变化后终止...")

        while True:
            current_counts = {d: count_files(d) for d in datasets}
            total = sum(current_counts.values())

            # 打印各数据集当前文件数
            status = ', '.join(f"{d.name}: {n}个文件" for d, n in current_counts.items())
            print(f"[等待] {status}")

            if current_counts == last_counts:
                stable_count += 1
                print(f"[等待] 文件数量稳定 {stable_count}/{required_stable_checks} 次（共{total}个文件）")
                if stable_count >= required_stable_checks:
                    print(f"[等待] 文件数量已稳定 {stable_seconds} 秒，共 {total} 个文件，写入完毕")
                    return
            else:
                stable_count = 0  # 有变化，重置计数

            last_counts = current_counts
            time.sleep(check_interval)

    def _scan_new_datasets(self, output_dir: Path, date_pattern: str,
                            pre_existing: Set[str], found_datasets: List[Path],
                            found_names: Set[str]):
        """扫描输出目录，查找新生成的包含指定日期的数据集"""
        if not output_dir.exists():
            return

        for item in output_dir.iterdir():
            if not item.is_dir():
                continue
            # 文件夹名中必须包含日期 YYYY-MM-DD
            if date_pattern not in item.name:
                continue
            # 排除压缩前已存在的数据集
            if item.name in pre_existing:
                continue
            # 去重
            if item.name in found_names:
                continue

            found_names.add(item.name)
            found_datasets.append(item)
            print(f"\n[发现] 新数据集: {item}")

    def _move_datasets(self, datasets: List[Path]) -> Path:
        """移动数据集到归档目录"""
        archive_dir = Path(ARCHIVE_BASE_DIR) / self.date_str
        archive_dir.mkdir(parents=True, exist_ok=True)

        print(f"[创建] 归档目录: {archive_dir}")

        for dataset in datasets:
            dest_path = archive_dir / dataset.name
            if dest_path.exists():
                print(f"[跳过] 目标已存在: {dest_path}")
            else:
                shutil.move(str(dataset), str(dest_path))
                print(f"[移动] {dataset.name} -> {dest_path}")

        return archive_dir

    def _print_summary(self, subdirs: List[str], datasets: List[Path], archive_dir: Path):
        """输出汇总信息"""
        print("\n" + "=" * 80)
        print("[汇总信息]")
        print("=" * 80)

        print(f"\n1. 原始数据集路径:")
        print(f"   OSS路径: oss://{self.raw_data_url}")
        print(f"   本地路径: {self.local_data_path}")

        print(f"\n2. 该目录下的所有子目录 ({len(subdirs)} 个):")
        for subdir in subdirs:
            print(f"   - {subdir}")

        print(f"\n3. 压缩完成后的子数据集 ({len(datasets)} 个):")
        for dataset in datasets:
            print(f"   - {dataset}")

        print(f"\n4. 移动到的新目录:")
        print(f"   {archive_dir}")
        if archive_dir.exists():
            for item in archive_dir.iterdir():
                if item.is_dir():
                    print(f"   - {item}")
        else:
            print(f"   [警告] 归档目录不存在")

        print("=" * 80)


def main():
    """主函数"""
    try:
        tool = DataCompressionArchive()
        tool.run()
        return 0
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())