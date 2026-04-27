import pandas as pd
import numpy as np
import csv

def readfullcsv(file_path,colindex,helpindex=[]):
    """
    通用数据读取函数
    :param file_path: 文件路径
    :param colindex: 目标列索引 要将目标文件中的内容与固定存储的数据格式相对应
    : 0-time 1:3-att 4:6-vn 7:9-pos 后面为可选 10:12-eb 13:15-db 16:18-kod  最后1列为status
    :param helpindex: 目标列索引 状态的辅助参数
    : 接着前面的参数 0:2-pos_std 3-sat_num
    :return: data: 提取的数据
    """
    try:
        # 使用csv模块读取文件，这样可以处理不同行有不同列数的情况
        data_list = []
        with open(file_path, 'r') as f:
            # 读取第一行来判断分隔符类型
            first_line = f.readline().strip()
            f.seek(0)
            
            # 检测分隔符类型
            is_space_delimited = False
            if ',' in first_line:
                # 包含逗号，优先使用 CSV reader
                csv_reader = csv.reader(f, delimiter=',')
                # 跳过第一行（标题行）
                next(csv_reader, None)
                for row in csv_reader:
                    if row and any(field.strip() for field in row):
                        numeric_row = []
                        for field in row:
                            field = field.strip()
                            try:
                                numeric_row.append(float(field))
                            except ValueError:
                                continue
                        if numeric_row:
                            data_list.append(numeric_row)
            else:
                # 不包含逗号，可能是空格分隔
                # 对于空格分隔，使用 split() 方法（能处理多个连续空格）
                header_skipped = False
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 跳过标题行（假设第一行是标题）
                    if not header_skipped:
                        # 检查是否是标题行
                        line_lower = line.lower()
                        if 'time' in line_lower or 'att' in line_lower or 'pos' in line_lower or 'vn' in line_lower:
                            header_skipped = True
                            continue
                        # 如果不是标题行，第一行是数据，继续处理
                    
                    # 使用 split() 分割（默认按任意空白字符分割）
                    fields = line.split()
                    if fields and any(field.strip() for field in fields):
                        numeric_row = []
                        for field in fields:
                            field = field.strip()
                            try:
                                numeric_row.append(float(field))
                            except ValueError:
                                continue
                        if numeric_row:
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
    
    colshelp = len(helpindex)
    cols = len(colindex)
    data = np.zeros((full_data.shape[0],cols + colshelp))
    for i in range(cols):
        icol = colindex[i]
        if icol >= 0:
            data[:,i] = full_data[:, icol] 
    for i in range(colshelp):
        icol = helpindex[i]
        if icol >= 0:
            data[:,i + cols] = full_data[:, icol] 
    
    return data