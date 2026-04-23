"""
时间范围处理函数
对应MATLAB函数: subtractTimeRangesVectorized
"""

import numpy as np


def subtractTimeRangesVectorized(tsm0, tem0, t_start, t_end):
    """
    从原始时间范围中减去指定的子范围
    :param tsm0: 原始时间范围起始点（列表或标量）
    :param tem0: 原始时间范围结束点（列表或标量）
    :param t_start: 要减去的子范围起始点（列表或标量）
    :param t_end: 要减去的子范围结束点（列表或标量）
    :return: new_tsm0: 新的时间范围起始点
             new_tem0: 新的时间范围结束点
    """
    # 转换为numpy数组以便处理
    tsm0 = np.array([tsm0]) if np.isscalar(tsm0) else np.array(tsm0)
    tem0 = np.array([tem0]) if np.isscalar(tem0) else np.array(tem0)
    t_start = np.array([t_start]) if np.isscalar(t_start) else np.array(t_start)
    t_end = np.array([t_end]) if np.isscalar(t_end) else np.array(t_end)
    
    # 检查输入长度是否一致
    if len(tsm0) != len(tem0):
        raise ValueError('tsm0 and tem0 must have the same length')
    if len(t_start) != len(t_end):
        raise ValueError('t_start and t_end must have the same length')
    
    # 如果没有要减去的范围，直接返回原始范围
    if len(t_start) == 0:
        return tsm0, tem0
    
    new_tsm0 = []
    new_tem0 = []
    
    # 对每个原始时间范围进行处理
    for i in range(len(tsm0)):
        start_range = tsm0[i]
        end_range = tem0[i]
        
        # 初始化当前剩余的范围
        current_ranges = [(start_range, end_range)]
        
        # 对每个要减去的子范围进行处理
        for j in range(len(t_start)):
            sub_start = t_start[j]
            sub_end = t_end[j]
            
            new_ranges = []
            
            # 对当前每个剩余范围，检查是否与子范围有重叠
            for (cur_start, cur_end) in current_ranges:
                # 如果子范围完全在当前范围之外，保留当前范围
                if sub_end <= cur_start or sub_start >= cur_end:
                    new_ranges.append((cur_start, cur_end))
                # 如果子范围完全包含当前范围，不添加任何范围
                elif sub_start <= cur_start and sub_end >= cur_end:
                    continue
                # 如果子范围与当前范围部分重叠
                else:
                    # 子范围从左边开始切割
                    if sub_start > cur_start and sub_start < cur_end:
                        # 保留左边部分
                        if sub_start > cur_start:
                            new_ranges.append((cur_start, sub_start))
                    
                    # 子范围从右边结束切割
                    if sub_end > cur_start and sub_end < cur_end:
                        # 保留右边部分
                        if sub_end < cur_end:
                            new_ranges.append((sub_end, cur_end))
                    
                    # 如果子范围完全在当前范围内，分割成两部分
                    if sub_start <= cur_start and sub_end >= cur_end:
                        continue  # 完全覆盖，不添加
                    elif sub_start > cur_start and sub_end < cur_end:
                        new_ranges.append((cur_start, sub_start))
                        new_ranges.append((sub_end, cur_end))
            
            current_ranges = new_ranges
            
            # 如果没有剩余范围，提前终止
            if len(current_ranges) == 0:
                break
        
        # 将当前处理后的范围添加到结果中
        for (s, e) in current_ranges:
            new_tsm0.append(s)
            new_tem0.append(e)
    
    # 转换为numpy数组并返回
    new_tsm0 = np.array(new_tsm0) if new_tsm0 else np.array([])
    new_tem0 = np.array(new_tem0) if new_tem0 else np.array([])
    
    return new_tsm0, new_tem0