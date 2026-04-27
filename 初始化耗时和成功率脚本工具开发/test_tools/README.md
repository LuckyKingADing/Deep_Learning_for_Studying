# Localization 初始化测试工具

本目录包含用于测试 localization 模块（TCMSF 和 DR）初始化成功率和耗时的工具集。

## 目录结构

```
test_tools/
├── test_runner.py       # 主测试运行器（驱动 TCMSF/DR 二进制程序执行测试）
├── post_process.py      # 后处理器（分析 CSV 输出 + 日志，提取指标）
├── analyze_results.py   # 结果分析器（汇总 JSON 结果，生成统计报告和图表）
├── requirements.txt    # Python 依赖
└── README.md           # 本文档
```

## 依赖安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 方式一：直接运行测试

```bash
# 测试 TCMSF 模块
python test_runner.py \
    --records /path/to/records/ \
    --output ./test_results/ \
    --module tcmsf

# 测试 DR 模块
python test_runner.py \
    --records /path/to/records/ \
    --output ./test_results/ \
    --module dr

# 同时测试两个模块
python test_runner.py \
    --records /path/to/records/ \
    --output ./test_results/ \
    --module both

# 并行测试
python test_runner.py \
    --records /path/to/records/ \
    --output ./test_results/ \
    --module both \
    --parallel 4
```

### 方式二：后处理已有结果

如果二进制程序已经运行过，直接分析输出的 CSV 和日志文件：

```bash
# 分析单个记录目录
python post_process.py \
    --data-dir /path/to/record_001/ \
    --output ./analysis/

# 分析多个目录
python post_process.py \
    --data-dirs ./data/record_001/ ./data/record_002/ ./data/record_003/ \
    --output ./analysis/

# 指定模块类型
python post_process.py \
    --data-dir ./data/record_001/ \
    --module tcmsf \
    --output ./analysis/
```

### 方式三：分析测试汇总结果

```bash
# 分析 test_runner.py 输出的 JSON 结果文件
python analyze_results.py \
    --input ./test_results/init_test_summary_*.json \
    --output ./analysis/ \
    --format both
```

## 模块说明

### 1. test_runner.py — 主测试运行器

驱动 localization 二进制程序执行测试，解析日志输出。

**使用前提：** 需要先通过 Bazel 构建 `TCMSF` 和 `DR` 二进制文件：

```bash
# 在 Apollo 源码目录下
bazel build //modules/localization/src/TCMSF:TCMSF
bazel build //modules/localization/src/dead_reckoning:DR

# 设置二进制路径
export TCMSF_BINARY=/path/to/bazel-bin/modules/localization/src/TCMSF/TCMSF
export DR_BINARY=/path/to/bazel-bin/modules/localization/src/dead_reckoning/DR
```

**参数说明：**

| 参数 | 说明 |
|------|------|
| `--records` | Apollo record 文件路径或目录（支持 glob 模式） |
| `--output` | 测试结果输出目录 |
| `--module` | 测试模块：`tcmsf`、`dr` 或 `both` |
| `--config` | TCMSF 的 IMU 配置文件路径（可选） |
| `--timeout` | 单次测试超时时间（秒），默认 300s |
| `--parallel` | 并行测试数量，默认 1 |
| `--verbose` | 显示详细输出 |

**输出文件：**
- `test_output.log` — 每次测试的完整日志
- `init_test_summary_<timestamp>.json` — 所有测试用例的汇总 JSON
- `init_test_results_<timestamp>.csv` — CSV 格式的测试结果

### 2. post_process.py — 后处理器

直接分析 TCMSF/DR 二进制输出的 CSV 文件和日志，无需重新运行测试。

**分析内容：**

对于 TCMSF：
- 解析 pose CSV，统计融合状态分布
- 从日志提取 `[INIT-TIMING]` 标记的耗时数据
- 计算 MSF Ready、MSF Aligned 耗时
- 统计 RTK FIX 率、传感器数据质量

对于 DR：
- 解析 dr_replay.csv
- 从日志提取初始化各阶段耗时
- 统计首次输出耗时

### 3. analyze_results.py — 结果分析器

分析 `test_runner.py` 输出的汇总 JSON，生成统计报告和可视化。

**功能：**
- 计算各耗时指标的均值、中位数、标准差、分位数
- 统计成功率、MSF Ready 率、Aligned 率
- 生成 Markdown / HTML 格式报告
- 生成耗时分布直方图
- 生成状态分布柱状图
- 拟合正态分布曲线

## C++ 代码改动说明

### TCMSF Component (`TCMSF/tcmsf_component.cc`)

新增了 `InitTiming` 结构体，在以下位置记录时间戳：

1. **构造函数** — 记录 `component_start`
2. **Init()** — 记录各子步骤完成时间
   - `iif_created` — IIF 接口创建完成
   - `resolve_created` — RTCM Resolve 创建完成
   - `tcmsf_created` — TCMSF 实例创建完成
   - `callbacks_registered` — 回调函数注册完成
   - `readers_created` — 所有 Reader 创建完成
   - `writers_created` — 所有 Writer 创建完成
   - `fusion_started` — 融合守护线程启动
3. **回调函数** — 记录首次数据到达时间
   - GPS、IMU、Vehicle 首帧到达时间
   - 有效 RTK FIX 到达时间
   - 首次 MSF 输出的融合状态和对准状态
4. **结果回调** — 输出 `[INIT-TIMING]` 日志
   - 首次输出时打印各阶段耗时
   - MSF Ready 状态到达时打印耗时
   - MSF Aligned 状态到达时打印耗时

### DR Component (`dead_reckoning/dr_component.cc`)

新增了 `DRInitTiming` 结构体，在以下位置记录时间戳：

1. **构造函数** — 记录 `component_start`
2. **Init()** — 记录各子步骤完成时间
   - `config_parsed` — 配置文件解析完成
   - `iif_created` — IIF 接口创建完成
   - `callbacks_registered` — 回调函数注册完成
   - `readers_created` — 所有 Reader 创建完成
   - `writers_created` — 所有 Writer 创建完成
3. **回调函数** — 记录首次数据到达时间
   - GPS、IMU、Vehicle 首帧到达时间
4. **DR 结果回调** — 记录首次 DR 输出时间

### Debug 基础设施 (`TCMSF/tcmsf/processor/include/processor_debug.h`)

- 新增 `init_timing.csv` 输出文件
- 将 `init_state.csv` 扩展用于初始化过程分析

## 关键日志标记

### TCMSF 日志

```
[INIT-TIMING] First MSF output at   123.45ms from start | imu_to_out:  98.12ms | gps_to_out: 102.34ms | fuse_start_to_out:  15.00ms | fusion_status:3 | align_status:2
[INIT-TIMING] MSF Ready! duration:1567.89ms from start
[INIT-TIMING] MSF ALIGNED! duration:2345.67ms from start
```

### DR 日志

```
[INIT-TIMING] DR Init complete in  12.34ms | config: 1.23ms | cbs: 5.67ms | readers: 8.90ms | writers:11.12ms
[INIT-TIMING] DR first output | init: 12.34ms | imu->out: 56.78ms | gps->out: 67.89ms | veh->out: 78.90ms | heading: 45.67
```

## 初始化状态机

```
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    │  ┌──────────┐     ┌──────────┐     ┌────▼─────┐
                    │  │ UNALIGNED│────►│COARSE_  │────►│FINE_     │────► ALIGNED
                    │  └──────────┘     │ALIGN    │     │ALIGN     │
                    │                   └──────────┘     └──────────┘
                    │                        ▲
                    │                        │
                    │                (GNSS 观测累积)
                    │                        │
                    └────────────────────────┘
                    (GNSS 观测异常时回退)
```

### 融合状态 (FusionStatus)

| 值 | 名称 | 说明 |
|----|------|------|
| 0 | UNINIT | 未初始化 |
| 1 | INIT | 初始化中 |
| 2 | GPSONLY | 仅 GPS 可用 |
| 3 | FULLSTATE | 全状态融合 |
| 4 | VFMODE | 仅视觉融合 |
| 5 | DRMODE | 仅 DR |

### 对准状态 (AlignType)

| 值 | 名称 | 说明 |
|----|------|------|
| 0 | UNALIGNED | 未对准 |
| 1 | COARSE_ALIGN | 粗对准 |
| 2 | FINE_ALIGN | 精对准 |
| 3 | ALIGNED | 完成对准 |

## 典型测试场景

### 场景 1：E2E 测试

```bash
# 准备记录数据
python test_runner.py \
    --records ./apollo_record_data/ \
    --output ./e2e_results/ \
    --module both \
    --parallel 4 \
    --timeout 600
```

### 场景 2：分析历史数据

```bash
# 后处理已有的测试数据
python post_process.py \
    --data-dirs ./results/2025_*/ \
    --output ./analysis/ \
    --module tcmsf

# 生成分析报告
python analyze_results.py \
    --input ./e2e_results/init_test_summary_latest.json \
    --output ./analysis/
```

### 场景 3：性能回归测试

```bash
# 运行基线测试
python test_runner.py --records ./records/ --output ./baseline/ --module tcmsf

# 修改代码后运行对比测试
python test_runner.py --records ./records/ --output ./after_change/ --module tcmsf

# 对比分析
python analyze_results.py --input ./baseline/init_test_summary_*.json --output ./analysis/baseline/
python analyze_results.py --input ./after_change/init_test_summary_*.json --output ./analysis/after_change/
```

## 注意事项

1. **Debug 模式**：TCMSF 的 `processor_debug.h` 默认只在 x86 架构下启用文件 IO。如果在 ARM 嵌入式平台运行，这些输出不会生成，但日志中的 `[INIT-TIMING]` 标记仍然可用。

2. **记录文件命名**：记录目录应包含 Apollo record 文件（`.record` 后缀）。脚本会自动递归搜索子目录。

3. **并行测试**：并行数不应超过 CPU 核心数。建议值为 CPU 核心数减 1。

4. **超时设置**：对于较长的记录文件，建议增加 `--timeout` 参数，避免测试被强制终止。

5. **二进制路径**：确保 `TCMSF_BINARY` 和 `DR_BINARY` 环境变量指向正确的 Bazel 构建产物。
