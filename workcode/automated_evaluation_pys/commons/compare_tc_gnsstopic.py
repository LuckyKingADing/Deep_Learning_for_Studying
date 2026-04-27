import numpy as np
import matplotlib.pyplot as plt
from readSensorData import read_sensor_data
from alignDataByTimeTcSol import alignDataByTimeTcSol  # 注意：MATLAB中的alignDataByTime在Python中使用已有的alignDataByTimeTcSol

def alignDataByTime(data1i, time1i, data2, time2, tol):
    """
    时间对齐函数（带容差）
    :param data1i: 第一个数据集
    :param time1i: 第一个时间序列
    :param data2: 第二个数据集
    :param time2: 第二个时间序列
    :param tol: 时间容差
    :return: data1_aligned: 对齐后的第一个数据集
             data2_aligned: 对齐后的第二个数据集
             common_time: 共同时间序列
    """
    # 根据条件选择数据（这里采用else分支，即直接使用输入数据）
    data1 = data1i
    time1 = time1i

    # 计算时间的容差化整
    rounded_time1 = np.round(time1 / tol)
    rounded_time2 = np.round(time2 / tol)

    # 寻找交集
    # 使用numpy的intersect1d来找到共同元素及其索引
    common_vals, idx1, idx2 = np.intersect1d(rounded_time1, rounded_time2, return_indices=True)

    # 根据找到的索引提取对齐的数据
    data1_aligned = data1[idx1, :]
    data2_aligned = data2[idx2, :]
    common_time = time1[idx1]

    return data1_aligned, data2_aligned, common_time

def calculateDifference(data1, data2):
    """
    差值计算函数
    :param data1: 第一个数据集
    :param data2: 第二个数据集
    :return: diff_data: 差值数据
    """
    validateInputSize(data1, data2)
    diff_data = data1[:, 1:7] - data2[:, 1:7]  # 按前6列计算差值 (Python索引从0开始，所以第2-7列是索引1-6)
    return diff_data

def visualizeResults(data, pk, time, plot_options=None, unit=None, timeformat=0, ymax=0.5, xmin=0, xmax=60):
    """
    可视化模块
    :param data: 差值数据
    :param pk: pk数据
    :param time: 时间数据
    :param plot_options: 绘图选项
    :param unit: 单位转换系数
    :param timeformat: 时间格式
    :param ymax: y轴最大值
    :param xmin: x轴最小值
    :param xmax: x轴最大值
    """
    if unit is None:
        RE = 6378137
        pi = 3.14159265358979
        d2r = pi / 180
        unit = [RE * d2r, RE * d2r] + [1.0] * 4  # [RE*d2r, RE*d2r, 1, 1, 1, 1]
    
    # 应用单位转换
    data = data * unit
    
    timepk = pk[:, -1]  # 最后一列
    
    if timeformat == 0:
        initial_time = time[0] if len(time) > 0 else 0
        time = time - initial_time
        timepk = timepk - initial_time
    elif timeformat == -1:
        # 保持时间不变
        pass
    else:
        time = time - timeformat
        timepk = timepk - timeformat

    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 5))
    
    titles = ['Latitude', 'Longitude', 'Height', 'Ve', 'Vn', 'Vu']
    rkb = ['r', 'k', 'b']  # 颜色
    
    for i in range(1):  # 只循环一次，对应MATLAB中的i=1:1
        # 绘制三个差值曲线
        ax.plot(time, data[:, 3*i], '.-', color=rkb[0], linewidth=2, markersize=3, label=f'{titles[3*i]} Diff')
        ax.plot(time, data[:, 3*i + 1], '.-', color=rkb[1], linewidth=2, markersize=3, label=f'{titles[3*i + 1]} Diff')
        ax.plot(time, data[:, 3*i + 2], '.-', color=rkb[2], linewidth=2, markersize=3, label=f'{titles[3*i + 2]} Diff')
        
        ax.set_title(f'{titles[0]} Difference')  # 使用第一个标题
        ax.set_xlabel('GPS Time')
        ax.set_ylabel('Delta Value')
        ax.set_ylim([-ymax, ymax])
        ax.set_xlim([xmin, xmax])
        ax.grid(True)
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.legend()

    plt.tight_layout()
    plt.show()
    
    # 第二个图形
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    
    for i in range(1):  # 只循环一次，对应MATLAB中的i=1:1
        ax2.plot(timepk, pk[:, 6], '.-', color='r', label=titles[0])  # 第7列 (索引6)
        ax2.plot(timepk, pk[:, 7], '.-', color='k', label=titles[1])  # 第8列 (索引7)
        ax2.plot(timepk, pk[:, 8], '.-', color='b', label=titles[2])  # 第9列 (索引8)
        
        ax2.set_title(f'{titles[0]} Difference')
        ax2.set_xlabel('GPS Time')
        ax2.set_ylabel('Delta Value')
        ax2.set_ylim([-ymax, ymax])
        ax2.set_xlim([0, xmax])
        ax2.grid(True)
        ax2.tick_params(axis='both', which='major', labelsize=10)
        ax2.legend()

    plt.suptitle('Multi-Sensor Data Comparison', fontsize=14)
    plt.tight_layout()
    plt.show()

def generateFormatString(n_col):
    """
    生成格式字符串
    :param n_col: 列数
    :return: format_str: 格式字符串
    """
    format_str = ''.join(['%f'] * n_col) + '%*[^\n]'  # 跳过行尾可能存在的非数字内容
    return format_str

def validateInputSize(data1, data2):
    """
    验证输入数据尺寸
    :param data1: 第一个数据集
    :param data2: 第二个数据集
    """
    if data1.shape[0] != data2.shape[0] or data1.shape[1] < 6 or data2.shape[1] < 6:
        raise ValueError('InconsistentDataDimensions')

def errorHandler(ME):
    """
    错误处理函数
    :param ME: 异常对象
    """
    print(f'[ERROR] {ME}')
    print('Stack trace:')

def main():
    """
    主程序入口
    """
    # 定义常量
    RE = 6378137
    pi = 3.14159265358979
    d2r = pi / 180
    col_pk = np.arange(1, 23)  # 1:22 in Python
    
    # 配置参数
    config = {
        'file1_path': 'D:\\dockers\\tcmsf\\rtk.sol',
        'file2_path': 'D:\\dockers\\tcmsf\\gnss.csv',
        'pk_path': 'D:\\dockers\\tcmsf\\pk.txt',
        'file1_delimiter': ' ',
        'file2_delimiter': ',',
        'pk_delimiter': ',',
        'file1_cols': [4, 7, 8, 9, 10, 11, 12, 13],  # 文件1目标列
        'file2_cols': [4, 5, 6, 7, 8, 9, 10, 11],    # 文件2目标列
        'pk_cols': list(range(1, 23)),                 # 1:22 in Python
        'file1_time_col': 4,                          # 文件1时间列索引
        'file2_time_col': 4,                          # 文件2时间列索引
        'pk_time_col': 1,                             # pk时间列索引
        'time_tol': 1e-3,                             # 时间对齐容差
        'plot_options': [{'LineWidth': 1.5, 'Color': '#0072BD'}],  # 绘图样式
        'unit': [RE * d2r, RE * d2r] + [1.0] * 4,    # 对比时转换的系数
        'timeformat': 0,                              # 绘图横轴时间格式
        'ymax': 0.5,                                  # y轴最大值
        'xmin': 0,                                    # x轴最小值
        'xmax': 60                                    # x轴最大值
    }

    # 执行流程
    try:
        data1, time1 = read_sensor_data(config['file1_path'], config['file1_cols'], config['file1_time_col'], 'file1', config['file1_delimiter'])
        data2, time2 = read_sensor_data(config['file2_path'], config['file2_cols'], config['file2_time_col'], 'file2', config['file2_delimiter'])
        data_pk, time_pk = read_sensor_data(config['pk_path'], config['pk_cols'], config['pk_time_col'], 'pk', config['pk_delimiter'])

        aligned_data1, aligned_data2, common_time = alignDataByTime(
            data1, time1, data2, time2, config['time_tol'])

        diff_data = calculateDifference(aligned_data1, aligned_data2)

        visualizeResults(diff_data, np.column_stack([data_pk, time_pk]), common_time, 
                        config['plot_options'], config['unit'], config['timeformat'],
                        config['ymax'], config['xmin'], config['xmax'])

    except Exception as ME:
        errorHandler(ME)

# 如果直接运行此脚本，则执行main函数
if __name__ == "__main__":
    main()
