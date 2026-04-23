import numpy as np
import os

def StatsComparisonAll(statsall, save_dir):
    """
    统计比较所有数据
    :param statsall: 包含统计数据的列表
    :param save_dir: 保存目录
    """
    len_stats = len(statsall) - 1
    sums = np.zeros((len_stats, 6))
    
    for i in range(len_stats):
        stati = statsall[i]
        sums[i, 0] = stati.TC.max_abs[5] - stati.LC.max_abs[5]  # 第6个元素，Python索引为5
        sums[i, 1] = stati.TC.max_abs[6] - stati.LC.max_abs[6]  # 第7个元素，Python索引为6
        sums[i, 2] = stati.TC.interval_percent[0, 0] - stati.LC.interval_percent[0, 0]  # 第1行第1列
        sums[i, 3] = stati.TC.interval_percent[1, 0] - stati.LC.interval_percent[1, 0]  # 第2行第1列
        sums[i, 4] = stati.TC.interval_percent[0, 3] - stati.LC.interval_percent[0, 3]  # 第1行第4列
        sums[i, 5] = stati.TC.interval_percent[1, 3] - stati.LC.interval_percent[1, 3]  # 第2行第4列

    # 创建保存目录（如果不存在）
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    with open(os.path.join(save_dir, 'statistics_compare.txt'), 'w') as fid:
        fid.write('%27sstatistical indicators changed table%25s\n' % (' ', ' '))
        fid.write('%5s%16s%16s%16s%16s%16s%16s\n' % ('type', 'H_max_error(m)',
            'V_max_error(m)', 'H_eror_0-0.2(%)', 'V_eror_0-0.2(%)',
            'H_eror_>1(%)', 'H_eror_>1(%)'))
        fid.write('%5s' % 'min')
        for val in min(sums):
            fid.write('%16.3f' % val)  # 制表符分隔各列结果
        fid.write('\n')
        fid.write('%5s' % 'max')
        for val in max(sums):
            fid.write('%16.3f' % val)  # 制表符分隔各列结果
        fid.write('\n')
        fid.write('%5s' % 'mean')
        for val in np.mean(sums, axis=0):
            fid.write('%16.3f' % val)  # 制表符分隔各列结果
        fid.write('\n')
    
    print(min(sums))
    print(max(sums))
    print(np.mean(sums, axis=0))

# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的统计数据和保存目录）
    # StatsComparisonAll(your_statsall, 'your_save_directory')
    pass
