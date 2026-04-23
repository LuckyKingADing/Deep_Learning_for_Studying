import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def compareTCHisStatistics(file1, file2, outputDir):
    """
    比较两个TC历史统计数据
    :param file1: 第一个文件路径
    :param file2: 第二个文件路径
    :param outputDir: 输出目录
    """
    # 确保输出目录存在
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    # 读取两个文件的数据
    tbl1 = readCustomFile(file1)
    tbl2 = readCustomFile(file2)

    # 提取TC数据（第1、4、5、8列对应的索引）
    tc_mask1 = tbl1['type'] == 'TC'
    tc_data1 = tbl1.loc[tc_mask1, ['H02', 'H1', 'V02', 'V1']].values  # H:0-0.2, H:>1, V:0-0.2, V:>1
    datasets = tbl1.loc[tc_mask1, 'dataset'].values

    tc_mask2 = tbl2['type'] == 'TC'
    tc_data2 = tbl2.loc[tc_mask2, ['H02', 'H1', 'V02', 'V1']].values

    # 计算差值
    diff_data = tc_data2 - tc_data1

    # 保存统计结果
    saveStats(diff_data, datasets, outputDir)

    # 生成对比图
    plotComparison(diff_data, datasets, outputDir)


def readCustomFile(filename):
    """
    读取自定义格式的文件
    :param filename: 文件路径
    :return: DataFrame
    """
    # 读取原始数据（跳过第一行说明）
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()[1:]  # 跳过第一行

    # 解析数据
    data = []
    for line in lines:
        line = line.strip()
        if line:
            parts = line.split('\t')  # 假设是制表符分隔
            if len(parts) >= 10:
                data.append(parts[:10])  # 取前10列

    # 创建DataFrame
    df = pd.DataFrame(data, columns=['dataset', 'type', 'H02', 'H25', 'H51', 'H1', 'V02', 'V25', 'V51', 'V1'])

    # 处理缺失的dataset名称
    for i in range(1, len(df)):
        if df.iloc[i]['dataset'] == '':
            df.iat[i, 0] = df.iloc[i-1]['dataset']  # 继承上一行的dataset名称

    # 转换数值列
    num_cols = ['H02', 'H25', 'H51', 'H1', 'V02', 'V25', 'V51', 'V1']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def saveStats(diffData, datasets, outputDir):
    """
    保存统计结果
    :param diffData: 差值数据
    :param datasets: 数据集名称
    :param outputDir: 输出目录
    """
    # 计算均值
    mean_diff = np.mean(diffData, axis=0)
    all_data = np.vstack([diffData, mean_diff])
    
    # 创建DataFrame
    df = pd.DataFrame(all_data, 
                     columns=['H_0_0.2', 'H_gt1', 'V_0_0.2', 'V_gt1'],
                     index=list(datasets) + ['Mean'])
    
    # 保存结果
    output_file = os.path.join(outputDir, 'TC_Difference_Statistics.csv')
    df.to_csv(output_file)
    print(f'统计结果已保存至: {output_file}')


def plotComparison(diffData, datasets, outputDir):
    """
    绘制对比图
    :param diffData: 差值数据
    :param datasets: 数据集名称
    :param outputDir: 输出目录
    """
    # 图1：误差0-0.2米对比
    fig1 = plt.figure(figsize=(10, 8), facecolor='white')
    fig1.suptitle('误差0-0.2米占比对比')

    # 水平误差
    plt.subplot(2, 1, 1)
    bars = plt.bar(range(len(diffData[:, 0])), diffData[:, 0], color=[0.2, 0.6, 0.8])
    plt.title('水平误差0-0.2米')
    plt.ylabel('占比差值(%)')
    
    # 添加数值标签
    for i, (bar, y_val) in enumerate(zip(bars, diffData[:, 0])):
        plt.text(bar.get_x() + bar.get_width()/2, y_val + np.sign(y_val)*0.5, 
                 f'{y_val:.2f}', 
                 ha='center', va='bottom' if y_val >= 0 else 'top',
                 fontsize=9, fontweight='bold')
    
    plt.xticks(range(len(datasets)), datasets, rotation=45, ha='right')
    plt.grid(True)

    # 高程误差
    plt.subplot(2, 1, 2)
    bars = plt.bar(range(len(diffData[:, 2])), diffData[:, 2], color=[0.8, 0.4, 0.2])
    plt.title('高程误差0-0.2米')
    plt.ylabel('占比差值(%)')
    
    # 添加数值标签
    for i, (bar, y_val) in enumerate(zip(bars, diffData[:, 2])):
        plt.text(bar.get_x() + bar.get_width()/2, y_val + np.sign(y_val)*0.5, 
                 f'{y_val:.2f}', 
                 ha='center', va='bottom' if y_val >= 0 else 'top',
                 fontsize=9, fontweight='bold')
    
    plt.xticks(range(len(datasets)), datasets, rotation=45, ha='right')
    plt.grid(True)

    plt.tight_layout()
    
    # 图2：误差>1.0米对比
    fig2 = plt.figure(figsize=(10, 8), facecolor='white')
    fig2.suptitle('误差>1.0米占比对比')

    # 水平误差
    plt.subplot(2, 1, 1)
    bars = plt.bar(range(len(diffData[:, 1])), diffData[:, 1], color=[0.2, 0.6, 0.8])
    plt.title('水平误差>1.0米')
    plt.ylabel('占比差值(%)')
    
    # 添加数值标签
    for i, (bar, y_val) in enumerate(zip(bars, diffData[:, 1])):
        plt.text(bar.get_x() + bar.get_width()/2, y_val + np.sign(y_val)*0.5, 
                 f'{y_val:.2f}', 
                 ha='center', va='bottom' if y_val >= 0 else 'top',
                 fontsize=9, fontweight='bold')
    
    plt.xticks(range(len(datasets)), datasets, rotation=45, ha='right')
    plt.grid(True)

    # 高程误差
    plt.subplot(2, 1, 2)
    bars = plt.bar(range(len(diffData[:, 3])), diffData[:, 3], color=[0.8, 0.4, 0.2])
    plt.title('高程误差>1.0米')
    plt.ylabel('占比差值(%)')
    
    # 添加数值标签
    for i, (bar, y_val) in enumerate(zip(bars, diffData[:, 3])):
        plt.text(bar.get_x() + bar.get_width()/2, y_val + np.sign(y_val)*0.5, 
                 f'{y_val:.2f}', 
                 ha='center', va='bottom' if y_val >= 0 else 'top',
                 fontsize=9, fontweight='bold')
    
    plt.xticks(range(len(datasets)), datasets, rotation=45, ha='right')
    plt.grid(True)

    plt.tight_layout()
    
    # 保存图像
    fig1.savefig(os.path.join(outputDir, 'Error_0-0.2m_Comparison.png'), dpi=300, bbox_inches='tight')
    fig2.savefig(os.path.join(outputDir, 'Error_gt1m_Comparison.png'), dpi=300, bbox_inches='tight')
    print(f'图表已保存至: {outputDir}')
    
    plt.close(fig1)
    plt.close(fig2)


# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的参数）
    # compareTCHisStatistics(file1, file2, outputDir)
    pass
