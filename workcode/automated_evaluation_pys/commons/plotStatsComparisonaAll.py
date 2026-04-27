import matplotlib.pyplot as plt
import numpy as np
import os

def plotGroupedBars(ax, data_LC, data_TC, groupLabels, colors, width, xlabelon):
    """
    绘制分组柱状图
    :param ax: matplotlib轴对象
    :param data_LC: LC数据
    :param data_TC: TC数据
    :param groupLabels: 组标签
    :param colors: 颜色字典
    :param width: 柱状图宽度
    :param xlabelon: 是否显示x轴标签
    """
    # 计算每组位置
    x = np.arange(1, len(data_LC) + 1)

    # 绘制LC柱状图
    bars_LC = ax.bar(x - width/4, data_LC, width/2, 
                     color=colors['LC'], 
                     edgecolor='k', 
                     label='LC')

    # 绘制TC柱状图
    bars_TC = ax.bar(x + width/4, data_TC, width/2, 
                     color=colors['TC'], 
                     edgecolor='k', 
                     label='TC')

    # 添加数值标签
    for i in range(len(data_LC)):
        ax.text(x[i] - width/4, data_LC[i], 
                f'{data_LC[i]:.2f}', 
                ha='center', va='bottom', fontsize=8)

        ax.text(x[i] + width/4, data_TC[i], 
                f'{data_TC[i]:.2f}', 
                ha='center', va='bottom', fontsize=8)

    # 设置坐标轴属性
    if xlabelon:
        ax.set_xticks(x)
        ax.set_xticklabels(groupLabels, rotation=45, ha='right')
    else:
        ax.set_xticks(x)
        ax.set_xticklabels([])

    # 添加参考线
    y_range = ax.get_ylim()
    ax.plot(ax.get_xlim(), [0, 0], 'k-', linewidth=0.5)
    ax.set_ylim(y_range)  # 保持Y轴范围不变

def plotStatsComparisonAll(statsall, save_dir):
    """
    绘制统计比较图
    :param statsall: 包含统计数据的列表
    :param save_dir: 保存目录
    """
    # ===== 1. 参数初始化 =====
    datasets = [s.dataset for s in statsall]  # 所有数据集名称
    numGroups = len(statsall)  # 数据集数量
    colors = {'LC': [0.2, 0.6, 0.8], 'TC': [0.8, 0.4, 0.2]}  # LC蓝/TC橙
    barWidth = 0.8  # 柱状图宽度

    # ===== 2. 提取关键数据 =====
    # 极值数据 (max_abs)
    comp6_LC = [s.LC.max_abs[5] for s in statsall]  # 第6个元素，Python索引为5
    comp6_TC = [s.TC.max_abs[5] for s in statsall]
    comp7_LC = [s.LC.max_abs[6] for s in statsall]  # 第7个元素，Python索引为6
    comp7_TC = [s.TC.max_abs[6] for s in statsall]

    # 区间数据 (interval_percent)
    inth1_LC = [s.LC.interval_percent[0, 0] for s in statsall]  # 第1行第1列
    inth1_TC = [s.TC.interval_percent[0, 0] for s in statsall]
    inth4_LC = [s.LC.interval_percent[0, 3] for s in statsall]  # 第1行第4列
    inth4_TC = [s.TC.interval_percent[0, 3] for s in statsall]
    intv1_LC = [s.LC.interval_percent[1, 0] for s in statsall]  # 第2行第1列
    intv1_TC = [s.TC.interval_percent[1, 0] for s in statsall]
    intv4_LC = [s.LC.interval_percent[1, 3] for s in statsall]  # 第2行第4列
    intv4_TC = [s.TC.interval_percent[1, 3] for s in statsall]

    # ===== 3. 绘制图1：极值误差对比 =====
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig1.suptitle('极值误差对比')

    # 子图1：第6元素对比（水平误差）
    plotGroupedBars(ax1, comp6_LC, comp6_TC, datasets, colors, barWidth, 0)
    ax1.set_ylabel('水平误差值')
    ax1.legend(loc='upper right')

    # 子图2：第7元素对比（高程误差）
    plotGroupedBars(ax2, comp7_LC, comp7_TC, datasets, colors, barWidth, 1)
    ax2.set_ylabel('高程误差值')

    # ===== 4. 绘制图2：区间分布1 =====
    fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(10, 6))
    fig2.suptitle('误差区间分布(0-0.2)')

    # 子图1：水平误差
    plotGroupedBars(ax3, inth1_LC, inth1_TC, datasets, colors, barWidth, 0)
    ax3.set_ylabel('水平误差百分比(%)')
    ax3.grid(True)

    # 子图2：高程误差
    plotGroupedBars(ax4, intv1_LC, intv1_TC, datasets, colors, barWidth, 1)
    ax4.set_ylabel('高程误差百分比(%)')
    ax4.grid(True)
    ax4.legend(loc='upper right')

    # ===== 5. 绘制图3：区间分布4 =====
    fig3, (ax5, ax6) = plt.subplots(2, 1, figsize=(10, 6))
    fig3.suptitle('误差区间分布(>1)')

    # 子图1：水平误差
    plotGroupedBars(ax5, inth4_LC, inth4_TC, datasets, colors, barWidth, 0)
    ax5.set_ylabel('水平误差百分比(%)')
    ax5.grid(True)

    # 子图2：高程误差
    plotGroupedBars(ax6, intv4_LC, intv4_TC, datasets, colors, barWidth, 1)
    ax6.set_ylabel('高程误差百分比(%)')
    ax6.grid(True)
    ax6.legend(loc='upper right')

    # 创建保存目录（如果不存在）
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 保存图片
    fig1.savefig(os.path.join(save_dir, 'max_error.emf'))
    fig1.savefig(os.path.join(save_dir, 'max_error.png'), dpi=300, bbox_inches='tight')
    fig2.savefig(os.path.join(save_dir, 'true_error_his1.emf'))
    fig2.savefig(os.path.join(save_dir, 'true_error_his1.png'), dpi=300, bbox_inches='tight')
    fig3.savefig(os.path.join(save_dir, 'true_error_his4.emf'))
    fig3.savefig(os.path.join(save_dir, 'true_error_his4.png'), dpi=300, bbox_inches='tight')

    # 关闭图形以释放内存
    plt.close(fig1)
    plt.close(fig2)
    plt.close(fig3)

# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的统计数据和保存目录）
    # plotStatsComparisonAll(your_statsall, 'your_save_directory')
    pass
