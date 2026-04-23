"""
输出精度分析结果
对应MATLAB函数: outpre_new
"""
import numpy as np
from calculate_errors import calculate_errors

def calculate_cep(data):
    """
    计算CEP、CEP95、CEP99
    :param data: 数据数组
    :return: cep, cep95, cep99
    """
    if len(data) == 0:
        return 0, 0, 0
    
    # 计算CEP（50%分位数）
    cep = np.percentile(data, 50)
    
    # 计算CEP95（95%分位数）
    cep95 = np.percentile(data, 95)
    
    # 计算CEP99（99%分位数）
    cep99 = np.percentile(data, 99)
    
    return cep, cep95, cep99


def calculate_odometry(data):
    """
    计算里程数
    :param data: 原始数据，假设位置信息在第7、8、9列（对应MATLAB的8、9、10列）
    :return: 里程数组
    """
    if len(data) == 0:
        return np.array([0])
    
    # 提取位置信息
    x = data[:, 7]  # 东向位置
    y = data[:, 8]  # 北向位置
    z = data[:, 9]  # 垂直位置
    
    # 计算相邻点之间的距离
    dx = np.diff(x)
    dy = np.diff(y)
    dz = np.diff(z)
    
    # 计算距离
    distances = np.sqrt(dx**2 + dy**2 + dz**2)
    
    # 计算累积里程
    odom = np.zeros(len(data))
    odom[1:] = np.cumsum(distances)
    
    return odom


def rms(data):
    """
    计算均方根
    :param data: 数据数组
    :return: RMS值
    """
    if len(data) == 0:
        return 0
    return np.sqrt(np.mean(data**2))


def outpre_new(outfile, diff_datalc, diff_datatc, diff_datagnss, 
               lcs, tcs, gnss, yaw, tcstart, t_start=None, t_end=None,
               type_label=None, append_mode=False, return_stats=False,
               lcver='LC', tcver='TC'):
    """
    输出精度分析结果到文件或返回统计结果
    :param outfile: 输出文件路径
    :param diff_datalc: LC差异数据
    :param diff_datatc: TC差异数据
    :param diff_datagnss: GNSS差异数据
    :param lcs: LC原始数据
    :param tcs: TC原始数据
    :param gnss: GNSS原始数据
    :param tcstart: TC数据起始索引
    :param t_start: 时间范围起始点（可选）
    :param t_end: 时间范围结束点（可选）
    :param type_label: 场景类型标签（可选）
    :param append_mode: 是否追加模式（默认False为覆盖模式）
    :param return_stats: 是否返回统计结果（默认False，True时不写入文件）
    :param lcver: LC版本标识
    :param tcver: TC版本标识
    :return: 如果return_stats为True，返回统计结果字典；否则返回None
    """
    # 如果是返回统计结果模式，不打开文件
    fid = None
    if not return_stats:
        try:
            mode = 'a' if append_mode else 'w'
            fid = open(outfile, mode)
        except Exception as e:
            print(f'无法打开文件: {outfile}')
            raise e
        
        # 如果是追加模式，先写入场景分隔符和场景类型标签
        if append_mode and type_label is not None:
            fid.write('\n')
            fid.write('='*80 + '\n')
            fid.write(f'场景类型 (Scene Type): {type_label}\n')
            fid.write('='*80 + '\n\n')
        elif not append_mode and type_label is not None:
            # 第一个场景，也写入场景类型标签
            fid.write(f'场景类型 (Scene Type): {type_label}\n')
            fid.write('='*80 + '\n\n')
    
    # 创建数据的副本，避免修改原始数据
    diff_datalc = diff_datalc.copy() if diff_datalc is not None else None
    diff_datatc = diff_datatc.copy() if diff_datatc is not None else None
    diff_datagnss = diff_datagnss.copy() if diff_datagnss is not None else None
    
    # 获取时间向量
    time_lc = []
    time_tc = []
    time_gnss = []
    
    if diff_datalc is not None and len(diff_datalc) > 0:
        time_lc = diff_datalc[:, 0]  # LC时间向量
        print(f'Debug: LC时间向量范围: {time_lc[0]:.2f} - {time_lc[-1]:.2f}')
    
    if diff_datatc is not None and len(diff_datatc) > 0:
        time_tc = diff_datatc[:, 0]  # TC时间向量
        print(f'Debug: TC时间向量范围: {time_tc[0]:.2f} - {time_tc[-1]:.2f}')
    
    if diff_datagnss is not None and len(diff_datagnss) > 0:
        time_gnss = diff_datagnss[:, 0]  # GNSS时间向量
        print(f'Debug: GNSS时间向量范围: {time_gnss[0]:.2f} - {time_gnss[-1]:.2f}')
    
    # 根据时间范围筛选数据
    time_ranges = []
    if t_start is not None and t_end is not None:
        # 处理向量形式的时间范围
        if np.isscalar(t_start) and np.isscalar(t_end):
            # 单个时间范围
            time_ranges = [[t_start, t_end]]
        elif isinstance(t_start, (list, np.ndarray)) and isinstance(t_end, (list, np.ndarray)) and len(t_start) == len(t_end):
            # 多个时间范围
            time_ranges = []
            for i in range(len(t_start)):
                time_ranges.append([t_start[i], t_end[i]])
        else:
            # 不支持的时间范围格式，使用所有数据
            time_ranges = []
    else:
        # 没有时间范围参数，使用所有数据
        time_ranges = []
    
    # 如果有有效的时间范围，筛选数据
    if len(time_ranges) > 0:
        # 筛选LC数据
        if diff_datalc is not None and len(diff_datalc) > 0 and len(time_lc) > 0:
            valid_indices = []
            for i in range(len(time_ranges)):
                range_start = time_ranges[i][0]
                range_end = time_ranges[i][1]
                indices = np.where((time_lc >= range_start) & (time_lc <= range_end))[0]
                if len(indices) > 0:
                    valid_indices.extend(indices)
            # 去除重复的索引并排序
            lc_indices = np.unique(valid_indices)
            
            if len(lc_indices) > 0:
                diff_datalc = diff_datalc[lc_indices, :]
            else:
                # 如果没有数据在时间范围内，清空数据
                diff_datalc = None
        
        # 筛选TC数据
        if diff_datatc is not None and len(diff_datatc) > 0 and len(time_tc) > 0:
            valid_indices = []
            for i in range(len(time_ranges)):
                range_start = time_ranges[i][0]
                range_end = time_ranges[i][1]
                indices = np.where((time_tc >= range_start) & (time_tc <= range_end))[0]
                if len(indices) > 0:
                    valid_indices.extend(indices)
            # 去除重复的索引并排序
            tc_indices = np.unique(valid_indices)
            
            if len(tc_indices) > 0:
                diff_datatc = diff_datatc[tc_indices, :]
            else:
                # 如果没有数据在时间范围内，清空数据
                diff_datatc = None
        
        # 筛选GNSS数据
        if diff_datagnss is not None and len(diff_datagnss) > 0 and len(time_gnss) > 0:
            valid_indices = []
            for i in range(len(time_ranges)):
                range_start = time_ranges[i][0]
                range_end = time_ranges[i][1]
                indices = np.where((time_gnss >= range_start) & (time_gnss <= range_end))[0]
                if len(indices) > 0:
                    valid_indices.extend(indices)
            # 去除重复的索引并排序
            gnss_indices = np.unique(valid_indices)
            
            if len(gnss_indices) > 0:
                diff_datagnss = diff_datagnss[gnss_indices, :]
            else:
                # 如果没有数据在时间范围内，清空数据
                diff_datagnss = None
    
    # 检查所有数据源是否都为空
    all_data_empty = True
    lc_has_data = False
    tc_has_data = False
    gnss_has_data = False
    if (diff_datalc is not None and len(diff_datalc) > 0):
        lc_has_data = True
        all_data_empty = False
    if (diff_datatc is not None and len(diff_datatc) > 0):
        tc_has_data = True
        all_data_empty = False
    if (diff_datagnss is not None and len(diff_datagnss) > 0):
        all_data_empty = False
        gnss_has_data = True
    
    if all_data_empty:
        if fid is not None:
            fid.write('Error: 所有差值数据（LC、TC、GNSS）均为空\n')
            fid.write('\n')
            fid.close()
            print("Warning: 所有差值数据均为空，跳过统计")
        
        # 返回空统计结果
        if return_stats:
            return {
                'lc': {
                    'odom': 0,
                    'horizontal_rms': 0,
                    'horizontal_cep95': 0,
                    'horizontal_cep99': 0,
                    'horizontal_max': 0,
                    'lateral_rms': 0,
                    'lateral_cep95': 0,
                    'lateral_cep99': 0,
                    'lateral_max': 0,
                    'forward_rms': 0,
                    'forward_cep95': 0,
                    'forward_cep99': 0,
                    'forward_max': 0,
                    'vertical_rms': 0,
                    'vertical_cep95': 0,
                    'vertical_cep99': 0,
                    'vertical_max': 0
                },
                'tc': {
                    'odom': 0,
                    'horizontal_rms': 0,
                    'horizontal_cep95': 0,
                    'horizontal_cep99': 0,
                    'horizontal_max': 0,
                    'lateral_rms': 0,
                    'lateral_cep95': 0,
                    'lateral_cep99': 0,
                    'lateral_max': 0,
                    'forward_rms': 0,
                    'forward_cep95': 0,
                    'forward_cep99': 0,
                    'forward_max': 0,
                    'vertical_rms': 0,
                    'vertical_cep95': 0,
                    'vertical_cep99': 0,
                    'vertical_max': 0
                },
                'gnss': {
                    'odom': 0,
                    'horizontal_rms': 0,
                    'horizontal_cep95': 0,
                    'horizontal_cep99': 0,
                    'horizontal_max': 0,
                    'lateral_rms': 0,
                    'lateral_cep95': 0,
                    'lateral_cep99': 0,
                    'lateral_max': 0,
                    'forward_rms': 0,
                    'forward_cep95': 0,
                    'forward_cep99': 0,
                    'forward_max': 0,
                    'vertical_rms': 0,
                    'vertical_cep95': 0,
                    'vertical_cep99': 0,
                    'vertical_max': 0
                }
            }
        return None
    
    # 计算LC的误差
    lc_horizontal = []
    lc_lateral = []
    lc_vertical = []
    lc_forward = []
    lc_cep = 0
    lc_cep95 = 0
    lc_cep99 = 0
    lc_lateral_cep = 0
    lc_lateral_cep95 = 0
    lc_lateral_cep99 = 0
    lc_forward_cep = 0
    lc_forward_cep95 = 0
    lc_forward_cep99 = 0
    lc_vertical_cep = 0
    lc_vertical_cep95 = 0
    lc_vertical_cep99 = 0
    
    if lc_has_data:
        lc_heading = yaw  # 航向角在第4列（Python索引3）
        lc_horizontal, lc_lateral, lc_vertical, lc_forward = calculate_errors(diff_datalc, lc_heading)
        lc_cep, lc_cep95, lc_cep99 = calculate_cep(lc_horizontal)
        lc_lateral_cep, lc_lateral_cep95, lc_lateral_cep99 = calculate_cep(np.abs(lc_lateral))
        lc_forward_cep, lc_forward_cep95, lc_forward_cep99 = calculate_cep(np.abs(lc_forward))
        lc_vertical_cep, lc_vertical_cep95, lc_vertical_cep99 = calculate_cep(np.abs(lc_vertical))
    
    # 计算LC里程数
    if lcs is not None and len(lcs) > 0:
        if t_start is not None and t_end is not None and len(time_ranges) > 0:
            # 对于多段时间范围，分别计算每段时间范围内的里程，然后相加
            lc_total_odom = 0
            print(f'Debug: LC时间范围数量: {len(time_ranges)}')
            for i in range(len(time_ranges)):
                range_start = time_ranges[i][0]
                range_end = time_ranges[i][1]
                print(f'Debug: LC时间范围 {i+1}: {range_start:.2f} - {range_end:.2f}')
                # 使用lcs的时间向量来筛选lcs数据
                indices = np.where((lcs[:, 0] >= range_start) & (lcs[:, 0] <= range_end))[0]
                print(f'Debug: LC找到的索引数量: {len(indices)}')
                if len(indices) > 0:
                    # 确保indices在lcs的有效范围内
                    print(f'Debug: LC索引范围: {min(indices)} - {max(indices)}')
                    valid_indices = indices[indices < len(lcs)]
                    print(f'Debug: LC有效索引数量: {len(valid_indices)}')
                    if len(valid_indices) > 0:
                        # 使用原始数据中的位置信息计算里程
                        # 假设位置信息在第7、8、9列（对应MATLAB的8、9、10列）
                        segment_data = lcs[valid_indices, :]
                        segment_odom = calculate_odometry(segment_data)
                        print(f'Debug: LC段里程: {segment_odom[-1]:.2f}')
                        lc_total_odom = lc_total_odom + segment_odom[-1]
            print(f'Debug: LC总里程: {lc_total_odom:.2f}')
            lc_odom = lc_total_odom
        else:
            # 没有时间范围限制，计算所有数据的里程
            print('Debug: 没有时间范围限制，计算所有LC数据的里程')
            # 使用原始数据中的位置信息计算里程
            # 假设位置信息在第7、8、9列（对应MATLAB的8、9、10列）
            lc_odom = calculate_odometry(lcs)
            print(f'Debug: LC总里程: {lc_odom[-1]:.2f}')
    else:
        print('Debug: LC数据为空')
        lc_odom = 0
    
    # 计算TC的误差（如果有TC数据）
    tc_horizontal = []
    tc_lateral = []
    tc_vertical = []
    tc_forward = []
    tc_cep = 0
    tc_cep95 = 0
    tc_cep99 = 0
    tc_odom = 0
    
    if diff_datatc is not None and len(diff_datatc) > 0:
        tc_heading = yaw  # 航向角在第4列（Python索引3）
        tc_horizontal, tc_lateral, tc_vertical, tc_forward = calculate_errors(diff_datatc, tc_heading)
        tc_cep, tc_cep95, tc_cep99 = calculate_cep(tc_horizontal)
        tc_lateral_cep, tc_lateral_cep95, tc_lateral_cep99 = calculate_cep(np.abs(tc_lateral))
        tc_forward_cep, tc_forward_cep95, tc_forward_cep99 = calculate_cep(np.abs(tc_forward))
        tc_vertical_cep, tc_vertical_cep95, tc_vertical_cep99 = calculate_cep(np.abs(tc_vertical))
        
        # 计算TC里程数
        if tcs is not None and len(tcs) > 0:
            if t_start is not None and t_end is not None and len(time_ranges) > 0:
                # 对于多段时间范围，分别计算每段时间范围内的里程，然后相加
                tc_total_odom = 0
                print(f'Debug: TC时间范围数量: {len(time_ranges)}')
                for i in range(len(time_ranges)):
                    range_start = time_ranges[i][0]
                    range_end = time_ranges[i][1]
                    print(f'Debug: TC时间范围 {i+1}: {range_start:.2f} - {range_end:.2f}')
                    # 使用tcs的时间向量来筛选tcs数据
                    indices = np.where((tcs[:, 0] >= range_start) & (tcs[:, 0] <= range_end))[0]
                    print(f'Debug: TC找到的索引数量: {len(indices)}')
                    if len(indices) > 0:
                        # 确保indices在tcs的有效范围内
                        print(f'Debug: TC索引范围: {min(indices)} - {max(indices)}')
                        valid_indices = indices[indices < len(tcs)]
                        print(f'Debug: TC有效索引数量: {len(valid_indices)}')
                        if len(valid_indices) > 0:
                            # 使用原始数据中的位置信息计算里程
                            # 假设位置信息在第7、8、9列（对应MATLAB的8、9、10列）
                            segment_data = tcs[valid_indices, :]
                            segment_odom = calculate_odometry(segment_data)
                            print(f'Debug: TC段里程: {segment_odom[-1]:.2f}')
                            tc_total_odom = tc_total_odom + segment_odom[-1]
                print(f'Debug: TC总里程: {tc_total_odom:.2f}')
                tc_odom = tc_total_odom
            else:
                # 没有时间范围限制，计算所有数据的里程
                print('Debug: 没有时间范围限制，计算所有TC数据的里程')
                # 使用原始数据中的位置信息计算里程
                # 假设位置信息在第7、8、9列（对应MATLAB的8、9、10列）
                tc_odom = calculate_odometry(tcs)
                print(f'Debug: TC总里程: {tc_odom[-1]:.2f}')
        else:
            print('Debug: TC数据为空')
            tc_odom = 0
    
    # 计算GNSS的误差（如果有GNSS数据）
    gnss_horizontal = []
    gnss_lateral = []
    gnss_vertical = []
    gnss_forward = []
    gnss_cep = 0
    gnss_cep95 = 0
    gnss_cep99 = 0
    gnss_odom = 0
    
    if diff_datagnss is not None and len(diff_datagnss) > 0:
        gnss_heading = yaw  # 航向角在第4列（Python索引3）
        gnss_horizontal, gnss_lateral, gnss_vertical, gnss_forward = calculate_errors(diff_datagnss, gnss_heading)
        gnss_cep, gnss_cep95, gnss_cep99 = calculate_cep(gnss_horizontal)
        gnss_lateral_cep, gnss_lateral_cep95, gnss_lateral_cep99 = calculate_cep(np.abs(gnss_lateral))
        gnss_forward_cep, gnss_forward_cep95, gnss_forward_cep99 = calculate_cep(np.abs(gnss_forward))
        gnss_vertical_cep, gnss_vertical_cep95, gnss_vertical_cep99 = calculate_cep(np.abs(gnss_vertical))
        
        # 计算GNSS里程数
        if gnss is not None and len(gnss) > 0:
            if t_start is not None and t_end is not None and len(time_ranges) > 0:
                # 对于多段时间范围，分别计算每段时间范围内的里程，然后相加
                gnss_total_odom = 0
                print(f'Debug: GNSS时间范围数量: {len(time_ranges)}')
                for i in range(len(time_ranges)):
                    range_start = time_ranges[i][0]
                    range_end = time_ranges[i][1]
                    print(f'Debug: GNSS时间范围 {i+1}: {range_start:.2f} - {range_end:.2f}')
                    # 使用gnss的时间向量来筛选gnss数据
                    indices = np.where((gnss[:, 0] >= range_start) & (gnss[:, 0] <= range_end))[0]
                    print(f'Debug: GNSS找到的索引数量: {len(indices)}')
                    if len(indices) > 0:
                        # 确保indices在gnss的有效范围内
                        print(f'Debug: GNSS索引范围: {min(indices)} - {max(indices)}')
                        valid_indices = indices[indices < len(gnss)]
                        print(f'Debug: GNSS有效索引数量: {len(valid_indices)}')
                        if len(valid_indices) > 0:
                            # 使用原始数据中的位置信息计算里程
                            # 假设位置信息在第7、8、9列（对应MATLAB的8、9、10列）
                            segment_data = gnss[valid_indices, :]
                            segment_odom = calculate_odometry(segment_data)
                            print(f'Debug: GNSS段里程: {segment_odom[-1]:.2f}')
                            gnss_total_odom = gnss_total_odom + segment_odom[-1]
                print(f'Debug: GNSS总里程: {gnss_total_odom:.2f}')
                gnss_odom = gnss_total_odom
            else:
                # 没有时间范围限制，计算所有数据的里程
                print('Debug: 没有时间范围限制，计算所有GNSS数据的里程')
                # 使用原始数据中的位置信息计算里程
                # 假设位置信息在第7、8、9列（对应MATLAB的8、9、10列）
                gnss_odom = calculate_odometry(gnss)
                print(f'Debug: GNSS总里程: {gnss_odom[-1]:.2f}')
        else:
            print('Debug: GNSS数据为空')
            gnss_odom = 0
    
    # ===== LC部分 =====
    if fid is not None:
        fid.write(f'{lcver} Statistics:\n')
        fid.write('----------------------------------------\n')
        
        # 添加检查确保变量不为空
        if len(lc_horizontal) > 0 and len(lc_lateral) > 0 and len(lc_vertical) > 0 and len(lc_forward) > 0:
            # 打印表头 (中文标题)
            fid.write('%-24s  %-24s  %-24s  %-24s\n' % (
                '水平位置误差/m', '横向位置误差/m', '前进方向位置误差/m', '高程位置误差/m'))
            # 打印表头 (英文指标和里程)
            fid.write('%-12s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s\n' % (
                'Total Odom(km)', 'rms', 'CEP95', 'CEP99', 'max',
                'rms', 'CEP95', 'CEP99', 'max',
                'rms', 'CEP95', 'CEP99', 'max',
                'rms', 'CEP95', 'CEP99', 'max'))
            # 打印数据行 (里程和误差数据)
            fid.write('%-12.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f\n' % (
                lc_odom / 1000 if isinstance(lc_odom, (int, float)) else lc_odom[-1] / 1000,
                rms(lc_horizontal), lc_cep95, lc_cep99, np.max(lc_horizontal),
                rms(lc_lateral), lc_lateral_cep95, lc_lateral_cep99, np.max(np.abs(lc_lateral)),
                rms(lc_forward), lc_forward_cep95, lc_forward_cep99, np.max(np.abs(lc_forward)),
                rms(lc_vertical), lc_vertical_cep95, lc_vertical_cep99, np.max(np.abs(lc_vertical))))
        else:
            fid.write(f'Error: {lcver}数据计算出错\n')
        fid.write('\n')
    
    # ===== TC部分 =====
    if fid is not None and diff_datatc is not None and len(diff_datatc) > 0:
        fid.write(f'{tcver} Statistics:\n')
        fid.write('----------------------------------------\n')
        
        # 添加检查确保变量不为空
        if len(tc_horizontal) > 0 and len(tc_lateral) > 0 and len(tc_vertical) > 0 and len(tc_forward) > 0:
            # 打印表头 (中文标题)
            fid.write('%-24s  %-24s  %-24s  %-24s\n' % (
                '水平位置误差/m', '横向位置误差/m', '前进方向位置误差/m', '高程位置误差/m'))
            # 打印表头 (英文指标和里程)
            fid.write('%-12s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s\n' % (
                'Total Odom(km)', 'rms', 'CEP95', 'CEP99', 'max',
                'rms', 'CEP95', 'CEP99', 'max',
                'rms', 'CEP95', 'CEP99', 'max',
                'rms', 'CEP95', 'CEP99', 'max'))
            # 打印数据行 (里程和误差数据)
            fid.write('%-12.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f\n' % (
                tc_odom / 1000 if isinstance(tc_odom, (int, float)) else tc_odom[-1] / 1000,
                rms(tc_horizontal), tc_cep95, tc_cep99, np.max(tc_horizontal),
                rms(tc_lateral), tc_lateral_cep95, tc_lateral_cep99, np.max(np.abs(tc_lateral)),
                rms(tc_forward), tc_forward_cep95, tc_forward_cep99, np.max(np.abs(tc_forward)),
                rms(tc_vertical), tc_vertical_cep95, tc_vertical_cep99, np.max(np.abs(tc_vertical))))
        else:
            fid.write(f'Error: {tcver}数据计算出错\n')
        fid.write('\n')
    
    # ===== GNSS部分 =====
    if fid is not None and diff_datagnss is not None and len(diff_datagnss) > 0:
        fid.write('GNSS Statistics:\n')
        fid.write('----------------------------------------\n')
        
        # 添加检查确保变量不为空
        if len(gnss_horizontal) > 0 and len(gnss_lateral) > 0 and len(gnss_vertical) > 0 and len(gnss_forward) > 0:
            # 打印表头 (中文标题)
            fid.write('%-24s  %-24s  %-24s  %-24s\n' % (
                '水平位置误差/m', '横向位置误差/m', '前进方向位置误差/m', '高程位置误差/m'))
            # 打印表头 (英文指标和里程)
            fid.write('%-12s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s\n' % (
                'Total Odom(km)', 'rms', 'CEP95', 'CEP99', 'max',
                'rms', 'CEP95', 'CEP99', 'max',
                'rms', 'CEP95', 'CEP99', 'max',
                'rms', 'CEP95', 'CEP99', 'max'))
            # 打印数据行 (里程和误差数据)
            fid.write('%-12.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f  %-6.3f\n' % (
                gnss_odom / 1000 if isinstance(gnss_odom, (int, float)) else gnss_odom[-1] / 1000,
                rms(gnss_horizontal), gnss_cep95, gnss_cep99, np.max(gnss_horizontal),
                rms(gnss_lateral), gnss_lateral_cep95, gnss_lateral_cep99, np.max(np.abs(gnss_lateral)),
                rms(gnss_forward), gnss_forward_cep95, gnss_forward_cep99, np.max(np.abs(gnss_forward)),
                rms(gnss_vertical), gnss_vertical_cep95, gnss_vertical_cep99, np.max(np.abs(gnss_vertical))))
        else:
            fid.write('Error: GNSS数据计算出错\n')
        fid.write('\n')
    
    if fid is not None:
        fid.close()
        print(f"精度统计结果已保存到: {outfile}")
    
    # 返回统计结果
    if return_stats:
        return {
            'lc': {
                'odom': lc_odom / 1000 if isinstance(lc_odom, (int, float)) else (lc_odom[-1] / 1000 if len(lc_odom) > 0 else 0),
                'horizontal_rms': rms(lc_horizontal) if len(lc_horizontal) > 0 else 0,
                'horizontal_cep95': lc_cep95 if len(lc_horizontal) > 0 else 0,
                'horizontal_cep99': lc_cep99 if len(lc_horizontal) > 0 else 0,
                'horizontal_max': np.max(lc_horizontal) if len(lc_horizontal) > 0 else 0,
                'lateral_rms': rms(lc_lateral) if len(lc_lateral) > 0 else 0,
                'lateral_cep95': lc_lateral_cep95 if len(lc_lateral) > 0 else 0,
                'lateral_cep99': lc_lateral_cep99 if len(lc_lateral) > 0 else 0,
                'lateral_max': np.max(np.abs(lc_lateral)) if len(lc_lateral) > 0 else 0,
                'forward_rms': rms(lc_forward) if len(lc_forward) > 0 else 0,
                'forward_cep95': lc_forward_cep95 if len(lc_forward) > 0 else 0,
                'forward_cep99': lc_forward_cep99 if len(lc_forward) > 0 else 0,
                'forward_max': np.max(np.abs(lc_forward)) if len(lc_forward) > 0 else 0,
                'vertical_rms': rms(lc_vertical) if len(lc_vertical) > 0 else 0,
                'vertical_cep95': lc_vertical_cep95 if len(lc_vertical) > 0 else 0,
                'vertical_cep99': lc_vertical_cep99 if len(lc_vertical) > 0 else 0,
                'vertical_max': np.max(np.abs(lc_vertical)) if len(lc_vertical) > 0 else 0
            },
            'tc': {
                'odom': tc_odom / 1000 if isinstance(tc_odom, (int, float)) else (tc_odom[-1] / 1000 if len(tc_odom) > 0 else 0),
                'horizontal_rms': rms(tc_horizontal) if len(tc_horizontal) > 0 else 0,
                'horizontal_cep95': tc_cep95 if len(tc_horizontal) > 0 else 0,
                'horizontal_cep99': tc_cep99 if len(tc_horizontal) > 0 else 0,
                'horizontal_max': np.max(tc_horizontal) if len(tc_horizontal) > 0 else 0,
                'lateral_rms': rms(tc_lateral) if len(tc_lateral) > 0 else 0,
                'lateral_cep95': tc_lateral_cep95 if len(tc_lateral) > 0 else 0,
                'lateral_cep99': tc_lateral_cep99 if len(tc_lateral) > 0 else 0,
                'lateral_max': np.max(np.abs(tc_lateral)) if len(tc_lateral) > 0 else 0,
                'forward_rms': rms(tc_forward) if len(tc_forward) > 0 else 0,
                'forward_cep95': tc_forward_cep95 if len(tc_forward) > 0 else 0,
                'forward_cep99': tc_forward_cep99 if len(tc_forward) > 0 else 0,
                'forward_max': np.max(np.abs(tc_forward)) if len(tc_forward) > 0 else 0,
                'vertical_rms': rms(tc_vertical) if len(tc_vertical) > 0 else 0,
                'vertical_cep95': tc_vertical_cep95 if len(tc_vertical) > 0 else 0,
                'vertical_cep99': tc_vertical_cep99 if len(tc_vertical) > 0 else 0,
                'vertical_max': np.max(np.abs(tc_vertical)) if len(tc_vertical) > 0 else 0
            },
            'gnss': {
                'odom': gnss_odom / 1000 if isinstance(gnss_odom, (int, float)) else (gnss_odom[-1] / 1000 if len(gnss_odom) > 0 else 0),
                'horizontal_rms': rms(gnss_horizontal) if len(gnss_horizontal) > 0 else 0,
                'horizontal_cep95': gnss_cep95 if len(gnss_horizontal) > 0 else 0,
                'horizontal_cep99': gnss_cep99 if len(gnss_horizontal) > 0 else 0,
                'horizontal_max': np.max(gnss_horizontal) if len(gnss_horizontal) > 0 else 0,
                'lateral_rms': rms(gnss_lateral) if len(gnss_lateral) > 0 else 0,
                'lateral_cep95': gnss_lateral_cep95 if len(gnss_lateral) > 0 else 0,
                'lateral_cep99': gnss_lateral_cep99 if len(gnss_lateral) > 0 else 0,
                'lateral_max': np.max(np.abs(gnss_lateral)) if len(gnss_lateral) > 0 else 0,
                'forward_rms': rms(gnss_forward) if len(gnss_forward) > 0 else 0,
                'forward_cep95': gnss_forward_cep95 if len(gnss_forward) > 0 else 0,
                'forward_cep99': gnss_forward_cep99 if len(gnss_forward) > 0 else 0,
                'forward_max': np.max(np.abs(gnss_forward)) if len(gnss_forward) > 0 else 0,
                'vertical_rms': rms(gnss_vertical) if len(gnss_vertical) > 0 else 0,
                'vertical_cep95': gnss_vertical_cep95 if len(gnss_vertical) > 0 else 0,
                'vertical_cep99': gnss_vertical_cep99 if len(gnss_vertical) > 0 else 0,
                'vertical_max': np.max(np.abs(gnss_vertical)) if len(gnss_vertical) > 0 else 0
            }
        }
    
    return None
