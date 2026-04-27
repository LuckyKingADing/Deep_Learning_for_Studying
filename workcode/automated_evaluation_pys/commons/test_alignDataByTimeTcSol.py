import numpy as np
from alignDataByTimeTcSol import alignDataByTimeTcSol

def test_alignDataByTimeTcSol():
    """
    测试alignDataByTimeTcSol函数的正确性
    """
    print("测试alignDataByTimeTcSol函数...")
    
    # 创建测试数据
    # 模拟时间戳，其中一个值为102.22
    time1 = np.array([10.0, 20.0, 102.22, 40.0, 50.0])
    data1 = np.column_stack((time1, np.ones((len(time1), 5))))  # 6列数据，第一列为时间
    
    time2 = np.array([10.01, 20.02, 102.23, 40.01, 60.0])  # 与time1接近的时间
    data2 = np.column_stack((time2, np.ones((len(time2), 5)) * 2))  # 6列数据，第一列为时间
    
    # 测试原始功能（x=1，即不进行额外的归化）
    print("\n测试1: 原始功能 (x=1)")
    print(f"time1: {time1}")
    print(f"time2: {time2}")
    
    aligned_data1, aligned_data2, common_time = alignDataByTimeTcSol(data1, time1, data2, time2, 0.01, 1)
    
    print(f"对齐后的数据1形状: {aligned_data1.shape}")
    print(f"对齐后的数据2形状: {aligned_data2.shape}")
    print(f"共同时间长度: {len(common_time)}")
    print(f"对齐后的数据1时间列: {aligned_data1[:, 0]}")
    print(f"对齐后的数据2时间列: {aligned_data2[:, 0]}")
    
    # 测试新功能（x=10，即按10的倍数归化）
    print("\n测试2: 按10的倍数归化 (x=10)")
    aligned_data1_x10, aligned_data2_x10, common_time_x10 = alignDataByTimeTcSol(data1, time1, data2, time2, 0.01, 10)
    
    print(f"对齐后的数据1形状: {aligned_data1_x10.shape}")
    print(f"对齐后的数据2形状: {aligned_data2_x10.shape}")
    print(f"共同时间长度: {len(common_time_x10)}")
    print(f"对齐后的数据1时间列: {aligned_data1_x10[:, 0]}")
    print(f"对齐后的数据2时间列: {aligned_data2_x10[:, 0]}")
    
    # 详细展示时间处理过程
    print("\n时间处理过程演示:")
    print(f"原始时间1: {time1}")
    print(f"原始时间2: {time2}")
    
    # 按容差处理
    tol = 0.01
    rounded_time1 = np.round(time1 / tol)
    rounded_time2 = np.round(time2 / tol)
    print(f"按容差{tol}处理后的时间1: {rounded_time1}")
    print(f"按容差{tol}处理后的时间2: {rounded_time2}")
    
    # 按x=10归化
    x = 10
    normalized_time1 = np.round(rounded_time1 / x) * x
    normalized_time2 = np.round(rounded_time2 / x) * x
    print(f"按{x}的倍数归化后的时间1: {normalized_time1}")
    print(f"按{x}的倍数归化后的时间2: {normalized_time2}")
    
    # 测试特定案例：数字102.22，tol为0.01，x=10
    print("\n测试特定案例: 数字是102.22，tol为0.01，x=10")
    time_specific = np.array([102.22])
    data_specific = np.column_stack((time_specific, np.ones((len(time_specific), 5))))
    
    # 手动计算预期结果
    temp_rounded = np.round(102.22 / 0.01)  # = np.round(10222.0) = 10222
    normalized = np.round(temp_rounded / 10) * 10  # = np.round(1022.2) * 10 = 1022 * 10 = 10220
    print(f"手动计算: np.round({102.22} / {0.01}) = {temp_rounded}")
    print(f"然后: np.round({temp_rounded} / {x}) * {x} = {normalized}")
    
    # 使用函数验证
    aligned_data1_spec, aligned_data2_spec, common_time_spec = alignDataByTimeTcSol(
        data_specific, time_specific, data_specific, time_specific, 0.01, 10)
    
    print(f"函数返回的对齐数据时间: {aligned_data1_spec[:, 0] if len(aligned_data1_spec) > 0 else '无匹配数据'}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_alignDataByTimeTcSol()
