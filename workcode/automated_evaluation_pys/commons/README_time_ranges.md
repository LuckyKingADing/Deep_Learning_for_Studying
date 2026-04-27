# 时间范围配置使用说明

## 概述

`precision_head_topic_ref_100c_wdh.py` 现在支持从TOML配置文件读取时间范围配置，并可以循环处理多个type的数据。

## 配置文件格式

在TOML配置文件中添加 `[time_ranges]` 配置节：

```toml
[time_ranges]
# 时间范围配置，支持多个type，每个type可以配置多个时间范围
# 格式: [[start1, end1], [start2, end2], ...]
# 时间为绝对时间（秒）

# Type 0: 20251205
[[time_ranges.type_config]]
type_label = "0"
type_time_range = [[444255.6, 444624.3], [446783.1, 447156.6]]

# Type 1: 20251209
[[time_ranges.type_config]]
type_label = "1"
type_time_range = [[200226.0, 200613.0], [215751.0, 215980.0]]

# Type 2: 20251216
[[time_ranges.type_config]]
type_label = "2"
type_time_range = [[183292.4, 183656.6], [187694.8, 191014.2]]

# Type 3: 20251217
[[time_ranges.type_config]]
type_label = "3"
type_time_range = [[278606.8, 281264.8]]

# Type 4: 20260105
[[time_ranges.type_config]]
type_label = "4"
type_time_range = []
```

## 配置参数说明

- `type_label`: type的标签，用于标识不同的数据类型
- `type_time_range`: 时间范围列表，每个元素是一个 `[start, end]` 对
  - `start`: 时间范围的起始点（绝对时间，单位：秒）
  - `end`: 时间范围的结束点（绝对时间，单位：秒）
  - 如果为空数组 `[]`，则表示使用全部数据，不进行时间范围筛选

## 使用方法

### 1. 准备配置文件

编辑 `precision_head_topic_ref_100c_wdh_config.toml` 文件，添加 `[time_ranges]` 配置节。

### 2. 运行脚本

```bash
python precision_head_topic_ref_100c_wdh.py precision_head_topic_ref_100c_wdh_config.toml
```

### 3. 输出结果

脚本会为每个type生成以下文件：

- `precison_statistics_type_{type_label}.txt`: 该type的精度统计结果
- `error_analysis_type_{type_label}_with_gnss.png`: 该type的误差曲线图（包含GNSS）
- `error_analysis_type_{type_label}_without_gnss.png`: 该type的误差曲线图（不包含GNSS）

## 向后兼容性

如果配置文件中没有 `[time_ranges]` 配置节，脚本会自动使用旧的 `seldataset` 逻辑，确保向后兼容。

## 示例

### 示例1: 配置多个type的时间范围

```toml
[time_ranges]

# 直线行驶场景
[[time_ranges.type_config]]
type_label = "straight"
type_time_range = [[100.0, 200.0], [500.0, 600.0]]

# 转弯场景
[[time_ranges.type_config]]
type_label = "turn"
type_time_range = [[300.0, 400.0]]

# 停车场景
[[time_ranges.type_config]]
type_label = "parking"
type_time_range = [[700.0, 800.0]]
```

### 示例2: 使用全部数据

```toml
[time_ranges]

[[time_ranges.type_config]]
type_label = "all_data"
type_time_range = []
```

## 注意事项

1. 时间范围使用绝对时间（秒），需要根据实际数据的时间戳进行配置
2. 每个type的时间范围可以有多个，脚本会合并所有范围内的数据
3. 如果时间范围配置为空数组，则使用全部数据
4. 输出文件名会包含type_label，便于区分不同type的结果

## 故障排除

### 问题: 配置文件中没有时间范围配置

**解决方案**: 检查TOML配置文件是否包含 `[time_ranges]` 配置节，如果没有，脚本会使用旧的seldataset逻辑。

### 问题: 时间范围没有数据

**解决方案**: 检查配置的时间范围是否在数据的时间范围内，可以通过查看数据的时间戳来确认。

### 问题: 输出文件没有生成

**解决方案**: 检查输出目录是否有写权限，以及数据文件是否存在。