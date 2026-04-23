import pandas as pd
import numpy as np
import csv

def read_sensor_data(file_path, target_cols, time_col, file_type, delimiter=None):
    """
    通用数据读取函数
    :param file_path: 文件路径
    :param target_cols: 目标列索引（从1开始）
    :param time_col: 时间列索引（从1开始）
    :param file_type: 文件类型 ('file1', 'file2', 'pk')
    :param delimiter: 分隔符
    :return: data: 目标数据, time: 时间数据
    """
    # 验证输入参数
    if not isinstance(target_cols, (list, tuple, np.ndarray)) or not all(isinstance(col, (int, float)) and col > 0 for col in target_cols):
        raise ValueError("target_cols must be a vector of positive numbers")
    if not isinstance(time_col, (int, float)) or time_col <= 0:
        raise ValueError("time_col must be a positive scalar")
    
    # 根据文件类型读取数据
    if file_type == 'file1':
        # 固定格式文件读取
        if delimiter is None:
            delimiter = ' '  # 默认为空格
        
        # 读取整个文件
        with open(file_path, 'r') as fid:
            lines = fid.readlines()
        
        # 跳过注释行（跳过非数字开头的行）
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            # 检查第一字符是否为数字或符号
            first_char = line[0]
            if first_char.isdigit() or first_char in ['+', '-']:
                break
            i += 1
        
        # 从有效行开始读取数据
        valid_lines = lines[i:]
        
        # 解析数据
        data_rows = []
        for line in valid_lines:
            line = line.strip()
            if line:
                parts = [part.strip() for part in line.split(delimiter)]
                # 尝试将字符串转换为浮点数
                row = []
                for part in parts:
                    try:
                        row.append(float(part))
                    except ValueError:
                        # 如果无法转换为数字，保留原始字符串
                        row.append(part)
                data_rows.append(row)
        
        # 转换为numpy数组
        raw_data = np.array(data_rows)
        
    elif file_type in ['pk', 'file2']:
        # CSV格式读取，使用csv模块处理不同列数的情况
        try:
            data_list = []
            with open(file_path, 'r') as f:
                csv_reader = csv.reader(f, delimiter=delimiter if delimiter else ',')
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
            raw_data = np.array(padded_data)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"FileNotFound: {file_path}")
    
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    # 提取数据列（注意MATLAB索引从1开始，Python从0开始）
    # 检查目标列和时间列是否超出数据范围
    available_cols = raw_data.shape[1]
    
    # 检查时间列是否有效
    time_col_idx = int(time_col) - 1
    if time_col_idx >= available_cols:
        raise IndexError(f"Time column index {time_col} exceeds available columns {available_cols}")
    
    # 检查目标列是否有效
    target_col_indices = [int(col) - 1 for col in target_cols]
    for col_idx in target_col_indices:
        if col_idx >= available_cols:
            raise IndexError(f"Target column index {col_idx + 1} exceeds available columns {available_cols}")
    
    time = raw_data[:, time_col_idx]  # 时间列
    data = raw_data[:, target_col_indices]  # 目标列
    
    return data, time
