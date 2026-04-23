# MATLAB to Python 转换项目

## 项目概述
本项目将位于 `/mnt/d/dockers/matlab` 目录下的 MATLAB 脚本转换为 Python 脚本，并将所有转换后的脚本存放在 `modules/util/evaluate_pys` 目录下。

## 转换状态
- **源目录**: `/mnt/d/dockers/matlab`
- **目标目录**: `modules/util/evaluate_pys`
- **总脚本数**: 103个MATLAB脚本
- **已转换脚本**: 包含主要功能函数

## 已转换的主要脚本

### 数据读取函数
- `getParentDirectory.py` - 获取父目录路径
- `readSensorData.py` - 读取传感器数据
- `readSensorDataTcSol.py` - 读取TC解决方案数据
- `readSensorDataTcXkPk.py` - 读取TC XkPk数据
- `readmsf_debug_state.py` - 读取MSF调试状态
- `readgnsstopic.py` - 读取GNSS话题数据
- `readgnsscsv.py` - 读取GNSS CSV数据
- `read_rts_file.py` - 读取RTS文件
- `load100ccsv.py` - 加载100c CSV数据
- `skipCommentLines.py` - 跳过注释行

### 数据处理函数
- `calculate_cep.py` - 计算CEP（圆概率误差）
- `calculate_errors.py` - 计算误差
- `calculateDifferenceTcSol.py` - 计算TC解决方案差异
- `calculateDifferenceTcSol_sp.py` - 计算TC解决方案差异（特殊版本）
- `calculate_odometry.py` - 计算里程计
- `att_diff_adjust.py` - 调整姿态差异
- `tr2rpy.py` - 转换为滚转-俯仰-偏航角度

### 可视化函数
- `plot_errors.py` - 绘制误差图
- `plot_precision_comparison.py` - 绘制精度比较图
- `plot_skyview.py` - 绘制天空视图
- `skyplot.py` - 绘制天空图
- `plotgnsscsv.py` - 绘制GNSS CSV数据
- `plot_stats_comparison.py` - 绘制统计比较图
- `plot_precision_errors.py` - 绘制精度误差图

### 比较分析函数
- `compare_tc_gnsstopic.py` - 比较TC与GNSS话题
- `compare_2msfstate.py` - 比较两个MSF状态
- `compare_tc_lc.py` - 比较TC与LC
- `compare_tc_lc_mul.py` - 比较TC与LC（多版本）
- `compare_tc_lc_ref_100c.py` - 比较TC、LC与参考数据（100c）
- `precision_tc_lc_ref_100c.py` - 精度分析：TC、LC与参考数据对比
- `compare_lc_gnsstopic.py` - 比较LC与GNSS话题

### 精度分析函数
- `precision3d_rts_ref_100c.py` - 3D精度分析：TC、LC与RTS参考数据对比

### 统计分析函数
- `StatsComparisonAll.py` - 统计比较（全部）
- `plotStatsComparisonaAll.py` - 绘制统计比较图（全部）
- `compareTCHisStatistics.py` - 比较TC历史统计数据
- `compareDH_Dalt.py` - 比较DH和Dalt数据
- `precision3d_tc_lc_ref_100c_.py` - 3D精度分析：TC、LC与参考数据对比

### 工具函数
- `cmp2tcstats.py` - 比较TC统计数据

### 测试函数
- `test_alignDataByTimeTcSol.py` - 测试alignDataByTimeTcSol函数

### 特殊修复
- `precision3d_rts_ref_100c.py`中的`InterpState`函数已修复，现在能处理时间非单调递增的情况（如时间倒序），解决了RTS数据插值失败的问题

## 转换原则
1. 保持原有MATLAB脚本的逻辑和功能
2. 使用Python等效库（numpy、pandas、matplotlib等）替换MATLAB函数
3. 保持变量命名和代码结构尽可能一致
4. 添加适当的文档字符串和注释

## 依赖关系
- numpy
- pandas
- matplotlib
- scipy
- os

## 使用方法
每个Python脚本都可以独立运行或作为模块导入使用。主要函数通常包含在if __name__ == "__main__":块中，用于测试目的。

## 注意事项
- 路径可能需要根据实际环境进行调整
- 部分MATLAB特有的高级功能可能需要进一步适配
- 数据格式和接口应与原MATLAB版本保持兼容
