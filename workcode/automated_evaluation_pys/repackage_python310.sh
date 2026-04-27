#!/bin/bash
################################################################################
# PVT RTK LC Evaluation Package - Python 3.10 重新打包脚本
# 用于创建适合 Python 3.10 的离线部署包
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

DEPLOYMENT_DIR="deployment_python310"
DEPLOYMENT_FILE="pvt_rtk_lc_evaluation_deploy_python310.tar.gz"
TEMP_PACKAGES_DIR="python_packages_310"

echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}PVT RTK LC Evaluation 打包工具${NC}"
echo -e "${GREEN}目标版本: Python 3.10${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""

# 检查 Python 版本
echo "[1/7] 检查系统 Python 版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo -e "  检测到 Python 版本: ${YELLOW}$PYTHON_VERSION${NC}"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "  ${RED}错误: 需要 Python 3.10 或更高版本${NC}"
    echo -e "  当前版本: $PYTHON_VERSION"
    echo ""
    echo "请安装 Python 3.10 后重试："
    echo "  Ubuntu/Debian: sudo apt install python3.10 python3.10-venv"
    echo "  或使用 pyenv: pyenv install 3.10.12 && pyenv local 3.10.12"
    exit 1
fi

echo -e "  ${GREEN}✓ Python 版本符合要求${NC}"
echo ""

# 检查 pip
echo "[2/7] 检查 pip..."
if ! python3 -m pip --version >/dev/null 2>&1; then
    echo -e "  ${RED}错误: pip 未安装${NC}"
    echo "  请运行: sudo apt install python3-pip"
    exit 1
fi
echo -e "  ${GREEN}✓ pip 可用${NC}"
echo ""

# 检查 requirements.txt
echo "[3/7] 检查依赖清单..."
if [ ! -f "requirements.txt" ]; then
    echo -e "  ${RED}错误: requirements.txt 不存在${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓ requirements.txt 存在${NC}"
echo ""

# 下载依赖包
echo "[4/7] 下载 Python 3.10 依赖包..."
if [ -d "$TEMP_PACKAGES_DIR" ]; then
    echo "  清理旧的依赖包目录..."
    rm -rf "$TEMP_PACKAGES_DIR"
fi

mkdir -p "$TEMP_PACKAGES_DIR"

echo "  正在下载依赖包（这可能需要几分钟）..."
python3 -m pip download -r requirements.txt -d "$TEMP_PACKAGES_DIR/" --no-cache-dir

if [ $? -ne 0 ]; then
    echo -e "  ${RED}✗ 依赖包下载失败${NC}"
    exit 1
fi

# 统计下载的包
PKG_COUNT=$(ls -1 "$TEMP_PACKAGES_DIR" | wc -l)
PKG_SIZE=$(du -sh "$TEMP_PACKAGES_DIR" | awk '{print $1}')
echo -e "  ${GREEN}✓ 下载完成 ($PKG_COUNT 个包, $PKG_SIZE)${NC}"
echo ""

# 创建新的部署目录
echo "[5/7] 创建部署目录结构..."
if [ -d "$DEPLOYMENT_DIR" ]; then
    echo "  清理旧的部署目录..."
    rm -rf "$DEPLOYMENT_DIR"
fi

mkdir -p "$DEPLOYMENT_DIR"

# 创建虚拟环境
echo "  创建 Python 3.10 虚拟环境..."
python3 -m venv "$DEPLOYMENT_DIR/venv"

if [ $? -ne 0 ]; then
    echo -e "  ${RED}✗ 虚拟环境创建失败${NC}"
    exit 1
fi

# 激活虚拟环境并安装依赖
echo "  安装依赖到虚拟环境..."
source "$DEPLOYMENT_DIR/venv/bin/activate"
pip install --no-index --find-links="$TEMP_PACKAGES_DIR/" -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "  ${RED}✗ 依赖安装失败${NC}"
    deactivate
    exit 1
fi

deactivate

# 复制依赖包到部署目录
echo "  复制依赖包..."
cp -r "$TEMP_PACKAGES_DIR" "$DEPLOYMENT_DIR/python_packages"

# 复制程序文件
echo "  复制程序文件..."

if [ -d "pvt_rtk_lc_evaluation" ]; then
    cp -r pvt_rtk_lc_evaluation "$DEPLOYMENT_DIR/"
fi

if [ -d "commons" ]; then
    mkdir -p "$DEPLOYMENT_DIR/commons"
    cp commons/*.py "$DEPLOYMENT_DIR/commons/" 2>/dev/null || true
fi

cp requirements.txt "$DEPLOYMENT_DIR/"

# 复制脚本文件
if [ -f "install.sh" ]; then
    cp install.sh "$DEPLOYMENT_DIR/"
    chmod +x "$DEPLOYMENT_DIR/install.sh"
fi

if [ -f "deployment/run_eval.sh" ]; then
    cp deployment/run_eval.sh "$DEPLOYMENT_DIR/"
    chmod +x "$DEPLOYMENT_DIR/run_eval.sh"
fi

if [ -f "deployment/README_DEPLOYMENT.md" ]; then
    cp deployment/README_DEPLOYMENT.md "$DEPLOYMENT_DIR/"
fi

echo -e "  ${GREEN}✓ 部署目录创建完成${NC}"
echo ""

# 生成版本信息
echo "[6/7] 生成版本信息..."
cat > "$DEPLOYMENT_DIR/VERSION.txt" << EOF
PVT RTK LC Evaluation Package - 离线部署包版本信息

版本: 1.0.0 (Python 3.10)
更新日期: $(date '+%Y-%m-%d %H:%M:%S')
Python版本要求: 3.10+
目标平台: Linux x86_64

包含的Python包:
EOF

# 列出所有包及其版本
for pkg in "$TEMP_PACKAGES_DIR"/*.whl; do
    if [ -f "$pkg" ]; then
        basename "$pkg" | sed 's/-py3.*//' | sed 's/-cp310.*//' | sed 's/.whl//' | sed 's/_/-/g' | awk '{print "  - " $0}'
    fi
done >> "$DEPLOYMENT_DIR/VERSION.txt"

cat >> "$DEPLOYMENT_DIR/VERSION.txt" << EOF

包含的程序模块:
- pvt_rtk_lc_evaluation (主评估包)
- commons (本地依赖模块)

依赖包大小: $(du -sh "$TEMP_PACKAGES_DIR" | awk '{print $1}')
解压后大小: ~500MB

打包方式:
- 使用 Python 3.10 虚拟环境
- 包含预安装的依赖包
- 提供离线安装脚本
- 完全独立运行

部署说明:
详见 README_DEPLOYMENT.md

注意:
本部署包专为 Python 3.10.x 环境打包
与 Python 3.8 版本的依赖包不兼容
EOF

echo -e "  ${GREEN}✓ 版本信息已生成${NC}"
echo ""

# 打包
echo "[7/7] 打包部署文件..."
echo "  正在打包（这可能需要几分钟）..."

rm -f "$DEPLOYMENT_FILE"
tar -czf "$DEPLOYMENT_FILE" "$DEPLOYMENT_DIR/"

if [ $? -eq 0 ]; then
    FILE_SIZE=$(ls -lh "$DEPLOYMENT_FILE" | awk '{print $5}')
    echo -e "  ${GREEN}✓ 打包完成${NC}"
    echo ""
    echo -e "${GREEN}==================================${NC}"
    echo -e "${GREEN}✓ 打包成功！${NC}"
    echo -e "${GREEN}==================================${NC}"
    echo ""
    echo "部署包信息:"
    echo "  文件: $DEPLOYMENT_FILE"
    echo "  大小: $FILE_SIZE"
    echo "  位置: $(pwd)/$DEPLOYMENT_FILE"
    echo ""
    echo "部署步骤:"
    echo "  1. 上传部署包到目标服务器:"
    echo "     scp $DEPLOYMENT_FILE user@server:/path/to/destination/"
    echo ""
    echo "  2. 在目标服务器解压:"
    echo "     tar -xzf $DEPLOYMENT_FILE"
    echo "     cd $DEPLOYMENT_DIR/"
    echo ""
    echo "  3. 运行安装脚本:"
    echo "     bash install.sh"
    echo ""
    echo "  4. 激活虚拟环境并使用:"
    echo "     source venv/bin/activate"
    echo "     python your_script.py"
    echo ""
    echo "清理提示:"
    echo "  临时依赖包目录: $TEMP_PACKAGES_DIR"
    echo "  如不再需要，可删除: rm -rf $TEMP_PACKAGES_DIR"
    echo ""
else
    echo -e "  ${RED}✗ 打包失败${NC}"
    exit 1
fi