# 精度统计文件聚合工具

## 功能说明

该工具用于聚合多个精度统计文件（`position_precision.txt`），按照以下规则计算总体评估结果：

1. **自动查找文件**：从指定目录递归查找所有精度统计文件
2. **数据提取**：解析每个文件中的 LC、TC、GNSS 三种统计数据
3. **加权平均计算**：
   - 对同类场景（如 "All"）按里程占总里程占比取加权均值
   - odo（里程）取和
   - 完全为0的场景不参与加权平均
4. **输出结果**：生成与原格式相同的 lc、tc、gnss 分类总体评估结果

## 配置文件

使用 TOML 格式的配置文件 `aggregate_precision_statistics_config.toml` 来配置输入参数：

```toml
[general]
# 输入目录，会递归查找所有精度统计文件
input_dir = "/mnt/d/dockers/rt/rtk_pvt/2026"

# 输出文件路径
output_file = "position_precision_aggregated.txt"

[options]
# 是否跳过全为0的场景（默认true）
skip_zero_scenes = true

# 是否在控制台打印详细信息（默认true）
verbose = true
```

## 使用方法

### 1. 使用默认配置文件

```bash
python3 aggregate_precision_statistics.py
```

这将自动加载同目录下的 `aggregate_precision_statistics_config.toml` 配置文件。

### 2. 指定配置文件

```bash
python3 aggregate_precision_statistics.py --config /path/to/custom_config.toml
```

### 3. 使用命令行参数覆盖配置

```bash
# 覆盖输入目录
python3 aggregate_precision_statistics.py --input-dir /custom/input/dir

# 覆盖输出文件
python3 aggregate_precision_statistics.py --output-file custom_output.txt

# 同时覆盖多个参数
python3 aggregate_precision_statistics.py \
  --input-dir /custom/input/dir \
  --output-file custom_output.txt
```

### 4. 配置文件 + 命令行参数

```bash
# 使用配置文件，但覆盖部分参数
python3 aggregate_precision_statistics.py \
  --config aggregate_precision_statistics_config.toml \
  --input-dir /custom/input/dir
```

## 依赖项

- Python 3.6+
- toml 库（可选，用于解析配置文件）

安装 toml 库：

```bash
pip install toml
```

如果未安装 toml 库，脚本将使用默认配置运行，但无法加载自定义配置文件。

## 示例

### 示例 1：默认配置运行

```bash
cd /home/wufengbo/workcode/repos/cnoa/byd_adas_app
python3 modules/util/automated_evaluation_pys/pvt_rtk_lc_evaluation/aggregate_precision_statistics.py
```

输出：
```
正在查找目录 /mnt/d/dockers/rt/rtk_pvt/2026 中的精度统计文件...
找到 2 个精度统计文件:
  - /mnt/d/dockers/rt/rtk_pvt/2026/0319/results/position_precision.txt
  - /mnt/d/dockers/rt/rtk_pvt/2026/0324/results0/pvt_2026-03-24_19-30-11/position_precision.txt

正在解析文件...
  已解析: /mnt/d/dockers/rt/rtk_pvt/2026/0319/results/position_precision.txt
  已解析: /mnt/d/dockers/rt/rtk_pvt/2026/0324/results0/pvt_2026-03-24_19-30-11/position_precision.txt

正在聚合统计数据...
正在生成输出...

聚合结果已保存到: position_precision_aggregated.txt

聚合统计信息:

LC (pvtlc_vcpb_a3fc76c):
  场景数量: 2
    All: odom=71.064km, H-rms=3.624m
    Normal (LC, No Tunnel): odom=36.478km, H-rms=4.141m
...
```

### 示例 2：自定义配置文件

创建自定义配置文件 `my_config.toml`：

```toml
[general]
input_dir = "/mnt/d/dockers/rt/rtk_pvt/2026"
output_file = "my_aggregated_result.txt"

[options]
skip_zero_scenes = true
verbose = false
```

运行：

```bash
python3 aggregate_precision_statistics.py --config my_config.toml
```

## 输出格式

生成的聚合结果文件格式与原始精度统计文件相同，包含：

- LC 版本统计
- TC 版本统计
- GNSS 统计

每个统计包含以下场景类型的加权平均值：
- All
- Highway
- Conventional Urban Area
- Tree-lined Roads
- Elevated Structure
- Urban Canyon
- Satellite Repeater
- Long Tunnel
- Normal (LC, No Tunnel)
- Normal (TC, No Tunnel)
- Normal (GNSS, No Tunnel/Repeater)

每个场景包含以下指标：
- Odom(km): 总里程
- H-rms: 水平位置误差均方根
- H-CEP95: 水平位置误差95%圆误差概率
- H-CEP99: 水平位置误差99%圆误差概率
- H-max: 水平位置误差最大值
- L-rms: 横向误差均方根
- L-CEP95: 横向误差95%圆误差概率
- L-CEP99: 横向误差99%圆误差概率
- L-max: 横向误差最大值
- F-rms: 前进方向误差均方根
- F-CEP95: 前进方向误差95%圆误差概率
- F-CEP99: 前进方向误差99%圆误差概率
- F-max: 前进方向误差最大值

## 注意事项

1. 配置文件中的路径可以是绝对路径或相对路径
2. 命令行参数的优先级高于配置文件
3. 如果未安装 toml 库，脚本会显示警告并使用默认配置
4. 完全为0的场景（odom=0且所有指标=0）会被自动跳过
5. 输出文件会被覆盖，请确保重要数据已备份