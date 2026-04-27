import matplotlib.pyplot as plt
import numpy as np
import os

def plot_stats_comparison(stats, save_dir):
    """
    绘制统计对比图
    :param stats: 统计数据，包含LC和TC的rms、max_abs、interval_percent等信息
    :param save_dir: 保存目录
    """
    # 创建第一幅图：误差统计对比
    fig1 = plt.figure(figsize=(10, 8))

    # ===== 上图：RMS对比 =====
    plt.subplot(2, 1, 1)

    # 提取后4列数据 (vh, vu, dh, dalt)
    lc_rms = stats.LC.rms[3:7]  # Python索引从0开始，所以4:7对应3:7
    tc_rms = stats.TC.rms[3:7]

    # 柱状图绘制
    bar_width = 0.35
    x = np.arange(1, 5)  # 1:4
    bar1 = plt.bar(x - bar_width/2, lc_rms, bar_width, color=[0.2, 0.5, 0.8], label='LC')
    bar2 = plt.bar(x + bar_width/2, tc_rms, bar_width, color=[0.8, 0.4, 0.2], label='TC')

    # 添加数值标签
    for i in range(4):
        plt.text(x[i] - bar_width/2, lc_rms[i] + 0.05*max(plt.gca().get_ylim()), 
                 f'{lc_rms[i]:.3f}', 
                 ha='center', fontsize=10)
        plt.text(x[i] + bar_width/2, tc_rms[i] + 0.05*max(plt.gca().get_ylim()), 
                 f'{tc_rms[i]:.3f}', 
                 ha='center', fontsize=10)

    # 图形美化
    plt.xticks(x, ['vh', 'vu', 'dh', 'dalt'])
    plt.ylabel('RMS误差')
    plt.title('RMS误差对比')
    plt.legend(loc='upper left')
    plt.grid(True)

    # ===== 下图：最大绝对误差对比 =====
    plt.subplot(2, 1, 2)

    # 提取后4列数据
    lc_max = stats.LC.max_abs[3:7]  # Python索引从0开始，所以4:7对应3:7
    tc_max = stats.TC.max_abs[3:7]

    # 柱状图绘制
    bar1 = plt.bar(x - bar_width/2, lc_max, bar_width, color=[0.2, 0.5, 0.8], label='LC')
    bar2 = plt.bar(x + bar_width/2, tc_max, bar_width, color=[0.8, 0.4, 0.2], label='TC')

    # 添加数值标签
    for i in range(4):
        plt.text(x[i] - bar_width/2, lc_max[i] + 0.05*max(plt.gca().get_ylim()), 
                 f'{lc_max[i]:.3f}', 
                 ha='center', fontsize=10)
        plt.text(x[i] + bar_width/2, tc_max[i] + 0.05*max(plt.gca().get_ylim()), 
                 f'{tc_max[i]:.3f}', 
                 ha='center', fontsize=10)

    # 图形美化
    plt.xticks(x, ['vh', 'vu', 'dh', 'dalt'])
    plt.ylabel('最大绝对误差')
    plt.title('最大绝对误差对比')
    plt.grid(True)

    # 为整个图形设置标题
    fig1.suptitle(stats.dataset)

    # 创建保存目录（如果不存在）
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 保存第一幅图
    plt.savefig(os.path.join(save_dir, 'true_error.emf'))
    plt.savefig(os.path.join(save_dir, 'true_error.png'), dpi=300, bbox_inches='tight')
    plt.close(fig1)

    # 创建第二幅图：区间分布对比
    fig2 = plt.figure(figsize=(10, 8))

    # 定义区间标签
    interval_labels = ['≤0.2', '0.2-0.5', '0.5-1', '>1']

    # ===== 上图：水平位置误差区间分布 =====
    plt.subplot(2, 1, 1)

    # 提取水平位置误差数据 (第1行，Python索引为0)
    lc_hor_pos = stats.LC.interval_percent[0, :]
    tc_hor_pos = stats.TC.interval_percent[0, :]

    # 柱状图绘制
    bar_width = 0.35
    x = np.arange(1, 5)  # 1:4
    bar1 = plt.bar(x - bar_width/2, lc_hor_pos, bar_width, color=[0.3, 0.7, 0.4], label='LC')
    bar2 = plt.bar(x + bar_width/2, tc_hor_pos, bar_width, color=[0.7, 0.2, 0.5], label='TC')

    # 添加数值标签
    for i in range(4):
        plt.text(x[i] - bar_width/2, lc_hor_pos[i] + 1, 
                 f'{lc_hor_pos[i]:.2f}%', 
                 ha='center', fontsize=9)
        plt.text(x[i] + bar_width/2, tc_hor_pos[i] + 1, 
                 f'{tc_hor_pos[i]:.2f}%', 
                 ha='center', fontsize=9)

    # 图形美化
    plt.xticks(x, interval_labels)
    plt.ylabel('百分比 (%)')
    plt.title('水平位置误差 (dh) 区间分布对比')
    plt.legend(loc='upper left')
    plt.ylim([0, max(max(lc_hor_pos), max(tc_hor_pos)) * 1.2])
    plt.grid(True)

    # ===== 下图：垂直误差区间分布 =====
    plt.subplot(2, 1, 2)

    # 提取垂直误差数据 (第2行，Python索引为1)
    lc_alt = stats.LC.interval_percent[1, :]  # 假设这里应该是第2行而不是第3行，因为Python索引从0开始
    tc_alt = stats.TC.interval_percent[1, :]

    # 柱状图绘制
    bar1 = plt.bar(x - bar_width/2, lc_alt, bar_width, color=[0.3, 0.7, 0.4], label='LC')
    bar2 = plt.bar(x + bar_width/2, tc_alt, bar_width, color=[0.7, 0.2, 0.5], label='TC')

    # 添加数值标签
    for i in range(4):
        plt.text(x[i] - bar_width/2, lc_alt[i] + 1, 
                 f'{lc_alt[i]:.2f}%', 
                 ha='center', fontsize=9)
        plt.text(x[i] + bar_width/2, tc_alt[i] + 1, 
                 f'{tc_alt[i]:.2f}%', 
                 ha='center', fontsize=9)

    # 图形美化
    plt.xticks(x, interval_labels)
    plt.ylabel('百分比 (%)')
    plt.title('高程误差 (dalt) 区间分布对比')
    plt.ylim([0, max(max(lc_alt), max(tc_alt)) * 1.2])
    plt.grid(True)

    # 为整个图形设置标题
    fig2.suptitle(stats.dataset)

    # 保存第二幅图
    plt.savefig(os.path.join(save_dir, 'true_error_his.emf'))
    plt.savefig(os.path.join(save_dir, 'true_error_his.png'), dpi=300, bbox_inches='tight')
    plt.close(fig2)

# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的统计数据和保存目录）
    # plot_stats_comparison(your_stats, 'your_save_directory')
    pass
