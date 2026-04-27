import pandas as pd
import numpy as np
import csv

def readSensorDataTcSol(file_path, dt):
    """
    读取传感器数据
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
    
    # 检查是否有足够的列来处理角度数据（至少需要4列）
    if data.shape[1] >= 4:
        # 处理第4列的角度数据
        for i in range(data.shape[0]):
            if data[i, 3] < 0:  # 第4列（索引3）
                data[i, 3] = -data[i, 3]
            else:
                data[i, 3] = -data[i, 3] + 360
    
    return data
