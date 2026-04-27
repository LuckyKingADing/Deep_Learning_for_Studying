# 批量执行tcmsf脚本使用说明

## 概述

`batch_run_tcmsf.py` 是一个用于批量执行tcmsf的Python脚本，它可以自动处理多个数据集，执行以下操作：

1. **第一轮**：对每个数据集执行tcmsf（命令A）并复制结果（命令B）
2. **第二轮**：修改配置文件后再次执行tcmsf（命令A）并复制结果（命令B）
3. **第三轮**：执行topic_parse（命令C）和WGS to Mars坐标转换（命令D）

## 功能特点

- 自动遍历指定路径下的所有子目录
- 支持两轮tcmsf执行（原始配置和修改配置后）
- 自动创建结果目录并复制结果文件
- 支持配置文件的自动备份和恢复
- 详细的执行日志和错误处理
- 灵活的命令行参数配置

## 前置要求

### 1. 编译依赖

确保以下可执行文件已编译：

```bash
# 编译tcmsf
bazel build -c opt modules/localization/src/TCMSF/TCMSF

# 编译record_parser（用于topic_parse）
bazel build -c opt modules/util/post_process/record_parser
```

### 2. 目录结构要求

输入路径应包含多个数据集子目录，每个子目录包含待处理的数据。例如：

```
/mnt/d/dockers/test/
├── dataset1/
├── dataset2/
├── dataset3/
└── ...
```

## 使用方法

### 基本用法

```bash
# 最简单的用法：处理指定路径下的所有数据集
python batch_run_tcmsf.py /mnt/d/dockers/test
```

### 完整参数

```bash
python batch_run_tcmsf.py <输入路径> [选项]
```

### 参数说明

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `input_path` | str | 输入路径，包含多个数据集子目录（必需） | - |
| `--tcmsf-bin` | str | tcmsf可执行文件路径 | `bazel-bin/modules/localization/src/TCMSF/TCMSF` |
| `--record-parser-bin` | str | record_parser可执行文件路径 | `bazel-bin/modules/util/post_process/record_parser` |
| `--config` | str | 需要修改的配置文件路径（可选） | `None` |
| `--suffix1` | str | 第一轮结果后缀 | `result_v1` |
| `--suffix2` | str | 第二轮结果后缀 | `result_v2` |
| `-v, --verbose` | flag | 显示详细输出 | `False` |
| `--no-backup` | flag | 不备份配置文件 | `False` |

## 使用示例

### 示例1：基本批量处理

```bash
# 处理测试路径下的所有数据集
python batch_run_tcmsf.py /mnt/d/dockers/test
```

生成的目录结构：

```
/mnt/d/dockers/test/
├── dataset1/
│   ├── result_v1/      # 第一轮结果（原始配置）
│   └── result_v2/      # 第二轮结果（修改配置后）
├── dataset2/
│   ├── result_v1/
│   └── result_v2/
└── ...
```

### 示例2：指定配置文件

```bash
# 使用指定的配置文件，并在处理后修改配置
python batch_run_tcmsf.py /mnt/d/dockers/test \
    --config /path/to/tcmsf_config.toml
```

配置文件修改需要在脚本中通过 `config_modifications` 字典定义要修改的配置项。

### 示例3：自定义结果后缀

```bash
# 使用自定义的结果目录后缀
python batch_run_tcmsf.py /mnt/d/dockers/test \
    --suffix1 original \
    --suffix2 modified
```

### 示例4：详细输出模式

```bash
# 显示详细的执行信息，便于调试
python batch_run_tcmsf.py /mnt/d/dockers/test -v
```

### 示例5：自定义可执行文件路径

```bash
# 使用特定路径的tcmsf可执行文件
python batch_run_tcmsf.py /mnt/d/dockers/test \
    --tcmsf-bin /custom/path/to/TCMSF \
    --record-parser-bin /custom/path/to/record_parser
```

## 执行流程说明

### 第一轮：原始配置执行

对每个数据集执行：

1. **命令A - 执行tcmsf**：
   ```bash
   bazel-bin/modules/localization/src/TCMSF/TCMSF <dataset_path> tcmsf
   ```

2. **命令B - 复制结果**：
   ```bash
   cp data/tmp/*.* <dataset_path>/result_v1/
   ```

### 第二轮：修改配置后执行

如果指定了配置文件：

1. 备份原配置文件（`.toml.bak`）
2. 修改配置文件中的指定参数
3. **命令A - 执行tcmsf**（使用修改后的配置）
4. **命令B - 复制结果**
5. 恢复原配置文件

### 第三轮：后处理

1. **命令C - 执行topic_parse**：
   - 创建 `topic_parse` 目录
   - 执行 record_parser 解析数据

2. **命令D - WGS to Mars坐标转换**：
   - 将WGS84坐标转换为火星坐标系（GCJ02）
   - 保存转换结果

## 配置修改

要在脚本中修改配置文件，需要在 `process_single_dataset` 方法中定义 `config_modifications` 字典。

示例：

```python
config_modifications = {
    "enable_variance_inflation": "false",
    "enable_satellite_r_inflation": "true",
    "fix_satellite_threshold": "9"
}
```

脚本会自动查找匹配的配置项并更新其值。

## 注意事项

### 1. 数据源目录

脚本假设tcmsf的结果输出到 `data/tmp/` 目录。如果实际输出目录不同，需要修改 `copy_results` 方法中的 `source_dir` 参数。

### 2. 权限要求

复制结果文件可能需要写权限。如果遇到权限问题：

```bash
# 以sudo权限运行（不推荐，仅在必要时使用）
sudo python batch_run_tcmsf.py /mnt/d/dockers/test
```

### 3. 记录文件处理

`record_parser` 的具体参数可能需要根据其实现调整。需要查看 `record_parser` 的帮助信息：

```bash
./bazel-bin/modules/util/post_process/record_parser --help
```

然后相应修改 `run_topic_parse` 方法中的命令参数。

### 4. WGS to Mars转换

脚本中提供了WGS to Mars转换的框架，但具体实现需要根据实际的转换工具进行调整。如果有坐标转换脚本：

```python
# 在 run_wgs_to_mars 方法中
command = ["python", "wgs_to_mars_converter.py", str(dataset_path)]
success = self.run_command(command, f"WGS to Mars - {dataset_name}")
```

## 错误处理

脚本包含完善的错误处理机制：

- 命令执行失败会显示详细的错误信息
- 单个数据集处理失败不会中断整体流程
- 最终会输出统计信息（成功/失败数量）

## 输出示例

```
============================================================
[开始处理] 数据集: dataset1
============================================================

[第一轮] 执行tcmsf（初始配置）
[信息] 创建结果目录: /mnt/d/dockers/test/dataset1/result_v1
[成功] 第一轮完成 - dataset1

[第二轮] 修改配置后执行tcmsf
[信息] 备份配置文件: /path/to/config.toml.bak
[修改] enable_variance_inflation = false
[成功] 第二轮完成 - dataset1

[第三轮] 执行topic_parse和wgs to mars
[信息] 执行WGS to Mars坐标转换 - dataset1
[成功] 第三轮完成 - dataset1

============================================================
[完成] 数据集 dataset1 处理完成
============================================================

[信息] 找到 10 个数据集
...

============================================================
[汇总] 批量处理完成
  总数: 10
  成功: 9
  失败: 1
============================================================
```

## 故障排除

### 问题1：tcmsf命令失败

**症状**：`[错误] 命令执行失败`

**解决方案**：
- 确认tcmsf已编译：检查 `bazel-bin/modules/localization/src/TCMSF/TCMSF` 是否存在
- 使用 `-v` 参数查看详细错误信息
- 手动测试tcmsf是否正常工作

### 问题2：结果复制失败

**症状**：`[警告] 源目录不存在: data/tmp`

**解决方案**：
- 检查tcmsf的实际输出目录
- 修改 `copy_results` 方法中的 `source_dir` 参数

### 问题3：配置文件修改失败

**症状**：`[错误] 修改配置文件失败`

**解决方案**：
- 检查配置文件格式（确保是TOML格式）
- 检查配置项名称是否正确
- 使用 `--no-backup` 参数跳过备份（如果备份失败）

### 问题4：解析record失败

**症状**：topic_parse执行失败

**解决方案**：
- 确认record_parser已编译
- 查看record_parser的参数要求
- 根据实际情况修改 `run_topic_parse` 方法中的命令

## 扩展功能

### 添加新的处理步骤

如果需要添加新的处理步骤，可以在 `process_single_dataset` 方法中添加新的方法调用：

```python
# 在第三轮后添加
print(f"\n[第四轮] 执行自定义处理")
if not self.run_custom_processing(dataset_path):
    print(f"[失败] 自定义处理失败 - {dataset_name}")
    all_success = False
```

### 过滤特定数据集

如果只想处理特定名称的数据集，可以修改 `get_subdirectories` 方法：

```python
def get_subdirectories(self) -> List[Path]:
    """获取输入路径下的所有子目录"""
    subdirs = []
    for item in self.input_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # 只处理名称包含特定关键词的目录
            if "关键词" in item.name:
                subdirs.append(item)
    
    subdirs.sort(key=lambda x: x.name)
    return subdirs
```

## 联系与支持

如有问题或建议，请联系开发团队。