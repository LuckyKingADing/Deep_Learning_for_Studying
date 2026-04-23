#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ref.txt (IE格式/WGS84) 转换工具

功能：
  将 IE 格式的 ref.txt 同时转换为：
    1. ref_84.txt  —— CSV格式，保留 WGS84 坐标（仅格式转换）
    2. ref_02.txt  —— CSV格式，WGS84 → GCJ-02 坐标偏移

用法：
  python convert_ref.py /path/to/ref.txt
  python convert_ref.py /path/to/ref.txt --force        # 强制覆盖已有文件
  python convert_ref.py /path/to/ref.txt --only-84      # 仅生成 ref_84.txt
  python convert_ref.py /path/to/ref.txt --only-02      # 仅生成 ref_02.txt

输出文件与 ref.txt 同目录。
"""

import argparse
import ctypes
import sys
from pathlib import Path

# ==================== 加载 libkcoords_plugin.so，直接调用 wgtochina_lb ====================

def _find_kcoords_so() -> Path:
    """在项目中搜索 libkcoords_plugin.so，返回找到的路径，找不到返回 None。"""
    script_dir = Path(__file__).resolve().parent
    # 从脚本目录向上查找到工作区根目录
    root = script_dir
    for _ in range(10):
        if (root / 'localization').exists() or (root / 'util').exists():
            break
        root = root.parent
    candidates = [
        root / 'localization/TCMSF/third_party/wgs84_to_mars/lib/x86/libkcoords_plugin.so',
        root / 'localization/TCMSF/third_party/wgs84_to_mars/lib/arm/libkcoords_plugin.so',
        root / 'util/pykit/wgs84_gcj02_convert/lib/libkcoords_plugin.so',
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _make_wgs84_to_gcj02_ctypes(so_path: Path):
    """用 ctypes 封装 wgtochina_lb，返回 wgs84_to_gcj02(lng, lat) -> (gcj02_lng, gcj02_lat)。"""
    lib = ctypes.CDLL(str(so_path))
    _fn = lib.wgtochina_lb
    _fn.restype  = ctypes.c_uint
    _fn.argtypes = [
        ctypes.c_int,    # wg_flag
        ctypes.c_double, # wg_lng
        ctypes.c_double, # wg_lat
        ctypes.c_int,    # wg_heit
        ctypes.c_int,    # wg_week
        ctypes.c_uint,   # wg_time
        ctypes.POINTER(ctypes.c_double),  # china_lng
        ctypes.POINTER(ctypes.c_double),  # china_lat
    ]
    def wgs84_to_gcj02(lng: float, lat: float):
        out_lng = ctypes.c_double(0.0)
        out_lat = ctypes.c_double(0.0)
        _fn(0, lng, lat, 0, 0, 0, ctypes.byref(out_lng), ctypes.byref(out_lat))
        return out_lng.value, out_lat.value
    return wgs84_to_gcj02


# 尝试 pybind11 封装，再尝试 ctypes，都失败则报错退出
try:
    from wgs84_gcj02_convert import wgs84_to_gcj02
    print("[信息] GCJ-02 转换后端: wgs84_gcj02_convert (pybind11)", file=sys.stderr)
except ImportError:
    _so = _find_kcoords_so()
    if _so is None:
        print("[错误] 找不到 libkcoords_plugin.so，请检查项目目录中是否存在：")
        print("       localization/TCMSF/third_party/wgs84_to_mars/lib/x86/libkcoords_plugin.so")
        sys.exit(2)
    wgs84_to_gcj02 = _make_wgs84_to_gcj02_ctypes(_so)
    print(f"[信息] GCJ-02 转换后端: ctypes -> {_so}", file=sys.stderr)


# ==================== IE 格式解析 & CSV 输出 ====================

def parse_ie_ref(ref_file: Path) -> list:
    """
    解析 IE 格式的 ref.txt，返回数据行列表。
    每个元素为 18 个字段的 list[str]。
    """
    with open(ref_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # 定位数据起始：包含 "(sec)" 的标记行（兼容含/不含 "(weeks)" 的两种格式）
    body_start = -1
    for i, line in enumerate(lines):
        if '(sec)' in line and ('(weeks)' in line or '(deg)' in line):
            body_start = i + 1
            break

    if body_start < 0:
        print(f"[错误] ref.txt 中未找到 IE 格式标记行（含 '(sec)' 的表头行）")
        return []

    records = []
    for i in range(body_start, len(lines)):
        line = lines[i].strip()
        # 空行或字段数明显不足（行长 < 50）表示数据结束
        if not line or len(line) < 50:
            break

        fields = line.split()
        if len(fields) < 17:
            print(f"[警告] 第 {i+1} 行字段数不足 17 ({len(fields)})，跳过")
            continue
        # 标准格式为 18 列（第2列为 GPS Week）；
        # 17 列格式缺少 GPS Week，在索引 1 处补 "0" 以统一后续处理
        if len(fields) == 17:
            fields.insert(1, "0")
        records.append(fields[:18])

    return records


def format_csv_line(fields: list, lat: float, lon: float) -> str:
    """
    将原始字段 + 替换后的 lat/lon 格式化为 CSV 行。
    输出格式与 convert_ie.cpp 完全一致。
    （17列格式已在 parse_ie_ref 中补齐 GPS Week 为 "0"，此处统一按 18 列处理）
    """
    return "{},{},{:>15.10f},{:>15.10f},{:>9s},{:>9s},{:>9s},{:>9s},{:>15.10f},{:>15.10f},{:>15.10f},{:>15.10f},{:>15.10f},{:>15.10f},{},{},{},{}\n".format(
        fields[0], fields[1],
        lat, lon,
        fields[4],
        fields[5], fields[6], fields[7],
        float(fields[8]), float(fields[9]),
        float(fields[10]), float(fields[11]),
        float(fields[12]), float(fields[13]),
        fields[14], fields[15], fields[16], fields[17]
    )


def generate_ref_84(records: list, output_file: Path) -> bool:
    """
    生成 ref_84.txt —— CSV 格式 / WGS84 坐标（仅格式转换，不做坐标偏移）
    """
    try:
        count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for fields in records:
                lat = float(fields[2])
                lon = float(fields[3])
                f.write(format_csv_line(fields, lat, lon))
                count += 1
        print(f"[成功] 生成 ref_84.txt ({count} 行): {output_file}")
        return True
    except Exception as e:
        print(f"[错误] 生成 ref_84.txt 失败: {e}")
        return False


def generate_ref_02(records: list, output_file: Path) -> bool:
    """
    生成 ref_02.txt —— CSV 格式 / GCJ-02 坐标（WGS84 → GCJ-02 偏移）
    注意: convert_ie.cpp 中 wgtochina_lb 参数顺序为 (0, lon, lat, alt, ...)
          返回 (gcj02_lon, gcj02_lat)，输出 CSV 列顺序为 lat, lon
    """
    try:
        count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for fields in records:
                wgs_lat = float(fields[2])
                wgs_lon = float(fields[3])
                wgs_alt = float(fields[4]) if fields[4].replace('.', '').replace('-', '').isdigit() else 0

                # 与 convert_ie.cpp 一致: wgtochina_lb(0, lon, lat, alt, 0, 0, ...)
                gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)

                f.write(format_csv_line(fields, gcj_lat, gcj_lon))
                count += 1
        print(f"[成功] 生成 ref_02.txt ({count} 行, C++ wgtochina_lb): {output_file}")
        return True
    except Exception as e:
        print(f"[错误] 生成 ref_02.txt 失败: {e}")
        return False


# ==================== gnss.csv → gnss_02.csv ====================

# gnss.csv 中经纬度列的列索引（0-based）
_GNSS_LON_COL = 3   # lon(deg)
_GNSS_LAT_COL = 4   # lat(deg)


def convert_gnss_csv(input_file: Path, output_file: Path) -> bool:
    """
    将 gnss.csv（WGS84）转换为 gnss_02.csv（GCJ-02）。

    格式要求（标准表头）：
        gps_week,sec_in_gps_week(s),timestamp,lon(deg),lat(deg),alt,...

    仅替换第 {_GNSS_LON_COL} 列（lon）和第 {_GNSS_LAT_COL} 列（lat），其余列保持不变。
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[错误] 读取文件失败: {e}")
        return False

    if not lines:
        print("[错误] 文件为空")
        return False

    out_lines = [lines[0]]  # 保留原始表头
    converted = 0
    skipped = 0

    for lineno, line in enumerate(lines[1:], start=2):
        stripped = line.rstrip("\n")
        if not stripped.strip():
            out_lines.append(line)
            continue

        fields = stripped.split(",")
        if len(fields) <= max(_GNSS_LON_COL, _GNSS_LAT_COL):
            out_lines.append(line)
            skipped += 1
            continue

        try:
            lon = float(fields[_GNSS_LON_COL])
            lat = float(fields[_GNSS_LAT_COL])
        except ValueError:
            out_lines.append(line)
            skipped += 1
            continue

        gcj_lon, gcj_lat = wgs84_to_gcj02(lon, lat)
        fields[_GNSS_LON_COL] = f"{gcj_lon:.10f}"
        fields[_GNSS_LAT_COL] = f"{gcj_lat:.10f}"
        out_lines.append(",".join(fields) + "\n")
        converted += 1

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(out_lines)
    except Exception as e:
        print(f"[错误] 写入文件失败: {e}")
        return False

    print(f"[成功] gnss_02.csv 已写入: {output_file}")
    print(f"[信息] 转换记录数: {converted}，跳过行数: {skipped}")
    return True


def _is_gnss_csv(file_path: Path) -> bool:
    """检测文件是否为 gnss.csv 格式（首行含 gps_week 表头）。"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()
        return first_line.startswith("gps_week")
    except Exception:
        return False


# ==================== 主入口 ====================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "坐标转换工具：\n"
            "  • ref.txt (IE格式/WGS84)  → ref_84.txt (CSV/WGS84) + ref_02.txt (CSV/GCJ-02)\n"
            "  • gnss.csv (CSV/WGS84)    → gnss_02.csv (CSV/GCJ-02)\n"
            "\n"
            "文件类型根据首行内容自动识别，无需额外参数。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python convert_ref.py /data/20260324/ref.txt\n"
            "  python convert_ref.py /data/20260324/ref.txt --force\n"
            "  python convert_ref.py /data/20260324/ref.txt --only-84\n"
            "  python convert_ref.py /data/20260324/ref.txt --only-02\n"
            "  python convert_ref.py /data/20260324/gnss.csv\n"
            "  python convert_ref.py /data/20260324/gnss.csv --force\n"
        ),
    )
    parser.add_argument("ref_file", type=str, help="输入文件路径（ref.txt 或 gnss.csv）")
    parser.add_argument("--force", action="store_true", help="强制覆盖已有的输出文件")
    parser.add_argument("--only-84", action="store_true", dest="only_84", help="[ref.txt模式] 仅生成 ref_84.txt")
    parser.add_argument("--only-02", action="store_true", dest="only_02", help="[ref.txt模式] 仅生成 ref_02.txt")
    args = parser.parse_args()

    input_path = Path(args.ref_file).resolve()
    if not input_path.exists():
        print(f"[错误] 找不到文件: {input_path}")
        sys.exit(1)
    if not input_path.is_file():
        print(f"[错误] 不是文件: {input_path}")
        sys.exit(1)

    # ── 自动识别文件类型 ────────────────────────────────────────────────
    if _is_gnss_csv(input_path):
        # gnss.csv 模式：输出文件名 = 原文件名（去掉.csv）+ _02.csv
        # 例: gnss.csv -> gnss_02.csv, gnss1.csv -> gnss1_02.csv
        out_path = input_path.parent / (input_path.stem + "_02.csv")
        if out_path.exists() and not args.force:
            print(f"[跳过] gnss_02.csv 已存在: {out_path} (使用 --force 覆盖)")
            sys.exit(0)
        print(f"[信息] 识别为 gnss.csv 格式，输入: {input_path}")
        if not convert_gnss_csv(input_path, out_path):
            sys.exit(1)
        return

    # ── ref.txt 模式 ────────────────────────────────────────────────────
    out_dir = input_path.parent
    ref_84_path = out_dir / "ref_84.txt"
    ref_02_path = out_dir / "ref_02.txt"

    gen_84 = not args.only_02
    gen_02 = not args.only_84

    if not args.force:
        if gen_84 and ref_84_path.exists():
            print(f"[跳过] ref_84.txt 已存在: {ref_84_path} (使用 --force 覆盖)")
            gen_84 = False
        if gen_02 and ref_02_path.exists():
            print(f"[跳过] ref_02.txt 已存在: {ref_02_path} (使用 --force 覆盖)")
            gen_02 = False

    if not gen_84 and not gen_02:
        print("[信息] 无需生成任何文件")
        sys.exit(0)

    print(f"[信息] 识别为 ref.txt (IE) 格式，输入: {input_path}")
    records = parse_ie_ref(input_path)
    if not records:
        print("[错误] 未从 ref.txt 中提取到有效数据")
        sys.exit(1)
    print(f"[信息] 解析到 {len(records)} 条数据记录")

    success = True
    if gen_84:
        if not generate_ref_84(records, ref_84_path):
            success = False
    if gen_02:
        if not generate_ref_02(records, ref_02_path):
            success = False

    if success:
        print("[完成] 所有转换成功")
    else:
        print("[警告] 部分转换失败，请检查上方日志")
        sys.exit(1)


if __name__ == "__main__":
    main()
