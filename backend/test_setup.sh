#!/bin/bash
# ATP Backend 设置验证脚本

set -e

echo "🔍 ATP Backend 设置验证"
echo "========================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker
echo "1️⃣  检查 Docker..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker 已安装: $(docker --version)"
else
    echo -e "${RED}✗${NC} Docker 未安装"
    exit 1
fi

# 检查 Docker Compose
echo ""
echo "2️⃣  检查 Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose 已安装: $(docker-compose --version)"
else
    echo -e "${RED}✗${NC} Docker Compose 未安装"
    exit 1
fi

# 检查 Python
echo ""
echo "3️⃣  检查 Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python 已安装: $PYTHON_VERSION"
    
    # 检查 Python 版本是否 >= 3.11
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        echo -e "${GREEN}✓${NC} Python 版本符合要求 (>= 3.11)"
    else
        echo -e "${YELLOW}⚠${NC} Python 版本建议升级到 3.11+"
    fi
else
    echo -e "${RED}✗${NC} Python 未安装"
    exit 1
fi

# 检查 Poetry
echo ""
echo "4️⃣  检查 Poetry..."
if command -v poetry &> /dev/null; then
    echo -e "${GREEN}✓${NC} Poetry 已安装: $(poetry --version)"
else
    echo -e "${YELLOW}⚠${NC} Poetry 未安装，请运行: curl -sSL https://install.python-poetry.org | python3 -"
fi

# 检查项目文件
echo ""
echo "5️⃣  检查项目文件..."

FILES=(
    "../docker-compose.yml"
    "pyproject.toml"
    "app/main.py"
    "app/core/config.py"
    "app/db/session.py"
    "app/api/endpoints/health.py"
    ".env.example"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file 不存在"
    fi
done

# 检查 .env 文件
echo ""
echo "6️⃣  检查环境配置..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env 文件存在"
else
    echo -e "${YELLOW}⚠${NC} .env 文件不存在，将从 .env.example 复制"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} 已创建 .env 文件"
    fi
fi

# 检查 Docker 服务
echo ""
echo "7️⃣  检查 Docker 服务状态..."
cd ..
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓${NC} Docker 服务正在运行"
    docker-compose ps
else
    echo -e "${YELLOW}⚠${NC} Docker 服务未运行"
    echo "   运行以下命令启动服务:"
    echo "   docker-compose up -d"
fi

echo ""
echo "========================"
echo -e "${GREEN}✅ 验证完成！${NC}"
echo ""
echo "📝 下一步操作："
echo "   1. 启动基础设施: docker-compose up -d"
echo "   2. 安装依赖: cd backend && poetry install"
echo "   3. 启动后端: poetry run uvicorn app.main:app --reload"
echo "   4. 访问文档: http://localhost:8000/api/v1/docs"
echo ""
