import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import re

def plot_skyview(filename):
    """
    绘制天空视图 - 方位角/高度角分布
    :param filename: 输入文件名
    """
    # 步骤1：读取文件数据
    try:
        with open(filename, 'r') as fileID:
            lines = fileID.readlines()
    except IOError:
        raise IOError(f'文件无法打开: {filename}')

    # 解析每行数据
    ids = []
    azimuth = []
    elevation = []
    
    for line in lines:
        line = line.strip()
        if line:
            # 使用正则表达式解析数据，处理可能的多种分隔符
            parts = re.split(r'[,\s]+', line)
            parts = [part for part in parts if part]  # 移除空元素
            
            if len(parts) >= 5:
                try:
                    id_val = int(parts[1])  # 第3列：编号
                    az_val = float(parts[3])  # 第6列：方位角
                    el_val = float(parts[4])  # 第7列：高度角
                    
                    ids.append(id_val)
                    azimuth.append(az_val)
                    elevation.append(el_val)
                except ValueError:
                    continue  # 跳过无法解析的行

    # 转换为numpy数组
    ids = np.array(ids)
    azimuth = np.array(azimuth)
    elevation = np.array(elevation)

    # 步骤2：数据去重（相同ID只保留第一个）
    _, unique_idx = np.unique(ids, return_index=True)
    unique_ids = ids[unique_idx]
    unique_azimuth = azimuth[unique_idx]
    unique_elevation = elevation[unique_idx]

    # 步骤3：创建天空视图极坐标图
    fig, ax = plt.subplots(subplot_kw=dict(projection='polar'), figsize=(8, 8))
    
    # 设置极坐标属性
    ax.set_theta_zero_location('N')  # 0°方位角在顶部（北向）
    ax.set_theta_direction(-1)       # 顺时针增加角度
    ax.set_ylim(90, 0)               # 反向半径轴（天顶在中心），高度角范围0-90度
    
    # 坐标转换
    theta = np.deg2rad(unique_azimuth)  # 方位角转弧度
    r = unique_elevation               # 高度角作为半径
    
    # 绘制星点
    scatter = ax.scatter(theta, r, s=80, c=[0.8, 0.2, 0.2], 
                        edgecolors='k', alpha=0.7, zorder=3)

    # 标注编号
    for i in range(len(unique_ids)):
        ax.text(theta[i], r[i], str(unique_ids[i]), 
                color='yellow', fontsize=8, fontweight='bold',
                ha='center', va='center', zorder=4)

    # 设置天顶圈标注
    ax.set_rticks([0, 18, 36, 54, 72])  # 设置径向刻度
    ax.set_rlabel_position(0)  # 径向标签位置
    ax.set_title('天空视图 - 方位角/高度角分布', pad=20)
    ax.grid(True)

    # 添加方向标注
    ax.text(np.deg2rad(180), 95, 'N', fontweight='bold', fontsize=12, ha='center')
    ax.text(np.deg2rad(270), 95, 'E', fontweight='bold', fontsize=12, ha='center')
    ax.text(np.deg2rad(0), 95, 'S', fontweight='bold', fontsize=12, ha='center')
    ax.text(np.deg2rad(90), 95, 'W', fontweight='bold', fontsize=12, ha='center')

    plt.tight_layout()
    plt.show()

# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的文件路径）
    # plot_skyview('/mnt/d/sky.txt')
    pass
