"""
读取GPS参考数据
对应MATLAB函数: read_gps_data_wdh
"""

import numpy as np
import csv


def read_gps_data_wdh(file_path):
    """
    读取GPS参考数据文件
    :param file_path: 文件路径
    :return: data: 读取的数据 (N x M)
    """
    try:
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
    
    return data