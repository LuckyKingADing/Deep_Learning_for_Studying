import pandas as pd
import numpy as np
import csv
import globalvariation as glv

def readmsf_debug_state(file_path, dt):
    """
    读取MSF调试状态数据
    :param file_path: 文件路径
    :param dt: 时间差值
    :return: data: 处理后的数据
    """
    try:
        # 使用csv模块读取文件，这样可以处理不同行有不同列数的情况
        data_list = []
        with open(file_path, 'r') as f:
            csv_reader = csv.reader(f, delimiter=',')
            for row in csv_reader:
                # 过滤掉空行
                if row and any(field.strip() for field in row):
                    # 将每一行转换为数值
                    numeric_row = []
                    for field in row:
                        field = field.strip()
                        try:
                            # 尝试转换为浮点数
                            numeric_row.append(float(field))
                        except ValueError:
                            # 如果转换失败，跳过这一行或这一列
                            continue
                    if numeric_row:  # 确保行不为空
                        data_list.append(numeric_row)
        
        if not data_list:
            raise ValueError(f'File empty or contains no valid numeric data: {file_path}')
        
        # 找到最大列数，用于后续填充
        max_cols = max(len(row) for row in data_list)
        
        # 填充较短的行，使所有行长度一致
        padded_data = []
        for row in data_list:
            padded_row = row + [np.nan] * (max_cols - len(row))
            padded_data.append(padded_row)
        
        # 转换为numpy数组
        data = np.array(padded_data)
        
    except FileNotFoundError:
        raise FileNotFoundError(f'FileNotFound: {file_path}')
    
    # 从第一列减去dt
    data[:, 0] = data[:, 0] - dt

    # 检查是否有足够的列来进行数据交换（至少需要10列）
    if data.shape[1] >= 10:
        # 交换数据列
        # temp = data[:, 1:4].copy()  # 第2-4列 (vech)
        temp = data[:, 81:84].copy()  # ant
        data[:, 1:4] = data[:, 4:7]  # 第5-7列赋给第2-4列 (Python索引4-6对应MATLAB的5-7)
        # data[:, 3] = 360 - data[:, 3]  # 第4列 (Python索引3对应MATLAB的4)
        mask_negative = data[:, 3] < 0
        data[mask_negative, 3] = -data[mask_negative, 3]  # 负值取反
        data[~mask_negative, 3] = 360 - data[~mask_negative, 3]  # 正值用360减去
        data[:, 4:7] = data[:, 7:10]  # 第8-10列赋给第5-7列 (Python索引7-9对应MATLAB的8-10)
        data[:, 7:10] = temp  # 原来的第2-4列赋给第8-10列
        data[:, 10:13] = data[:, 10:13] / glv.DPS
        data[:, 13:16] = data[:, 13:16] / glv.MG
        data[:, 16] = data[:, 34] / glv.DEG
        data[:, 18] = data[:, 36] / glv.DEG
        
        #std
        data[:, 19:22] = data[:, 19:22] / glv.DEG
        data[:, 28:31] = data[:, 28:31] / glv.DPS
        data[:, 31:34] = data[:, 31:34] / glv.MG
        data[:, 34] = data[:, 34] / glv.DEG
        data[:, 36] = data[:, 36] / glv.DEG
    
    data[:,0] = data[:,87] #assign sow
    #剔除周内秒不合理的数值（因msf数据输出阶段未必有靠谱sow值）
    ind = np.where(data[:,0] < 604800)[0]
    dataout = data[ind, :]
    
    return dataout
