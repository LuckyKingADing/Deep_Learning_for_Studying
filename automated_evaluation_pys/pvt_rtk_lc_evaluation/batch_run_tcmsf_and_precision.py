#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串联执行 TCMSF 处理、精度评估和精度统计聚合的脚本

功能说明：
1. 调用 batch_run_tcmsf.py 执行 TCMSF 处理
2. 调用 batch_run_precision_head_horizontal.py 执行精度评估
3. 调用 aggregate_precision_statistics.py 执行精度统计聚合
4. 自动生成所需的配置文件并处理数据流转

使用方法：
    python batch_run_tcmsf_and_precision.py <配置文件路径>

示例：
    python batch_run_tcmsf_and_precision.py /path/to/config.toml

依赖：
    - batch_run_tcmsf.py
    - batch_run_precision_head_horizontal.py
    - aggregate_precision_statistics.py
    - 需要sudo权限来复制文件
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import toml


def run_command(command: list, description: str = "") -> bool:
    """
    执行shell命令
    
    参数:
        command: 命令及其参数列表
        description: 命令描述（用于日志）
    
    返回:
        命令是否执行成功
    """
    print(f"\n[执行命令] {description}")
    print(f"  命令: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.stdout:
            print(f"[标准输出]\n{result.stdout}")
        if result.stderr:
            print(f"[标准错误]\n{result.stderr}")
        
        print(f"[成功] 命令执行完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[错误] 命令执行失败")
        print(f"[错误] 返回码: {e.returncode}")
        if e.stdout:
            print(f"[标准输出]\n{e.stdout}")
        if e.stderr:
            print(f"[错误] 错误信息:\n{e.stderr}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="串联执行 TCMSF 处理、精度评估和精度统计聚合",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 指定配置文件
  python batch_run_tcmsf_and_precision.py /path/to/config.toml

流程说明:
  1. 从配置文件读取 input_path（原始数据集路径）
  2. 执行 batch_run_tcmsf.py，将原始数据集处理为 TCMSF 结果
  3. 执行 batch_run_precision_head_horizontal.py，对 TCMSF 结果进行精度评估
     （精度评估内部会自动运行 gap_detection.py 检测大段缺失）
  4. 执行 aggregate_precision_statistics.py，聚合精度统计结果

说明:
  gap 检测的阈值通过配置文件中的 gap_threshold 字段控制，
  默认 5.0 秒，设置为 null 可跳过检测。
        """
    )
    
    parser.add_argument(
        "config_file",
        type=str,
        help="配置文件路径（包含 input_path 等配置项）"
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
    
    # 从配置文件读取输入路径
    input_path_str = config.get('input_path')
    if not input_path_str:
        print(f"[错误] 配置文件中缺少 input_path 配置项")
        sys.exit(1)
    
    # 验证路径
    original_data_path = Path(input_path_str)
    if not original_data_path.exists():
        print(f"[错误] 原始数据路径不存在: {original_data_path}")
        sys.exit(1)
    
    if not original_data_path.is_dir():
        print(f"[错误] 原始数据路径不是目录: {original_data_path}")
        sys.exit(1)
    
    # 获取输出路径（默认与输入路径相同）
    output_path_str = config.get('output_base_dir', input_path_str)
    output_path = Path(output_path_str)
    
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent
    
    # 步骤1: 执行 batch_run_tcmsf.py
    print(f"\n{'='*80}")
    print("步骤 1: 执行 TCMSF 处理")
    print(f"{'='*80}")
    print(f"  输入路径: {original_data_path}")
    print(f"  输出路径: {output_path}")
    print(f"  配置文件: {config_file}")
    print(f"{'='*80}\n")
    
    tcmsf_script = current_dir / "batch_run_tcmsf.py"
    tcmsf_command = [
        sys.executable,
        str(tcmsf_script),
        str(config_file)
    ]
    
    tcmsf_success = True
    jump_tcmsf = False #for debug
    if not jump_tcmsf:
        tcmsf_success = run_command(
            tcmsf_command,
            description="执行 batch_run_tcmsf.py"
        )
        
        if not tcmsf_success:
            print(f"\n[失败] TCMSF 处理失败，终止执行")
            sys.exit(1)
    
    # 步骤2: 执行 batch_run_precision_head_horizontal.py
    print(f"\n{'='*80}")
    print("步骤 2: 执行精度评估")
    print(f"{'='*80}")

    # 检查是否有 datasets 配置
    datasets_config = config.get('datasets', [])
    
    precision_script = current_dir / "batch_run_precision_head_horizontal.py"
    
    # 从配置文件读取模式字符串（如果有）
    pvtlc_pattern = config.get('pvtlc_pattern', 'pvtlc')
    rtklc_pattern = config.get('rtklc_pattern', 'rtklc')
    
    if datasets_config:
        # 使用 datasets 配置模式：为每个 dataset 单独执行精度评估
        print(f"[信息] 使用 datasets 配置模式进行精度评估")
        print(f"[信息] 找到 {len(datasets_config)} 个 dataset 配置")
        
        # 读取默认的 GNSS 参数（用于 dataset 配置中未指定的参数）
        default_gnss_subdir = config.get('gnss_subdir', 'topic_parse')
        default_gnss_filename = config.get('gnss_filename', 'gnss.csv')
        default_gnss_pos_index_1 = config.get('gnss_pos_index_1', 12)
        default_gnss_pos_index_2 = config.get('gnss_pos_index_2', 13)
        default_gnss_pos_index_3 = config.get('gnss_pos_index_3', 4)
        default_lc_label = config.get('lc_label', 'LC')
        default_tc_label = config.get('tc_label', 'TC')
        default_gnss_label = config.get('gnss_label', 'RTK')
        default_horizontal_only = config.get('horizontal_only', 1)
        
        success_count = 0
        fail_count = 0
        
        # 遍历每个 dataset 配置
        for dataset_config in datasets_config:
            dataset_name = dataset_config['name']
            
            print(f"\n{'='*80}")
            print(f"[Dataset] {dataset_name}")
            print(f"{'='*80}")
            
            # 获取该 dataset 的输出目录
            dataset_output_path = output_path / dataset_name
            
            # 获取该 dataset 的原始数据目录
            dataset_original_path = original_data_path / dataset_name
            
            if not dataset_output_path.exists():
                os.makedirs(dataset_output_path)
                print(f"[警告] Dataset 输出目录不存在: {dataset_output_path} ，新建一个")
                #fail_count += 1
                #continue
            
            # 从 dataset 配置读取参数，如果未指定则使用默认值
            gnss_subdir = dataset_config.get('gnss_subdir', default_gnss_subdir)
            gnss_filename = dataset_config.get('gnss_filename', default_gnss_filename)
            gnss_pos_index_1 = dataset_config.get('gnss_pos_index_1', default_gnss_pos_index_1)
            gnss_pos_index_2 = dataset_config.get('gnss_pos_index_2', default_gnss_pos_index_2)
            gnss_pos_index_3 = dataset_config.get('gnss_pos_index_3', default_gnss_pos_index_3)
            lc_label = dataset_config.get('lc_label', default_lc_label)
            tc_label = dataset_config.get('tc_label', default_tc_label)
            gnss_label = dataset_config.get('gnss_label', default_gnss_label)
            # horizontal_only 使用全局配置，不从 dataset 配置中读取
            horizontal_only = default_horizontal_only
            
            print(f"  输出目录: {dataset_output_path}")
            print(f"  原始数据目录: {dataset_original_path}")
            print(f"  GNSS子目录: {gnss_subdir}")
            print(f"  GNSS文件名: {gnss_filename}")
            print(f"  GNSS位置索引: [{gnss_pos_index_1}, {gnss_pos_index_2}, {gnss_pos_index_3}]")
            print(f"  标签配置: LC={lc_label}, TC={tc_label}, GNSS={gnss_label}")
            print(f"  水平评估模式: {'仅水平' if horizontal_only == 1 else '水平和垂直'}")
            
            # 构建精度评估命令
            precision_command = [
                sys.executable,
                str(precision_script),
                str(dataset_output_path),
                str(dataset_original_path),
                '--pvtlc-pattern', pvtlc_pattern,
                '--rtklc-pattern', rtklc_pattern,
                '--gnss-subdir', gnss_subdir,
                '--gnss-filename', gnss_filename,
                '--gnss-pos-index-1', str(gnss_pos_index_1),
                '--gnss-pos-index-2', str(gnss_pos_index_2),
                '--gnss-pos-index-3', str(gnss_pos_index_3),
                '--lc-label', lc_label,
                '--tc-label', tc_label,
                '--gnss-label', gnss_label,
                '--horizontal-only', str(horizontal_only)
            ]
            
            precision_success = run_command(
                precision_command,
                description=f"执行 batch_run_precision_head_horizontal.py - {dataset_name}"
            )
            
            if precision_success:
                success_count += 1
            else:
                fail_count += 1
        
        # 输出统计信息
        print(f"\n{'='*80}")
        print(f"[汇总] 精度评估完成")
        print(f"  总数: {len(datasets_config)}")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        if len(datasets_config) > 0:
            print(f"  成功率: {success_count/len(datasets_config)*100:.2f}%")
        print(f"{'='*80}\n")
        
        if fail_count > 0:
            print(f"\n[失败] 精度评估失败")
            sys.exit(1)
    else:
        # 原有模式：对整个输出目录执行精度评估
        print(f"[信息] 使用原有模式（兼容旧配置）")
        print(f"  TCMSF 输出目录: {output_path}")
        print(f"  原始数据集目录: {original_data_path}")
        print(f"{'='*80}\n")
        
        # 从配置文件读取GNSS参数（如果有）
        gnss_subdir = config.get('gnss_subdir', 'topic_parse')
        gnss_filename = config.get('gnss_filename', 'gnss.csv')
        gnss_pos_index_1 = config.get('gnss_pos_index_1', 12)
        gnss_pos_index_2 = config.get('gnss_pos_index_2', 13)
        gnss_pos_index_3 = config.get('gnss_pos_index_3', 4)
        lc_label = config.get('lc_label', 'LC')
        tc_label = config.get('tc_label', 'TC')
        gnss_label = config.get('gnss_label', 'RTK')
        horizontal_only = config.get('horizontal_only', 1)
        
        print(f"  GNSS子目录: {gnss_subdir}")
        print(f"  GNSS文件名: {gnss_filename}")
        print(f"  GNSS位置索引: [{gnss_pos_index_1}, {gnss_pos_index_2}, {gnss_pos_index_3}]")
        print(f"  标签配置: LC={lc_label}, TC={tc_label}, GNSS={gnss_label}")
        print(f"  水平评估模式: {'仅水平' if horizontal_only == 1 else '水平和垂直'}")
        print(f"{'='*80}\n")
        
        precision_command = [
            sys.executable,
            str(precision_script),
            str(output_path),
            str(original_data_path),
            '--pvtlc-pattern', pvtlc_pattern,
            '--rtklc-pattern', rtklc_pattern,
            '--gnss-subdir', gnss_subdir,
            '--gnss-filename', gnss_filename,
            '--gnss-pos-index-1', str(gnss_pos_index_1),
            '--gnss-pos-index-2', str(gnss_pos_index_2),
            '--gnss-pos-index-3', str(gnss_pos_index_3),
            '--lc-label', lc_label,
            '--tc-label', tc_label,
            '--gnss-label', gnss_label,
            '--horizontal-only', str(horizontal_only)
        ]
        
        precision_success = run_command(
            precision_command,
            description="执行 batch_run_precision_head_horizontal.py"
        )
        
        if not precision_success:
            print(f"\n[失败] 精度评估失败")
            sys.exit(1)
    
    # 步骤3: 执行 aggregate_precision_statistics.py
    print(f"\n{'='*80}")
    print("步骤 3: 执行精度统计聚合")
    print(f"{'='*80}")
    print(f"  输入目录: {output_path}")
    print(f"  输出目录: {output_path}")
    print(f"{'='*80}\n")
    
    aggregate_script = current_dir / "aggregate_precision_statistics.py"
    # 输出文件路径
    precision_output_file = output_path / "position_precision_aggregated.txt"
    velocity_output_file = output_path / "velocity_precision_aggregated.txt"
    
    aggregate_command = [
        sys.executable,
        str(aggregate_script),
        "--no-config",  # 不使用配置文件，直接使用命令行参数
        "--input-dir", str(output_path),
        "--output-file", str(precision_output_file),
        "--velocity-output-file", str(velocity_output_file),
        "--skip-zero-scenes",
        "--verbose"
    ]
    
    aggregate_success = run_command(
        aggregate_command,
        description="执行 aggregate_precision_statistics.py"
    )
    
    if not aggregate_success:
        print(f"\n[失败] 精度统计聚合失败")

    # 完成
    print(f"\n{'='*80}")
    print("全部执行完成!")
    print(f"{'='*80}")
    print(f"  TCMSF 处理: {'成功' if tcmsf_success else '失败'}")
    print(f"  精度评估: {'成功' if precision_success else '失败'}")
    print(f"  精度统计聚合: {'成功' if aggregate_success else '失败'}")
    print(f"\n聚合结果文件:")
    print(f"  - {precision_output_file}")
    print(f"  - {velocity_output_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    sys.exit(main())