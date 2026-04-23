#!/usr/bin/env python3
"""
测试plotStatsComparisonaAll函数的脚本
"""

import numpy as np
import os
import sys
from pathlib import Path

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bppaps_msfdebg_rts import plotStatsComparisonaAll

def generate_test_data(n_datasets=3):
    """
    生成测试统计数据
    """
    statsall = []
    
    for i in range(n_datasets):
        # 生成模拟统计数据
        lc_rms = np.random.rand(7) * 0.5  # 7个参数的RMS值
        tc_rms = np.random.rand(7) * 0.5
        lc_max = np.random.rand(7) * 1.0  # 7个参数的最大绝对误差
        tc_max = np.random.rand(7) * 1.0
        
        # 区间统计 (2行4列 - 水平位置和高程，4个区间)
        lc_intervals = np.random.rand(2, 4) * 100  # 百分比
        tc_intervals = np.random.rand(2, 4) * 100
        
        stat = {
            'LC': {
                'rms': lc_rms,
                'max_abs': lc_max,
                'interval_percent': lc_intervals
            },
            'TC': {
                'rms': tc_rms,
                'max_abs': tc_max,
                'interval_percent': tc_intervals
            },
            'dataset': f'Dataset_{i}'
        }
        
        statsall.append(stat)
    
    return statsall

def main():
    """
    主函数 - 测试plotStatsComparisonaAll
    """
    print("开始测试plotStatsComparisonaAll函数...")
    
    # 生成测试数据
    print("生成测试数据...")
    test_statsall = generate_test_data(n_datasets=3)  # 减少数据集数量以便观察
    
    # 创建保存目录
    save_dir = "/tmp/test_plotStatsComparisonaAll"
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"在目录 {save_dir} 中生成图表...")
    
    # 调用绘图函数
    plotStatsComparisonaAll(test_statsall, save_dir)
    
    # 检查生成的文件
    # 根据最新的实现，应该生成：
    # 1. 每个参数的RMS和MAX对比图（共7个）
    # 2. 'Hor Pos'和'Alt'的误差分布图（共2个）
    # 3. 三个总的对比图
    param_labels = ['pitch', 'roll', 'yaw', 'hor_vel', 'ver_vel', 'hor_pos', 'alt']
    expected_files = [
        'rms_comparison.png',
        'max_comparison.png',
        'stats_comparison.png'
    ]
    
    # 添加每个参数的RMS和MAX对比图
    for label in param_labels:
        expected_files.append(f'{label}_stats_comparison.png')
    
    # 添加'Hor Pos'和'Alt'的误差分布图
    expected_files.extend([
        'hor_pos_error_distribution.png',
        'alt_error_distribution.png'
    ])
    
    print("检查生成的文件:")
    for filename in expected_files:
        filepath = os.path.join(save_dir, filename)
        if os.path.exists(filepath):
            print(f"  ✓ {filename} 已生成 ({os.path.getsize(filepath)} bytes)")
        else:
            print(f"  ✗ {filename} 未生成")
    
    print(f"\n测试完成！图表已保存到: {save_dir}")

if __name__ == "__main__":
    main()
