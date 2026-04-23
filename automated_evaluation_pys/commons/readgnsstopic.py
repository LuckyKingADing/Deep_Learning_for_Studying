import pandas as pd
import numpy as np
import csv

def readgnsstopic(file_path, target_cols):
    """
    通用数据读取函数
    :param file_path: 文件路径
    :param target_cols: 目标列索引（从1开始的索引，转换为Python的从0开始）
    :return: data: 提取的数据
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
        full_data = np.array(padded_data)
        
    except FileNotFoundError:
        raise FileNotFoundError(f'FileNotFound: {file_path}')
    
    # 将MATLAB风格的1基索引转换为Python的0基索引
    python_cols = [col - 1 for col in target_cols]
    
    # 检查目标列是否超出数据范围
    available_cols = full_data.shape[1]
    valid_python_cols = [col for col in python_cols if col < available_cols]
    
    if not valid_python_cols:
        raise IndexError(f'No valid columns found. Requested columns: {python_cols}, Available columns: {available_cols}')
    
    # 提取目标列数据
    data = full_data[:, valid_python_cols]
    
    return data
