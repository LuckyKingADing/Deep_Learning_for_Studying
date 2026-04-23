#!/usr/bin/env python3
"""
批量运行 precision_head_topic_ref_100c_wdh_main.py 的脚本

功能:
- 扫描指定目录下的所有数据集子目录
- 为每个数据集自动生成配置文件
- 配置文件中的 ref_02 和 time_ranges 路径指向原始数据集下的文件
- 依次运行每个配置文件
- 记录运行日志和结果

使用方法:
    python batch_run_precision_head_horizontal.py <tcmsf_output_directory> <original_data_directory>
    python batch_run_precision_head_horizontal.py <tcmsf_output_directory> <original_data_directory> --pvtlc-pattern <pattern> --rtklc-pattern <pattern>

参数:
    tcmsf_output_directory: batch_run_tcmsf.py 的输出目录（包含各数据集的处理结果）
    original_data_directory: 原始数据集路径（包含 ref_02.txt 和 time_ranges 配置）
    --pvtlc-pattern: 用于查找 PVT LC 文件夹的模式字符串（默认: 'pvtlc'）
    --rtklc-pattern: 用于查找 RTK LC 文件夹的模式字符串（默认: 'rtklc'）
    --gnss-subdir: GNSS数据子目录（默认: 'topic_parse'）
    --gnss-filename: GNSS数据文件名（默认: 'gnss.csv'）
    --gnss-pos-index-1: GNSS位置索引1，对应gnssindex[7]（默认: 12）
    --gnss-pos-index-2: GNSS位置索引2，对应gnssindex[8]（默认: 13）
    --gnss-pos-index-3: GNSS位置索引3，对应gnssindex[9]（默认: 4）
    --lc-label: LC标签（默认: 'LC'）
    --tc-label: TC标签（默认: 'TC'）
    --gnss-label: GNSS标签（默认: 'RTK'）
    --skip-gap-detection: 跳过连续性检测，直接进行精度评估
    --gap-threshold: 大段缺失阈值秒数（默认: 5.0）

流程说明:
    1. 遍历 tcmsf_output_directory 下的所有数据集子目录
    1b. 为每个数据集运行 gap_detection.py（除非 --skip-gap-detection）
    2. 为每个数据集生成配置文件（从 original_data_directory 读取 ref_02 和 time_ranges）
    3. 运行精度评估脚本
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import argparse
from pathlib import Path
import shutil
import toml


def run_single_config(config_path, script_path, log_dir, dataset_name=None):
    """
    运行单个配置文件
    
    Args:
        config_path: 配置文件路径
        script_path: 评估脚本路径
        log_dir: 日志目录
        dataset_name: 数据集名称，如20260227
    
    Returns:
        success: 是否成功
        duration: 运行耗时（秒）
    """
    config_name = os.path.basename(config_path)
    # 使用数据集名称作为日志前缀，避免所有配置文件同名导致日志覆盖
    log_prefix = dataset_name if dataset_name else config_name
    print(f"\n{'='*80}")
    print(f"开始运行配置文件: {config_name}")
    print(f"{'='*80}")
    
    # 创建日志文件（以数据集名称命名，确保唯一）
    log_file = os.path.join(log_dir, f"{log_prefix}.log")
    error_log_file = os.path.join(log_dir, f"{log_prefix}_error.log")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 运行脚本，将输出重定向到日志文件
        with open(log_file, 'w', encoding='utf-8') as f_out, \
             open(error_log_file, 'w', encoding='utf-8') as f_err:
            
            process = subprocess.Popen(
                [sys.executable, script_path, config_path],
                stdout=f_out,
                stderr=f_err,
                text=True
            )
            
            # 等待进程完成
            return_code = process.wait()
            
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        if return_code == 0:
            print(f"✓ {config_name} 运行成功 (耗时: {duration:.2f}秒)")
            return True, duration
        else:
            print(f"✗ {config_name} 运行失败 (返回码: {return_code}, 耗时: {duration:.2f}秒)")
            print(f"  日志文件: {log_file}")
            print(f"  错误日志: {error_log_file}")
            # 打印错误日志内容以便快速定位问题
            try:
                with open(error_log_file, 'r', encoding='utf-8') as f_err_read:
                    err_content = f_err_read.read().strip()
                if err_content:
                    print(f"  --- 错误日志内容 ---")
                    # 只打印最后30行避免过多输出
                    err_lines = err_content.split('\n')
                    if len(err_lines) > 30:
                        print(f"  (仅显示最后30行，共{len(err_lines)}行)")
                        err_lines = err_lines[-30:]
                    for line in err_lines:
                        print(f"  | {line}")
                    print(f"  --- 错误日志结束 ---")
                else:
                    # 错误日志为空，尝试读取标准输出日志的最后几行
                    with open(log_file, 'r', encoding='utf-8') as f_log_read:
                        log_content = f_log_read.read().strip()
                    if log_content:
                        log_lines = log_content.split('\n')
                        tail_lines = log_lines[-20:] if len(log_lines) > 20 else log_lines
                        print(f"  --- 标准输出日志(最后{len(tail_lines)}行) ---")
                        for line in tail_lines:
                            print(f"  | {line}")
                        print(f"  --- 标准输出日志结束 ---")
            except Exception:
                pass
            return False, duration
            
    except Exception as e:
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✗ {config_name} 运行异常: {str(e)} (耗时: {duration:.2f}秒)")
        return False, duration


def find_dataset_directories(tcmsf_output_dir):
    """
    查找 TCMSF 输出目录下的所有数据集子目录
    
    Args:
        tcmsf_output_dir: TCMSF 输出目录
    
    Returns:
        dataset_dirs: 数据集目录列表
    """
    dataset_dirs = []
    
    if not os.path.isdir(tcmsf_output_dir):
        print(f"错误: 目录不存在: {tcmsf_output_dir}")
        return dataset_dirs
    
    # 遍历目录，找到所有包含 topic_parse 子目录的目录
    for item in os.listdir(tcmsf_output_dir):
        item_path = os.path.join(tcmsf_output_dir, item)
        if os.path.isdir(item_path) and not item.startswith('.') and item != 'batch_run_logs':
            # 检查是否包含 topic_parse 目录
            topic_parse_dir = os.path.join(item_path, 'topic_parse')
            if os.path.isdir(topic_parse_dir):
                dataset_dirs.append(item_path)
    
    return dataset_dirs


def generate_config_file(dataset_dir, original_data_dir, config_template_path=None, 
                        pvtlc_pattern='pvtlc', rtklc_pattern='rtklc',
                        gnss_subdir='topic_parse', gnss_filename='gnss.csv',
                        gnss_pos_index_1=12, gnss_pos_index_2=13, gnss_pos_index_3=4,
                        lc_label='LC', tc_label='TC', gnss_label='RTK',
                        horizontal_only=1):
    """
    为数据集生成配置文件
    
    Args:
        dataset_dir: 数据集目录（TCMSF 输出）
        original_data_dir: 原始数据集目录（包含 ref_02.txt 和 time_ranges 配置）
        config_template_path: 配置文件模板路径（可选）
        pvtlc_pattern: 用于查找 PVT LC 文件夹的模式字符串（默认: 'pvtlc'）
        rtklc_pattern: 用于查找 RTK LC 文件夹的模式字符串（默认: 'rtklc'）
        gnss_subdir: GNSS数据子目录（默认: 'topic_parse'）
        gnss_filename: GNSS数据文件名（默认: 'gnss.csv'）
        gnss_pos_index_1: GNSS位置索引1，对应gnssindex[7]（默认: 12）
        gnss_pos_index_2: GNSS位置索引2，对应gnssindex[8]（默认: 13）
        gnss_pos_index_3: GNSS位置索引3，对应gnssindex[9]（默认: 4）
        lc_label: LC标签（默认: 'LC'）
        tc_label: TC标签（默认: 'TC'）
        gnss_label: GNSS标签（默认: 'RTK'）
        horizontal_only: 是否只评估水平误差（1=仅水平，0=水平和垂直，默认: 1）
    
    Returns:
        config_path: 生成的配置文件路径
        success: 是否成功
    """
    dataset_name = os.path.basename(dataset_dir)
    
    # 确定配置文件路径（放在数据集目录下）
    config_path = os.path.join(dataset_dir, 'precision_head_topic_ref_100c_wdh_config.toml')
    
    # 查找原始数据集目录
    original_dataset_dir = os.path.join(original_data_dir, dataset_name)
    dataset_parent_dir = None  # dataset级别的中间目录（如 .../20260324/）
    if not os.path.isdir(original_dataset_dir):
        # multi-dataset模式：数据集可能在 original_data_dir 的子目录中
        # 例如: original_data_dir/20260324/2026-03-24_11-52-51
        found = False
        try:
            for subdir in sorted(os.listdir(original_data_dir)):
                subdir_path = os.path.join(original_data_dir, subdir)
                if os.path.isdir(subdir_path):
                    candidate = os.path.join(subdir_path, dataset_name)
                    if os.path.isdir(candidate):
                        original_dataset_dir = candidate
                        dataset_parent_dir = subdir_path
                        print(f"  在子目录中找到原始数据集: {original_dataset_dir}")
                        found = True
                        break
        except OSError:
            pass
        if not found:
            print(f"  警告: 原始数据集目录不存在: {original_dataset_dir}")
            print(f"  将尝试在原始数据集根目录查找 ref_02.txt 和 time_ranges 配置")
            original_dataset_dir = original_data_dir
    
    # 读取 ref_type 标记文件（由 batch_run_tcmsf.py 写入）
    ref_type = 'gcj02'  # 默认
    ref_type_marker = os.path.join(dataset_dir, '.ref_type')
    if os.path.exists(ref_type_marker):
        try:
            with open(ref_type_marker, 'r') as f:
                ref_type = f.read().strip()
            print(f"  参考坐标类型: {ref_type}")
        except Exception as e:
            print(f"  警告: 读取ref_type标记失败: {e}，使用默认值: gcj02")
    else:
        print(f"  未找到ref_type标记文件，使用默认值: gcj02")
    
    # 查找参考文件
    # ref_type="wgs84" 时优先使用 ref_84.txt（CSV格式/WGS84坐标，由batch_run_tcmsf生成）
    # ref_type="gcj02" 时优先使用 ref_02.txt（CSV格式/GCJ-02坐标）
    # 搜索路径: 子数据集目录 → dataset父目录 → 根目录
    search_dirs = [original_dataset_dir]
    if dataset_parent_dir:
        search_dirs.append(dataset_parent_dir)
    search_dirs.append(original_data_dir)
    
    ref_candidates = []
    for search_dir in search_dirs:
        if ref_type == 'wgs84':
            # WGS84模式: ref_84.txt（CSV/WGS84）优先，fallback到ref_02.txt
            ref_candidates.append(os.path.join(search_dir, 'ref_84.txt'))
            ref_candidates.append(os.path.join(search_dir, 'ref_02.txt'))
        else:
            # GCJ-02模式(默认): ref_02.txt 优先
            ref_candidates.append(os.path.join(search_dir, 'ref_02.txt'))
            ref_candidates.append(os.path.join(search_dir, 'ref_84.txt'))
    
    ref_02_path = None
    for candidate in ref_candidates:
        if os.path.exists(candidate):
            ref_02_path = candidate
            if candidate.endswith('ref_84.txt'):
                print(f"  使用 WGS84 参考文件(CSV): {candidate}")
            elif candidate.endswith('ref_02.txt'):
                print(f"  使用 GCJ-02 参考文件: {candidate}")
            else:
                print(f"  使用参考文件: {candidate}")
            break
    
    if ref_02_path is None:
        print(f"  错误: 未找到参考文件 (ref_84.txt, ref_02.txt)")
        print(f"  已搜索路径: {ref_candidates}")
        return None, False
    
    # 查找 time_ranges 配置文件
    # 优先级顺序:
    # 1. original_dataset_dir/time_ranges.toml (原始数据集目录下的 time_ranges.toml)
    # 2. original_data_dir/time_ranges.toml (原始数据根目录下的 time_ranges.toml)
    # 3. original_dataset_dir/precision_head_topic_ref_100c_wdh_config.toml (从完整配置文件中提取)
    # 4. original_data_dir/precision_head_topic_ref_100c_wdh_config.toml (从根目录配置文件中提取)
    time_ranges_candidates = [
        ('数据集目录', os.path.join(original_dataset_dir, 'time_ranges.toml')),
    ]
    if dataset_parent_dir:
        time_ranges_candidates.append(
            ('dataset父目录', os.path.join(dataset_parent_dir, 'time_ranges.toml'))
        )
    time_ranges_candidates.extend([
        ('根目录', os.path.join(original_data_dir, 'time_ranges.toml')),
        ('数据集配置文件', os.path.join(original_dataset_dir, 'precision_head_topic_ref_100c_wdh_config.toml')),
    ])
    if dataset_parent_dir:
        time_ranges_candidates.append(
            ('dataset父目录配置文件', os.path.join(dataset_parent_dir, 'precision_head_topic_ref_100c_wdh_config.toml'))
        )
    time_ranges_candidates.append(
        ('根目录配置文件', os.path.join(original_data_dir, 'precision_head_topic_ref_100c_wdh_config.toml'))
    )
    time_ranges_config = None
    time_ranges_source = None
    
    for source_name, candidate in time_ranges_candidates:
        if os.path.exists(candidate):
            try:
                with open(candidate, 'r', encoding='utf-8') as f:
                    config_data = toml.load(f)
                    if 'time_ranges' in config_data:
                        time_ranges_config = config_data['time_ranges']
                        time_ranges_source = source_name
                        print(f"  ✓ 从 {source_name} 读取 time_ranges 配置: {candidate}")
                        break
            except Exception as e:
                print(f"  警告: 读取配置文件失败: {candidate}, 错误: {e}")
                continue
    
    # 如果没有找到 time_ranges 配置，使用默认配置
    if time_ranges_config is None:
        print(f"  警告: 未找到 time_ranges 配置文件，使用默认配置")
        print(f"  已搜索路径:")
        for source_name, candidate in time_ranges_candidates:
            print(f"    - {source_name}: {candidate}")
        time_ranges_config = {
            'type_config': [
                {
                    'type_label': 'All',
                    'type_time_range': [[-1, -1]]
                }
            ]
        }
    
    # 动态查找包含 pvtlc_pattern 和 rtklc_pattern 的文件夹名
    lcver = None
    tcver = None
    
    # 查找包含 pvtlc_pattern 的文件夹（用于 lcver）
    if os.path.isdir(dataset_dir):
        for item in os.listdir(dataset_dir):
            item_path = os.path.join(dataset_dir, item)
            if os.path.isdir(item_path) and pvtlc_pattern.lower() in item.lower():
                lcver = item
                print(f"  找到包含 '{pvtlc_pattern}' 的文件夹: {lcver}")
                break
    
    # 查找包含 rtklc_pattern 的文件夹（用于 tcver）
    if os.path.isdir(dataset_dir):
        for item in os.listdir(dataset_dir):
            item_path = os.path.join(dataset_dir, item)
            if os.path.isdir(item_path) and rtklc_pattern.lower() in item.lower():
                tcver = item
                print(f"  找到包含 '{rtklc_pattern}' 的文件夹: {tcver}")
                break
    
    # 如果没有找到，使用默认值
    if lcver is None:
        lcver = f'{pvtlc_pattern}_vcpb_a3fc76c'
        print(f"  警告: 未找到包含 '{pvtlc_pattern}' 的文件夹，使用默认值: {lcver}")
    
    if tcver is None:
        tcver = f'{rtklc_pattern}_vcpb_a3fc76c'
        print(f"  警告: 未找到包含 '{rtklc_pattern}' 的文件夹，使用默认值: {tcver}")
    
    # 构建配置文件内容
    config = {
        'data': {
            'basefold': dataset_dir,
            'reffile': ref_02_path,
            'lcver': lcver,
            'tcver': tcver,
            'dataset': '',
            'dt': 0.0,
            # GNSS数据路径配置
            'gnss_subdir': gnss_subdir,
            'gnss_filename': gnss_filename,
            # GNSS数据列索引配置
            'gnss_pos_index_1': gnss_pos_index_1,
            'gnss_pos_index_2': gnss_pos_index_2,
            'gnss_pos_index_3': gnss_pos_index_3,
            # 数据源标识符配置
            'lc_label': lc_label,
            'tc_label': tc_label,
            'gnss_label': gnss_label
        },
        'plot': {
            'plotlc': True,
            'plottc': True,
            'plotgnssstat': True
        },
        'evaluation': {
            'tthreshod': 0.001,
            'horizontal_only': horizontal_only
        },
        'detail_plot': {
            'horizontal_error_threshold_meters': 10.0,
            'vertical_error_threshold_meters': 15.0,
            'detail_window_seconds': 25.0
        },
        'clip_plot': {
            'saveclip': 1,
            'horizontal_error_threshold_meters': 10.0,
            'vertical_error_threshold_meters': 15.0,
            'clip_plot_interval_seconds': 50.0
        },
        'normal_scene_exclusions': {
            'lc_tc_exclude': ['隧道'],
            'gnss_exclude': ['隧道', '转发器']
        },
        'output': {
            'output_dir': dataset_dir
        },
        'advanced': {
            'reftype': 1,
            'statetype': 1
        },
        'time_ranges': time_ranges_config
    }
    
    # 如果提供了配置模板，尝试读取并合并
    if config_template_path and os.path.exists(config_template_path):
        try:
            with open(config_template_path, 'r', encoding='utf-8') as f:
                template_config = toml.load(f)
                # 合并配置（模板配置的优先级较低）
                for section, values in template_config.items():
                    if section not in config:
                        config[section] = values
                    else:
                        if isinstance(values, dict):
                            for key, value in values.items():
                                if key not in config[section]:
                                    config[section][key] = value
            print(f"  已合并配置模板: {config_template_path}")
        except Exception as e:
            print(f"  警告: 读取配置模板失败: {e}")
    
    # 写入配置文件
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(config, f)
        print(f"  ✓ 配置文件已生成: {config_path}")
        return config_path, True
    except Exception as e:
        print(f"  ✗ 配置文件生成失败: {e}")
        return None, False


def generate_all_configs(tcmsf_output_dir, original_data_dir, config_template_path=None, 
                        pvtlc_pattern='pvtlc', rtklc_pattern='rtklc',
                        gnss_subdir='topic_parse', gnss_filename='gnss.csv',
                        gnss_pos_index_1=12, gnss_pos_index_2=13, gnss_pos_index_3=4,
                        lc_label='LC', tc_label='TC', gnss_label='RTK',
                        horizontal_only=1):
    """
    为所有数据集生成配置文件
    
    Args:
        tcmsf_output_dir: 数据集
        original_data_dir: 原始数据集目录
        config_template_path: 配置文件模板路径（可选）
        pvtlc_pattern: 用于查找 PVT LC 文件夹的模式字符串（默认: 'pvtlc'）
        rtklc_pattern: 用于查找 RTK LC 文件夹的模式字符串（默认: 'rtklc'）
        gnss_subdir: GNSS数据子目录（默认: 'topic_parse'）
        gnss_filename: GNSS数据文件名（默认: 'gnss.csv'）
        gnss_pos_index_1: GNSS位置索引1，对应gnssindex[7]（默认: 12）
        gnss_pos_index_2: GNSS位置索引2，对应gnssindex[8]（默认: 13）
        gnss_pos_index_3: GNSS位置索引3，对应gnssindex[9]（默认: 4）
        lc_label: LC标签（默认: 'LC'）
        tc_label: TC标签（默认: 'TC'）
        gnss_label: GNSS标签（默认: 'RTK'）
        horizontal_only: 是否只评估水平误差（1=仅水平，0=水平和垂直，默认: 1）
    
    Returns:
        config_files: 生成的配置文件列表
        success_count: 成功生成的配置文件数量
        fail_count: 失败的数量
    """
    config_files = []
    success_count = 0
    fail_count = 0
    
    dataset_dirs = find_dataset_directories(tcmsf_output_dir)
    print(f"\n开始为 {len(dataset_dirs)} 个数据集生成配置文件...")
    print(f"  原始数据集目录: {original_data_dir}")
    if config_template_path:
        print(f"  配置模板路径: {config_template_path}")
    print(f"  PVT LC 模式字符串: {pvtlc_pattern}")
    print(f"  RTK LC 模式字符串: {rtklc_pattern}")
    print(f"  GNSS子目录: {gnss_subdir}")
    print(f"  GNSS文件名: {gnss_filename}")
    print(f"  GNSS位置索引: [{gnss_pos_index_1}, {gnss_pos_index_2}, {gnss_pos_index_3}]")
    print(f"  标签配置: LC={lc_label}, TC={tc_label}, GNSS={gnss_label}")
    
    for i, dataset_dir in enumerate(dataset_dirs, 1):
        dataset_name = os.path.basename(dataset_dir)
        print(f"\n[{i}/{len(dataset_dirs)}] 处理数据集: {dataset_name}")
        
        config_path, success = generate_config_file(
            dataset_dir, original_data_dir, config_template_path, 
            pvtlc_pattern, rtklc_pattern,
            gnss_subdir, gnss_filename,
            gnss_pos_index_1, gnss_pos_index_2, gnss_pos_index_3,
            lc_label, tc_label, gnss_label,
            horizontal_only
        )
        
        if success:
            config_files.append(config_path)
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n配置文件生成完成:")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    
    return config_files, success_count, fail_count


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='批量运行 precision_head_topic_ref_100c_wdh_main.py 脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    python batch_run_precision_head_horizontal.py /path/to/tcmsf_output /path/to/original_data
    python batch_run_precision_head_horizontal.py /path/to/tcmsf_output /path/to/original_data /path/to/config_template.toml
    python batch_run_precision_head_horizontal.py /path/to/tcmsf_output /path/to/original_data --pvtlc-pattern pvtlc --rtklc-pattern rtklc
    python batch_run_precision_head_horizontal.py /path/to/tcmsf_output /path/to/original_data --gnss-subdir topic_parse --gnss-filename gnss.csv
        """
    )
    
    parser.add_argument(
        'tcmsf_output_directory',
        type=str,
        help='batch_run_tcmsf.py 的输出目录（包含各数据集的处理结果）'
    )
    
    parser.add_argument(
        'original_data_directory',
        type=str,
        help='原始数据集路径（包含 ref_02.txt 和 time_ranges 配置）'
    )
    
    parser.add_argument(
        'config_template',
        type=str,
        nargs='?',
        default=None,
        help='配置文件模板路径（可选）'
    )
    
    parser.add_argument(
        '--pvtlc-pattern',
        type=str,
        default='pvtlc',
        help='用于查找 PVT LC 文件夹的模式字符串（默认: pvtlc）'
    )
    
    parser.add_argument(
        '--rtklc-pattern',
        type=str,
        default='rtklc',
        help='用于查找 RTK LC 文件夹的模式字符串（默认: rtklc）'
    )
    
    # GNSS数据路径配置参数
    parser.add_argument(
        '--gnss-subdir',
        type=str,
        default='topic_parse',
        help='GNSS数据子目录（默认: topic_parse）'
    )
    
    parser.add_argument(
        '--gnss-filename',
        type=str,
        default='gnss.csv',
        help='GNSS数据文件名（默认: gnss.csv）'
    )
    
    # GNSS数据列索引配置参数
    parser.add_argument(
        '--gnss-pos-index-1',
        type=int,
        default=12,
        help='GNSS位置索引1，对应gnssindex[7]（默认: 12）'
    )
    
    parser.add_argument(
        '--gnss-pos-index-2',
        type=int,
        default=13,
        help='GNSS位置索引2，对应gnssindex[8]（默认: 13）'
    )
    
    parser.add_argument(
        '--gnss-pos-index-3',
        type=int,
        default=4,
        help='GNSS位置索引3，对应gnssindex[9]（默认: 4）'
    )
    
    # 数据源标识符配置参数
    parser.add_argument(
        '--lc-label',
        type=str,
        default='LC',
        help='LC标签（默认: LC）'
    )
    
    parser.add_argument(
        '--tc-label',
        type=str,
        default='TC',
        help='TC标签（默认: TC）'
    )
    
    parser.add_argument(
        '--gnss-label',
        type=str,
        default='RTK',
        help='GNSS标签（默认: RTK）'
    )
    
    parser.add_argument(
        '--horizontal-only',
        type=int,
        default=1,
        help='是否只评估水平误差（1=仅水平，0=水平和垂直，默认: 1）'
    )

    parser.add_argument(
        '--skip-gap-detection',
        action='store_true',
        default=False,
        help='跳过连续性检测（gap_detection.py），直接进行精度评估'
    )

    parser.add_argument(
        '--gap-threshold',
        type=float,
        default=5.0,
        dest='gap_threshold',
        help='连续性检测的大段缺失阈值（秒，默认: 5.0）'
    )

    args = parser.parse_args()
    
    tcmsf_output_dir = args.tcmsf_output_directory
    original_data_dir = args.original_data_directory
    config_template_path = args.config_template
    pvtlc_pattern = args.pvtlc_pattern
    rtklc_pattern = args.rtklc_pattern
    gnss_subdir = args.gnss_subdir
    gnss_filename = args.gnss_filename
    gnss_pos_index_1 = args.gnss_pos_index_1
    gnss_pos_index_2 = args.gnss_pos_index_2
    gnss_pos_index_3 = args.gnss_pos_index_3
    lc_label = args.lc_label
    tc_label = args.tc_label
    gnss_label = args.gnss_label
    horizontal_only = args.horizontal_only
    skip_gap_detection = args.skip_gap_detection
    gap_threshold = args.gap_threshold
    
    # 检查目录是否存在
    if not os.path.isdir(tcmsf_output_dir):
        print(f"错误: TCMSF 输出目录不存在: {tcmsf_output_dir}")
        sys.exit(1)
    
    if not os.path.isdir(original_data_dir):
        print(f"错误: 原始数据集目录不存在: {original_data_dir}")
        sys.exit(1)
    
    if config_template_path and not os.path.exists(config_template_path):
        print(f"错误: 配置模板文件不存在: {config_template_path}")
        sys.exit(1)
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置评估脚本路径
    script_path = os.path.join(current_dir, 'precision_head_topic_ref_100c_wdh_main.py')
    
    if not os.path.exists(script_path):
        print(f"错误: 评估脚本不存在: {script_path}")
        sys.exit(1)
    
    print(f"{'='*80}")
    print("批量精度评估脚本")
    print(f"{'='*80}")
    print(f"TCMSF 输出目录: {tcmsf_output_dir}")
    print(f"原始数据集目录: {original_data_dir}")
    if config_template_path:
        print(f"配置模板路径: {config_template_path}")
    print(f"PVT LC 模式字符串: {pvtlc_pattern}")
    print(f"RTK LC 模式字符串: {rtklc_pattern}")
    print(f"GNSS子目录: {gnss_subdir}")
    print(f"GNSS文件名: {gnss_filename}")
    print(f"GNSS位置索引: [{gnss_pos_index_1}, {gnss_pos_index_2}, {gnss_pos_index_3}]")
    print(f"标签配置: LC={lc_label}, TC={tc_label}, GNSS={gnss_label}")
    print(f"评估脚本路径: {script_path}")
    print(f"跳过连续性检测: {skip_gap_detection}")
    print(f"Gap检测阈值: {gap_threshold}s")
    print(f"{'='*80}\n")
    
    # 查找所有数据集目录
    print(f"扫描 TCMSF 输出目录，查找数据集...")
    dataset_dirs = find_dataset_directories(tcmsf_output_dir)
    
    if len(dataset_dirs) == 0:
        print(f"警告: 在目录 {tcmsf_output_dir} 中未找到任何数据集")
        print(f"请确保目录下包含 topic_parse 子目录的数据集目录")
        sys.exit(0)
    
    print(f"找到 {len(dataset_dirs)} 个数据集:")
    for i, dataset_dir in enumerate(dataset_dirs, 1):
        dataset_name = os.path.basename(dataset_dir)
        print(f"  {i}. {dataset_name}")
    
    # ---- 任务1：运行 gap_detection.py 进行连续性检测 ----
    if not skip_gap_detection:
        print(f"\n{'='*80}")
        print(f"[Step 0] 融合定位连续性检测 (gap_detection.py)")
        print(f"{'='*80}")
        print(f"检测阈值: >= {gap_threshold}s 判定为大段缺失")
        print(f"")

        gap_detection_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'commons', 'gap_detection.py'
        )
        gap_detection_script = os.path.normpath(gap_detection_script)

        if not os.path.exists(gap_detection_script):
            print(f"[警告] gap_detection.py 不存在: {gap_detection_script}")
            print(f"跳过连续性检测")
        else:
            for dataset_dir in dataset_dirs:
                dataset_name = os.path.basename(dataset_dir)
                print(f"\n--- 检测数据集: {dataset_name} ---")

                gap_cmd = [
                    sys.executable, gap_detection_script,
                    dataset_dir,
                    '--threshold', str(gap_threshold)
                ]

                try:
                    result = subprocess.run(
                        gap_cmd,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if result.returncode == 0:
                        print(f"  ✓ {dataset_name} 连续性检测完成")
                    else:
                        print(f"  ✗ {dataset_name} 连续性检测失败 (返回码: {result.returncode})")
                        if result.stderr:
                            for line in result.stderr.strip().split('\n')[-5:]:
                                print(f"    {line}")
                except subprocess.TimeoutExpired:
                    print(f"  ✗ {dataset_name} 连续性检测超时（>5分钟）")
                except Exception as e:
                    print(f"  ✗ {dataset_name} 连续性检测异常: {e}")
    else:
        print(f"\n[跳过] 连续性检测（--skip-gap-detection）\n")

    # 为所有数据集生成配置文件
    config_files, config_success_count, config_fail_count = generate_all_configs(
        tcmsf_output_dir, original_data_dir, config_template_path, 
        pvtlc_pattern, rtklc_pattern,
        gnss_subdir, gnss_filename,
        gnss_pos_index_1, gnss_pos_index_2, gnss_pos_index_3,
        lc_label, tc_label, gnss_label,
        horizontal_only
    )
    
    if len(config_files) == 0:
        print(f"\n错误: 没有成功生成任何配置文件")
        sys.exit(1)
    
    # 创建日志目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(tcmsf_output_dir, f'batch_run_logs_{timestamp}')
    os.makedirs(log_dir, exist_ok=True)
    print(f"\n日志目录: {log_dir}")
    
    # 批量运行配置文件
    print(f"\n开始批量运行...")
    print(f"{'='*80}")
    
    success_count = 0
    fail_count = 0
    total_duration = 0
    
    summary_log = os.path.join(log_dir, 'batch_summary.txt')
    
    with open(summary_log, 'w', encoding='utf-8') as f_summary:
        f_summary.write('='*80 + '\n')
        f_summary.write('批量运行总结\n')
        f_summary.write('='*80 + '\n')
        f_summary.write(f'开始时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f_summary.write(f'TCMSF 输出目录: {tcmsf_output_dir}\n')
        f_summary.write(f'原始数据集目录: {original_data_dir}\n')
        if config_template_path:
            f_summary.write(f'配置模板路径: {config_template_path}\n')
        f_summary.write(f'PVT LC 模式字符串: {pvtlc_pattern}\n')
        f_summary.write(f'RTK LC 模式字符串: {rtklc_pattern}\n')
        f_summary.write(f'GNSS子目录: {gnss_subdir}\n')
        f_summary.write(f'GNSS文件名: {gnss_filename}\n')
        f_summary.write(f'GNSS位置索引: [{gnss_pos_index_1}, {gnss_pos_index_2}, {gnss_pos_index_3}]\n')
        f_summary.write(f'标签配置: LC={lc_label}, TC={tc_label}, GNSS={gnss_label}\n')
        f_summary.write(f'数据集总数: {len(dataset_dirs)}\n')
        f_summary.write(f'配置文件生成成功: {config_success_count}\n')
        f_summary.write(f'配置文件生成失败: {config_fail_count}\n')
        f_summary.write('='*80 + '\n\n')
        
        for i, config_path in enumerate(config_files, 1):
            dataset_name = os.path.basename(os.path.dirname(config_path))
            print(f"\n进度: [{i}/{len(config_files)}] 数据集: {dataset_name}")
            
            success, duration = run_single_config(config_path, script_path, log_dir, dataset_name=dataset_name)
            total_duration += duration
            
            # 记录运行结果到总结
            f_summary.write(f"数据集 {i}/{len(config_files)}: {dataset_name}\n")
            f_summary.write(f"  配置文件: {config_path}\n")
            f_summary.write(f"  状态: {'成功' if success else '失败'}\n")
            f_summary.write(f"  耗时: {duration:.2f}秒\n")
            f_summary.write(f"  日志文件: {log_dir}/{dataset_name}.log\n")
            f_summary.write('-'*80 + '\n')
            
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        # 写入总结信息
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f_summary.write('\n' + '='*80 + '\n')
        f_summary.write('总体统计\n')
        f_summary.write('='*80 + '\n')
        f_summary.write(f'结束时间: {end_time}\n')
        f_summary.write(f'总耗时: {total_duration:.2f}秒 ({total_duration/60:.2f}分钟)\n')
        f_summary.write(f'配置文件总数: {len(config_files)}\n')
        f_summary.write(f'评估成功: {success_count}\n')
        f_summary.write(f'评估失败: {fail_count}\n')
        f_summary.write(f'成功率: {success_count/len(config_files)*100:.2f}%\n')
        f_summary.write('='*80 + '\n')
    
    # 输出最终总结
    print(f"\n{'='*80}")
    print("批量运行完成!")
    print(f"{'='*80}")
    print(f"配置文件总数: {len(config_files)}")
    print(f"评估成功: {success_count}")
    print(f"评估失败: {fail_count}")
    print(f"成功率: {success_count/len(config_files)*100:.2f}%")
    print(f"总耗时: {total_duration:.2f}秒 ({total_duration/60:.2f}分钟)")
    print(f"\n日志目录: {log_dir}")
    print(f"总结文件: {summary_log}")
    
    if fail_count > 0:
        print(f"\n失败的数据集请查看日志: {log_dir}/*_error.log")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()