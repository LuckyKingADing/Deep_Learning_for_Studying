import numpy as np
import csv
from skipCommentLines import skipCommentLines

def load100ccsv(file_path, gpst0, gpste):
    """
    加载100c CSV数据
    :param file_path: 文件路径
    :param gpst0: GPS起始时间
    :param gpste: GPS结束时间
    :return: data: 处理后的数据
    """
    # 固定格式文件读取
    with open(file_path, 'r') as fid:
        # 跳过注释行
        skipCommentLines(fid)
        
        # 读取所有数据
        lines = fid.readlines()
        raw_data_list = []
        for line in lines:
            line = line.strip()
            if line:
                # 使用csv解析器处理可能的引号和逗号问题
                row = next(csv.reader([line]))
                # 将每行数据转换为数值
                numeric_row = []
                for x in row:
                    try:
                        numeric_row.append(float(x))
                    except ValueError:
                        # 如果不能转换为数字，跳过该行
                        break
                else:
                    raw_data_list.append(numeric_row)
        
        if not raw_data_list:
            raise ValueError(f'File empty or contains no valid numeric data: {file_path}')
        
        # 找到最大列数，用于后续填充
        max_cols = max(len(row) for row in raw_data_list)
        
        # 填充较短的行，使所有行长度一致
        padded_data_list = []
        for row in raw_data_list:
            padded_row = row + [np.nan] * (max_cols - len(row))
            padded_data_list.append(padded_row)
        
        raw_data = np.array(padded_data_list)
    
    d2r = 3.14159265358979 / 180
    
    # 初始化输出数据
    sz = raw_data.shape
    if gpste > 0 and raw_data.shape[0] > 0:
        # 查找起始和结束索引
        if raw_data.shape[1] > 1:  # 确保有足够的列
            time_col = raw_data[:, 1] / 1000  # 第2列除以1000作为时间
            idx0 = np.where(time_col >= gpst0)[0]
            if len(idx0) > 0:
                idx0 = idx0[0]
            else:
                idx0 = 0
                
            idxe = np.where(time_col >= gpste)[0]
            if len(idxe) > 0:
                idxe = idxe[0]
            else:
                idxe = len(time_col) - 1
        else:
            idx0 = 0
            idxe = len(raw_data) - 1
    else:
        idx0 = 0
        idxe = len(raw_data) - 1
    
    # 确保索引有效
    idx0 = max(0, min(idx0, len(raw_data)-1))
    idxe = max(0, min(idxe, len(raw_data)-1))
    
    # 创建输出数据矩阵
    if idxe >= idx0:
        data = np.zeros((idxe - idx0 + 1, sz[1]))
        
        # gpst (第1列是第2列/1000)
        if raw_data.shape[1] > 1:  # 确保有足够的列
            data[:, 0] = raw_data[idx0:idxe+1, 1] / 1000  # gpst
        
        # pitch roll yaw (deg)
        if raw_data.shape[1] > 19:  # 确保有足够的列
            data[:, 2] = raw_data[idx0:idxe+1, 18]  # 第19列
            data[:, 1] = raw_data[idx0:idxe+1, 19]  # 第20列
        
        if raw_data.shape[1] > 17:  # 确保有足够的列
            data[:, 3] = -raw_data[idx0:idxe+1, 17]  # 第18列取负
            for i in range(len(data)):
                if not np.isnan(data[i, 3]):  # 检查是否为NaN
                    if data[i, 3] < 0:
                        data[i, 3] = -data[i, 3]
                    else:
                        data[i, 3] = -data[i, 3] + 360
        
        # ve vn vu (第15-17列)
        if raw_data.shape[1] > 16:  # 确保有足够的列
            data[:, 4:7] = raw_data[idx0:idxe+1, 14:17]  # 第15-17列
        
        # lat(rad) lon(rad) alt (第6-8列)
        if raw_data.shape[1] > 7:  # 确保有足够的列
            data[:, 7:10] = raw_data[idx0:idxe+1, 5:8]  # 第6-8列
    else:
        # 如果索引无效，返回空数组
        data = np.array([]).reshape(0, sz[1] if len(sz) > 1 else 0)
    
    return data

# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的文件路径和时间参数）
    # data = load100ccsv('your_file_path', 0, 0)
    pass
