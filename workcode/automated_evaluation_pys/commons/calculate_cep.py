import numpy as np

def calculate_cep(horizontal_error):
    """
    CALCULATE_CEP 计算CEP、CEP95和CEP99
    :param horizontal_error: 水平误差向量
    :return: cep: 圆概率误差（50%的值在此范围内）
             cep95: 95%的值在此范围内的圆概率误差
             cep99: 99%的值在此范围内的圆概率误差
    """
    # 方法2：基于百分位数的精确计算（推荐）
    # 对误差进行排序
    sorted_errors = np.sort(horizontal_error)

    # 计算不同百分位数的误差值
    n = len(sorted_errors)
    cep = sorted_errors[int(np.ceil(0.5 * n)) - 1]      # 50%分位数 (Python索引从0开始)
    cep95 = sorted_errors[int(np.ceil(0.95 * n)) - 1]   # 95%分位数
    cep99 = sorted_errors[int(np.ceil(0.99 * n)) - 1]   # 99%分位数

    return cep, cep95, cep99
