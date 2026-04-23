#!/bin/bash
################################################################################
# PVT RTK LC Evaluation Package - 快速重新打包脚本
# 用于快速更新部署包（仅更新变化的文件，不重新下载依赖）
################################################################################

set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

DEPLOYMENT_DIR="deployment"
DEPLOYMENT_FILE="pvt_rtk_lc_evaluation_deploy.tar.gz"

echo "=================================="
echo "PVT RTK LC Evaluation 快速重新打包"
echo "=================================="
echo ""

# 检查deployment目录是否存在
if [ ! -d "$DEPLOYMENT_DIR" ]; then
    echo "错误: deployment目录不存在"
    echo "请先运行完整的打包流程"
    exit 1
fi

echo "[1/4] 同步程序文件..."
# 同步主程序包
if [ -d "pvt_rtk_lc_evaluation" ]; then
    echo "  同步 pvt_rtk_lc_evaluation/"
    cp -r pvt_rtk_lc_evaluation/* "$DEPLOYMENT_DIR/pvt_rtk_lc_evaluation/"
fi

# 同步commons模块
if [ -d "commons" ]; then
    echo "  同步 commons/"
    cp commons/*.py "$DEPLOYMENT_DIR/commons/" 2>/dev/null || true
fi

# 同步requirements.txt
if [ -f "requirements.txt" ]; then
    echo "  同步 requirements.txt"
    cp requirements.txt "$DEPLOYMENT_DIR/"
fi

echo "  ✓ 文件同步完成"
echo ""

echo "[2/4] 检查脚本文件..."
# 检查install.sh
if [ -f "$DEPLOYMENT_DIR/install.sh" ]; then
    chmod +x "$DEPLOYMENT_DIR/install.sh"
    echo "  ✓ install.sh 已设置执行权限"
fi

# 检查run_eval.sh
if [ -f "$DEPLOYMENT_DIR/run_eval.sh" ]; then
    chmod +x "$DEPLOYMENT_DIR/run_eval.sh"
    echo "  ✓ run_eval.sh 已设置执行权限"
fi

echo ""

echo "[3/4] 更新版本信息..."
cat > "$DEPLOYMENT_DIR/VERSION.txt" << EOF
PVT RTK LC Evaluation Package - 离线部署包版本信息

版本: 1.0.0 (快速更新)
更新日期: $(date '+%Y-%m-%d %H:%M:%S')
Python版本要求: >=3.7
目标平台: Linux x86_64

包含的Python包:
- numpy 1.24.4
- pandas 2.0.3
- matplotlib 3.7.5
- scipy 1.10.1
- toml 0.10.2
- pillow 10.4.0
- 及其他依赖项

包含的程序模块:
- pvt_rtk_lc_evaluation (主评估包)
- commons (本地依赖模块)

部署包大小: ~180MB
解压后大小: ~500MB

打包方式:
- 使用Python虚拟环境
- 包含预安装的依赖包
- 提供离线安装脚本
- 完全独立运行

部署说明:
详见 README_DEPLOYMENT.md

注意:
本次更新仅同步了程序代码，未重新下载依赖包
EOF

echo "  ✓ 版本信息已更新"
echo ""

echo "[4/4] 打包部署包..."
rm -f "$DEPLOYMENT_FILE"
tar -czf "$DEPLOYMENT_FILE" "$DEPLOYMENT_DIR/"

if [ $? -eq 0 ]; then
    FILE_SIZE=$(ls -lh "$DEPLOYMENT_FILE" | awk '{print $5}')
    echo "  ✓ 打包完成"
    echo ""
    echo "=================================="
    echo "✓ 快速重新打包完成！"
    echo "=================================="
    echo ""
    echo "部署包信息:"
    echo "  文件: $DEPLOYMENT_FILE"
    echo "  大小: $FILE_SIZE"
    echo "  位置: $(pwd)/$DEPLOYMENT_FILE"
    echo ""
    echo "更新内容:"
    echo "  - pvt_rtk_lc_evaluation/ 程序代码"
    echo "  - commons/ 依赖模块"
    echo "  - requirements.txt 依赖清单"
    echo "  - 脚本文件权限"
    echo "  - VERSION.txt 版本信息"
    echo ""
    echo "注意: 虚拟环境和Python依赖包未更新"
    echo ""
else
    echo "  ✗ 打包失败"
    exit 1
fi