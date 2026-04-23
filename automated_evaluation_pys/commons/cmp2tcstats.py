import os
from compareTCHisStatistics import compareTCHisStatistics
from compareDH_Dalt import compareDH_Dalt

def cmp2tcstats():
    """
    比较两个TC统计数据
    """
    fold1 = 'D:/dockers/test_summary/tcmsf_7c846ff'
    fold2 = 'D:/dockers/test_summary/tcmsf_005c10e'
    output_dir = 'path/to/results_folder'

    file1 = os.path.join(fold1, 'statistics_his.txt')
    file2 = os.path.join(fold2, 'statistics_his.txt')

    # 执行主函数
    compareTCHisStatistics(file1, file2, fold2)

    file1 = os.path.join(fold1, 'statistics_max.txt')
    file2 = os.path.join(fold2, 'statistics_max.txt')
    compareDH_Dalt(file1, file2, fold2)

# 如果直接运行此脚本，则执行cmp2tcstats函数
if __name__ == "__main__":
    cmp2tcstats()
