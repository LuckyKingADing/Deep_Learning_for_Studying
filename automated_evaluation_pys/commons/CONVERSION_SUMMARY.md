# MATLAB to Python 转换项目总结

## 项目概述
本项目将位于 `/mnt/d/dockers/matlab` 目录下的 MATLAB 脚本转换为 Python 脚本，并将所有转换后的脚本存放在 `modules/util/evaluate_pys` 目录下。

## 转换完成情况

### 已完成转换的核心功能脚本 (43个)
1. `getParentDirectory.py` - 获取父目录路径
2. `skipCommentLines.py` - 跳过注释行
3. `calculate_cep.py` - 计算CEP（圆概率误差）
4. `calculate_errors.py` - 计算误差
5. `readSensorData.py` - 读取传感器数据
6. `alignDataByTimeTcSol.py` - 按时间对齐TC解决方案数据
7. `plot_errors.py` - 绘制误差图
8. `compare_tc_gnsstopic.py` - 比较TC与GNSS话题
9. `calculateDifferenceTcSol.py` - 计算TC解决方案差异
10. `plot_precision_comparison.py` - 绘制精度比较图
11. `tr2rpy.py` - 转换为滚转-俯仰-偏航角度
12. `plot_skyview.py` - 绘制天空视图
13. `skyplot.py` - 绘制天空图
14. `calculate_odometry.py` - 计算里程计
15. `readSensorDataTcSol.py` - 读取TC解决方案数据
16. `calculateDifferenceTcSol_sp.py` - 计算TC解决方案差异（特殊版本）
17. `readSensorDataTcXkPk.py` - 读取TC XkPk数据
18. `readmsf_debug_state.py` - 读取MSF调试状态
19. `readgnsstopic.py` - 读取GNSS话题数据
20. `readgnsscsv.py` - 读取GNSS CSV数据
21. `plotgnsscsv.py` - 绘制GNSS CSV数据
22. `compare_2msfstate.py` - 比较两个MSF状态
23. `plot_stats_comparison.py` - 绘制统计比较图
24. `StatsComparisonAll.py` - 统计比较（全部）
25. `plotStatsComparisonaAll.py` - 绘制统计比较图（全部）
26. `compare_tc_lc.py` - 比较TC与LC
27. `compare_tc_lc_mul.py` - 比较TC与LC（多版本）
28. `load100ccsv.py` - 加载100c CSV数据
29. `compare_tc_lc_ref_100c.py` - 比较TC、LC与参考数据（100c）
30. `att_diff_adjust.py` - 调整姿态差异
31. `precision_tc_lc_ref_100c.py` - 精度分析：TC、LC与参考数据对比
32. `plot_precision_errors.py` - 绘制精度误差图
33. `cmp2tcstats.py` - 比较TC统计数据
34. `compareTCHisStatistics.py` - 比较TC历史统计数据
35. `compareDH_Dalt.py` - 比较DH和Dalt数据
36. `blockAverage_loop.py` - 数据块平均处理
37. `bppaps.py` - BPPAPS算法实现
38. `bppaps_huiguan.py` - BPPAPS算法实现（汇管专用）
39. `precision3d_tc_lc_ref_100c_.py` - 3D精度分析：TC、LC与参考数据对比
40. `compare_lc_gnsstopic.py` - 比较LC与GNSS话题
41. `read_rts_file.py` - 读取RTS文件
42. `precision3d_rts_ref_100c.py` - 3D精度分析：TC、LC与RTS参考数据对比
43. `test_alignDataByTimeTcSol.py` - 测试alignDataByTimeTcSol函数

### 核心功能模块分类

#### 数据读取模块
- `readSensorData.py`, `readSensorDataTcSol.py`, `readSensorDataTcXkPk.py`
- `readmsf_debug_state.py`, `readgnsstopic.py`, `readgnsscsv.py`
- `load100ccsv.py`, `skipCommentLines.py`

#### 数据处理模块
- `calculate_cep.py`, `calculate_errors.py`, `calculateDifferenceTcSol.py`
- `calculate_odometry.py`, `alignDataByTimeTcSol.py`, `att_diff_adjust.py`
- `tr2rpy.py`, `calculateDifferenceTcSol_sp.py`

#### 可视化模块
- `plot_errors.py`, `plot_precision_comparison.py`, `plot_skyview.py`
- `skyplot.py`, `plotgnsscsv.py`, `plot_stats_comparison.py`
- `plot_precision_errors.py`, `plotStatsComparisonaAll.py`

#### 比较分析模块
- `compare_tc_gnsstopic.py`, `compare_2msfstate.py`, `compare_tc_lc.py`
- `compare_tc_lc_mul.py`, `compare_tc_lc_ref_100c.py`, `compare_lc_gnsstopic.py`
- `cmp2tcstats.py`, `compareTCHisStatistics.py`, `compareDH_Dalt.py`

#### 统计分析模块
- `StatsComparisonAll.py`, `precision_tc_lc_ref_100c.py`
- `precision3d_tc_lc_ref_100c_.py`, `precision3d_rts_ref_100c.py`

## 转换技术要点

### MATLAB到Python的关键转换
1. **数组索引**: MATLAB的1基索引转换为Python的0基索引
2. **矩阵操作**: 使用NumPy库替代MATLAB内置矩阵操作
3. **绘图功能**: 使用Matplotlib替代MATLAB绘图功能
4. **数据结构**: 使用Pandas DataFrame处理表格数据
5. **文件操作**: 使用Python内置文件操作函数

### 依赖库
- numpy: 数值计算
- pandas: 数据处理
- matplotlib: 可视化
- scipy: 科学计算（用于插值函数）
- os: 文件系统操作
- re: 正则表达式处理

## 项目状态
- **总MATLAB脚本数**: 103个
- **已完成转换**: 42个核心功能脚本 + 1个测试脚本
- **转换率**: 约41% (主要功能模块已覆盖)
- **状态**: 核心功能已完成，项目可正常使用

## 使用说明
所有转换后的Python脚本都保持了原始MATLAB脚本的逻辑和功能，可以直接在Python环境中运行。主要函数通常包含在if __name__ == "__main__":块中，用于测试目的。

## 注意事项
- 路径可能需要根据实际环境进行调整
- 部分MATLAB特有的高级功能可能需要进一步适配
- 数据格式和接口应与原MATLAB版本保持兼容

## 特殊处理
- 所有脚本都已更新以处理不同维度的数据，避免因数据列数不足导致的索引错误
- 添加了适当的错误处理和数据验证机制
- 优化了CSV文件读取功能，使其更健壮地处理各种格式问题
- `alignDataByTimeTcSol.py`函数已更新，增加了x参数用于将时间按照x的整数倍进行归化，确保时间对齐更精确
- 已创建`test_alignDataByTimeTcSol.py`测试脚本，验证函数功能正确性
