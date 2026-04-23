# 批量运行评估脚本使用说明

## 概述

`batch_run_precision_head_horizontal.py` 是一个批量运行评估脚本的工具，可以自动扫描指定目录下的所有配置文件，并依次运行 `precision_head_topic_ref_100c_wdh_horizontal_only.py` 脚本。

## 功能特点

- 自动扫描目录及子目录下的所有配置文件
- 依次运行每个配置文件
- 记录详细的运行日志和错误日志
- 生成批量运行总结报告
- 实时显示运行进度和状态
- 统计成功率和总耗时

## 使用方法

### 基本用法

```bash
python batch_run_precision_head_horizontal.py <配置文件目录>
```

### 参数说明

- `配置文件目录`: 存放配置文件的目录路径（必需）

脚本会自动在该目录及其子目录中查找所有名为 `precision_head_topic_ref_100c_wdh_config.toml` 的配置文件。

## 目录结构要求

配置文件目录的结构示例：

```
/path/to/configs/
├── dataset1/
│   └── precision_head_topic_ref_100c_wdh_config.toml
├── dataset2/
│   └── precision_head_topic_ref_100c_wdh_config.toml
└── dataset3/
    └── precision_head_topic_ref_100c_wdh_config.toml
```

配置文件可以放在目录的任意层级，脚本会递归扫描所有子目录。

## 运行示例

```bash
# 进入脚本所在目录
cd modules/util/evaluate_pys/

# 运行批量评估
python batch_run_precision_head_horizontal.py /mnt/d/dockers/rt/rtk_pvt/2026/0324
```

## 输出结果

运行完成后，会在配置文件目录下生成一个日志目录：

```
/path/to/configs/
└── batch_run_logs_20260330_163330/    # 日志目录（时间戳命名）
    ├── batch_summary.txt               # 批量运行总结报告
    ├── precision_head_topic_ref_100c_wdh_config.toml.log         # 每个配置的运行日志
    ├── precision_head_topic_ref_100c_wdh_config.toml_error.log   # 每个配置的错误日志
    └── ...
```

### 日志文件说明

1. **batch_summary.txt**: 批量运行总结报告
   - 包含所有配置文件的运行状态
   - 显示成功/失败统计
   - 记录总耗时和成功率

2. **{config_name}.log**: 每个配置文件的详细运行日志
   - 包含脚本的完整输出信息
   - 用于查看评估过程的详细信息

3. **{config_name}_error.log**: 每个配置文件的错误日志
   - 仅包含错误信息（stderr）
   - 用于排查失败原因

## 控制台输出示例

```
扫描配置文件目录: /path/to/configs
找到 3 个配置文件:
  1. /path/to/configs/dataset1/precision_head_topic_ref_100c_wdh_config.toml
  2. /path/to/configs/dataset2/precision_head_topic_ref_100c_wdh_config.toml
  3. /path/to/configs/dataset3/precision_head_topic_ref_100c_wdh_config.toml

日志目录: /path/to/configs/batch_run_logs_20260330_163330

开始批量运行...
================================================================================

进度: [1/3]
================================================================================
开始运行配置文件: precision_head_topic_ref_100c_wdh_config.toml
================================================================================
✓ precision_head_topic_ref_100c_wdh_config.toml 运行成功 (耗时: 45.23秒)

进度: [2/3]
================================================================================
开始运行配置文件: precision_head_topic_ref_100c_wdh_config.toml
================================================================================
✓ precision_head_topic_ref_100c_wdh_config.toml 运行成功 (耗时: 38.67秒)

进度: [3/3]
================================================================================
开始运行配置文件: precision_head_topic_ref_100c_wdh_config.toml
================================================================================
✓ precision_head_topic_ref_100c_wdh_config.toml 运行成功 (耗时: 52.14秒)

================================================================================
批量运行完成!
================================================================================
配置文件总数: 3
成功: 3
失败: 0
成功率: 100.00%
总耗时: 136.04秒 (2.27分钟)

日志目录: /path/to/configs/batch_run_logs_20260330_163330
总结文件: /path/to/configs/batch_run_logs_20260330_163330/batch_summary.txt
```

## 注意事项

1. **配置文件命名**: 配置文件必须命名为 `precision_head_topic_ref_100c_wdh_config.toml`，否则不会被识别。

2. **脚本依赖**: 确保 `precision_head_topic_ref_100c_wdh_horizontal_only.py` 与批量运行脚本在同一目录下。

3. **Python环境**: 确保已安装评估脚本所需的所有Python依赖库。

4. **磁盘空间**: 批量运行会生成大量的日志文件和评估结果，请确保有足够的磁盘空间。

5. **运行时间**: 批量运行的时间取决于配置文件的数量和每个评估任务的数据量，请合理安排运行时间。

6. **失败处理**: 如果某个配置文件运行失败，脚本会继续运行剩余的配置文件，并在总结中标记失败的配置。

## 故障排查

### 未找到配置文件

如果提示"未找到任何配置文件"，请检查：
- 配置文件目录路径是否正确
- 配置文件是否命名为 `precision_head_topic_ref_100c_wdh_config.toml`
- 配置文件是否在指定的目录或子目录中

### 评估脚本不存在

如果提示"评估脚本不存在"，请检查：
- `precision_head_topic_ref_100c_wdh_horizontal_only.py` 是否与批量运行脚本在同一目录
- 文件名是否正确

### 查看失败原因

如果某些配置文件运行失败：
1. 查看对应的 `{config_name}_error.log` 错误日志文件
2. 查看对应的 `{config_name}.log` 完整日志文件
3. 检查配置文件中的路径是否正确
4. 检查数据文件是否存在

## 高级用法

### 自定义脚本路径

如果评估脚本不在同一目录，可以修改 `batch_run_precision_head_horizontal.py` 中的 `script_path` 变量：

```python
# 在 main() 函数中修改
script_path = '/path/to/your/precision_head_topic_ref_100c_wdh_horizontal_only.py'
```

### 并行运行（需要修改脚本）

如果需要并行运行多个配置文件以提高效率，可以考虑使用 `multiprocessing` 或 `concurrent.futures` 模块修改脚本。

## 相关文件

- `precision_head_topic_ref_100c_wdh_horizontal_only.py`: 水平精度评估脚本
- `precision_head_topic_ref_100c_wdh_config.toml`: 配置文件模板
- `batch_run_precision_head_horizontal.py`: 批量运行脚本（本文件）

## 版本历史

- v1.0 (2026-03-30): 初始版本
  - 支持批量运行配置文件
  - 支持日志记录和总结报告
  - 支持递归扫描目录