# aggregate_precision_statistics.py 使用说明

## 功能概述

该脚本用于聚合多个精度统计文件（位置精度和速度精度），按里程加权平均计算总体评估结果。

## 命令行参数

### 配置文件相关参数

- `--config CONFIG`: 指定配置文件路径（默认: `aggregate_precision_statistics_config.toml`）
- `--no-config`: 不使用配置文件，仅使用命令行参数

### 通用参数

- `--input-dir INPUT_DIR`: 输入目录，会递归查找所有精度统计文件
- `--output-file OUTPUT_FILE`: 位置精度输出文件路径
- `--velocity-output-file VELOCITY_OUTPUT_FILE`: 速度精度输出文件路径

### 选项参数

- `--skip-zero-scenes`: 跳过全为0的场景
- `--no-skip-zero-scenes`: 不跳过全为0的场景
- `--verbose`: 在控制台打印详细信息
- `--quiet`, `-q`: 静默模式，不打印详细信息

## 使用示例

### 1. 使用默认配置文件

```bash
python3 aggregate_precision_statistics.py
```

### 2. 使用指定的配置文件

```bash
python3 aggregate_precision_statistics.py --config /path/to/my_config.toml
```

### 3. 完全通过命令行指定参数

```bash
python3 aggregate_precision_statistics.py \
  --input-dir /data/results \
  --output-file /output/precision.txt \
  --velocity-output-file /output/velocity.txt \
  --skip-zero-scenes \
  --verbose
```

### 4. 跳过配置文件，仅使用命令行参数

```bash
python3 aggregate_precision_statistics.py \
  --no-config \
  --input-dir /mnt/d/dockers/rt/rtk_pvt/2026/pvtres/pvtrtk \
  --output-file output.txt \
  --velocity-output-file velocity.txt \
  --verbose
```

### 5. 使用配置文件，但覆盖部分参数

```bash
# 使用配置文件的默认设置，但覆盖输入目录
python3 aggregate_precision_statistics.py \
  --input-dir /custom/input/dir

# 使用配置文件，但覆盖输出文件和静默模式
python3 aggregate_precision_statistics.py \
  --output-file custom_output.txt \
  --quiet
```

## 配置文件格式

配置文件使用 TOML 格式，示例：

```toml
# 聚合精度统计文件配置文件（位置精度和速度精度）

[general]
# 输入目录，会递归查找所有精度统计文件
input_dir = "/mnt/d/dockers/rt/rtk_pvt/2026/pvtres/pvtrtk"

# 位置精度输出文件路径
output_file = "position_precision_aggregated.txt"

# 速度精度输出文件路径
velocity_output_file = "velocity_precision_aggregated.txt"

[options]
# 是否跳过全为0的场景（默认true）
skip_zero_scenes = true

# 是否在控制台打印详细信息（默认true）
verbose = true
```

## 参数优先级

参数的优先级从高到低为：

1. 命令行参数（最高优先级）
2. 配置文件
3. 代码中的默认值（最低优先级）

## 集成到其他脚本

由于现在支持完整的命令行参数，该脚本可以轻松集成到其他系统或批处理脚本中：

### 示例：Bash 脚本集成

```bash
#!/bin/bash

# 设置参数
INPUT_DIR="/data/evaluation/results"
OUTPUT_DIR="/data/evaluation/aggregated"

# 运行聚合脚本
python3 aggregate_precision_statistics.py \
  --no-config \
  --input-dir "$INPUT_DIR" \
  --output-file "$OUTPUT_DIR/precision.txt" \
  --velocity-output-file "$OUTPUT_DIR/velocity.txt" \
  --skip-zero-scenes \
  --quiet

echo "聚合完成！"
```

### 示例：Python 脚本集成

```python
import subprocess
import os

def run_aggregation(input_dir, output_dir):
    """运行聚合脚本"""
    cmd = [
        'python3', 'aggregate_precision_statistics.py',
        '--no-config',
        '--input-dir', input_dir,
        '--output-file', os.path.join(output_dir, 'precision.txt'),
        '--velocity-output-file', os.path.join(output_dir, 'velocity.txt'),
        '--verbose'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("聚合成功！")
        print(result.stdout)
    else:
        print("聚合失败！")
        print(result.stderr)
    
    return result.returncode == 0

# 使用示例
run_aggregation('/data/results', '/data/output')
```

## 注意事项

1. 如果不使用 `--no-config` 且配置文件不存在或加载失败，会使用默认配置
2. 所有参数都是可选的，未指定的参数会使用配置文件或默认值
3. 使用 `--quiet` 或 `-q` 可以减少输出信息，适合批处理场景
4. 命令行参数会覆盖配置文件中的相同设置

## 故障排查

### 问题：提示无法加载配置文件

**解决方案**：
- 检查配置文件路径是否正确
- 使用 `--no-config` 跳过配置文件，直接使用命令行参数
- 确保安装了 `toml` 库：`pip install toml`

### 问题：找不到精度统计文件

**解决方案**：
- 检查 `--input-dir` 指定的目录是否正确
- 确保目录下存在 `position_precision.txt` 和 `velocity_precision.txt` 文件
- 使用 `--verbose` 查看详细的搜索过程