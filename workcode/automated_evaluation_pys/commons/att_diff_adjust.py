import numpy as np

def att_diff_adjust(att):
    """
    调整姿态差异
    :param att: 输入的姿态数据
    :return: 调整后的姿态数据
    """
    # 找到第3列（索引为2）大于180的索引
    idx1 = np.where(att[:, 2] > 180)[0]
    # 找到第3列（索引为2）小于-180的索引
    idx2 = np.where(att[:, 2] < -180)[0]
    
    # 如果idx1不为空
    if len(idx1) > 0:
        att[idx1, 2] = att[idx1, 2] - 360
    
    # 如果idx2不为空
    if len(idx2) > 0:
        att[idx2, 2] = att[idx2, 2] + 360
    
    return att

# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的数据）
    # att = att_diff_adjust(your_att_data)
    pass
