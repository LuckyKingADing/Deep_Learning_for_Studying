# automated_evaluation_pys 技术深度解析

## 1. 项目概览表

| 属性 | 信息 |
|------|------|
| **项目名称** | automated_evaluation_pys（PVT RTK LC 精度评估工具包） |
| **项目来源** | BYD ADAS Team，MATLAB 转 Python 项目 |
| **主要语言** | Python（Python 3.7+），少量 Bash 脚本 |
| **许可协议** | 未声明（内部工具） |
| **发表会议/期刊** | 无（工业级内部工具） |
| **核心依赖** | numpy, pandas, matplotlib, scipy, toml |
| **仓库路径** | `/Work_code/ota630/automated_evaluation_pys` |
| **构建方式** | `setup.py` 打包，提供 `console_scripts` 入口点 |
| **前置依赖** | Apollo/bazel 编译的 TCMSF 二进制可执行文件（TCMSF, PARSER, convert_ie） |

---

## 2. 核心贡献与创新点

### 2.1 项目定位

本项目是一个**完整的 PVT（Position Velocity Time）/RTK（Real-Time Kinematic）/LC（Loosely Coupled）组合定位精度自动化评估工具链**，实现了从原始传感器录制数据到精度统计报告的全流程自动化。核心功能由三个阶段组成：

```
原始录制数据 ──► TCMSF融合定位处理 ──► GNSS数据解析 ──► 精度评估与可视化
```

### 2.2 系统架构总览

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         automated_evaluation_pys                              │
│                              工具链整体架构                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────┐                │
│  │ 阶段一：数据预处理（batch_run_tcmsf.py）                     │                │
│  │                                                             │                │
│  │  ┌──────────────┐    ┌──────────────┐    ┌────────────┐   │                │
│  │  │ TCMSF 融合   │───►│ topic_parse │───►│ WGS→Mars  │   │                │
│  │  │ 多 fusion    │    │ GNSS 解析   │    │ 坐标转换   │   │                │
│  │  │ mode 并行    │    │             │    │            │   │                │
│  │  └──────────────┘    └──────────────┘    └────────────┘   │                │
│  │        mode=[0,2,3]        (PARSER)        (convert_ie)   │                │
│  └─────────────────────────────────────────────────────────────┘                │
│                            │                                                 │
│                            ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────┐                │
│  │ 阶段二：精度评估（precision_head_topic_ref_100c_wdh_*.py）  │                │
│  │                                                             │                │
│  │  ┌──────────────┐    ┌──────────────┐    ┌────────────┐   │                │
│  │  │ 参考数据读取  │───►│ 时间对齐 &    │───►│ 误差分解    │   │                │
│  │  │ ref_02/84    │    │ 差值计算     │    │ H/L/F/V   │   │                │
│  │  └──────────────┘    └──────────────┘    └────────────┘   │                │
│  │                                                              │                │
│  │  ┌──────────────┐    ┌──────────────┐                      │                │
│  │  │ 误差曲线绘图  │    │ 精度统计输出  │                      │                │
│  │  │ + 极值子图    │    │ CEP/RMS/Max  │                      │                │
│  │  └──────────────┘    └──────────────┘                      │                │
│  └─────────────────────────────────────────────────────────────┘                │
│                            │                                                 │
│                            ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────┐                │
│  │ 阶段三：聚合统计（aggregate_precision_statistics.py）        │                │
│  │                                                             │                │
│  │  ┌──────────────┐    ┌──────────────┐                      │                │
│  │  │ 递归文件查找  │───►│ 里程加权聚合  │                      │                │
│  │  │ 多数据集汇总  │    │ 跨场景合并    │                      │                │
│  │  └──────────────┘    └──────────────┘                      │                │
│  └─────────────────────────────────────────────────────────────┘                │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────┐                │
│  │ 通用工具库（commons/）                                      │                │
│  │  ├── 数据读取：readSensorDataTcXkPk, readmsf_debug_state   │                │
│  │  ├── 坐标转换：dpos2den, alignDataByTimeTcSol             │                │
│  │  ├── 误差计算：calculate_errors, calculate_cep             │                │
│  │  ├── 里程计算：calculate_odometry                          │                │
│  │  ├── 可视化：plot_errors                                   │                │
│  │  └── 工具函数：fileutils, evaluation_utils                 │                │
│  └─────────────────────────────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 核心创新点

#### （1）多模式融合定位的批量自动评估

TCMSF（ Tightly Coupled Multi-Sensor Fusion）支持多种融合模式（PVTL C、PVTTC、RTKLC、RTKTC），`batch_run_tcmsf.py` 自动化完成所有模式的批量执行与结果管理，无需人工干预。

#### （2）WGS84 / GCJ-02 双坐标系智能适配

系统支持两种参考坐标系评估，自动识别参考文件格式（`*_84.txt` 或 `*_02.txt`），并根据 LC/TC 输出坐标系的差异，智能选择对应的参考数据进行对齐评估。

#### （3）场景化时间范围切片评估

通过 TOML 配置文件定义多种场景类型（开阔、半遮挡、双边遮挡、隧道、转发器），自动完成场景切分，支持特殊场景排除后的"正常场景"动态计算。

#### （4）多层级精度指标体系

- **位置精度**：水平（H）、横向（L）、前进方向（F）、高程（V）
- **统计指标**：RMS、CEP50、CEP95、CEP99、Max
- **里程加权聚合**：多数据集跨场景加权平均
- **速度精度**：额外的水平速度误差统计

#### （5）MATLAB 到 Python 的完整迁移

43 个 MATLAB 脚本完整迁移为 Python 实现，保持算法逻辑一致，包括 `alignDataByTimeTcSol`、`calculate_errors`、`CEP` 等核心算法。

---

## 3. 系统架构详解

### 3.1 模块结构

```
automated_evaluation_pys/
├── pvt_rtk_lc_evaluation/           # 顶层入口模块（打包为可安装包）
│   ├── __init__.py                   # 版本信息 (__version__)
│   ├── batch_run_tcmsf.py            # 阶段一：TCMSF批量处理主入口
│   ├── batch_run_tcmsf_and_precision.py  # 联合执行脚本
│   ├── batch_run_precision_head_horizontal.py  # 阶段二：批量精度评估
│   ├── precision_head_topic_ref_100c_wdh_main.py  # 统一入口（模式切换）
│   ├── precision_head_topic_ref_100c_wdh.py  # 完整评估（含高程）
│   ├── precision_head_topic_ref_100c_wdh_horizontal_only.py  # 水平精度专用
│   ├── aggregate_precision_statistics.py  # 阶段三：多数据集聚合统计
│   ├── convert_ref.py               # 参考数据转换
│   ├── *.toml                       # 各类配置文件模板
│   └── data/tmp/                    # 临时配置存放
│
├── commons/                         # 公共工具库（供所有模块调用）
│   ├── __init__.py
│   ├── evaluation_utils.py           # 评估工具公共函数（配置加载、数据处理、速度统计）
│   ├── utils.py                     # 数学工具：dpos2den、alignDataByTimeTcSol、calculateDifference、InterpState
│   ├── fileutils.py                 # 文件读取：readfullcsv（通用CSV解析）
│   ├── calculate_errors.py           # 误差计算：horizontal/lateral/forward/vertical 分解
│   ├── calculate_cep.py              # CEP 分位数计算
│   ├── calculate_odometry.py        # 里程累积计算
│   ├── plot_errors.py               # 误差曲线可视化
│   ├── outpre_new.py                # 精度统计输出（核心输出函数）
│   ├── readSensorDataTcXkPk.py      # TCMSF 融合结果读取
│   ├── readmsf_debug_state.py       # MSF 调试状态读取
│   ├── readSensorDataTcSol.py       # TC 解决方案数据读取
│   ├── readSensorData.py            # 通用传感器数据读取
│   ├── readgnsscsv.py              # GNSS CSV 读取
│   ├── readgnsstopic.py             # GNSS topic 读取
│   ├── read_rts_file.py             # RTS 文件读取
│   ├── compare_*.py                # 各类对比分析脚本（~10个）
│   ├── plot_*.py                    # 各类绘图脚本（~8个）
│   └── *.py                         # 其他辅助工具
│
├── data_compression_archive.py      # 数据压缩打包工具
├── setup.py                         # 包安装配置
└── requirements.txt                 # 依赖声明
```

### 3.2 核心模块详解

#### 模块 A：`batch_run_tcmsf.py`（数据预处理流水线）

**职责**：对原始录制数据进行 TCMSF 融合定位处理，生成标准化输出目录。

**关键处理流程**：

```
遍历输入目录 ──► 对每个子数据集执行：
  ├─ [命令A] TCMSF融合定位（多fusion_mode循环）
  │         ├─ 修改配置文件（gnss_oem_type, vehicle_info, gnss_fusion_mode）
  │         ├─ 执行 TCMSF 二进制
  │         └─ 复制 data/tmp 输出到 {fusion_type}_{tcmsf_ver} 目录
  ├─ [命令C] topic_parse（GNSS数据解析，PARSER 二进制）
  │         └─ 输出到 topic_parse/ 子目录
  ├─ [命令D] WGS→Mars 坐标转换（convert_ie 二进制）
  │         ├─ ref.txt → ref_02.txt（GCJ-02）
  │         └─ ref.txt → ref_84.txt（WGS84，Python实现）
  └─ 写入 .ref_type 标记文件
```

**关键设计**：

- **多数据集配置**：支持 TOML 中 `[[datasets]]` 配置段，为每个 dataset 设置独立的 `gnss_oem_type`、`vehicle_info_file`、`ref_type`
- **环境变量注入**：检测 `source_env.sh` 并通过 shell source 继承 Apollo 环境变量
- **配置备份与恢复**：每次执行前备份原始配置文件，执行后自动恢复
- **WGS84 参考数据生成**：当 `ref_type=wgs84` 时，Python 实现 `convert_ie_to_csv_wgs84()` 替代 C++ 二进制完成格式转换

#### 模块 B：`precision_head_topic_ref_100c_wdh_main.py`（精度评估统一入口）

**职责**：根据配置文件中的 `horizontal_only` 参数，路由到完整评估或水平精度专用评估。

**关键设计**：

```python
# 自动模式切换逻辑
if horizontal_only == 1:
    precision_head_topic_ref_100c_wdh_horizontal_only(...)  # 水平专用
else:
    precision_head_topic_ref_100c_wdh(...)  # 完整版（含高程）
```

#### 模块 C：`precision_head_topic_ref_100c_wdh.py`（完整评估）

**职责**：读取融合定位结果与参考真值，完成时间对齐、误差计算、统计输出。

**数据流**：

```
reffile (ref_02.txt/ref_84.txt)
      │
      ▼
┌─────────────┐
│ fileutils.  │  读取参考数据：列映射 [0,6,7,5,15,14,16,2,3,4,-1]
│ readfullcsv │  → time, lat, lon, height, ve, vn, vu, roll, pitch, yaw, quality
└─────────────┘
      │
      ▼ dpos2den（经纬度→ENU米）
┌─────────────┐
│   refdata   │  shape: (N, 11) ENU坐标系
└─────────────┘
      │
      ├──────────────────────────────┬──────────────────────┐
      ▼                              ▼                      ▼
┌─────────────┐              ┌─────────────┐      ┌─────────────┐
│  LC 数据    │              │  TC 数据    │      │  GNSS 数据  │
│ tcmsf_sol   │              │msf_debug   │      │  pvt.csv   │
│ .csv        │              │_state.csv   │      │            │
└─────────────┘              └─────────────┘      └─────────────┘
      │                              │                      │
      ▼                              ▼                      ▼
┌─────────────┐              ┌─────────────┐      ┌─────────────┐
│ readSensor  │              │readSensor   │      │ readfullcsv │
│ DataTcXkPk │              │TcXkPk /    │      │ + gnssindex │
│             │              │readmsf_    │      │ 列筛选      │
│             │              │debug_state │      │             │
└─────────────┘              └─────────────┘      └─────────────┘
      │                              │                      │
      ▼ dpos2den                    ▼ dpos2den           ▼ dpos2den
┌─────────────┐              ┌─────────────┐      ┌─────────────┐
│  lcs        │              │  tcs        │      │  gnss      │
│ (ENU, GPS T)│              │ (ENU, GPS T)│      │ (ENU, GPS T)│
└─────────────┘              └─────────────┘      └─────────────┘
      │                              │                      │
      ▼ alignDataByTimeTcSol       ▼ alignDataByTimeTcSol ▼ alignDataByTimeTcSol
┌─────────────┐              ┌─────────────┐      ┌─────────────┐
│ diff_datalc │              │ diff_datatc │      │diff_datagnss│
│ (GPS T)     │              │ (GPS T)     │      │ (GPS T)    │
└─────────────┘              └─────────────┘      └─────────────┘
      │                              │                      │
      └──────────┬──────────────────┴──────────────────────┘
                 ▼
        ┌────────────────┐
        │ calculate_errors │  航向角投影 → 横向/前进方向分解
        │  (dlat,dlon,dalt)│
        └────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐
│横向误差 │  │前进误差 │  │高程误差 │
│Lateral │  │Forward │  │Vertical│
└────────┘  └────────┘  └────────┘
    │            │            │
    └─────┬──────┴────────────┘
          ▼
   ┌──────────────────┐
   │  outpre_new()     │  RMS / CEP95 / CEP99 / Max / Odom
   └──────────────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
统计TXT文件   误差曲线图PNG
```

#### 模块 D：`commons/utils.py`（数学与数据处理核心）

包含四个核心函数：

| 函数 | 功能 | 算法/原理 |
|------|------|---------|
| `dpos2den()` | 经纬度 → ENU 局部坐标系 | $x = (lat - lat_0) \cdot \frac{\pi}{180} \cdot 6378137$，$y = (lon - lon_0) \cdot \frac{\pi}{180} \cdot 6378137 \cdot \cos(lat_0 \cdot \frac{\pi}{180})$ |
| `alignDataByTimeTcSol()` | 按 GPS 时间对齐两数据集 | 时间容差化整 → 交集查找 → 索引映射 |
| `calculateDifference()` | 两数据集对应元素相减 | 行对行差值，角度列特殊处理（wrap to [-180, 180]°） |
| `InterpState()` | 线性插值重采样 | `scipy.interp1d`，支持时间非单调、数据外推 |

#### 模块 E：`commons/calculate_errors.py`（误差分解）

**关键算法**：利用航向角将 ENU 误差向量投影到车辆坐标系：

```
在 ENU 坐标系中：
  dlat = 北向误差（y 轴分量）
  dlon = 东向误差（x 轴分量）
  dalt = 高程误差

航向角定义：北偏西为正（逆时针，正值范围 -180° 到 180°）

前进方向误差 = -dlon * sin(heading) + dlat * cos(heading)
横向误差     = dlon * cos(heading) + dlat * sin(heading)
水平误差     = sqrt(dlat² + dlon²)  （不依赖航向角）
高程误差     = dalt
```

**关键函数** `find_discontinuous_indices()`：处理 heading 和 diff_data 之间可能存在的不连续索引映射问题（车辆特殊场景下时间可能跳跃）。

#### 模块 F：`commons/outpre_new.py`（统计输出）

**核心职责**：将误差数据转换为可读的统计指标，写入 TXT 文件或返回统计字典。

**统计指标计算**：

| 指标 | 计算方法 |
|------|---------|
| **RMS** | $\sqrt{\frac{1}{N}\sum_{i=1}^{N}e_i^2}$ |
| **CEP** | 排序后 50% 分位数（Python 0基索引：`sorted[int(ceil(0.5*N))-1]`） |
| **CEP95** | 排序后 95% 分位数 |
| **CEP99** | 排序后 99% 分位数 |
| **Max** | 最大误差值 |
| **Odom** | 累积3D位移：$\sum_{i=1}^{N-1}\sqrt{(x_{i+1}-x_i)^2 + (y_{i+1}-y_i)^2 + (z_{i+1}-z_i)^2}$ |

#### 模块 G：`commons/evaluation_utils.py`（评估工具公共函数）

| 函数 | 功能 |
|------|------|
| `load_config_from_toml()` | 解析 TOML 配置文件 |
| `process_sensor_data()` | 读取 LC/TC 数据、执行坐标转换、时间对齐、差值计算的统一封装 |
| `calculate_normal_scene_time_ranges()` | 从总时间范围中减去特殊场景（隧道等）得到正常场景时间 |
| `calculate_horizontal_velocity_stats()` | 计算水平速度误差统计（RMS/CEP 分位数） |
| `save_horizontal_velocity_stats()` | 将速度统计写入 TXT 文件 |

#### 模块 H：`aggregate_precision_statistics.py`（多数据集聚合）

**职责**：递归扫描多个精度统计文件，按场景类型分类，按里程加权平均聚合。

**核心算法**：

```
输入：多个数据集的统计文件（每个文件含多个场景）
处理：
  1. 解析每个文件的 LC/TC/GNSS 统计数据
  2. 按场景类型分组（Highway, Urban Canyon, Tunnel 等）
  3. 对每个指标按里程占比加权平均
     aggregated[metric] = Σ(odom_i × metric_i) / Σ(odom_i)
  4. 全0场景不参与聚合
输出：统一的聚合统计文件 + tar.gz 压缩包
```

#### 模块 I：可视化模块（`plot_errors.py`）

**输出内容**：

- **带 GNSS 误差图**（`error_analysis_*_with_gnss.png`）：4行子图，水平/横向/前进/高程误差曲线
- **不带 GNSS 误差图**（`error_analysis_*_without_gnss.png`）
- **极值详细子图**（`details/detail_subplot_*.png`）：当 All 场景中某时刻误差超过阈值时自动触发，绘制该时刻前后 ±N 秒的放大窗口
- **GNSS Clip 子图**（`clip/clip_subplot_*.png`）：误差超标段落的连续绘图

---

## 4. 技术规格

### 4.1 依赖环境

| 维度 | 内容 |
|------|------|
| **Python 版本** | Python 3.7+（已测试 3.9, 3.10, 3.13） |
| **核心依赖** | numpy >= 1.21.0, pandas >= 1.3.0, matplotlib >= 3.4.0, scipy >= 1.7.0, toml >= 0.10.2 |
| **操作系统** | Linux（Ubuntu/CentOS）、macOS（测试通过）、WSL2（已验证） |
| **前置二进制** | TCMSF（bazel 编译）、PARSER（topic 解析）、convert_ie（WGS84→GCJ-02） |
| **Apollo 环境** | 可能需要 `source source_env.sh` 加载环境变量 |
| **硬件要求** | 无特殊要求，评估计算密集度低，主要为 I/O 操作 |

### 4.2 输入输出

#### 4.2.1 数据格式

| 数据类型 | 文件格式 | 关键列 |
|---------|---------|--------|
| **参考真值** | IE格式文本 或 CSV（WGS84/GCJ-02） | time, lat, lon, height, ve, vn, vu, roll, pitch, yaw, quality |
| **LC 结果** | CSV（TCMSF 输出） | GPS周内秒 + 位置/速度/姿态/状态 |
| **TC 结果** | CSV（MSF Debug State） | 同上，但为平滑后结果 |
| **GNSS PVT** | CSV（Parser 输出） | Unix时间戳, GPS周内秒, 经纬度, 高程, 速度, std等 |
| **配置** | TOML | 分段配置：data, plot, evaluation, time_ranges 等 |

#### 4.2.2 输出文件

| 文件类型 | 命名 | 位置 |
|---------|------|------|
| 精度统计 | `position_precision.txt` / `precison_statistics_all_types_*.txt` | results/dataset/ |
| 速度统计 | `velocity_precision.txt` / `horizontal_velocity_precision.txt` | results/dataset/ |
| 误差曲线图 | `error_analysis_type_*.png` | results/dataset/ |
| 极值子图 | `detail_subplot_*.png` | results/dataset/details/ |
| Clip 图 | `clip_subplot_*.png` + `gnss_clip_raw_data.csv` | results/dataset/clip/ |
| TCMSF 结果 | `{pvtlc/rtklc/...}_{tcmsf_ver}/` | 各子数据集目录 |
| GNSS 解析 | `topic_parse/` | 各子数据集目录 |

### 4.3 关键参数配置

以下为核心 TOML 配置文件的参数说明：

```yaml
# ─────────────────────── 数据源配置 ───────────────────────
[data]
basefold           # 基础数据目录（TCMSF输出路径）
reffile           # 参考真值文件路径（ref_02.txt 或 ref_84.txt）
lcver             # LC 结果文件夹名（如 "pvtlc_vcpb"）
tcver             # TC 结果文件夹名（如 "rtktc_vcpb"）
dataset           # 数据集子目录名称
dt                # 时间偏移量（秒），用于处理录制时间差

# GNSS 路径配置
gnss_subdir       # GNSS 数据子目录（默认: "topic_parse"）
gnss_filename    # GNSS 数据文件名（默认: "pvt.csv"）
gnss_pos_index_1 # GNSS 经度列索引（填充 gnssindex[7]）
gnss_pos_index_2 # GNSS 纬度列索引（填充 gnssindex[8]）
gnss_pos_index_3 # GNSS 高程列索引（填充 gnssindex[9]）

# ─────────────────────── 绘图开关 ───────────────────────
[plot]
plotlc            # 是否绘制 LC 误差曲线（默认: True）
plottc            # 是否绘制 TC 误差曲线（默认: False）
plotgnssstat     # 是否绘制 GNSS 误差曲线（默认: True）

# ─────────────────────── 评估参数 ───────────────────────
[evaluation]
tthreshod        # 时间对齐容差（秒，默认: 5e-3，即 5ms）
horizontal_only   # 水平精度专用模式 0=完整 1=仅水平（默认: 0）

# ─────────────────────── 极值子图参数 ───────────────────────
[detail_plot]
horizontal_error_threshold_meters  # 水平误差触发阈值（默认: 10.0m）
vertical_error_threshold_meters   # 高程误差触发阈值（默认: 15.0m）
detail_window_seconds             # 极值子图时间窗口（默认: 25.0s）

# ─────────────────────── Clip 处理参数 ───────────────────────
[clip_plot]
saveclip          # 是否保存 clip 数据（1=启用，0=禁用）
horizontal_error_threshold_meters # clip 水平误差阈值
clip_plot_interval_seconds       # clip 子图间隔（默认: 50.0s）

# ─────────────────────── 场景配置 ───────────────────────
[time_ranges.type_config]
# 多个 type_config 块，每个定义一个场景
type_label        # 场景名称（如 "开阔场景"、"隧道"）
type_time_range   # 时间范围列表 [[start1, end1], [start2, end2]]
                  # -1 表示使用数据的实际起点/终点
```

---

## 5. 快速开始指南

### 5.1 安装

```bash
# 克隆或解压到目标目录
cd /path/to/automated_evaluation_pys

# 安装 Python 依赖
pip install -r requirements.txt

# 安装为可执行包（可选）
pip install -e .
```

### 5.2 阶段一：数据预处理

```bash
# 编辑配置文件
vim batch_run_tcmsf_config_non_apollo.toml

# 执行 TCMSF 批量处理
python pvt_rtk_lc_evaluation/batch_run_tcmsf.py \
    batch_run_tcmsf_config_non_apollo.toml \
    /path/to/input_data

# 或使用打包后的入口点
python -m pvt_rtk_lc_evaluation.batch_run_tcmsf \
    batch_run_tcmsf_config_non_apollo.toml
```

### 5.3 阶段二：精度评估

```bash
# 方法一：使用已生成的配置文件（由 batch_run_precision_head_horizontal.py 自动生成）
python pvt_rtk_lc_evaluation/precision_head_topic_ref_100c_wdh_main.py \
    /path/to/dataset/precision_head_topic_ref_100c_wdh_config.toml

# 方法二：批量自动运行
python pvt_rtk_lc_evaluation/batch_run_precision_head_horizontal.py \
    /path/to/tcmsf_output_dir \
    /path/to/original_data_dir

# 方法三：完整评估（包含高程）
python pvt_rtk_lc_evaluation/precision_head_topic_ref_100c_wdh.py \
    precision_head_topic_ref_100c_wdh_config.toml
```

### 5.4 阶段三：多数据集聚合

```bash
# 聚合多数据集统计结果
python pvt_rtk_lc_evaluation/aggregate_precision_statistics.py \
    --config aggregate_precision_statistics_config.toml

# 或仅用命令行参数
python pvt_rtk_lc_evaluation/aggregate_precision_statistics.py \
    --input-dir /path/to/all_results \
    --output-file aggregated_precision.txt \
    --velocity-output-file aggregated_velocity.txt \
    --verbose
```

---

## 6. 参数配置指南

### 6.1 batch_run_tcmsf.py 核心参数

```yaml
# 路径配置
tcmsf_bin          # TCMSF 可执行文件绝对路径
record_parser_bin  # PARSER 可执行文件路径
convert_bin        # convert_ie 可执行文件路径（WGS→Mars）
config_file        # TCMSF 配置文件（.toml）
tcmsf_ver          # 版本标识（用于输出目录命名）
output_base_dir   # 输出基础目录

# 数据集配置
gnss_oem_type      # GNSS OEM 型号（LG695P 等）
vehicle_info_file  # 车辆参数配置文件路径

# 执行控制
fusion_modes       # 融合模式列表 [0, 2, 3]
                   # 0=PVTL C, 1=PVTTC, 2=RTKLC, 3=RTKTC
skip_dirs          # 跳过目录列表（如输出目录、临时目录）
config_backup      # 是否备份配置文件（默认: True）
verbose            # 详细输出（默认: False）

# 坐标参考
reffold            # 参考文件目录（可选，留空则搜索 dataset 目录）
datasets           # 多数据集配置数组（每个含独立参数）
```

### 6.2 精度评估核心参数

```yaml
# 时间阈值：决定哪些时刻被认为"同时"
tthreshod = 5e-3     # 5ms 容差，超过此间隔的数据点视为不同步
tthreshod = 1e-3     # 1ms 高精度（默认）

# 坐标参考选择逻辑
# lcver/tcver 包含 "pvt" → 使用 WGS84 参考（ref_84.txt）
# lcver/tcver 不含 "pvt" → 使用 GCJ-02 参考（ref_02.txt）

# 正常场景排除
normal_scene_exclusions:
  lc_tc_exclude = ["隧道"]      # LC/TC 正常场景排除的场景
  gnss_exclude = ["隧道", "转发器"]  # GNSS 正常场景排除的场景
```

### 6.3 调优建议

| 参数 | 建议值 | 说明 |
|------|-------|------|
| `tthreshod` | 1e-3 ~ 5e-3 | GPS 数据通常 1-5ms 采样，过小可能漏对齐，过大引入噪声 |
| `gnss_pos_index_*` | 根据 Parser 输出文件列号调整 | 解析失败时检查 pvt.csv 列数是否与索引匹配 |
| `detail_window_seconds` | 20~30s | 极值子图窗口，太小看不清上下文，太大丢失细节 |
| `horizontal_only` | 1 | 工业评估推荐水平专用模式，减少高程噪声干扰 |

---

## 7. 常见问题与解决方案

### Q1: TCMSF 执行失败，报错 "配置文件不存在"

**原因**：相对路径的配置文件未基于项目根目录解析。

**解决**：
```bash
# 确认 config_file 使用绝对路径，或确保从项目根目录执行
cd /path/to/apollo_project_root
python pvt_rtk_lc_evaluation/batch_run_tcmsf.py config.toml
```

### Q2: GNSS 数据读取失败，列索引越界

**原因**：`gnss_pos_index_1/2/3` 与 Parser 输出的 CSV 列号不匹配。

**解决**：
```bash
# 先检查 pvt.csv 的列数和内容
head -n 2 /path/to/topic_parse/pvt.csv
# 根据实际列号修改配置文件
# gnss_pos_index_1 = 12  # 经度
# gnss_pos_index_2 = 13  # 纬度
# gnss_pos_index_3 = 4   # 高程
```

### Q3: 时间对齐后数据点数为 0

**原因**：
1. `tthreshod` 过小，GPS 时间戳无法匹配
2. 参考数据和 LC/TC 数据时间范围无交集
3. `dt` 时间偏移量不正确

**解决**：
```python
# 临时增大容差测试
tthreshod = 1.0  # 1秒容差

# 或检查时间范围是否重叠
# 参考数据：GPS 周内秒
# GNSS 数据：Unix 时间戳 或 GPS 周内秒（需确认 pvt.csv 首列格式）
```

### Q4: 坐标转换后误差异常大（>100m）

**原因**：参考坐标系与输出坐标系不匹配。

**解决**：
```bash
# 检查 ref_type 标记文件
cat /path/to/dataset/.ref_type
# 应为 "gcj02" 或 "wgs84"

# 确认 TCMSF 输出的坐标系：
# PVTL C / RTKLC → GCJ-02（需用 ref_02.txt）
# PVT 纯定位 → WGS84（需用 ref_84.txt）
```

### Q5: 批量处理中部分数据集失败后整体停止

**原因**：`process_single_dataset()` 遇到异常后继续下一个，但 `run_all()` 严格模式会中断。

**解决**：
```bash
# 使用 try-except 包装，在异常数据集处跳过继续
# 或检查日志中的失败原因，针对性修复后重新运行
cat batch_run_logs_*/failed_dataset_name_error.log
```

### Q6: matplotlib 绘图内存溢出

**原因**：大数据集（>10000 点）绘制 PNG 时 DPI=300 内存占用过高。

**解决**：
```python
# 在 plot_errors.py 中临时降低 DPI
fig.savefig(save_path, dpi=100, bbox_inches='tight')  # 改为 100 DPI
```

### Q7: `source_env.sh` 环境变量加载失败

**原因**：非 Apollo bazel-bin 路径时，脚本检测到 `source_env.sh` 但执行失败。

**解决**：
```bash
# 手动 source 后再运行
source /path/to/tcmsf_offline/source_env.sh
python batch_run_tcmsf.py config.toml
```

---

## 8. 项目结构

```
automated_evaluation_pys/
├── pvt_rtk_lc_evaluation/           # Python 包（setuptools）
│   ├── __init__.py                   # __version__ = '1.0.0'
│   │
│   │   ### 阶段一：数据预处理 ###
│   ├── batch_run_tcmsf.py            # TCMSF 批量处理主类 BatchRunTcmsf
│   ├── batch_run_tcmsf_and_precision.py  # 联合流水线脚本
│   ├── batch_run_tcmsf_config_non_apollo.toml  # 示例配置
│   │
│   │   ### 阶段二：精度评估 ###
│   ├── precision_head_topic_ref_100c_wdh_main.py  # 统一入口（自动路由）
│   ├── precision_head_topic_ref_100c_wdh.py       # 完整评估（含高程 V）
│   ├── precision_head_topic_ref_100c_wdh_horizontal_only.py  # 水平专用
│   ├── precision_head_topic_ref_100c_wdh_config.toml        # 评估配置示例
│   ├── precision_head_topic_ref_100c_wdh_README.md
│   ├── precision_head_topic_ref_100c_wdh_USAGE.md
│   ├── compare_tc_lc_ref_100c_wdh.toml       # 对比配置
│   ├── precision_head_topic_ref_100c_wdh_horizontal_only.py
│   │
│   │   ### 阶段三：聚合统计 ###
│   ├── aggregate_precision_statistics.py         # 多数据集聚合类 AggregateRunner
│   ├── aggregate_precision_statistics_README.md
│   ├── aggregate_precision_statistics_USAGE.md
│   ├── aggregate_precision_statistics_config.toml
│   │
│   │   ### 其他工具 ###
│   ├── batch_run_precision_head_horizontal.py   # 批量精度评估流水线
│   ├── batch_run_precision_head_horizontal_with_config.py
│   ├── batch_run_tcmsf.py
│   ├── convert_ref.py                        # 参考数据格式转换
│   └── data/tmp/                             # 临时配置存放
│
├── commons/                          # 公共工具库（utils）
│   ├── __init__.py
│   │
│   │   ### 数据读取 ###
│   ├── fileutils.py                  # readfullcsv（通用 CSV，含空格/逗号分隔自适应）
│   ├── readSensorData.py             # 通用传感器数据读取
│   ├── readSensorDataTcXkPk.py      # TCMSF 融合结果读取
│   ├── readSensorDataTcSol.py        # TC Solution 数据读取
│   ├── readmsf_debug_state.py        # MSF 调试状态读取
│   ├── readgnsscsv.py               # GNSS CSV 读取
│   ├── readgnsstopic.py             # GNSS topic 读取
│   ├── read_rts_file.py             # RTS 平滑文件读取
│   ├── read_gps_data_wdh.py         # GPS 数据读取（WDH 变体）
│   ├── read_gnss_cnoa.py            # GNSS CNoA 读取
│   ├── skipCommentLines.py          # 跳过注释行
│   │
│   │   ### 数学与数据处理 ###
│   ├── utils.py                     # 核心工具：dpos2den, alignDataByTimeTcSol,
│   │                               #           calculateDifference, InterpState
│   ├── calculate_errors.py           # 误差分解：horizontal/lateral/forward/vertical
│   ├── calculate_cep.py             # CEP 分位数计算
│   ├── calculate_odometry.py        # 3D 累积里程计算
│   ├── tr2rpy.py                   # 旋转向量转 Roll-Pitch-Yaw
│   ├── globalvariation.py           # 全局变量定义
│   ├── getParentDirectory.py        # 获取父目录路径
│   │
│   │   ### 统计与输出 ###
│   ├── outpre_new.py                # 精度统计输出（核心，含 RMS/CEP/Max/Odom）
│   ├── evaluation_utils.py          # 评估公共函数（配置加载、数据处理、速度统计）
│   ├── StatsComparisonAll.py        # 统计全局对比
│   ├── blockAverage_loop.py        # 数据块平均
│   │
│   │   ### 可视化 ###
│   ├── plot_errors.py              # 误差曲线（4行子图，含/不含 GNSS 两张图）
│   ├── plot_skyview.py            # 天空视图
│   ├── skyplot.py                 # 天空图
│   ├── plotgnsscsv.py             # GNSS CSV 绘图
│   ├── plot_precision_comparison.py  # 精度对比绘图
│   ├── plot_precision_errors.py      # 精度误差绘图
│   ├── plot_stats_comparison.py     # 统计对比绘图
│   ├── plotStatsComparisonaAll.py  # 全量统计绘图
│   ├── plot_rms_results.py          # RMS 结果绘图
│   ├── kf_performance_comparison.py  # KF 性能对比
│   ├── kf_performance_comparison.png  # 预生成图片
│   │
│   │   ### 对比分析 ###
│   ├── compare_tc_gnsstopic.py     # TC vs GNSS Topic 对比
│   ├── compare_lc_gnsstopic.py   # LC vs GNSS Topic 对比
│   ├── compare_tc_lc.py           # TC vs LC 对比
│   ├── compare_tc_lc_mul.py        # TC vs LC 多版本对比
│   ├── compare_tc_lc_ref_100c.py  # TC/LC vs 100c 参考对比
│   ├── compare_tc_lc_ref_rts.py   # TC/LC vs RTS 参考对比
│   ├── compare_2tc_lc_ref_100c_wdh.py  # WDH 变体
│   ├── compare_2tc_lc_ref_rts.py  # TC vs RTS 参考对比
│   ├── compare_pre_xp_ref_rts.py  # 前向预测 vs RTS 参考
│   ├── compare_2msfstate.py       # 两 MSF 状态对比
│   ├── compareDH_Dalt.py          # DH vs Dalt 对比
│   ├── compareTCHisStatistics.py   # TC 历史统计对比
│   ├── cmp2tcstats.py             # TC 统计对比
│   ├── two_version_cmp.py         # 两版本对比
│   ├── two_version_cmp_bias_esti_state.py  # 两版本偏差估计对比
│   ├── att_diff_adjust.py         # 姿态差异调整
│   │
│   │   ### BPPAPS 算法 ###
│   ├── bppaps.py                  # BPPAPS 算法（基准）
│   ├── bppaps_huiguan.py          # BPPAPS（汇管专用）
│   ├── bppaps_msfdebg_rts.py      # BPPAPS + MSF Debug + RTS
│   ├── bppaps_msfdebg_rts_enhanced.py  # BPPAPS 增强版
│   ├── debug_bppaps.py            # BPPAPS 调试脚本
│   │
│   │   ### 3D 精度分析 ###
│   ├── precision_tc_lc_ref_100c.py        # 3D 精度：TC/LC vs 100c 参考
│   ├── precision3d_tc_lc_ref_100c_.py     # 3D 精度（变体）
│   ├── precision3d_rts_ref_100c.py        # 3D 精度：TC/LC vs RTS 参考
│   ├── precision3d_2rts_ref_100c.py        # 3D 精度 vs 100c 双 RTS
│   ├── precision3d_2tc_lc_ref_100c.py      # 3D 精度 vs 100c 双 TC/LC
│   ├── precision3d_tc_lc_ref_100c__py  # [重名]
│   ├── precision_tc_lc_ref_100c.py        # 同上别名
│   │
│   │   ### 辅助工具 ###
│   ├── load100ccsv.py             # 加载 100c CSV
│   ├── simple_debug.py            # 简单调试脚本
│   ├── debug_rms_format.py       # RMS 格式调试
│   ├── conversion_status.py       # 转换状态工具
│   ├── sel_gnss_out.py           # GNSS 输出筛选
│   ├── convert_span_stdref_to_ref.py  # SPAN → 标准参考格式转换
│   ├── test_alignDataByTimeTcSol.py  # alignDataByTimeTcSol 测试
│   ├── test_plotStatsComparisonaAll.py  # 绘图测试
│   └── data_compression_archive.py  # 数据压缩打包
│
│   ### 文档 ###
│   ├── CONVERSION_SUMMARY.md     # MATLAB→Python 转换总结
│   ├── README.md                 # 通用 README
│   ├── README_batch_run.md       # 批量运行说明
│   └── README_batch_run_tcmsf.md  # TCMSF 批量运行说明
│   └── README_time_ranges.md     # 时间范围配置说明
│
│   ### 构建与依赖 ###
├── setup.py                      # setuptools 打包配置
├── requirements.txt              # pip 依赖声明
│
│   ### Shell 脚本 ###
├── repackage.sh                  # 打包脚本（Python 3.9）
├── repackage_python310.sh        # 打包脚本（Python 3.10）
├── py_changed_upload.sh          # Py 变更上传脚本
│
│   ### 配置示例 ###
├── 20260324_hc25_pvt1_nc.toml   # 实际使用的配置文件示例
│
└── data_compression_archive.py   # 数据压缩归档工具
```

---

## 9. 相关项目

| 项目 | 描述 | 与本项目关联 |
|------|------|------------|
| **Apollo Localization** | 百度 Apollo 自动驾驶定位模块，TCMSF 的宿主项目 | TCMSF 融合算法源自 Apollo，是本工具的输入数据来源 |
| **RTK-LC-PVT Evaluation** | PVT/RTK/LC 多源融合定位精度评估方法论 | 本项目的业务背景和技术目标 |
| **MATLAB Navigation Toolbox** | MATLAB 导航定位工具箱（原始实现参考） | 本项目从 MATLAB 迁移而来，算法一一对应 |
| **Google Cartographer** | 开源 SLAM 定位系统 | 类比：同为自动驾驶定位工具，但技术路线不同（视觉+激光 vs  GNSS+IMU） |
| **Kalman Filter Toolbox** | 多源传感器融合 Kalman 滤波工具 | 本项目 TC/LC 中的状态估计核心依赖 |

---

## 10. 引用格式

本项目为内部工程工具，无学术论文引用。如需引用，建议注明内部代码仓库：

```bibtex
@software{automated_evaluation_pys,
  title = {PVT RTK LC Precision Evaluation Toolkit},
  author = {BYD ADAS Team},
  year = {2025},
  url = {internal_repository_path},
  version = {1.0.0}
}
```

---

## 附录 A：数据列索引速查表

### A.1 参考数据列映射（`fileutils.readfullcsv`）

```
索引  │ 含义           │ 说明
─────┼──────────────┼────────────────────────────
0    │ time          │ GPS 周内秒
1    │ lat           │ 纬度（deg）
2    │ lon           │ 经度（deg）
3    │ height        │ 高程（m）
4    │ ve            │ 东向速度（m/s）
5    │ vn            │ 北向速度（m/s）
6    │ vu            │ 垂向速度（m/s）
7    │ roll          │ 横滚角（deg）
8    │ pitch         │ 俯仰角（deg）
9    │ yaw           │ 航向角（deg）
10   │ quality       │ 质量标志
```

### A.2 GNSS PVT 列映射（`gnssindex`）

```
gnssindex = [1, -1, -1, 8, 5, 6, 7,
             gnss_pos_index_1,  # 经度
             gnss_pos_index_2,  # 纬度
             gnss_pos_index_3,  # 高程
             10]               # 质量

extindex = [14, 15, 16, 9, 10]
# 14=std_x, 15=std_y, 16=std_z, 9=sat_num, 10=status
```

### A.3 差值数据列含义（`diff_data` 输出格式）

```
索引  │ 含义（对齐后参考-结果）  │ 说明
─────┼────────────────────┼────────────────────
0     │ time                │ GPS 周内秒（对齐后）
1-3   │ droll, dpitch, dyaw │ 姿态角差值
4     │ dve                 │ 东向速度差值
5     │ dvn                 │ 北向速度差值
6     │ dvu                 │ 垂向速度差值
7     │ dlat                │ 纬度差值（m，ENU）
8     │ dlon                │ 经度差值（m，ENU）
9     │ dalt                │ 高程差值（m）
```

---

## 附录 B：fusion_mode 速查

| fusion_mode | 含义 | 输出坐标系 |
|-------------|------|----------|
| 0 | **PVTL C** — PVT + Loose Coupling | GCJ-02 |
| 1 | **PVTTC** — PVT + Tight Coupling | GCJ-02 |
| 2 | **RTKLC** — RTK + Loose Coupling | GCJ-02 |
| 3 | **RTKTC** — RTK + Tight Coupling | GCJ-02 |

> 注：PVTL C/PVTTC/RTKLC/RTKTC 模式的输出均为 GCJ-02（国测局坐标系）坐标，需与对应坐标系的参考数据进行比较。

---

## 附录 C：进阶要求 —— 函数调用关系与执行流程详解

### C.1 完整系统函数调用总览

本工具链由三个主要入口脚本驱动，各自主导一个处理阶段。以下按执行顺序展示顶层调用架构：

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     automated_evaluation_pys                              │
│                        完整流水线函数调用总览                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  【阶段一】batch_run_tcmsf.py                                           │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ main()                                                             │    │
│  │ 【解析命令行参数，读取 TOML 配置文件，创建 BatchRunTcmsf 实例】       │    │
│  │       │                                                          │    │
│  │       ├──► BatchRunTcmsf.__init__(config_file, input_path_override)  │
│  │       │   【加载配置、查找项目根目录、初始化二进制路径】               │
│  │       │       │                                                   │
│  │       │       ├──► _source_environment_variables()                 │
│  │       │       │   【source 环境变量文件，加载 Apollo 环境】          │
│  │       │       └──► is_apollo_bin(bin_path)                        │
│  │       │           【判断是否为 Apollo bazel-bin 路径】              │
│  │       │                                                           │
│  │       └──► run_all()                                              │
│  │           【根据 datasets 配置决定分支】                              │
│  │               │                                                     │
│  │               ├─ [有 datasets] 两层循环                             │
│  │               │     对每个 dataset → 子数据集调用 process_single_dataset()
│  │               │                                                           │
│  │               └─ [无 datasets] 单层循环                             │
│  │                     对每个子目录调用 process_single_dataset()            │
│  │                                                                           │
│  │           process_single_dataset(dataset_path, subdatasets_name)            │
│  │           【单数据集处理主流程】                                         │
│  │               │                                                         │
│  │               ├──► get_dataset_config(parent_dataset_name)              │
│  │               │   【从 datasets 配置中查找 gnss_oem_type, vehicle_info】 │
│  │               │                                                           │
│  │               │   ┌─── fusion_modes 循环（e.g. [0, 2, 3]） ───┐      │
│  │               │   │                                                   │
│  │               │   ├──► modify_config_file(initial_modifications, ...) │
│  │               │   │   【写入 gnss_oem_type, vehicle_info, gnss_fusion_mode】│
│  │               │   │       │                                           │
│  │               │   │       └──► re.sub()  # 正则替换 TOML 配置项        │
│  │               │   │                                                           │
│  │               │   ├──► run_tcmsf(dataset_path)                          │
│  │               │   │   【执行 TCMSF 二进制，生成 data/tmp 输出】         │
│  │               │   │       └──► run_command(command, cwd=tcmsf_working_dir)│
│  │               │   │           【source env + 执行二进制】               │
│  │               │   │                                                           │
│  │               │   ├──► copy_results(dataset_path, fusion_mode, ...)     │
│  │               │   │   【复制 data/tmp → {fusion_type}_{tcmsf_ver}/】   │
│  │               │   │       └──► shutil.copytree()                        │
│  │               │   │                                                           │
│  │               │   └──► modify_config_file({gnss_fusion_mode})          │
│  │               │       【为下一个 fusion_mode 修改配置】                   │
│  │               │                                                           │
│  │               ├──► restore_config_file()                                │
│  │               │   【恢复原始配置文件】                                    │
│  │               │                                                           │
│  │               ├──► run_topic_parse(dataset_path, ...)                    │
│  │               │   【执行 PARSER 二进制，生成 topic_parse/】              │
│  │               │       └──► run_command(PARSER, cwd=bin_working_dir)    │
│  │               │                                                           │
│  │               └──► run_wgs_to_mars(dataset_path, ref_type)              │
│  │                   【WGS84 → GCJ-02 坐标转换】                           │
│  │                       │                                                   │
│  │                       ├──► convert_ie_to_csv_wgs84() [仅 ref_type='wgs84']│
│  │                       │   【Python 实现：IE格式 → CSV WGS84】              │
│  │                       │       └──► 文件解析 + 字段提取 + CSV 写入         │
│  │                       │                                                       │
│  │                       └──► run_command(convert_ie, cwd=bin_working_dir)  │
│  │                           【执行 C++ 二进制：WGS84 → GCJ-02】            │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  【阶段二】precision_head_topic_ref_100c_wdh_main.py                     │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ main()                                                             │    │
│  │ 【解析命令行参数，加载 TOML 配置文件】                                │    │
│  │       │                                                          │    │
│  │       ├──► load_config_from_toml(config_path)                      │
│  │       │   【evaluation_utils.py：toml.load()】                      │
│  │       │                                                           │
│  │       ├──► [horizontal_only == 1]                                  │
│  │       │     precision_head_topic_ref_100c_wdh_horizontal_only(...) │
│  │       │                                                           │
│  │       └──► [horizontal_only == 0]                                  │
│  │             precision_head_topic_ref_100c_wdh(...)                 │
│  │                                                                           │
│  │  precision_head_topic_ref_100c_wdh() / _horizontal_only()             │
│  │  【精度评估主函数】                                                     │
│  │      │                                                               │
│  │      ├──► fileutils.readfullcsv(reffile, [0,6,7,5,15,14,16,2,3,4,-1])  │
│  │      │   【读取参考数据 → refdata (N×11)】                            │
│  │      │       │                                                      │
│  │      │       └──► utils.dpos2den(refdata, pos0)                      │
│  │      │           【经纬度 → ENU 米坐标系（相对起始点）】               │
│  │      │                                                               │
│  │      ├──► [ref_filename.endswith('_84.txt')]                        │
│  │      │     尝试加载同目录的 *_02.txt 作为 GCJ-02 参考                  │
│  │      │                                                               │
│  │      ├──► process_sensor_data(lcpath, refdata_lc, ...)              │
│  │      │   【读取 LC 数据，执行坐标转换和时间对齐】                       │
│  │      │       │                                                      │
│  │      │       ├──► readSensorDataTcXkPk(filepath, dt)                 │
│  │      │       │   【commons/readSensorDataTcXkPk.py：CSV → numpy】   │
│  │      │       │       └──► csv.reader() + numpy.array()             │
│  │      │       │                                                      │
│  │      │       ├──► utils.dpos2den(data[:, 7:9], pos0)               │
│  │      │       │   【经纬度 → ENU 米】                                │
│  │      │       │                                                      │
│  │      │       └──► utils.alignDataByTimeTcSol() + calculateDifference() │
│  │      │           【时间对齐 + 差值计算 → diff_datalc】              │
│  │      │                                                               │
│  │      ├──► process_sensor_data(tcpath, refdata_tc, ...)              │
│  │      │   【读取 TC 数据（流程同上）】                                │
│  │      │                                                               │
│  │      ├──► fileutils.readfullcsv(gnsspath, gnssindex, extindex)     │
│  │      │   【读取 GNSS PVT 数据 → gnss (M×15)】                       │
│  │      │       │                                                      │
│  │      │       ├──► GNSS 时间映射建立                                  │
│  │      │       │   【Unix时间戳 ↔ GPS周内秒 映射字典】               │
│  │      │       └──► 状态筛选：gnss[:, -1] > 0                          │
│  │      │                                                               │
│  │      ├──► 对每个 time_ranges.type_config 循环：                      │
│  │      │     【多场景依次评估】                                         │
│  │      │       │                                                      │
│  │      │       ├──► outpre_new(...)                                  │
│  │      │       │   【计算并输出精度统计】                               │
│  │      │       │       │                                              │
│  │      │       │       ├──► calculate_errors(diff_datalc, yaw)          │
│  │      │       │       │   【commons/calculate_errors.py】            │
│  │      │       │       │       ├──► find_discontinuous_indices()        │
│  │      │       │       │       │   【查找 heading 与 diff_data 索引映射】 │
│  │      │       │       │       └──► 航向角投影计算                     │
│  │      │       │       │           【horizontal/lateral/forward/vertical 分解】│
│  │      │       │       │                                              │
│  │      │       │       ├──► calculate_cep(horizontal_error)            │
│  │      │       │       │   【commons/calculate_cep.py：CEP/RMS/Max 计算】│
│  │      │       │       │                                              │
│  │      │       │       ├──► calculate_odometry(lcs)                    │
│  │      │       │       │   【commons/calculate_odometry.py：累积3D位移】  │
│  │      │       │       │                                              │
│  │      │       │       └──► TXT 文件写入 / 统计字典返回                │
│  │      │       │                                                       │
│  │      │       └──► plot_errors(...)                                  │
│  │      │           【commons/plot_errors.py：误差曲线可视化】            │
│  │      │               │                                              │
│  │      │               └──► matplotlib 4行子图 + 保存 PNG              │
│  │      │                                                               │
│  │      ├──► [All 场景] plot_detail_subplots()                        │
│  │      │   【极值超阈值时自动绘制详细子图】                              │
│  │      │                                                               │
│  │      └──► [clip_plot 启用] save_and_plot_clips()                   │
│  │          【GNSS 误差超标段落的绘图与数据保存】                         │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  【阶段三】aggregate_precision_statistics.py                              │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ main()                                                             │    │
│  │ 【解析命令行参数，加载配置】                                          │    │
│  │       │                                                          │    │
│  │       ├──► find_all_precision_files(input_dir)                      │
│  │       │   【递归查找所有 precison_statistics_all_types_*.txt】       │
│  │       │       └──► os.walk() + 文件名匹配                         │
│  │       │                                                           │
│  │       ├──► parse_precision_file(filepath)                           │
│  │       │   【正则解析统计文件，提取 LC/TC/GNSS 各场景数据】           │
│  │       │       │                                                   │
│  │       │       └──► re.search() + re.match()  # 多版本号兼容       │
│  │       │                                                           │
│  │       ├──► aggregate_statistics(all_files_stats, ...)               │
│  │       │   【按场景类型分组，按里程加权平均】                          │
│  │       │       │                                                   │
│  │       │       └──► for scene_type: Σ(odom_i × metric_i) / Σ(odom_i)│
│  │       │                                                           │
│  │       ├──► format_output(aggregated_stats)                        │
│  │       │   【生成格式化 TXT 报告】                                   │
│  │       │                                                           │
│  │       └──► tarfile.open(archive_path, 'w:gz')                    │
│  │           【自动打包输入目录为 tar.gz】                              │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### C.2 各核心模块详细执行流程

#### C.2.1 `batch_run_tcmsf.py` → `BatchRunTcmsf` 类

```
BatchRunTcmsf.__init__(config_file, input_path_override)
【初始化批量执行器，加载配置并验证路径】
      │
      ├──► toml.load(config_file)
      │   【解析 TOML 配置】
      │
      ├──► Path.cwd() + 向上搜索 .bazelignore/WORKSPACE
      │   【定位 Apollo 项目根目录】
      │
      ├──► is_apollo_bin(tcmsf_bin)
      │   【判断是否使用 Apollo bazel-bin 路径】
      │   "bazel-bin" in bin_path → True/False
      │
      ├──► [_source_environment_variables()]
      │   【当 bin 路径不含 bazel-bin 时调用】
      │   source source_env.sh → subprocess.run(shell=True)
      │   解析 env 输出 → 更新 os.environ
      │
      └──► 项目根目录解析完毕，验证 input_path 存在
          mkdir output_base_dir

──────────────────────────────────────────────────────────

BatchRunTcmsf.process_single_dataset(dataset_path, subdatasets_name)
【处理单个数据集：执行 TCMSF → 复制结果 → 后处理】
      │
      ├──► get_dataset_config(parent_dataset_name)
      │   【根据父目录名在 datasets_config 中查找配置项】
      │   匹配 name 字段 → 返回 gnss_oem_type / vehicle_info_file / ref_type
      │
      ├──► [fusion_modes 循环: 0 → 2 → 3]
      │
      │   【第 1 次循环时】
      │   ├──► modify_config_file(initial_modifications, result_dir)
      │   │   【写入 gnss_oem_type 和 vehicle_info_override_file_path】
      │   │   正则替换 TOML 中的对应行
      │   │   同时写入 data/tmp/ 目录副本
      │   │   └──► shutil.copy2() 【备份到 result_dir】
      │   │
      │   【每次循环】
      │   ├──► modify_config_file({gnss_fusion_mode: str(fusion_mode)})
      │   │   【修改 gnss_fusion_mode 配置项】
      │   │
      │   ├──► run_tcmsf(dataset_path)
      │   │   【执行 TCMSF 二进制可执行文件】
      │   │   command = [TCMSF_binary, dataset_path, "tcmsf"]
      │   │   cwd = tcmsf_working_dir (tcmsf_offline/)
      │   │   └──► run_command(command, cwd=...)
      │   │       【含 source_env 时通过 shell 执行】
      │   │
      │   └──► copy_results(dataset_path, fusion_mode, subdatasets_name)
      │       【复制 data/tmp 目录到输出位置】
      │       目标: output_base_dir/dataset/{fusion_type}_{tcmsf_ver}/
      │       └──► shutil.copytree(source_dir, result_dir)
      │
      ├──► restore_config_file()
      │   【从 .bak 恢复原始 TCMSF 配置文件】
      │   └──► shutil.copy2(bak_path, config_path)
      │
      ├──► run_topic_parse(dataset_path, subdatasets_name)
      │   【执行 PARSER 二进制解析 GNSS topic 数据】
      │   command = [PARSER_binary, dataset_path, output_dir]
      │   输出到: output_base_dir/dataset/topic_parse/
      │
      └──► run_wgs_to_mars(dataset_path, ref_type)
          【坐标转换/格式转换】
              │
              ├──► [ref_type == 'wgs84']
              │   convert_ie_to_csv_wgs84(ref_file, ref_84_file)
              │   【Python 实现 IE→CSV 格式转换，保留 WGS84 原始坐标】
              │   查找 "(sec)    (weeks)" 标记行 → 提取 18 字段
              │
              └──► [ref_type == 'gcj02' 或 wgs84 均需生成]
              run_command(convert_ie, cwd=bin_working_dir)
              【C++ 二进制：WGS84 ref.txt → GCJ-02 ref_02.txt】

──────────────────────────────────────────────────────────

BatchRunTcmsf.run_command(command, description, cwd)
【统一命令执行封装】
      │
      ├──► [有 source_env_path]
      │   shell_cmd = f"source {env} && {' '.join(command)}"
      │   └──► subprocess.run(shell=True, executable='/bin/bash', cwd=cwd)
      │
      └──► [无 source_env_path]
          └──► subprocess.run(command, cwd=cwd, check=True)
```

#### C.2.2 `precision_head_topic_ref_100c_wdh.py` → `precision_head_topic_ref_100c_wdh()`

```
precision_head_topic_ref_100c_wdh(...)
【精度评估主函数：读取数据 → 对齐 → 误差分解 → 统计 → 可视化】
      │
      ├──► fileutils.readfullcsv(reffile, [0,6,7,5,15,14,16,2,3,4,-1])
      │   【读取参考真值数据：shape (N, 11)】
      │   列: time, lat, lon, height, ve, vn, vu, roll, pitch, yaw, quality
      │   ├──► csv.reader() 支持空格/逗号分隔自适应
      │   └──► numpy.array() 转换为数值数组
      │
      ├──► utils.dpos2den(refdata[:, 7:9], pos0)
      │   【经纬度 → ENU 局部米坐标系（以起点为原点）】
      │   d2r = π/180
      │   d2m_lat = d2r × 6378137
      │   d2m_lon = d2r × 6378137 × cos(lat0)
      │   x[m] = Δlat × d2m_lat
      │   y[m] = Δlon × d2m_lon
      │
      ├──► [ref_filename.endswith('_84.txt')]
      │   尝试加载同目录 *_02.txt → refdata_02
      │   判断 lcver/tcver 是否含 'pvt' → 决定使用哪套参考数据
      │
      ├──► process_sensor_data(lcpath, refdata_lc, pos0, tthreshod, statetype, dt, 'LC')
      │   【LC 数据处理流水线】
      │       │
      │       ├──► readSensorDataTcXkPk(lcpath, dt)  [statetype == 0]
      │       │   【CSV → numpy：GPS周内秒 - dt → 时间校正】
      │       │       └──► csv.reader() + numpy.array()
      │       │
      │       ├──► readmsf_debug_state(filepath, dt)  [statetype == 1]
      │       │   【MSF 调试状态读取 + 插值对齐到参考时间】
      │       │       └──► utils.InterpState()
      │       │
      │       ├──► utils.dpos2den(data[:, 7:9], pos0)
      │       │   【经纬度 → ENU 米】
      │       │
      │       └──► utils.alignDataByTimeTcSol() + calculateDifference()
      │           【时间对齐 + 差值计算 → diff_datalc】
      │
      ├──► process_sensor_data(tcpath, refdata_tc, ...)  [plottc]
      │   【TC 数据处理：流程同上，结果 → diff_datatc】
      │
      ├──► GNSS 数据读取 [plotgnssstat]
      │   ├──► fileutils.readfullcsv(gnsspath, [0, 1], [])
      │   │   【读取 Unix 时间戳列 + GPS 周内秒列】
      │   │   建立映射: gnss_time_mapping[GPS_week_sec] = unix_time
      │   │
      │   ├──► fileutils.readfullcsv(gnsspath, gnssindex, extindex)
      │   │   【gnssindex = [1,-1,-1,8,5,6,7,lon,lat,alt,10]
      │   │   extindex = [14,15,16,9,10] → std_x/y/z, sat_num, status
      │   │
      │   ├──► 航向角处理: gnss[:, 3] > 180 → -= 360
      │   │   【将经度从 [0,360] 转换到 [-180,180]】
      │   │
      │   ├──► 状态筛选: gnss[:, -1] > 0
      │   │   【只保留有效的 RTK 定位解】
      │   │
      │   ├──► utils.dpos2den(gnss[:, 7:9], pos0)
      │   │   【经纬度 → ENU 米】
      │   │
      │   └──► utils.alignDataByTimeTcSol() + calculateDifference()
      │       【时间对齐 + 差值计算 → diff_datagnss】
      │
      ├──► 提取航向角
      │   yaw = refdata[:, [0, 3]]
      │   yaw[:, 1] = -yaw[:, 1]
      │   【真北方位角 → 航向角（北偏西为正）】
      │
      ├──► [time_ranges.type_config 循环]
      │   对每个场景类型（All / 开阔场景 / 半遮挡 等）：
      │       │
      │       ├──► outpre_new(outfile_unified, diff_datalc, diff_datatc,
      │       │           diff_datagnss, lcs, tcs, gnss, yaw,
      │       │           t_start, t_end, type_label,
      │       │           append_mode=False, return_stats=True, ...)
      │       │   【精度统计计算 + 写入文件/返回字典】
      │       │       │
      │       │       ├──► calculate_errors(diff_datalc, yaw)
      │       │       │   【commons/calculate_errors.py】
      │       │       │   ├──► find_discontinuous_indices(heading, diff_data[:, 0])
      │       │       │   │   【处理 heading 与 diff_data 索引不连续问题】
      │       │       │   │   defaultdict + itertools.product 生成所有可能组合
      │       │       │   │
      │       │       │   ├──► heading_rad = np.deg2rad(heading[ind, 1])
      │       │       │   │
      │       │       │   └──► 误差投影到车辆坐标系:
      │       │       │       forward = -dlon·sin(heading) + dlat·cos(heading)
      │       │       │       lateral = dlon·cos(heading) + dlat·sin(heading)
      │       │       │       horizontal = sqrt(dlat² + dlon²)
      │       │       │       vertical = dalt
      │       │       │
      │       │       ├──► calculate_cep(horizontal_error)
      │       │       │   【commons/calculate_cep.py】
      │       │       │   对排序后的误差向量取 50/95/99 分位数
      │       │       │
      │       │       ├──► calculate_odometry(lcs)
      │       │       │   【commons/calculate_odometry.py】
      │       │       │   累积 3D 位移距离
      │       │       │
      │       │       └──► 文件写入 / 字典返回
      │       │           rms(horizontal_error) = sqrt(mean(error²))
      │       │           CEP95 = percentile(error, 95)
      │       │           Max = max(error)
      │       │
      │       └──► plot_errors(common_timelc, diff_datalc,
      │                       common_timetc, diff_datatc,
      │                       common_timegnss, diff_datagnss,
      │                       t0, save_path, yaw, t_start, t_end, ...)
      │           【commons/plot_errors.py】
      │               ├──► matplotlib.subplots(4, 1)  # 水平/横向/前进/高程
      │               ├──► 带 GNSS 版本 + 不带 GNSS 版本分别保存
      │               └──► fig.savefig(dpi=300, bbox_inches='tight')
      │
      ├──► [All 场景] plot_detail_subplots(...)
      │   【自动检测极值，绘制超阈值区间的详细子图】
      │       while True:
      │           找当前范围内最大误差点
      │           if max_error ≤ threshold: break
      │           绘制 ±detail_window 秒窗口
      │
      └──► [clip_plot.saveclip == 1] save_and_plot_clips(...)
          【GNSS 误差超标段落的连续绘图】
              识别连续超阈值数据段
              → 50s 间隔子图
              → 总览图 + 无 std 图
              → 原始数据 CSV 保存
```

#### C.2.3 `commons/utils.py` → 核心数学函数

```
dpos2den(data, pos0)
【经纬度 → ENU 局部米坐标，以 pos0 为原点】
      │
      ├──► d2r = π / 180
      ├──► d2m_lat = d2r × 6378137                    # 每度纬线弧长
      ├──► d2m_lon = d2r × 6378137 × cos(pos0[0]×d2r)  # 每度经线弧长
      │
      ├──► data[:, 0] = (lat - lat0) × d2m_lat          # 北向偏移（m）
      └──► data[:, 1] = (lon - lon0) × d2m_lon          # 东向偏移（m）
      【原地修改，data[:, 0]=北向(m), data[:, 1]=东向(m)】

──────────────────────────────────────────────────────────

alignDataByTimeTcSol(data1, time1, data2, time2, tol, x=1)
【按 GPS 时间对齐两个数据集，返回交集中的数据点】
      │
      ├──► temp_rounded_time1 = round(time1 / tol)
      ├──► temp_rounded_time2 = round(time2 / tol)
      │   【将时间按容差 tol 化整】
      │
      ├──► rounded_time1 = round(temp_rounded_time1 / x) × x
      ├──► rounded_time2 = round(temp_rounded_time2 / x) × x
      │   【按 x 的整数倍归化】
      │
      ├──► np.intersect1d(rounded_time1, rounded_time2, return_indices=True)
      │   【找到共同时间值及其在原数组中的索引】
      │
      └──► data1[idx1, :], data2[idx2, :], time1[idx1]
          【返回对齐后的两数据集 + 公共时间向量】

──────────────────────────────────────────────────────────

calculateDifference(data1, data2, radtag=0)
【计算两个行对行完全对齐的数据集的差值】
      │
      ├──► diff_data[:, 0] = data1[:, 0]           # 时间列不变
      ├──► diff_data[:, 1:] = data1[:, 1:] - data2[:, 1:]
      │   【位置、速度、姿态各列相减】
      │
      └──► [角度列特殊处理: 索引 1-3 → Roll/Pitch/Yaw]
          diff[:, i] = ((diff[:, i] + 180) % 360) - 180
          【将角度差值 wrap 到 [-180°, 180°]】

──────────────────────────────────────────────────────────

InterpState(state, t, t_ref)
【将 state 数据线性插值到 t_ref 时间点】
      │
      ├──► [时间非单调时] 排序后再处理
      │   sorted_indices = np.argsort(t)
      │
      ├──► 对每一列（姿态/速度/位置）：
      │   f = interp1d(t_sorted, state_sorted[:, i],
      │               kind='linear', bounds_error=False,
      │               fill_value='extrapolate')
      │   state_[:, i] = f(t_ref)
      │   【scipy 线性插值，支持数据范围外外推】
      │
      └──► return state_  # shape: (len(t_ref), num_cols)
```

#### C.2.4 `commons/calculate_errors.py` → `calculate_errors()`

```
calculate_errors(diff_data, heading)
【将 ENU 误差分解为横向/前进方向/高程误差】
      │
      ├──► dlat = diff_data[:, 7]   # 纬度误差（北向，m）
      ├──► dlon = diff_data[:, 8]   # 经度误差（东向，m）
      ├──► dalt = diff_data[:, 9]   # 高程误差（m）
      │   【注：ENU 坐标系下，dlat = 北向分量，dlon = 东向分量】
      │
      ├──► horizontal_error = sqrt(dlat² + dlon²)
      │   【水平面 2D 合成误差，与航向角无关】
      │
      ├──► find_discontinuous_indices(heading[:, 0], diff_data[:, 0])
      │   【处理 heading 和 diff_data 之间的时间不连续问题】
      │   defaultdict 建立 heading 时间→索引映射
      │   product 生成所有严格递增的索引组合
      │   ind = 第一个有效组合（航向角离散采样与误差数据点对应）
      │
      ├──► heading_rad = np.deg2rad(heading[ind, 1])
      │   【真北方位角（北偏西为正）→ 弧度】
      │
      └──► 航向角投影（ENU → 车辆坐标系）:
          │
          forward_error = -dlon·sin(heading_rad) + dlat·cos(heading_rad)
          lateral_error = dlon·cos(heading_rad) + dlat·sin(heading_rad)
          vertical_error = dalt
          【返回 horizontal / lateral / vertical / forward 四组误差】
```

#### C.2.5 `commons/outpre_new.py` → `outpre_new()`

```
outpre_new(outfile, diff_datalc, diff_datatc, diff_datagnss,
           lcs, tcs, gnss, yaw, tcstart,
           t_start, t_end, type_label,
           append_mode, return_stats, lcver, tcver)
【将误差数据转换为 RMS/CEP/Max 统计指标，输出 TXT 或返回字典】
      │
      ├──► [t_start/t_end 有值时] 时间范围筛选
      │   对每个时间范围 [start_i, end_i]：
      │       indices = where((time >= start_i) & (time <= end_i))
      │       合并所有范围的索引 → diff_datalc_filtered
      │
      ├──► 【LC 统计分支】
      │   ├──► calculate_errors(diff_datalc, yaw)
      │   │   → horizontal / lateral / vertical / forward 四组误差
      │   │
      │   ├──► calculate_cep(horizontal_error)
      │   │   【CEP = percentile(sorted, 50)】
      │   │   CEP95 = percentile(sorted, 95)
      │   │   CEP99 = percentile(sorted, 99)
      │   │
      │   ├──► rms(horizontal_error)
      │   │   【rms = sqrt(mean(error²))】
      │   │
      │   └──► calculate_odometry(lcs[valid_indices])
      │       【多段时间范围里程累加】
      │
      ├──► 【TC 统计分支】（同上，结果 → diff_datatc）
      │
      ├──► 【GNSS 统计分支】（同上，结果 → diff_datagnss）
      │
      └──► [return_stats == True]
          return {
              'lc': {odom, horizontal_rms, horizontal_cep95, ...},
              'tc': {...},
              'gnss': {...}
          }
          【返回统计字典供调用者聚合】

          [return_stats == False]
          写入 TXT 文件（覆盖/追加模式）
```

---

### C.3 核心数据结构流动

以下展示各数据从输入到输出所经过的完整模块路径：

```
【数据流 A: 参考真值】
原始 ref.txt（IE 格式）
  └──► fileutils.readfullcsv(colindex=[0,6,7,5,15,14,16,2,3,4,-1])
  └──► refdata (N×11): [time, lat, lon, height, ve, vn, vu, roll, pitch, yaw, quality]
        │
        └──► utils.dpos2den(refdata[:, 7:9], pos0)
        └──► refdata (ENU 米): [time, roll, pitch, yaw, ve, vn, vu, ΔN, ΔE, ΔU, quality]

【数据流 B: LC 融合结果】
原始 tcmsf_sol.csv
  └──► readSensorDataTcXkPk(filepath, dt) 或 readmsf_debug_state(filepath, dt)
  └──► lcs (M×16): [time, att, vn, pos, eb, db, kod, map, status]
        │
        ├──► utils.dpos2den(lcs[:, 7:9], pos0)
        │   【经纬度 → ENU 米】
        │
        └──► utils.alignDataByTimeTcSol(lcs, lcs[:, 0], refdata, refdata[:, 0], tthreshod)
              【时间对齐到参考时间轴】
              │
              └──► utils.calculateDifference(aligned_lcs, aligned_ref)
              └──► diff_datalc (K×10): [time, droll, dpitch, dyaw, dve, dvn, dvu, dlat, dlon, dalt]
                    │
                    └──► calculate_errors(diff_datalc, yaw)
                    └──► horizontal / lateral / forward / vertical 误差向量
                          │
                          └──► outpre_new() → RMS/CEP95/CEP99/Max/Odom

【数据流 C: GNSS PVT 数据】
原始 pvt.csv
  └──► fileutils.readfullcsv(gnsspath, gnssindex, extindex)
  └──► gnss (P×15): [gps_sec, -1, -1, heading, vn, ve, vu, lon, lat, alt, qual, std_x, std_y, std_z, sat, stat]
        │
        ├──► 航向角归一化: heading > 180 → -= 360
        ├──► 状态筛选: gnss[:, -1] > 0
        │
        └──► utils.dpos2den(gnss[:, 7:9], pos0)
              【经纬度 → ENU 米】
              │
              └──► utils.alignDataByTimeTcSol(gnss, gnss[:, 0], refdata, refdata[:, 0], tol)
                    【时间对齐到参考时间轴】
                    │
                    └──► utils.calculateDifference()
                    └──► diff_datagnss
                          │
                          └──► calculate_errors() → 误差向量
                                │
                                └──► outpre_new() → GNSS 精度统计
```

---

### C.4 关键函数速查表

| 文件 | 函数 | 功能说明 | 调用者 |
|------|------|---------|-------|
| `commons/fileutils.py` | `readfullcsv()` | **通用 CSV 解析** — 支持空格/逗号分隔、自适应列数、NaN 填充，返回 numpy 数组 | `precision_head_topic_ref_100c_wdh.py`、`evaluation_utils.py` |
| `commons/utils.py` | `dpos2den()` | **经纬度→ENU米** — 将 WGS84 经纬度以 pos0 为原点转换为 ENU 局部米坐标，原地修改数组 | 所有需要坐标转换的模块 |
| `commons/utils.py` | `alignDataByTimeTcSol()` | **时间对齐** — 按容差将两个 GPS 时间序列对齐到交集点，支持 x 倍归化 | `precision_head_topic_ref_100c_wdh.py`、`evaluation_utils.py` |
| `commons/utils.py` | `calculateDifference()` | **行对行差值** — 两个完全对齐数组对应列相减，角度列 wrap 到 [-180°, 180°] | `precision_head_topic_ref_100c_wdh.py`、`evaluation_utils.py` |
| `commons/utils.py` | `InterpState()` | **线性插值重采样** — 将传感器数据插值到参考时间轴，支持时间非单调、外推 | `evaluation_utils.py` |
| `commons/calculate_errors.py` | `calculate_errors()` | **误差分解** — 将 ENU 误差投影到车辆坐标系，得到 horizontal/lateral/forward/vertical 四组误差 | `precision_head_topic_ref_100c_wdh.py`、`outpre_new.py`、`plot_errors.py` |
| `commons/calculate_errors.py` | `find_discontinuous_indices()` | **离散索引映射** — 处理 heading 采样与误差数据时间不连续问题，生成严格递增的索引组合 | `calculate_errors()` |
| `commons/calculate_cep.py` | `calculate_cep()` | **CEP 分位数计算** — 对水平误差排序后取 50/95/99 分位数 | `outpre_new.py` |
| `commons/calculate_odometry.py` | `calculate_odometry()` | **3D 累积里程** — 累加相邻点之间的 3D 欧氏距离，返回累积里程向量 | `outpre_new.py` |
| `commons/outpre_new.py` | `outpre_new()` | **精度统计核心** — 计算 RMS/CEP95/CEP99/Max/Odom，支持时间范围筛选、TXT 输出或字典返回 | `precision_head_topic_ref_100c_wdh.py`、`_horizontal_only.py` |
| `commons/plot_errors.py` | `plot_errors()` | **误差曲线可视化** — matplotlib 4 行子图（水平/横向/前进/高程），带/不带 GNSS 两个版本，保存 300 DPI PNG | `precision_head_topic_ref_100c_wdh.py`、`_horizontal_only.py` |
| `commons/evaluation_utils.py` | `load_config_from_toml()` | **TOML 配置加载** — toml.load() 封装，含文件存在性检查 | 所有评估入口脚本 |
| `commons/evaluation_utils.py` | `process_sensor_data()` | **传感器数据处理流水线** — 读取→坐标转换→时间对齐→差值计算的统一封装 | `precision_head_topic_ref_100c_wdh.py` |
| `commons/evaluation_utils.py` | `calculate_horizontal_velocity_stats()` | **水平速度误差统计** — 从差值数据提取 ve/vn，计算水平速度误差 RMS/CEP 分位数 | `_horizontal_only.py` |
| `commons/evaluation_utils.py` | `calculate_normal_scene_time_ranges()` | **正常场景时间计算** — 从总时间范围减去特殊场景（隧道等），得到正常场景时间段 | `_horizontal_only.py` |
| `commons/readSensorDataTcXkPk.py` | `readSensorDataTcXkPk()` | **TCMSF 结果读取** — CSV → numpy，首列时间减去 dt 偏移 | `evaluation_utils.py` |
| `commons/readmsf_debug_state.py` | `readmsf_debug_state()` | **MSF 调试状态读取** — 读取调试状态 + 插值到参考时间 | `evaluation_utils.py` |
| `batch_run_tcmsf.py` | `BatchRunTcmsf.__init__()` | **批量执行器初始化** — 加载配置、定位项目根、source 环境变量 | `main()` |
| `batch_run_tcmsf.py` | `BatchRunTcmsf.process_single_dataset()` | **单数据集处理** — TCMSF 执行→结果复制→topic_parse→坐标转换的全流程 | `run_all()` |
| `batch_run_tcmsf.py` | `BatchRunTcmsf.modify_config_file()` | **TOML 配置修改** — 正则替换配置项，写入原位置和 data/tmp/ 双副本 | `process_single_dataset()` |
| `batch_run_tcmsf.py` | `BatchRunTcmsf.convert_ie_to_csv_wgs84()` | **IE→CSV WGS84 转换** — Python 实现的纯格式转换，保留 WGS84 原始坐标不偏移 | `run_wgs_to_mars()` |
| `batch_run_tcmsf.py` | `BatchRunTcmsf.run_command()` | **命令执行封装** — 支持 source_env.sh 注入环境变量的 shell 执行 | `run_tcmsf()`、`run_topic_parse()`、`run_wgs_to_mars()` |
| `precision_head_topic_ref_100c_wdh.py` | `precision_head_topic_ref_100c_wdh()` | **完整精度评估主函数** — 含高程误差的全面评估，数据读取→对齐→误差→统计→绘图全流程 | `main()`、`_main.py` |
| `precision_head_topic_ref_100c_wdh.py` | `plot_detail_subplots()` | **极值详细子图** — 循环查找超阈值极值点，绘制 ±N 秒放大窗口 | `precision_head_topic_ref_100c_wdh()` |
| `precision_head_topic_ref_100c_wdh.py` | `save_and_plot_clips()` | **GNSS Clip 处理** — 识别误差超标连续段，绘制 50s 间隔子图，保存原始数据 CSV | `precision_head_topic_ref_100c_wdh()` |
| `_horizontal_only.py` | `precision_head_topic_ref_100c_wdh_horizontal_only()` | **水平精度专用评估** — 仅统计水平误差（H/L/F），额外计算正常场景（排除隧道等） | `main()`、`_main.py` |
| `_horizontal_only.py` | `save_and_plot_clips_horizontal_only()` | **水平精度 Clip** — 仅处理水平误差，与完整版相比省略垂直误差子图 | `_horizontal_only()` |
| `aggregate_precision_statistics.py` | `parse_precision_file()` | **统计文件解析** — 正则匹配多版本号（兼容 LC/TC/GNSS），提取各场景数据 | `main()` |
| `aggregate_precision_statistics.py` | `aggregate_statistics()` | **里程加权聚合** — 按里程占总里程比加权平均同类场景统计指标，全 0 场景跳过 | `main()` |
| `batch_run_precision_head_horizontal.py` | `run_single_config()` | **单配置执行** — subprocess 调用评估脚本，重定向 stdout/stderr 到日志文件 | `main()` |
| `batch_run_precision_head_horizontal.py` | `generate_config_file()` | **动态配置生成** — 从原始数据集目录查找 ref 和 time_ranges，自动生成 TOML 配置 | `generate_all_configs()` |

---

*文档生成时间：2026-04-22（进阶要求追加：2026-04-22）*

