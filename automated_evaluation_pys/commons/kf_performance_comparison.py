#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
卡尔曼滤波性能对比脚本
用于对比优化版本和原始版本的时间消耗
"""

import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path


def parse_elapsed_time(file_path):
    """
    解析日志文件，提取时间消耗值（倒数第二列）
    
    Args:
        file_path: 日志文件路径
    
    Returns:
        numpy数组，包含所有时间值（单位：微秒）
    """
    times = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # 分割行，提取倒数第二列
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        # 倒数第二列应该是时间值
                        time_value = float(parts[-2])
                        times.append(time_value)
                    except (ValueError, IndexError):
                        continue
    except FileNotFoundError:
        print(f"警告: 文件 {file_path} 不存在")
        return np.array([])
    except Exception as e:
        print(f"警告: 读取文件 {file_path} 时出错: {e}")
        return np.array([])
    
    return np.array(times)


def plot_comparison(times_opt, times_orig, output_path='kf_performance_comparison.png'):
    """
    绘制性能对比图
    
    Args:
        times_opt: 优化版本的时间数组
        times_orig: 原始版本的时间数组
        output_path: 输出图片路径
    """
    plt.figure(figsize=(14, 7))
    
    # 绘制时间序列
    x_opt = range(len(times_opt))
    x_orig = range(len(times_orig))
    
    # 绘制两条曲线
    plt.plot(x_opt, times_opt, 'b-', alpha=0.5, label='优化版本 (kf_update_full_opt)', linewidth=1.5)
    plt.plot(x_orig, times_orig, 'r-', alpha=0.5, label='原始版本 (kf_update_full)', linewidth=1.5)
    
    # 添加平均值线
    if len(times_opt) > 0:
        mean_opt = np.mean(times_opt)
        plt.axhline(y=mean_opt, color='blue', linestyle='--', alpha=0.8, linewidth=2,
                   label=f'优化版本平均: {mean_opt:.2f} μs')
    
    if len(times_orig) > 0:
        mean_orig = np.mean(times_orig)
        plt.axhline(y=mean_orig, color='red', linestyle='--', alpha=0.8, linewidth=2,
                   label=f'原始版本平均: {mean_orig:.2f} μs')
    
    plt.xlabel('样本索引', fontsize=12)
    plt.ylabel('时间消耗 (μs)', fontsize=12)
    plt.title('卡尔曼滤波性能对比 - 时间消耗对比', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10, loc='best')
    plt.grid(True, alpha=0.3)
    
    # 设置中文字体（可选，如果需要支持中文）
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 保存图片
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存到: {output_path}")
    
    plt.close()


def main():
    """主函数"""
    # 文件路径
    file_opt = '/mnt/d/dockers/kf_update_full_opt_elapsed.txt'
    file_opt = '/mnt/d/dockers/kf_update_adp_elapsed.txt'
    # file_orig = '/mnt/d/dockers/kf_update_adp_elapsed.txt'
    file_orig = '/mnt/d/dockers/kf_update_org_elapsed.txt'
    
    # 读取数据
    print("="*70)
    print("卡尔曼滤波性能对比工具")
    print("="*70)
    print("\n正在读取数据...")
    times_opt = parse_elapsed_time(file_opt)
    times_orig = parse_elapsed_time(file_orig)
    
    # 检查数据
    if len(times_opt) == 0:
        print(f"错误: 无法从 {file_opt} 读取数据")
        print(f"请确认文件存在且格式正确")
        return
    
    if len(times_orig) == 0:
        print(f"错误: 无法从 {file_orig} 读取数据")
        print(f"请确认文件存在且格式正确")
        return
    
    print(f"✓ 优化版本样本数: {len(times_opt)}")
    print(f"✓ 原始版本样本数: {len(times_orig)}")
    
    # 计算统计信息
    mean_opt = np.mean(times_opt)
    mean_orig = np.mean(times_orig)
    std_opt = np.std(times_opt)
    std_orig = np.std(times_orig)
    median_opt = np.median(times_opt)
    median_orig = np.median(times_orig)
    diff = mean_orig - mean_opt
    improvement = (diff / mean_orig) * 100 if mean_orig > 0 else 0
    
    # 输出统计结果
    print("\n" + "="*70)
    print("性能对比统计结果")
    print("="*70)
    
    print(f"\n【优化版本】")
    print(f"  平均时间: {mean_opt:.2f} μs")
    print(f"  中位数:   {median_opt:.2f} μs")
    print(f"  标准差:   {std_opt:.2f} μs")
    print(f"  最小值:   {np.min(times_opt):.2f} μs")
    print(f"  最大值:   {np.max(times_opt):.2f} μs")
    
    print(f"\n【原始版本】")
    print(f"  平均时间: {mean_orig:.2f} μs")
    print(f"  中位数:   {median_orig:.2f} μs")
    print(f"  标准差:   {std_orig:.2f} μs")
    print(f"  最小值:   {np.min(times_orig):.2f} μs")
    print(f"  最大值:   {np.max(times_orig):.2f} μs")
    
    print(f"\n【性能提升】")
    print(f"  平均时间差值: {diff:.2f} μs")
    print(f"  性能提升:     {improvement:.2f}%")
    
    if improvement > 0:
        print(f"  评价:         优化版本比原始版本快 {improvement:.2f}%")
    else:
        print(f"  评价:         优化版本比原始版本慢 {abs(improvement):.2f}%")
    
    print("="*70)
    
    # 绘制对比图
    print("\n正在生成对比图...")
    output_file = Path(__file__).parent / 'kf_performance_comparison.png'
    plot_comparison(times_opt, times_orig, str(output_file))
    
    print("\n✓ 分析完成！")


if __name__ == '__main__':
    main()
