import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def compareDH_Dalt(file1, file2, outputDir):
    """
    比较两个文件中的DH和Dalt数据
    :param file1: 第一个文件路径
    :param file2: 第二个文件路径
    :param outputDir: 输出目录
    """
    # 确保输出目录存在
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    # 读取两个文件的数据（使用新解析方法）
    tbl1 = parseCustomFile(file1)
    tbl2 = parseCustomFile(file2)

    # 提取TC行数据（dh和dalt列）
    tc_mask1 = tbl1['type'].str.lower() == 'tc'
    tc_mask2 = tbl2['type'].str.lower() == 'tc'

    # 提取数据并计算差值
    tc_data1 = tbl1.loc[tc_mask1, ['dh', 'dalt']].values
    datasets = tbl1.loc[tc_mask1, 'dataset'].values
    tc_data2 = tbl2.loc[tc_mask2, ['dh', 'dalt']].values
    diff_data = tc_data2 - tc_data1  # [dh_diff, dalt_diff]

    # 保存统计结果
    saveStats(diff_data, datasets, outputDir)

    # 生成对比图
    plotComparison(diff_data, datasets, ['dh', 'dalt'], outputDir)


def parseCustomFile(filename):
    """
    解析自定义格式的文件
    :param filename: 文件路径
    :return: DataFrame
    """
    # 读取所有文本行
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 跳过空行
    lines = [line.strip() for line in lines if line.strip()]

    # 验证数据完整性
    if len(lines) < 2:
        raise ValueError('文件数据不完整，至少需要标题行+1组数据')

    # 提取标题
    headers = lines[0].split()
    
    # 初始化数据存储
    data_rows = []

    # 逐组处理LC/TC行
    i = 1
    while i < len(lines):
        if i+1 >= len(lines):
            break  # 防止越界

        # 解析LC行 (dataset存在)
        lc_data = lines[i].split()
        if len(lc_data) >= 9:
            current_dataset = lc_data[0]
            
            # 解析TC行 (dataset缺失)
            tc_data = lines[i+1].split()
            
            # 验证列数一致性
            if len(lc_data) == 9 and len(tc_data) == 8:
                # 合并数据集（TC行继承LC的dataset）
                data_rows.append([current_dataset] + lc_data[1:])  # LC行
                data_rows.append([current_dataset] + tc_data)      # TC行
                
        i += 2

    # 创建DataFrame
    if data_rows:
        # 使用适当的列名
        df = pd.DataFrame(data_rows, columns=['dataset', 'type', 'dh', 'dalt', 'col4', 'col5', 'col6', 'col7', 'col8'])
        
        # 只保留需要的列
        df = df[['dataset', 'type', 'dh', 'dalt']]
        
        # 转换数值列
        df['dh'] = pd.to_numeric(df['dh'], errors='coerce')
        df['dalt'] = pd.to_numeric(df['dalt'], errors='coerce')
    else:
        # 如果没有数据，创建空的DataFrame
        df = pd.DataFrame(columns=['dataset', 'type', 'dh', 'dalt'])

    return df


def saveStats(diffData, datasets, outputDir):
    """
    保存统计结果
    :param diffData: 差值数据
    :param datasets: 数据集名称
    :param outputDir: 输出目录
    """
    # 创建基础统计表
    df = pd.DataFrame(diffData, 
                      columns=['dh_diff', 'dalt_diff'],
                      index=datasets)

    # 计算全局均值（1x2向量）
    global_mean = np.mean(diffData, axis=0)

    # 将均值作为新行添加到表格底部
    mean_df = pd.DataFrame([global_mean], 
                           columns=['dh_diff', 'dalt_diff'],
                           index=['Mean'])
    stats_with_mean = pd.concat([df, mean_df])

    # 保存结果
    output_file = os.path.join(outputDir, 'TC_Difference_Statistics.csv')
    stats_with_mean.to_csv(output_file)
    print(f'✅ 统计结果已保存至: {output_file}')


def plotComparison(diffData, datasets, colNames, outputDir):
    """
    绘制对比图
    :param diffData: 差值数据
    :param datasets: 数据集名称
    :param colNames: 列名
    :param outputDir: 输出目录
    """
    colors = [[0.2, 0.5, 0.8], [0.8, 0.4, 0.2]]  # 蓝/橙配色

    fig = plt.figure(figsize=(11, 6), facecolor='white')
    fig.suptitle('max_error')

    for k in range(2):
        plt.subplot(2, 1, k+1)
        bars = plt.bar(range(len(diffData[:, k])), diffData[:, k], color=colors[k])
        plt.ylabel(f'{colNames[k]} 差值', fontweight='bold')
        plt.grid(True)

        # 设置X轴标签（45度防重叠）
        if k == 1:  # 只在第二个子图显示x轴标签
            plt.xticks(range(len(datasets)), datasets, rotation=45, ha='right')
        else:
            plt.xticks(range(len(datasets)), [])  # 第一个子图不显示x轴标签

        # 动态添加数值标签
        y_range = max(abs(diffData[:, k])) * 0.25  # 动态偏移基准
        for i, (bar, y_val) in enumerate(zip(bars, diffData[:, k])):
            offset = np.sign(y_val) * y_range  # 自动避让方向
            plt.text(bar.get_x() + bar.get_width()/2, y_val + offset, 
                     f'{y_val:.3f}',
                     ha='center', va='bottom',
                     fontsize=9, fontweight='bold',
                     color=[0.3, 0.3, 0.3])

    # 保存图像
    plt.tight_layout()
    output_file = os.path.join(outputDir, 'maxerror_comparison.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f'可视化图表已保存至: {outputDir}')
    
    plt.close(fig)


# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的参数）
    # compareDH_Dalt(file1, file2, outputDir)
    pass
