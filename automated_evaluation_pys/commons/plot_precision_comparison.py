import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd

def plot_precision_comparison():
    """
    绘制精度对比图
    """
    # 读取数据
    filename1 = 'd:/dockers/rt/tc_shiche_data/20251205_yiyuan/summary/precison_all.txt'
    filename2 = 'd:/dockers/rt/tc_shiche_data/20251209_yiyuan/summary/precison_all.txt'

    # 读取第一个文件数据
    data1 = readPrecisionData(filename1)
    # 读取第二个文件数据
    data2 = readPrecisionData(filename2)

    # 获取所有场景类型
    allSceneTypes = list(set(data1['sceneTypes'] + data2['sceneTypes']))

    # 重新排序场景类型：全场景优先，然后是去除隧道场景，最后是其他场景
    reorderedSceneTypes = reorderSceneTypes(allSceneTypes)

    # 创建对比数据
    comparisonData = createComparisonData(data1, data2, reorderedSceneTypes)

    # 黄金比例
    goldenRatio = (1 + np.sqrt(5)) / 2
    figWidth = 12
    figHeight = figWidth / goldenRatio

    # 创建保存路径
    save_dir = 'd:/dockers/rt/tc_shiche_data/20251209_yiyuan/cmp'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 绘制水平位置误差对比图
    plotHorizontalError(comparisonData, figWidth, figHeight, save_dir)

    # 绘制横向位置误差对比图
    plotLateralError(comparisonData, figWidth, figHeight, save_dir)

    # 绘制前进方向位置误差对比图
    plotForwardError(comparisonData, figWidth, figHeight, save_dir)

    print('所有图表已绘制并保存。')

def reorderSceneTypes(sceneTypes):
    """
    重新排序场景类型：全场景优先，然后是去除隧道场景，最后是其他场景
    :param sceneTypes: 场景类型列表
    :return: reorderedSceneTypes: 重新排序的场景类型列表
    """
    # 初始化输出
    reorderedSceneTypes = []

    # 首先查找全场景
    if '全场景' in sceneTypes:
        reorderedSceneTypes.append('全场景')

    # 然后查找去除隧道场景
    if '去除隧道场景' in sceneTypes:
        reorderedSceneTypes.append('去除隧道场景')

    # 最后添加其他场景（按原始顺序）
    for scene in sceneTypes:
        if scene != '全场景' and scene != '去除隧道场景':
            reorderedSceneTypes.append(scene)

    return reorderedSceneTypes

def readPrecisionData(filename):
    """
    读取精度数据
    :param filename: 文件名
    :return: data: 包含精度数据的字典
    """
    # 读取文件
    with open(filename, 'r', encoding='utf-8') as fid:
        lines = fid.readlines()

    # 跳过标题行
    dataLines = lines[2:]  # 跳过前两行标题

    # 初始化数据结构
    data = {
        'sceneTypes': [],
        'horizontal_rms': [],
        'horizontal_cep99': [],
        'horizontal_max': [],
        'lateral_rms': [],
        'lateral_cep99': [],
        'lateral_max': [],
        'forward_rms': [],
        'forward_cep99': [],
        'forward_max': []
    }

    # 解析每一行数据
    for line in dataLines:
        line = line.strip()
        if line:
            # 使用制表符分割数据
            parts = [part.strip() for part in line.split('\t')]
            parts = [part for part in parts if part]  # 移除空元素

            # 提取场景类型（第一列）
            data['sceneTypes'].append(parts[0])

            # 提取水平位置误差数据 (CEP99在第5列, max在第6列, rms在第3列)
            data['horizontal_rms'].append(float(parts[2]))
            data['horizontal_cep99'].append(float(parts[4]))
            data['horizontal_max'].append(float(parts[5]))

            # 提取横向位置误差数据 (CEP99在第9列, max在第10列, rms在第7列)
            data['lateral_rms'].append(float(parts[6]))
            data['lateral_cep99'].append(float(parts[8]))
            data['lateral_max'].append(float(parts[9]))

            # 提取前进方向位置误差数据 (CEP99在第13列, max在第14列, rms在第11列)
            data['forward_rms'].append(float(parts[10]))
            data['forward_cep99'].append(float(parts[12]))
            data['forward_max'].append(float(parts[13]))

    # 将列表转换为numpy数组
    for key in data:
        if key != 'sceneTypes':
            data[key] = np.array(data[key])

    return data

def createComparisonData(data1, data2, allSceneTypes):
    """
    创建对比数据
    :param data1: 第一个数据集
    :param data2: 第二个数据集
    :param allSceneTypes: 所有场景类型
    :return: comparisonData: 对比数据
    """
    numScenes = len(allSceneTypes)

    # 初始化对比数据结构
    comparisonData = {
        'sceneTypes': allSceneTypes,
        'rtk_horizontal_cep99': np.zeros(numScenes),
        'spp_horizontal_cep99': np.zeros(numScenes),
        'rtk_horizontal_max': np.zeros(numScenes),
        'spp_horizontal_max': np.zeros(numScenes),
        'rtk_horizontal_rms': np.zeros(numScenes),
        'spp_horizontal_rms': np.zeros(numScenes),
        'rtk_lateral_cep99': np.zeros(numScenes),
        'spp_lateral_cep99': np.zeros(numScenes),
        'rtk_lateral_max': np.zeros(numScenes),
        'spp_lateral_max': np.zeros(numScenes),
        'rtk_lateral_rms': np.zeros(numScenes),
        'spp_lateral_rms': np.zeros(numScenes),
        'rtk_forward_cep99': np.zeros(numScenes),
        'spp_forward_cep99': np.zeros(numScenes),
        'rtk_forward_max': np.zeros(numScenes),
        'spp_forward_max': np.zeros(numScenes),
        'rtk_forward_rms': np.zeros(numScenes),
        'spp_forward_rms': np.zeros(numScenes)
    }

    # 填充数据
    for i, scene in enumerate(allSceneTypes):
        # 查找RTK数据（来自第一个文件）
        if scene in data1['sceneTypes']:
            idx = data1['sceneTypes'].index(scene)
            comparisonData['rtk_horizontal_cep99'][i] = data1['horizontal_cep99'][idx]
            comparisonData['rtk_horizontal_max'][i] = data1['horizontal_max'][idx]
            comparisonData['rtk_horizontal_rms'][i] = data1['horizontal_rms'][idx]

            comparisonData['rtk_lateral_cep99'][i] = data1['lateral_cep99'][idx]
            comparisonData['rtk_lateral_max'][i] = data1['lateral_max'][idx]
            comparisonData['rtk_lateral_rms'][i] = data1['lateral_rms'][idx]

            comparisonData['rtk_forward_cep99'][i] = data1['forward_cep99'][idx]
            comparisonData['rtk_forward_max'][i] = data1['forward_max'][idx]
            comparisonData['rtk_forward_rms'][i] = data1['forward_rms'][idx]

        # 查找SPP数据（来自第二个文件）
        if scene in data2['sceneTypes']:
            idx = data2['sceneTypes'].index(scene)
            comparisonData['spp_horizontal_cep99'][i] = data2['horizontal_cep99'][idx]
            comparisonData['spp_horizontal_max'][i] = data2['horizontal_max'][idx]
            comparisonData['spp_horizontal_rms'][i] = data2['horizontal_rms'][idx]

            comparisonData['spp_lateral_cep99'][i] = data2['lateral_cep99'][idx]
            comparisonData['spp_lateral_max'][i] = data2['lateral_max'][idx]
            comparisonData['spp_lateral_rms'][i] = data2['lateral_rms'][idx]

            comparisonData['spp_forward_cep99'][i] = data2['forward_cep99'][idx]
            comparisonData['spp_forward_max'][i] = data2['forward_max'][idx]
            comparisonData['spp_forward_rms'][i] = data2['forward_rms'][idx]

    return comparisonData

def plotHorizontalError(comparisonData, figWidth, figHeight, save_dir):
    """
    绘制水平位置误差对比图
    :param comparisonData: 对比数据
    :param figWidth: 图形宽度
    :param figHeight: 图形高度
    :param save_dir: 保存目录
    """
    fig, axes = plt.subplots(3, 1, figsize=(figWidth, figHeight))
    fig.suptitle('水平位置误差对比')

    # CEP99
    x = np.arange(len(comparisonData['sceneTypes']))
    width = 0.35
    axes[0].bar(x - width/2, comparisonData['rtk_horizontal_cep99'], width, label='RTK', color='red', edgecolor='black')
    axes[0].bar(x + width/2, comparisonData['spp_horizontal_cep99'], width, label='SPP', color='blue', edgecolor='black')
    axes[0].set_title('水平位置误差 - CEP99')
    axes[0].set_ylabel('误差 (m)')
    axes[0].legend(loc='upper right')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(comparisonData['sceneTypes'], rotation=45, ha='right')
    axes[0].grid(True)

    # 在柱子上显示数值
    for i in range(len(comparisonData['sceneTypes'])):
        if comparisonData['rtk_horizontal_cep99'][i] > 0 and not np.isnan(comparisonData['rtk_horizontal_cep99'][i]):
            axes[0].text(i - width/2, comparisonData['rtk_horizontal_cep99'][i], 
                        f'{comparisonData["rtk_horizontal_cep99"][i]:.3f}', 
                        ha='center', va='bottom', color='red')
        if comparisonData['spp_horizontal_cep99'][i] > 0 and not np.isnan(comparisonData['spp_horizontal_cep99'][i]):
            axes[0].text(i + width/2, comparisonData['spp_horizontal_cep99'][i], 
                        f'{comparisonData["spp_horizontal_cep99"][i]:.3f}', 
                        ha='center', va='bottom', color='blue')

    # Max
    axes[1].bar(x - width/2, comparisonData['rtk_horizontal_max'], width, label='RTK', color='red', edgecolor='black')
    axes[1].bar(x + width/2, comparisonData['spp_horizontal_max'], width, label='SPP', color='blue', edgecolor='black')
    axes[1].set_title('水平位置误差 - Max')
    axes[1].set_ylabel('误差 (m)')
    axes[1].legend(loc='upper right')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(comparisonData['sceneTypes'], rotation=45, ha='right')
    axes[1].grid(True)

    # 在柱子上显示数值
    for i in range(len(comparisonData['sceneTypes'])):
        if comparisonData['rtk_horizontal_max'][i] > 0 and not np.isnan(comparisonData['rtk_horizontal_max'][i]):
            axes[1].text(i - width/2, comparisonData['rtk_horizontal_max'][i], 
                        f'{comparisonData["rtk_horizontal_max"][i]:.3f}', 
                        ha='center', va='bottom', color='red')
        if comparisonData['spp_horizontal_max'][i] > 0 and not np.isnan(comparisonData['spp_horizontal_max'][i]):
            axes[1].text(i + width/2, comparisonData['spp_horizontal_max'][i], 
                        f'{comparisonData["spp_horizontal_max"][i]:.3f}', 
                        ha='center', va='bottom', color='blue')

    # RMS
    axes[2].bar(x - width/2, comparisonData['rtk_horizontal_rms'], width, label='RTK', color='red', edgecolor='black')
    axes[2].bar(x + width/2, comparisonData['spp_horizontal_rms'], width, label='SPP', color='blue', edgecolor='black')
    axes[2].set_title('水平位置误差 - RMS')
    axes[2].set_ylabel('误差 (m)')
    axes[2].set_xlabel('场景类型')
    axes[2].legend(loc='upper right')
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(comparisonData['sceneTypes'], rotation=45, ha='right')
    axes[2].grid(True)

    # 在柱子上显示数值
    for i in range(len(comparisonData['sceneTypes'])):
        if comparisonData['rtk_horizontal_rms'][i] > 0 and not np.isnan(comparisonData['rtk_horizontal_rms'][i]):
            axes[2].text(i - width/2, comparisonData['rtk_horizontal_rms'][i], 
                        f'{comparisonData["rtk_horizontal_rms"][i]:.3f}', 
                        ha='center', va='bottom', color='red')
        if comparisonData['spp_horizontal_rms'][i] > 0 and not np.isnan(comparisonData['spp_horizontal_rms'][i]):
            axes[2].text(i + width/2, comparisonData['spp_horizontal_rms'][i], 
                        f'{comparisonData["spp_horizontal_rms"][i]:.3f}', 
                        ha='center', va='bottom', color='blue')

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'horizontal_position_error_comparison.png'), dpi=300, bbox_inches='tight')
    plt.show()

def plotLateralError(comparisonData, figWidth, figHeight, save_dir):
    """
    绘制横向位置误差对比图
    :param comparisonData: 对比数据
    :param figWidth: 图形宽度
    :param figHeight: 图形高度
    :param save_dir: 保存目录
    """
    fig, axes = plt.subplots(3, 1, figsize=(figWidth, figHeight))
    fig.suptitle('横向位置误差对比')

    # CEP99
    x = np.arange(len(comparisonData['sceneTypes']))
    width = 0.35
    axes[0].bar(x - width/2, comparisonData['rtk_lateral_cep99'], width, label='RTK', color='red', edgecolor='black')
    axes[0].bar(x + width/2, comparisonData['spp_lateral_cep99'], width, label='SPP', color='blue', edgecolor='black')
    axes[0].set_title('横向位置误差 - CEP99')
    axes[0].set_ylabel('误差 (m)')
    axes[0].legend(loc='upper right')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(comparisonData['sceneTypes'], rotation=45, ha='right')
    axes[0].grid(True)

    # 在柱子上显示数值
    for i in range(len(comparisonData['sceneTypes'])):
        if comparisonData['rtk_lateral_cep99'][i] > 0 and not np.isnan(comparisonData['rtk_lateral_cep99'][i]):
            axes[0].text(i - width/2, comparisonData['rtk_lateral_cep99'][i], 
                        f'{comparisonData["rtk_lateral_cep99"][i]:.3f}', 
                        ha='center', va='bottom', color='red')
        if comparisonData['spp_lateral_cep99'][i] > 0 and not np.isnan(comparisonData['spp_lateral_cep99'][i]):
            axes[0].text(i + width/2, comparisonData['spp_lateral_cep99'][i], 
                        f'{comparisonData["spp_lateral_cep99"][i]:.3f}', 
                        ha='center', va='bottom', color='blue')

    # Max
    axes[1].bar(x - width/2, comparisonData['rtk_lateral_max'], width, label='RTK', color='red', edgecolor='black')
    axes[1].bar(x + width/2, comparisonData['spp_lateral_max'], width, label='SPP', color='blue', edgecolor='black')
    axes[1].set_title('横向位置误差 - Max')
    axes[1].set_ylabel('误差 (m)')
    axes[1].legend(loc='upper right')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(comparisonData['sceneTypes'], rotation=45, ha='right')
    axes[1].grid(True)

    # 在柱子上显示数值
    for i in range(len(comparisonData['sceneTypes'])):
        if comparisonData['rtk_lateral_max'][i] > 0 and not np.isnan(comparisonData['rtk_lateral_max'][i]):
            axes[1].text(i - width/2, comparisonData['rtk_lateral_max'][i], 
                        f'{comparisonData["rtk_lateral_max"][i]:.3f}', 
                        ha='center', va='bottom', color='red')
        if comparisonData['spp_lateral_max'][i] > 0 and not np.isnan(comparisonData['spp_lateral_max'][i]):
            axes[1].text(i + width/2, comparisonData['spp_lateral_max'][i], 
                        f'{comparisonData["spp_lateral_max"][i]:.3f}', 
                        ha='center', va='bottom', color='blue')

    # RMS
    axes[2].bar(x - width/2, comparisonData['rtk_lateral_rms'], width, label='RTK', color='red', edgecolor='black')
    axes[2].bar(x + width/2, comparisonData['spp_lateral_rms'], width, label='SPP', color='blue', edgecolor='black')
    axes[2].set_title('横向位置误差 - RMS')
    axes[2].set_ylabel('误差 (m)')
    axes[2].set_xlabel('场景类型')
    axes[2].legend(loc='upper right')
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(comparisonData['sceneTypes'], rotation=45, ha='right')
    axes[2].grid(True)

    # 在柱子上显示数值
    for i in range(len(comparisonData['sceneTypes'])):
        if comparisonData['rtk_lateral_rms'][i] > 0 and not np.isnan(comparisonData['rtk_lateral_rms'][i]):
            axes[2].text(i - width/2, comparisonData['rtk_lateral_rms'][i], 
                        f'{comparisonData["rtk_lateral_rms"][i]:.3f}', 
                        ha='center', va='bottom', color='red')
        if comparisonData['spp_lateral_rms'][i] > 0 and not np.isnan(comparisonData['spp_lateral_rms'][i]):
            axes[2].text(i + width/2, comparisonData['spp_lateral_rms'][i], 
                        f'{comparisonData["spp_lateral_rms"][i]:.3f}', 
                        ha='center', va='bottom', color='blue')

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'lateral_position_error_comparison.png'), dpi=300, bbox_inches='tight')
    plt.show()

def plotForwardError(comparisonData, figWidth, figHeight, save_dir):
    """
    绘制前进方向位置误差对比图
    :param comparisonData: 对比数据
    :param figWidth: 图形宽度
    :param figHeight: 图形高度
    :param save_dir: 保存目录
    """
    fig, axes = plt.subplots(3, 1, figsize=(figWidth, figHeight))
    fig.suptitle('前进方向位置误差对比')

    # CEP99
    x = np.arange(len(comparisonData['sceneTypes']))
    width = 0.35
    axes[0].bar(x - width/2, comparisonData['rtk_forward_cep99'], width, label='RTK', color='red', edgecolor='black')
    axes[0].bar(x + width/2, comparisonData['spp_forward_cep99'], width, label='SPP', color='blue', edgecolor='black')
    axes[0].set_title('前进方向位置误差 - CEP99')
    axes[0].set_ylabel('误差 (m)')
    axes[0].legend(loc='upper right')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(comparisonData['sceneTypes'], rotation=45, ha='right')
    axes[0].grid(True)

    # 在柱子上显示数值
    for i in range(len(comparisonData['sceneTypes'])):
        if comparisonData['rtk_forward_cep99'][i] > 0 and not np.isnan(comparisonData['rtk_forward_cep99'][i]):
            axes[0].text(i - width/2, comparisonData['rtk_forward_cep99'][i], 
                        f'{comparisonData["rtk_forward_cep99"][i]:.3f}', 
                        ha='center', va='bottom', color='red')
        if comparisonData['spp_forward_cep99'][i] > 0 and not np.isnan(comparisonData['spp_forward_cep99'][i]):
            axes[0].text(i + width/2, comparisonData['spp_forward_cep99'][i], 
                        f'{comparisonData["spp_forward_cep99"][i]:.3f}', 
                        ha='center', va='bottom', color='blue')

    # Max
    axes[1].bar(x - width/2, comparisonData['rtk_forward_max'], width, label='RTK', color='red', edgecolor='black')
    axes[1].bar(x + width/2, comparisonData['spp_forward_max'], width, label='SPP', color='blue', edgecolor='black')
    axes[1].set_title('前进方向位置误差 - Max')
    axes[1].set_ylabel('误差 (m)')
    axes[1].legend(loc='upper right')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(comparisonData['sceneTypes'], rotation=45, ha='right')
    axes[1].grid(True)

    # 在柱子上显示数值
    for i in range(len(comparisonData['sceneTypes'])):
        if comparisonData['rtk_forward_max'][i] > 0 and not np.isnan(comparisonData['rtk_forward_max'][i]):
            axes[1].text(i - width/2, comparisonData['rtk_forward_max'][i], 
                        f'{comparisonData["rtk_forward_max"][i]:.3f}', 
                        ha='center', va='bottom', color='red')
        if comparisonData['spp_forward_max'][i] > 0 and not np.isnan(comparisonData['spp_forward_max'][i]):
            axes[1].text(i + width/2, comparisonData['spp_forward_max'][i], 
                        f'{comparisonData["spp_forward_max"][i]:.3f}', 
                        ha='center', va='bottom', color='blue')

    # RMS
    axes[2].bar(x - width/2, comparisonData['rtk_forward_rms'], width, label='RTK', color='red', edgecolor='black')
    axes[2].bar(x + width/2, comparisonData['spp_forward_rms'], width, label='SPP', color='blue', edgecolor='black')
    axes[2].set_title('前进方向位置误差 - RMS')
    axes[2].set_ylabel('误差 (m)')
    axes[2].set_xlabel('场景类型')
    axes[2].legend(loc='upper right')
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(comparisonData['sceneTypes'], rotation=45, ha='right')
    axes[2].grid(True)

    # 在柱子上显示数值
    for i in range(len(comparisonData['sceneTypes'])):
        if comparisonData['rtk_forward_rms'][i] > 0 and not np.isnan(comparisonData['rtk_forward_rms'][i]):
            axes[2].text(i - width/2, comparisonData['rtk_forward_rms'][i], 
                        f'{comparisonData["rtk_forward_rms"][i]:.3f}', 
                        ha='center', va='bottom', color='red')
        if comparisonData['spp_forward_rms'][i] > 0 and not np.isnan(comparisonData['spp_forward_rms'][i]):
            axes[2].text(i + width/2, comparisonData['spp_forward_rms'][i], 
                        f'{comparisonData["spp_forward_rms"][i]:.3f}', 
                        ha='center', va='bottom', color='blue')

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'forward_position_error_comparison.png'), dpi=300, bbox_inches='tight')
    plt.show()

# 如果直接运行此脚本，则执行plot_precision_comparison函数
if __name__ == "__main__":
    plot_precision_comparison()
