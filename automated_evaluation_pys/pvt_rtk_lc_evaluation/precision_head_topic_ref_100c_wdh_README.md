# precision_head_topic_ref_100c_wdh 使用说明

## 概述

`precision_head_topic_ref_100c_wdh.py` 是一个基于head topic和参考数据的精度评估脚本，对应MATLAB文件 `precision_head_topic_ref_100c_wdh.m`。

## 功能特性

- 读取LC数据 (tcmsf_sol.csv)
- 读取TC数据 (tcmsf_sol_msf.csv)
- 读取GNSS数据 (gnss.csv)
- 读取参考数据 (ref_02.txt)
- 进行时间对齐
- 计算误差
- 输出统计结果
- 绘制误差曲线

## 使用方法

### 方法1: 使用TOML配置文件（推荐）

```bash
python precision_head_topic_ref_100c_wdh.py config.toml
```

#### 配置文件示例

参考 `precision_head_topic_ref_100c_wdh_config.toml` 文件：

```toml
# precision_head_topic_ref_100c_wdh 配置文件示例

[data]
# 基础目录路径
basefold = "/path/to/data"
# 参考数据文件路径
reffile = "/path/to/ref.txt"
# LC版本名称 (默认: 空)
lcver = ""
# TC版本名称 (默认: 空)
tcver = ""
# 数据集名称 (默认: 空)
dataset = ""
# 时间偏移 (默认: 0)
dt = 0.0

[plot]
# 是否绘制LC数据
plotlc = true
# 是否绘制TC数据
plottc = false
# 是否绘制GNSS数据
plotgnssstat = true

[evaluation]
# 时间阈值
tthreshod = 0.005
# 选择数据集 (0-5)
# 0: 20251205
# 1: 20251209
# 2: 20251216
# 3: 20251217
# 4: 20260105
seldataset = 0

[output]
# 输出目录 (默认为basefold，如果为空字符串则使用basefold)
output_dir = ""

[advanced]
# 参考真值的数据类型
# 0: 2504月采集的真值
# 1: 后续wdh处理的真值
reftype = 0
# 状态文件的类型
# 0: tcmsf_sol.csv
# 1: msf_debug_state.csv
statetype = 0
```

#### 配置参数说明

**[data] 数据配置**
- `basefold`: 基础目录路径，包含所有数据文件
- `reffile`: 参考数据文件路径（真值）
- `lcver`: LC版本名称，用于构建LC数据文件路径
- `tcver`: TC版本名称，用于构建TC数据文件路径
- `dataset`: 数据集名称
- `dt`: 时间偏移量（秒）

**[plot] 绘图配置**
- `plotlc`: 是否绘制LC数据（true/false）
- `plottc`: 是否绘制TC数据（true/false）
- `plotgnssstat`: 是否绘制GNSS数据（true/false）

**[evaluation] 评估配置**
- `tthreshod`: 时间对齐阈值（秒）
- `seldataset`: 选择数据集编号（0-5）

**[output] 输出配置**
- `output_dir`: 输出目录，如果为空则使用basefold

**[advanced] 高级配置**
- `reftype`: 参考真值数据类型（0或1）
- `statetype`: 状态文件类型（0或1）

### 方法2: 使用命令行参数（已弃用）

```bash
python precision_head_topic_ref_100c_wdh.py <basefold> <reffile> [lcver] [tcver] [dataset] [dt] [plotlc] [plottc] [plotgnssstat] [seldataset]
```

**注意**: 命令行参数模式已弃用，建议使用TOML配置文件。

## 输出文件

脚本运行后会生成以下文件：

1. **precison_statistics.txt** - 精度统计结果
   - LC、TC、GNSS的均值、RMS、最大值、最小值
   - 数据点数量

2. **error_analysis.png** - 误差曲线图
   - 水平误差、横向误差、前进方向误差、垂直误差
   - 包含带GNSS和不带GNSS两个版本

## 数据集说明

脚本支持以下预定义数据集：

- **0**: 20251205 - 包含隧道、林荫路、城市峡谷、高架等场景
- **1**: 20251209 - 包含隧道、林荫路、城市峡谷、高快等场景
- **2**: 20251216 - 包含城市峡谷、高架、沈海高速等场景
- **3**: 20251217 - 包含林荫路、城市峡谷、高架、沈海高速等场景
- **4**: 20260105 - 完整数据集

## 依赖项

```python
numpy
pandas
matplotlib
toml
```

安装依赖：
```bash
pip install numpy pandas matplotlib toml
```

## 示例

### 示例1: 基本使用

1. 复制配置文件模板：
```bash
cp precision_head_topic_ref_100c_wdh_config.toml my_config.toml
```

2. 编辑配置文件，设置数据路径：
```toml
[data]
basefold = "/home/user/data/20251205"
reffile = "/home/user/data/ref_02.txt"
lcver = "lc_version_1"
tcver = "tc_version_1"
dataset = "test_run"
```

3. 运行脚本：
```bash
python precision_head_topic_ref_100c_wdh.py my_config.toml
```

### 示例2: 只评估LC数据

```toml
[plot]
plotlc = true
plottc = false
plotgnssstat = false
```

### 示例3: 自定义输出目录

```toml
[output]
output_dir = "/home/user/results"
```

## 注意事项

1. 确保所有数据文件路径正确
2. 参考数据文件必须存在
3. 时间偏移量需要根据实际情况调整
4. 输出目录需要有写入权限
5. 如果使用statetype=1，需要确保readmsf_debug_state函数可用

## 故障排除

### 问题1: 配置文件不存在
```
错误: 配置文件不存在: config.toml
```
**解决**: 检查配置文件路径是否正确

### 问题2: 无法解析配置文件
```
错误: 无法解析配置文件 - ...
```
**解决**: 检查TOML语法是否正确，使用在线TOML验证工具检查

### 问题3: 数据文件不存在
```
警告: LC文件不存在: /path/to/file.csv
```
**解决**: 检查basefold、lcver、tcver、dataset等参数是否正确

## 返回值

函数返回一个包含所有处理结果的字典：

```python
{
    'lcs': lcs,                    # LC原始数据
    'tcs': tcs,                    # TC原始数据
    'gnss': gnss,                  # GNSS原始数据
    'refdata': refdata,            # 参考数据
    'diff_datalc': diff_datalc,    # LC误差数据
    'diff_datatc': diff_datatc,    # TC误差数据
    'diff_datagnss': diff_datagnss,# GNSS误差数据
    'common_timelc': common_timelc,    # LC对齐时间
    'common_timetc': common_timetc,    # TC对齐时间
    'common_timegnss': common_timegnss,# GNSS对齐时间
    't0': t0,                      # 时间基准点
    't_start': t_start,            # 时间范围起始点
    't_end': t_end                 # 时间范围结束点
}
```

## 联系方式

如有问题，请联系开发团队。