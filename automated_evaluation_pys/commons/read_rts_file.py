import numpy as np
import pandas as pd
import os
import csv

def read_rts_file(file_path,t=0):
    """
    读取RTS文件并将周内秒移到第一列，其余数据按顺序排列
    RTS文件格式：1745898512.0054,-0.0016, 0.0139,-3.1310,-0.0010,-0.0009, 0.0002, 22.5374162302,113.9539224386, 2.3958,186565.64
    其中，最后一列为周内秒，2-10列分别为姿态、速度、位置
    输出格式：第一列为周内秒，其余列按原顺序排列
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # 读取文件内容
    data_list = []
    with open(file_path, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for line in csv_reader:
            line = [field.strip() for field in line if field.strip()]  # 去除空字段和空格
            if line:  # 忽略空行
                # 将数据转换为浮点数
                row_data = []
                for part in line:
                    try:
                        row_data.append(float(part))
                    except ValueError:
                        # 如果无法转换为数字，跳过该行
                        break
                else:
                    # 只有当所有字段都成功转换时才处理该行
                    if len(row_data) > 1:  # 确保至少有两列数据
                        # 提取最后一列（周内秒）作为第一列
                        if t==0:
                            week_seconds = row_data[-1]
                        else:
                            week_seconds = row_data[0]
                        
                        # 重组数据：周内秒在第一列，其余按原顺序
                        reordered_row = [week_seconds] + row_data[1:-1]
                        
                        data_list.append(reordered_row)
    
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
    data_array = np.array(padded_data)
    
    mask_negative = data_array[:, 3] < 0
    data_array[mask_negative, 3] = -data_array[mask_negative, 3]  # 负值取反
    data_array[~mask_negative, 3] = 360 - data_array[~mask_negative, 3]  # 正值用360减去
    
    return data_array

def read_rts_file_simple(file_path):
    """
    简单读取RTS文件，不做任何数据重排
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # 读取文件内容
    data_list = []
    with open(file_path, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for line in csv_reader:
            line = [field.strip() for field in line if field.strip()]  # 去除空字段和空格
            if line:  # 忽略空行
                # 将数据转换为浮点数
                row_data = []
                for part in line:
                    try:
                        row_data.append(float(part))
                    except ValueError:
                        # 如果无法转换为数字，跳过该行
                        break
                else:
                    # 只有当所有字段都成功转换时才添加该行
                    data_list.append(row_data)
    
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
    data_array = np.array(padded_data)
    
    return data_array

# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的文件路径）
    # file_path = os.path.join(basefold, dataset, 'rts', 'rts_result.csv')
    # data = read_rts_file(file_path)
    # print("Reordered data shape:", data.shape)
    # print("First few rows:")
    # print(data[:5, :])
    pass
