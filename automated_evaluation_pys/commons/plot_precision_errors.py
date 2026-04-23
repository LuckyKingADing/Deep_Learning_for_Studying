import numpy as np
import matplotlib.pyplot as plt
import os
import re

def plot_precision_errors(filename='d:/dockers/rt/tc_shiche_data/20251209_yiyuan/summary/precison_all.txt'):
    """
    绘制精度误差图
    :param filename: 输入文件路径
    """
    # 尝试打开文件
    try:
        with open(filename, 'r', encoding='utf-8') as fid:
            # 读取数据
            data_lines = []
            for line in fid:
                line = line.strip()
                if line:
                    data_lines.append(line)
    except FileNotFoundError:
        print("无法打开文件")
        return

    # 解析数据
    num_rows = len(data_lines)
    scene_types = []
    horizontal_rms = []
    horizontal_cep99 = []
    horizontal_max = []

    lateral_rms = []
    lateral_cep99 = []
    lateral_max = []

    forward_rms = []
    forward_cep99 = []
    forward_max = []

    # 解析每一行数据
    for i in range(1, num_rows):  # 跳过标题行
        line = data_lines[i]
        # 使用制表符分割数据
        parts = [part.strip() for part in line.split('\t') if part.strip()]

        if len(parts) < 14:  # 确保有足够的列
            continue

        # 提取场景类型（第一列）
        scene_types.append(parts[0])

        # 提取水平位置误差数据 (CEP99在第5列, max在第6列, rms在第3列)
        horizontal_rms.append(float(parts[2]))  # 第3列
        horizontal_cep99.append(float(parts[4]))  # 第5列
        horizontal_max.append(float(parts[5]))  # 第6列

        # 提取横向位置误差数据 (CEP99在第9列, max在第10列, rms在第7列)
        lateral_rms.append(float(parts[6]))  # 第7列
        lateral_cep99.append(float(parts[8]))  # 第9列
        lateral_max.append(float(parts[9]))  # 第10列

        # 提取前进方向位置误差数据 (CEP99在第13列, max在第14列, rms在第11列)
        forward_rms.append(float(parts[10]))  # 第11列
        forward_cep99.append(float(parts[12]))  # 第13列
        forward_max.append(float(parts[13]))  # 第14列

    # 移除最后两行 ("去除隧道场景" 和 "全场景")
    scene_types = scene_types[:-2]
    horizontal_rms = horizontal_rms[:-2]
    horizontal_cep99 = horizontal_cep99[:-2]
    horizontal_max = horizontal_max[:-2]

    lateral_rms = lateral_rms[:-2]
    lateral_cep99 = lateral_cep99[:-2]
    lateral_max = lateral_max[:-2]

    forward_rms = forward_rms[:-2]
    forward_cep99 = forward_cep99[:-2]
    forward_max = forward_max[:-2]

    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

    # 创建保存路径（保持与输入文件相同的目录）
    save_dir = os.path.dirname(filename)

    # 水平位置误差图
    fig, axes = plt.subplots(3, 1, figsize=(12, 9))
    fig.suptitle('水平位置误差')

    # CEP99
    axes[0].bar(range(len(horizontal_cep99)), horizontal_cep99, color='k', edgecolor='k')
    axes[0].set_title('水平位置误差 - CEP99')
    axes[0].set_ylabel('误差 (m)')
    axes[0].set_xticks(range(len(scene_types)))
    axes[0].set_xticklabels(scene_types, rotation=45, ha='right')
    axes[0].grid(True)
    # 在柱子上显示数值
    for i, v in enumerate(horizontal_cep99):
        axes[0].text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    # Max
    axes[1].bar(range(len(horizontal_max)), horizontal_max, color='k', edgecolor='k')
    axes[1].set_title('水平位置误差 - Max')
    axes[1].set_ylabel('误差 (m)')
    axes[1].set_xticks(range(len(scene_types)))
    axes[1].set_xticklabels(scene_types, rotation=45, ha='right')
    axes[1].grid(True)
    # 在柱子上显示数值
    for i, v in enumerate(horizontal_max):
        axes[1].text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    # RMS
    axes[2].bar(range(len(horizontal_rms)), horizontal_rms, color='k', edgecolor='k')
    axes[2].set_title('水平位置误差 - RMS')
    axes[2].set_ylabel('误差 (m)')
    axes[2].set_xticks(range(len(scene_types)))
    axes[2].set_xticklabels(scene_types, rotation=45, ha='right')
    axes[2].grid(True)
    # 在柱子上显示数值
    for i, v in enumerate(horizontal_rms):
        axes[2].text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'horizontal_position_errors.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 横向位置误差图
    fig, axes = plt.subplots(3, 1, figsize=(12, 9))
    fig.suptitle('横向位置误差')

    # CEP99
    axes[0].bar(range(len(lateral_cep99)), lateral_cep99, color='k', edgecolor='k')
    axes[0].set_title('横向位置误差 - CEP99')
    axes[0].set_ylabel('误差 (m)')
    axes[0].set_xticks(range(len(scene_types)))
    axes[0].set_xticklabels(scene_types, rotation=45, ha='right')
    axes[0].grid(True)
    # 在柱子上显示数值
    for i, v in enumerate(lateral_cep99):
        axes[0].text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    # Max
    axes[1].bar(range(len(lateral_max)), lateral_max, color='k', edgecolor='k')
    axes[1].set_title('横向位置误差 - Max')
    axes[1].set_ylabel('误差 (m)')
    axes[1].set_xticks(range(len(scene_types)))
    axes[1].set_xticklabels(scene_types, rotation=45, ha='right')
    axes[1].grid(True)
    # 在柱子上显示数值
    for i, v in enumerate(lateral_max):
        axes[1].text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    # RMS
    axes[2].bar(range(len(lateral_rms)), lateral_rms, color='k', edgecolor='k')
    axes[2].set_title('横向位置误差 - RMS')
    axes[2].set_ylabel('误差 (m)')
    axes[2].set_xticks(range(len(scene_types)))
    axes[2].set_xticklabels(scene_types, rotation=45, ha='right')
    axes[2].grid(True)
    # 在柱子上显示数值
    for i, v in enumerate(lateral_rms):
        axes[2].text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'lateral_position_errors.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 前进方向位置误差图
    fig, axes = plt.subplots(3, 1, figsize=(12, 9))
    fig.suptitle('前进方向位置误差')

    # CEP99
    axes[0].bar(range(len(forward_cep99)), forward_cep99, color='k', edgecolor='k')
    axes[0].set_title('前进方向位置误差 - CEP99')
    axes[0].set_ylabel('误差 (m)')
    axes[0].set_xticks(range(len(scene_types)))
    axes[0].set_xticklabels(scene_types, rotation=45, ha='right')
    axes[0].grid(True)
    # 在柱子上显示数值
    for i, v in enumerate(forward_cep99):
        axes[0].text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    # Max
    axes[1].bar(range(len(forward_max)), forward_max, color='k', edgecolor='k')
    axes[1].set_title('前进方向位置误差 - Max')
    axes[1].set_ylabel('误差 (m)')
    axes[1].set_xticks(range(len(scene_types)))
    axes[1].set_xticklabels(scene_types, rotation=45, ha='right')
    axes[1].grid(True)
    # 在柱子上显示数值
    for i, v in enumerate(forward_max):
        axes[1].text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    # RMS
    axes[2].bar(range(len(forward_rms)), forward_rms, color='k', edgecolor='k')
    axes[2].set_title('前进方向位置误差 - RMS')
    axes[2].set_ylabel('误差 (m)')
    axes[2].set_xticks(range(len(scene_types)))
    axes[2].set_xticklabels(scene_types, rotation=45, ha='right')
    axes[2].grid(True)
    # 在柱子上显示数值
    for i, v in enumerate(forward_rms):
        axes[2].text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'forward_position_errors.png'), dpi=300, bbox_inches='tight')
    plt.close()

    print('绘图已完成并保存。')

# 如果直接运行此脚本，则执行plot_precision_errors函数
if __name__ == "__main__":
    plot_precision_errors()
