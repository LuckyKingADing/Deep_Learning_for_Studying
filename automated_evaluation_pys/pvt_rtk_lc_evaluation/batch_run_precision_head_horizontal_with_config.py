#!/usr/bin/env python3
"""
批量运行 precision_head_topic_ref_100c_wdh_horizontal_only.py 的脚本（自动生成配置）

功能:
- 扫描指定目录下的所有文件夹（每个文件夹名为数据集名）
- 在每个文件夹内自动生成 precision_head_topic_ref_100c_wdh_config.toml 配置文件
- 批量运行每个数据集的评估脚本
- 自动从数据集名称中提取 lcver 和 tcver
- 记录运行日志和结果

使用方法:
    python batch_run_precision_head_horizontal_with_config.py <base_directory>

参数:
    base_directory: 存放数据集文件夹的根目录
"""

import os
import sys
import subprocess
import time
import re
from datetime import datetime
import argparse


def extract_version_from_dataset(dataset_name):
    """
    从数据集名称中提取 lcver 和 tcver
    
    Args:
        dataset_name: 数据集名称（文件夹名）
    
    Returns:
        (lcver, tcver): 版本信息，如果提取失败则返回默认值
    """
    # 默认值
    default_lcver = "pvtlc_vcpb_a3fc76c"
    default_tcver = "rtklc_vcpb_a3fc76c"
    
    # 尝试从文件夹名中提取带pvtlc的完整名
    lcver_match = re.search(r'pvtlc[^/]*', dataset_name)
    lcver = lcver_match.group(0) if lcver_match else default_lcver
    
    # 尝试从文件夹名中提取带rtklc的完整名
    tcver_match = re.search(r'rtklc[^/]*', dataset_name)
    tcver = tcver_match.group(0) if tcver_match else default_tcver
    
    return lcver, tcver


def generate_config_file(dataset_path, base_directory, dataset_name):
    """
    为数据集生成配置文件
    
    Args:
        dataset_path: 数据集完整路径
        base_directory: 根目录
        dataset_name: 数据集名称
    
    Returns:
        config_path: 生成的配置文件路径
    """
    # 提取版本信息
    lcver, tcver = extract_version_from_dataset(dataset_name)
    
    # 参考文件路径: 优先使用 ref_02.txt (GCJ-02坐标), 如果不存在则回退到 ref.txt (WGS84坐标)
    # 当 ref_type="wgs84" 时（如0227数据），不会生成 ref_02.txt，此时直接使用 ref.txt
    reffile_02 = os.path.join(dataset_path, "ref_02.txt")
    reffile_wgs = os.path.join(dataset_path, "ref.txt")
    if os.path.exists(reffile_02):
        reffile = reffile_02
    elif os.path.exists(reffile_wgs):
        reffile = reffile_wgs
        print(f"  [信息] ref_02.txt不存在，使用WGS84参考文件: {reffile}")
    else:
        reffile = reffile_02  # 保持原有行为，使用占位路径
    
    # time_ranges 占位符（后续需要从原始数据集的 time_ranges.txt 读取）
    # 这里使用默认的空配置
    
    # 生成配置文件内容
    config_content = f"""# precision_head_topic_ref_100c_wdh 配置文件
# 自动生成于: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

[data]
# 基础目录路径
basefold = "{base_directory}"
# 参考数据文件路径（占位符，需要根据原始数据集路径生成）
reffile = "{reffile}"
# LC版本名称
lcver = "{lcver}"
# TC版本名称
tcver = "{tcver}"
# 数据集名称
dataset = "{dataset_name}"
# 时间偏移 (默认: 0)
dt = 0.0

[plot]
# 是否绘制LC数据
plotlc = true
# 是否绘制TC数据
plottc = true
# 是否绘制GNSS数据
plotgnssstat = true

[evaluation]
# 时间阈值
tthreshod = 0.001
horizontal_only = 1

[detail_plot]
# 水平误差阈值（米），超过此值将自动绘制子图
horizontal_error_threshold_meters = 10.0
# 高程误差阈值（米），超过此值将自动绘制子图
vertical_error_threshold_meters = 15.0
# 子图时间窗口（秒），在极值点前后各取的时间长度
detail_window_seconds = 25.0

[clip_plot]
# 是否保存和绘制clip数据（1=启用，0=禁用）
saveclip = 1
# 水平误差阈值（米），超过此值的数据将被保存为clip
horizontal_error_threshold_meters = 10.0
# 垂直误差阈值（米），超过此值的数据将被保存为clip
vertical_error_threshold_meters = 15.0
# clip子图时间间隔（秒）
clip_plot_interval_seconds = 50.0

[normal_scene_exclusions]
# 正常场景需要排除的场景配置
# 这些场景标签必须与time_ranges.type_config中的type_label完全匹配（包括大小写）

# LC/TC正常场景需要排除的场景列表
lc_tc_exclude = ["隧道"]

# GNSS正常场景需要排除的场景列表
gnss_exclude = ["隧道", "转发器"]

[output]
# 输出目录 (默认为basefold，如果为空字符串则使用basefold)
output_dir = ""

[advanced]
# 参考真值的数据类型
# 0: 2504月采集的真值
# 1: 后续wdh处理的真值
reftype = 1
# 状态文件的类型
# 0: tcmsf_sol.csv
# 1: msf_debug_state.csv
statetype = 1

[time_ranges]
# 时间范围配置，支持多个type，每个type可以配置多个时间范围
# 格式: [[start1, end1], [start2, end2], ...]
# 时间为绝对时间（秒）
# 示例:
# [[type_label, type_time_range], ...]
# 例如: type "0" 对应的时间范围为 [[444255.6, 444624.3], [446783.1, 447156.6]]
# 可以配置多个type的数据

# Type 0: 20260105
[[time_ranges.type_config]]
type_label = "All"
type_time_range = [[-1,-1]]

# Type 1: 20251209
[[time_ranges.type_config]]
type_label = "Highway"
type_time_range = []

# Type 2: 20251205
[[time_ranges.type_config]]
type_label = "Conventional Urban Area"
type_time_range = []

# Type 3: 20251217
[[time_ranges.type_config]]
type_label = "Tree-lined Roads"
type_time_range = []

# Type 4: 20251217
[[time_ranges.type_config]]
type_label = "Elevated Structure"
type_time_range = []

# Type 5: 20260105
[[time_ranges.type_config]]
type_label = "Urban Canyon"
type_time_range = []

# Type 6: 20260105
[[time_ranges.type_config]]
type_label = "Satellite Repeater"
type_time_range = []

# Type 7: 20251216
[[time_ranges.type_config]]
type_label = "Long Tunnel"
type_time_range = []

# 注意: time_ranges 配置目前为占位符
# 后续需要从原始数据集目录的 time_ranges.txt 文件中读取并更新
"""
    
    # 写入配置文件
    config_path = os.path.join(dataset_path, "precision_head_topic_ref_100c_wdh_config.toml")
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    return config_path


def run_single_dataset(dataset_path, script_path, log_dir, base_directory):
    """
    运行单个数据集的评估
    
    Args:
        dataset_path: 数据集路径
        script_path: 评估脚本路径
        log_dir: 日志目录
        base_directory: 根目录
    
    Returns:
        success: 是否成功
        duration: 运行耗时（秒）
    """
    dataset_name = os.path.basename(dataset_path)
    print(f"\n{'='*80}")
    print(f"开始处理数据集: {dataset_name}")
    print(f"路径: {dataset_path}")
    print(f"{'='*80}")
    
    # 生成配置文件
    print(f"  生成配置文件...")
    try:
        config_path = generate_config_file(dataset_path, base_directory, dataset_name)
        print(f"  ✓ 配置文件已生成: {config_path}")
    except Exception as e:
        print(f"  ✗ 配置文件生成失败: {str(e)}")
        return False, 0
    
    # 创建日志文件
    log_file = os.path.join(log_dir, f"{dataset_name}.log")
    error_log_file = os.path.join(log_dir, f"{dataset_name}_error.log")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 运行脚本，将输出重定向到日志文件
        print(f"  运行评估脚本...")
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
            print(f"  ✓ {dataset_name} 运行成功 (耗时: {duration:.2f}秒)")
            return True, duration
        else:
            print(f"  ✗ {dataset_name} 运行失败 (返回码: {return_code}, 耗时: {duration:.2f}秒)")
            print(f"    日志文件: {log_file}")
            print(f"    错误日志: {error_log_file}")
            return False, duration
            
    except Exception as e:
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"  ✗ {dataset_name} 运行异常: {str(e)} (耗时: {duration:.2f}秒)")
        return False, duration


def find_dataset_folders(base_dir):
    """
    查找目录下所有的数据集文件夹
    
    Args:
        base_dir: 根目录
    
    Returns:
        dataset_folders: 数据集文件夹路径列表
    """
    dataset_folders = []
    
    if not os.path.isdir(base_dir):
        print(f"错误: 目录不存在: {base_dir}")
        return dataset_folders
    
    # 遍历根目录下的直接子文件夹
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            # 跳过隐藏目录和日志目录
            if item.startswith('.') or item.startswith('batch_run_logs_'):
                continue
            dataset_folders.append(item_path)
    
    # 按名称排序
    dataset_folders.sort()
    
    return dataset_folders


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='批量运行 precision_head_topic_ref_100c_wdh_horizontal_only.py 脚本（自动生成配置）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    python batch_run_precision_head_horizontal_with_config.py /path/to/datasets

说明:
    - 脚本会扫描指定目录下的所有文件夹（每个文件夹代表一个数据集）
    - 为每个数据集自动生成配置文件
    - 从数据集名称中提取 lcver 和 tcver
    - 批量运行评估脚本
    - reffile 和 time_ranges 当前为占位符，需要后续完善
        """
    )
    
    parser.add_argument(
        'base_directory',
        type=str,
        help='存放数据集文件夹的根目录'
    )
    
    args = parser.parse_args()
    
    base_dir = args.base_directory
    
    # 检查根目录是否存在
    if not os.path.isdir(base_dir):
        print(f"错误: 根目录不存在: {base_dir}")
        sys.exit(1)
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置评估脚本路径
    script_path = os.path.join(current_dir, 'precision_head_topic_ref_100c_wdh_horizontal_only.py')
    
    if not os.path.exists(script_path):
        print(f"错误: 评估脚本不存在: {script_path}")
        sys.exit(1)
    
    # 查找所有数据集文件夹
    print(f"扫描数据集目录: {base_dir}")
    dataset_folders = find_dataset_folders(base_dir)
    
    if len(dataset_folders) == 0:
        print(f"警告: 在目录 {base_dir} 中未找到任何数据集文件夹")
        print(f"请确保目录下有数据集文件夹")
        sys.exit(0)
    
    print(f"找到 {len(dataset_folders)} 个数据集:")
    for i, dataset_path in enumerate(dataset_folders, 1):
        dataset_name = os.path.basename(dataset_path)
        print(f"  {i}. {dataset_name}")
    
    # 创建日志目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(base_dir, f'batch_run_logs_{timestamp}')
    os.makedirs(log_dir, exist_ok=True)
    print(f"\n日志目录: {log_dir}")
    
    # 批量运行数据集
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
        f_summary.write(f'根目录: {base_dir}\n')
        f_summary.write(f'数据集数量: {len(dataset_folders)}\n')
        f_summary.write('='*80 + '\n\n')
        
        for i, dataset_path in enumerate(dataset_folders, 1):
            print(f"\n进度: [{i}/{len(dataset_folders)}]")
            
            success, duration = run_single_dataset(dataset_path, script_path, log_dir, base_dir)
            total_duration += duration
            
            dataset_name = os.path.basename(dataset_path)
            
            # 记录到总结文件
            f_summary.write(f"数据集 {i}/{len(dataset_folders)}: {dataset_name}\n")
            f_summary.write(f"  路径: {dataset_path}\n")
            f_summary.write(f"  状态: {'成功' if success else '失败'}\n")
            f_summary.write(f"  耗时: {duration:.2f}秒\n")
            f_summary.write(f"  日志文件: {log_dir}/{dataset_name}.log\n")
            f_summary.write(f"  配置文件: {dataset_path}/precision_head_topic_ref_100c_wdh_config.toml\n")
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
        f_summary.write(f'成功数量: {success_count}\n')
        f_summary.write(f'失败数量: {fail_count}\n')
        f_summary.write(f'成功率: {success_count/len(dataset_folders)*100:.2f}%\n')
        f_summary.write('='*80 + '\n')
        
        # 添加注意事项
        f_summary.write('\n' + '='*80 + '\n')
        f_summary.write('注意事项\n')
        f_summary.write('='*80 + '\n')
        f_summary.write('1. reffile 路径当前为占位符，需要根据原始数据集路径手动修改\n')
        f_summary.write('2. time_ranges 配置当前为占位符，需要从原始数据集的 time_ranges.txt 读取\n')
        f_summary.write('3. lcver 和 tcver 已自动从数据集名称中提取\n')
        f_summary.write('='*80 + '\n')
    
    # 输出最终总结
    print(f"\n{'='*80}")
    print("批量运行完成!")
    print(f"{'='*80}")
    print(f"数据集总数: {len(dataset_folders)}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"成功率: {success_count/len(dataset_folders)*100:.2f}%")
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