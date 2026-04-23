import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from readSensorData import read_sensor_data
from skipCommentLines import skipCommentLines

def main():
    """
    主程序入口
    """
    RE = 6378137
    d2r = np.pi / 180
    col_pk = list(range(1, 23))  # 1:22

    # 配置文件参数
    config = {
        'file1_path': 'D:/dockers/tcmsf/rtklc.sol',
        'file2_path': 'D:/dockers/tcmsf/gnss.csv',
        'pk_path': 'D:/dockers/tcmsf/pk.txt',
        'file1_delimiter': ' ',
        'file2_delimiter': ',',
        'pk_delimiter': ',',
        'file1_cols': [5, 7, 8, 9, 10, 11, 12],  # 文件1目标列
        'file2_cols': [2, 5, 6, 7, 8, 9, 10, 11],  # 文件2目标列
        'pk_cols': list(range(1, 23)),  # 1:22 文件2目标列
        'file1_time_col': 5,  # 文件1时间列索引
        'file2_time_col': 2,  # 文件2时间列索引
        'pk_time_col': 1,  # 文件2时间列索引
        'time_tol': 1e-2,  # 时间对齐容差
        'plot_options': [{'linewidth': 1.5, 'color': '#0072BD'}],  # 绘图样式
        'unit': [RE * d2r, RE * d2r] + [1] * 4,  # 对比时转换的系数
        'timeformat': 1742958576.5707,  # 绘图横轴时间格式,0-相对于起始时刻时间差 -1-gps秒 其他-指定时间
        'ymax': 4,  # 270624.10
        'xmax': 5  # 270624.10
    }

    # 执行流程
    try:
        data1, time1 = read_sensor_data(config['file1_path'], config['file1_cols'], config['file1_time_col'], 'file1', config['file1_delimiter'])
        data2, time2 = read_sensor_data(config['file2_path'], config['file2_cols'], config['file2_time_col'], 'file2', config['file2_delimiter'])
        data_pk, time_pk = read_sensor_data(config['pk_path'], config['pk_cols'], config['pk_time_col'], 'pk', config['pk_delimiter'])

        aligned_data1, aligned_data2, common_time = alignDataByTime(
            data1, time1, data2, time2, config['time_tol'])

        diff_data = calculateDifference(aligned_data1, aligned_data2)

        visualizeResults(diff_data, [data_pk, time_pk], common_time, config['plot_options'], config['unit'], config['timeformat'], config['ymax'], config['xmax'])

    except Exception as e:
        errorHandler(e)


def alignDataByTime(data1, time1, data2, time2, tol):
    """
    时间对齐函数（带容差）
    :param data1: 数据集1
    :param time1: 时间集1
    :param data2: 数据集2
    :param time2: 时间集2
    :param tol: 容差
    :return: 对齐后的数据
    """
    rounded_time1 = np.round(time1 / tol)
    rounded_time2 = np.round(time2 / tol)

    # 找到共同的时间点
    common_times = np.intersect1d(rounded_time1, rounded_time2)
    
    mask1 = np.isin(rounded_time1, common_times)
    mask2 = np.isin(rounded_time2, common_times)
    
    data1_aligned = data1[mask1]
    data2_aligned = data2[mask2]
    common_time = time1[mask1]
    
    return data1_aligned, data2_aligned, common_time


def calculateDifference(data1, data2):
    """
    差值计算函数
    :param data1: 数据集1
    :param data2: 数据集2
    :return: 差值
    """
    validateInputSize(data1, data2)
    # 检查数据维度是否足够
    min_cols = min(data1.shape[1], data2.shape[1])
    if min_cols > 6:
        diff_data = data1[:, 1:6] - data2[:, 1:6]  # 按前6列计算差值 (Python索引1:6对应MATLAB的2:7)
    elif min_cols > 1:
        diff_data = data1[:, 1:min_cols] - data2[:, 1:min_cols]  # 按可用列计算差值
    else:
        diff_data = data1 - data2  # 如果只有一列，计算全部差值
    return diff_data


def visualizeResults(data, pk, time, plot_options, unit, timeformat, ymax, xmax):
    """
    可视化模块
    :param data: 差值数据
    :param pk: pk数据
    :param time: 时间
    :param plot_options: 绘图选项
    :param unit: 单位
    :param timeformat: 时间格式
    :param ymax: y轴最大值
    :param xmax: x轴最大值
    """
    plt.figure(figsize=(10, 8))
    titles = ['Latitude', 'Longitude', 'Height', 'Ve', 'Vn', 'Vu']
    
    # 应用单位转换
    data = data * np.array(unit)
    
    # 提取pk数据和时间
    pk_data, time_pk = pk
    timepk = time_pk
    
    if timeformat == 0:
        time = time - time[0]
        timepk = timepk - timepk[0]
    elif timeformat == -1:
        time = time
    else:
        time = time - timeformat
        timepk = timepk - timeformat

    # 检查数据维度是否足够
    if data.shape[1] >= 6:
        for i in range(1, 3):  # 1:2
            plt.subplot(3, 1, i)
            start_idx = 3 * i - 3  # 对应MATLAB的3*i - 2 (因为Python索引从0开始)
            end_idx = 3 * i - 1    # 对应MATLAB的3*i (因为Python索引从0开始)
            if end_idx <= data.shape[1]:  # 确保不超过数据维度
                plt.plot(time, data[:, start_idx:end_idx], '.-')
                plt.title(f'{titles[i-1]} Difference')
                plt.xlabel('GPS Time')
                plt.ylabel('Delta Value')
                plt.ylim([-ymax, ymax])
                plt.xlim([0, xmax])
                plt.grid(True)
                plt.legend(titles[start_idx:end_idx])

    # 检查pk数据维度是否足够
    if pk_data is not None and pk_data.shape[1] >= 9:
        plt.subplot(3, 1, 3)
        plt.plot(timepk, pk_data[:, 6:9], '.-')  # 对应MATLAB的7:9 (Python索引6:9)
        plt.title('Position Difference')
        plt.xlabel('GPS Time')
        plt.ylabel('Delta Value')
        plt.ylim([-ymax, ymax])
        plt.xlim([0, xmax])
        plt.grid(True)
        plt.legend(titles[0:3])  # 对应MATLAB的titles(3*i - 2:3 * i)

    plt.suptitle('Multi-Sensor Data Comparison', fontsize=14)
    plt.tight_layout()
    plt.show()


def validateInputSize(data1, data2):
    """
    验证输入尺寸
    :param data1: 数据集1
    :param data2: 数据集2
    """
    if data1.shape[0] != data2.shape[0] or data1.shape[1] < 6 or data2.shape[1] < 6:
        raise ValueError('InconsistentDataDimensions')


def errorHandler(error):
    """
    错误处理函数
    :param error: 异常对象
    """
    print(f'[ERROR] {error}')
    import traceback
    print('Stack trace:')
    traceback.print_exc()


# 如果直接运行此脚本，则执行main函数
if __name__ == "__main__":
    main()
