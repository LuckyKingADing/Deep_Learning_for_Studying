#!/usr/bin/env python3
"""
Localization Initialization Testing Framework
=============================================
测试 localization 模块的初始化耗时和成功率。

Usage:
    python test_runner.py --records /path/to/records/ --output /path/to/output/ --module tcmsf
    python test_runner.py --records /path/to/records/ --output /path/to/output/ --module dr
    python test_runner.py --records /path/to/records/ --output /path/to/output/ --module both
"""

import argparse
import os
import sys
import subprocess
import json
import time
import re
import glob
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import multiprocessing


@dataclass
class TestCase:
    name: str
    record_path: str
    module: str
    output_dir: str
    config_path: Optional[str] = None
    timeout: int = 300


@dataclass
class InitTimingResult:
    """单次测试的初始化耗时结果"""
    case_name: str
    record_path: str
    module: str
    success: bool
    error_message: str = ""

    # 初始化阶段耗时
    init_start_to_end_ms: float = -1.0
    config_parse_ms: float = -1.0
    iif_create_ms: float = -1.0
    tcmsf_create_ms: float = -1.0
    callbacks_register_ms: float = -1.0
    readers_create_ms: float = -1.0
    writers_create_ms: float = -1.0
    fusion_daemon_start_ms: float = -1.0

    # 传感器数据到达耗时
    first_imu_to_first_output_ms: float = -1.0
    first_gps_to_first_output_ms: float = -1.0
    first_veh_to_first_output_ms: float = -1.0
    first_valid_imu_to_first_output_ms: float = -1.0
    first_valid_gps_to_first_output_ms: float = -1.0
    first_valid_rtk_to_first_output_ms: float = -1.0
    first_valid_rtk_arrival_ms: float = -1.0

    # MSF 状态耗时
    msf_ready_ms: float = -1.0
    msf_aligned_ms: float = -1.0
    msf_ready_reached: bool = False
    msf_aligned_reached: bool = False
    fusion_status_at_first_output: int = -1
    align_status_at_first_output: int = -1

    # DR 特有
    dr_first_output_ms: float = -1.0

    # 测试执行信息
    test_start_time: str = ""
    test_end_time: str = ""
    test_duration_s: float = 0.0
    first_output_timestamp: float = -1.0
    log_output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class InitTimingParser:
    """解析 localization 模块输出的初始化耗时日志"""

    # TCMSF Component 日志格式
    TCMSF_INIT_PATTERNS = {
        "component_start": r"TCMSF daemon thread started!",
        "first_output": r"\[INIT-TIMING\] First MSF output at\s+([0-9.]+)\s*ms from start",
        "msf_ready": r"\[INIT-TIMING\] MSF Ready! duration:([0-9.]+)ms from start",
        "msf_aligned": r"\[INIT-TIMING\] MSF ALIGNED! duration:([0-9.]+)ms from start",
        "fusion_status": r"fusion_status:(\d+)",
        "align_status": r"align_status:(\d+)",
    }

    # DR Component 日志格式
    DR_INIT_PATTERNS = {
        "init_complete": r"\[INIT-TIMING\] DR Init complete in\s+([0-9.]+)ms",
        "config_parse": r"config:([0-9.]+)ms",
        "callbacks_register": r"cbs:([0-9.]+)ms",
        "readers_create": r"readers:([0-9.]+)ms",
        "writers_create": r"writers:([0-9.]+)ms",
        "first_output": r"\[INIT-TIMING\] DR first output.*imu->out:([0-9.]+)ms.*gps->out:([0-9.]+)ms.*veh->out:([0-9.]+)ms",
    }

    # 通用传感器日志格式
    SENSOR_PATTERNS = {
        "first_imu": r"get imu msg",
        "first_gps": r"get gnss msg",
        "first_veh": r"get vehicle msg",
        "first_valid_imu": r"imu status ok",
        "first_valid_rtk": r"RTK FIX|rtk fix|position_status.*6",
    }

    @classmethod
    def parse_tcmsf_log(cls, log_text: str) -> Dict[str, Any]:
        result = {}

        for key, pattern in cls.TCMSF_INIT_PATTERNS.items():
            matches = re.findall(pattern, log_text)
            if matches:
                result[key] = matches[-1] if isinstance(matches[0], str) else matches[-1]

        return result

    @classmethod
    def parse_dr_log(cls, log_text: str) -> Dict[str, Any]:
        result = {}

        init_complete_match = re.search(
            r"\[INIT-TIMING\] DR Init complete in\s+([0-9.]+)ms.*?"
            r"config:([0-9.]+)ms.*?"
            r"cbs:([0-9.]+)ms.*?"
            r"readers:([0-9.]+)ms.*?"
            r"writers:([0-9.]+)ms",
            log_text, re.DOTALL
        )
        if init_complete_match:
            result["init_complete"] = float(init_complete_match.group(1))
            result["config_parse"] = float(init_complete_match.group(2))
            result["callbacks_register"] = float(init_complete_match.group(3))
            result["readers_create"] = float(init_complete_match.group(4))
            result["writers_create"] = float(init_complete_match.group(5))

        first_output_match = re.search(
            r"\[INIT-TIMING\] DR first output.*?"
            r"init:([0-9.]+)ms.*?"
            r"imu->out:([0-9.]+)ms.*?"
            r"gps->out:([0-9.]+)ms.*?"
            r"veh->out:([0-9.]+)ms",
            log_text, re.DOTALL
        )
        if first_output_match:
            result["first_output"] = {
                "init_ms": float(first_output_match.group(1)),
                "imu_to_out_ms": float(first_output_match.group(2)),
                "gps_to_out_ms": float(first_output_match.group(3)),
                "veh_to_out_ms": float(first_output_match.group(4)),
            }

        return result

    @classmethod
    def parse_log(cls, log_text: str, module: str) -> Dict[str, Any]:
        if module == "tcmsf":
            return cls.parse_tcmsf_log(log_text)
        elif module == "dr":
            return cls.parse_dr_log(log_text)
        return {}


def run_single_test(test_case: TestCase, verbose: bool = False) -> InitTimingResult:
    """运行单个测试用例"""
    result = InitTimingResult(
        case_name=test_case.name,
        record_path=test_case.record_path,
        module=test_case.module,
        success=False,
        test_start_time=datetime.now().isoformat(),
    )

    if not os.path.exists(test_case.record_path):
        result.error_message = f"Record file not found: {test_case.record_path}"
        return result

    output_case_dir = os.path.join(test_case.output_dir, test_case.name)
    os.makedirs(output_case_dir, exist_ok=True)

    log_file = os.path.join(output_case_dir, "test_output.log")

    binary_path = None
    if test_case.module == "tcmsf":
        binary_path = os.environ.get("TCMSF_BINARY", "TCMSF")
    elif test_case.module == "dr":
        binary_path = os.environ.get("DR_BINARY", "DR")

    cmd = []
    if test_case.module == "tcmsf":
        cmd = [binary_path, test_case.record_path, output_case_dir]
        if test_case.config_path:
            cmd.append(test_case.config_path)
    elif test_case.module == "dr":
        cmd = [binary_path, test_case.record_path, output_case_dir]

    if verbose:
        print(f"  Running: {' '.join(cmd)}")

    start_time = time.time()
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_lines = []
        for line in proc.stdout:
            output_lines.append(line)
            if verbose:
                print(f"    {line.rstrip()}")

        proc.wait(timeout=test_case.timeout)
        elapsed = time.time() - start_time

        result.test_end_time = datetime.now().isoformat()
        result.test_duration_s = elapsed

        log_content = "".join(output_lines)
        result.log_output = log_content

        with open(log_file, "w") as f:
            f.write(log_content)

        parsed = InitTimingParser.parse_log(log_content, test_case.module)
        result.success = proc.returncode == 0

        if test_case.module == "tcmsf":
            _fill_tcmsf_result(result, parsed, log_content)
        elif test_case.module == "dr":
            _fill_dr_result(result, parsed)

        if not result.success and not result.error_message:
            result.error_message = f"Process exited with code {proc.returncode}"

    except subprocess.TimeoutExpired:
        proc.kill()
        result.error_message = f"Test timeout after {test_case.timeout}s"
        result.test_end_time = datetime.now().isoformat()
        result.test_duration_s = time.time() - start_time
    except Exception as e:
        result.error_message = f"Exception: {str(e)}"
        result.test_end_time = datetime.now().isoformat()
        result.test_duration_s = time.time() - start_time

    return result


def _fill_tcmsf_result(result: InitTimingResult, parsed: Dict[str, Any], log_text: str):
    result.init_start_to_end_ms = parsed.get("component_start", -1.0)

    first_output = parsed.get("first_output")
    if first_output:
        if isinstance(first_output, dict):
            result.first_imu_to_first_output_ms = float(first_output.get("imu_to_out", -1))
            result.first_gps_to_first_output_ms = float(first_output.get("gps_to_out", -1))
        else:
            result.init_start_to_end_ms = float(first_output)

    if "msf_ready" in parsed:
        result.msf_ready_ms = float(parsed["msf_ready"])
        result.msf_ready_reached = True

    if "msf_aligned" in parsed:
        result.msf_aligned_ms = float(parsed["msf_aligned"])
        result.msf_aligned_reached = True

    if "fusion_status" in parsed:
        result.fusion_status_at_first_output = int(parsed["fusion_status"])
    if "align_status" in parsed:
        result.align_status_at_first_output = int(parsed["align_status"])

    rtk_match = re.search(r"\[INIT-TIMING\].*?gps_to_out:([0-9.]+)ms", log_text)
    if rtk_match:
        result.first_valid_gps_to_first_output_ms = float(rtk_match.group(1))


def _fill_dr_result(result: InitTimingResult, parsed: Dict[str, Any]):
    result.init_start_to_end_ms = parsed.get("init_complete", -1.0)
    result.config_parse_ms = parsed.get("config_parse", -1.0)
    result.callbacks_register_ms = parsed.get("callbacks_register", -1.0)
    result.readers_create_ms = parsed.get("readers_create", -1.0)
    result.writers_create_ms = parsed.get("writers_create", -1.0)

    first_output = parsed.get("first_output")
    if first_output:
        result.dr_first_output_ms = first_output.get("imu_to_out_ms", -1.0)
        result.first_imu_to_first_output_ms = first_output.get("imu_to_out_ms", -1.0)
        result.first_gps_to_first_output_ms = first_output.get("gps_to_out_ms", -1.0)
        result.first_veh_to_first_output_ms = first_output.get("veh_to_out_ms", -1.0)


def discover_records(records_path: str) -> List[str]:
    """发现记录文件"""
    path = Path(records_path)
    records = []

    if path.is_file():
        records = [str(path)]
    elif path.is_dir():
        for ext in ["*/*.record", "*/*.db", "*.record", "*.db"]:
            records.extend(glob.glob(str(path / ext)))
        if not records:
            records.extend(glob.glob(str(path / "**" / "*"), recursive=True))
            records = [r for r in records if os.path.isfile(r)]
        records.sort()

    return records


def run_tests(
    test_cases: List[TestCase],
    output_dir: str,
    parallel: int = 1,
    verbose: bool = False,
) -> List[InitTimingResult]:
    """运行所有测试用例"""
    os.makedirs(output_dir, exist_ok=True)

    all_results = []

    if parallel > 1:
        with multiprocessing.Pool(processes=parallel) as pool:
            futures = []
            for tc in test_cases:
                future = pool.apply_async(run_single_test, (tc, verbose))
                futures.append((tc, future))

            for tc, future in futures:
                print(f"  Waiting for: {tc.name}...")
                result = future.get()
                all_results.append(result)
                _print_result_summary(result)
    else:
        for tc in test_cases:
            print(f"  Running: {tc.name} ({tc.module})...")
            result = run_single_test(tc, verbose)
            all_results.append(result)
            _print_result_summary(result)

    return all_results


def _print_result_summary(result: InitTimingResult):
    status = "PASS" if result.success else "FAIL"
    if result.module == "tcmsf":
        ready = "READY" if result.msf_ready_reached else "NOT_READY"
        aligned = "ALIGNED" if result.msf_aligned_reached else "NOT_ALIGNED"
        print(f"    [{status}] init={result.init_start_to_end_ms:.1f}ms "
              f"msf_ready={result.msf_ready_ms:.1f}ms ({ready}) "
              f"aligned={result.msf_aligned_ms:.1f}ms ({aligned})")
    elif result.module == "dr":
        print(f"    [{status}] init={result.init_start_to_end_ms:.1f}ms "
              f"first_output={result.dr_first_output_ms:.1f}ms")


def save_results(results: List[InitTimingResult], output_dir: str):
    """保存测试结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary_file = os.path.join(output_dir, f"init_test_summary_{timestamp}.json")
    with open(summary_file, "w") as f:
        json.dump([r.to_dict() for r in results], f, indent=2, default=str)

    csv_file = os.path.join(output_dir, f"init_test_results_{timestamp}.csv")
    if results:
        import csv
        keys = list(results[0].to_dict().keys())
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in results:
                row = r.to_dict()
                for k, v in row.items():
                    if isinstance(v, (list, dict)):
                        row[k] = str(v)
                writer.writerow(row)

    print(f"\n  Results saved to:")
    print(f"    {summary_file}")
    print(f"    {csv_file}")

    return summary_file, csv_file


def main():
    parser = argparse.ArgumentParser(
        description="Localization Initialization Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py --records ./data/records/ --output ./results/ --module tcmsf
  python test_runner.py --records ./data/records/ --output ./results/ --module dr
  python test_runner.py --records ./data/records/ --output ./results/ --module both
  python test_runner.py --records ./data/records/ --output ./results/ --module tcmsf --parallel 4
  python test_runner.py --records ./data/single.record --output ./results/ --module tcmsf --name test_001
        """
    )
    parser.add_argument("--records", required=True, help="Record file or directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--module", required=True, choices=["tcmsf", "dr", "both"],
                        help="Module to test")
    parser.add_argument("--config", help="IMU config path for TCMSF")
    parser.add_argument("--name", help="Custom test name prefix")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout per test (seconds)")
    parser.add_argument("--parallel", type=int, default=1, help="Number of parallel tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip tests with existing output")

    args = parser.parse_args()

    records = discover_records(args.records)
    if not records:
        print(f"Error: No record files found in {args.records}")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"Localization Initialization Test")
    print(f"{'='*70}")
    print(f"  Records found: {len(records)}")
    print(f"  Output: {args.output}")
    print(f"  Module: {args.module}")
    print(f"  Parallel: {args.parallel}")
    print(f"{'='*70}\n")

    test_cases = []
    modules = ["tcmsf", "dr"] if args.module == "both" else [args.module]

    for rec in records:
        rec_name = os.path.basename(os.path.dirname(rec)) + "_" + os.path.splitext(os.path.basename(rec))[0]
        if args.name:
            rec_name = f"{args.name}_{rec_name}"

        for mod in modules:
            tc = TestCase(
                name=f"{rec_name}_{mod}",
                record_path=rec,
                module=mod,
                output_dir=args.output,
                config_path=args.config,
                timeout=args.timeout,
            )
            test_cases.append(tc)

    results = run_tests(test_cases, args.output, args.parallel, args.verbose)

    summary_file, csv_file = save_results(results, args.output)

    total = len(results)
    success_count = sum(1 for r in results if r.success)
    msf_ready_count = sum(1 for r in results if r.msf_ready_reached)
    msf_aligned_count = sum(1 for r in results if r.msf_aligned_reached)

    print(f"\n{'='*70}")
    print(f"Test Summary")
    print(f"{'='*70}")
    print(f"  Total tests: {total}")
    print(f"  Process success: {success_count}/{total} ({100*success_count/total:.1f}%)")
    if modules == ["tcmsf"] or args.module == "both":
        print(f"  MSF ready: {msf_ready_count}/{total} ({100*msf_ready_count/total:.1f}%)")
        print(f"  MSF aligned: {msf_aligned_count}/{total} ({100*msf_aligned_count/total:.1f}%)")
    print(f"{'='*70}\n")

    if success_count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
