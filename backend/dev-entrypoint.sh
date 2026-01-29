#!/bin/bash
# ATP Backend 开发环境智能启动脚本
# 功能：检测依赖变化并自动安装，然后启动开发服务器

set -e

echo "=========================================="
echo "ATP Backend Development Environment"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 调试模式
DEBUG="${DEBUG:-false}"
if [ "$DEBUG" = "true" ]; then
    set -x
fi

# 检查必要文件是否存在
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}错误: pyproject.toml 不存在${NC}"
    echo "请确保代码已正确挂载到 /app 目录"
    exit 1
fi

# 依赖检查和安装逻辑
# 使用持久化路径（挂载的 volume）而不是 /tmp
DEPS_HASH_FILE="/app/.deps_hash"
CURRENT_HASH=""

# 计算当前依赖文件的哈希值
if [ -f "poetry.lock" ]; then
    CURRENT_HASH=$(md5sum pyproject.toml poetry.lock 2>/dev/null | md5sum | cut -d' ' -f1)
else
    CURRENT_HASH=$(md5sum pyproject.toml 2>/dev/null | md5sum | cut -d' ' -f1)
fi

# 检查是否需要安装依赖
NEED_INSTALL=false

# 支持强制安装环境变量
if [ "$FORCE_INSTALL_DEPS" = "true" ]; then
    echo -e "${YELLOW}检测到 FORCE_INSTALL_DEPS=true，强制重新安装依赖${NC}"
    NEED_INSTALL=true
elif [ ! -f "$DEPS_HASH_FILE" ]; then
    echo -e "${YELLOW}首次启动，需要安装依赖...${NC}"
    NEED_INSTALL=true
else
    SAVED_HASH=$(cat "$DEPS_HASH_FILE")
    if [ "$CURRENT_HASH" != "$SAVED_HASH" ]; then
        echo -e "${YELLOW}检测到依赖文件变化，需要重新安装依赖...${NC}"
        echo "  - pyproject.toml 或 poetry.lock 已更新"
        NEED_INSTALL=true
    else
        echo -e "${GREEN}✓ 依赖文件未变化，跳过安装${NC}"
    fi
fi

# 执行依赖安装
if [ "$NEED_INSTALL" = true ]; then
    echo ""
    echo "=========================================="
    echo "安装 Python 依赖..."
    echo "=========================================="
    
    # 如果 poetry.lock 不存在，先生成
    if [ ! -f "poetry.lock" ]; then
        echo -e "${YELLOW}生成 poetry.lock...${NC}"
        poetry lock --no-update
    fi
    
    # 安装依赖（带重试机制）
    echo -e "${YELLOW}执行 poetry install...${NC}"
    MAX_RETRIES=3
    RETRY_COUNT=0
    INSTALL_SUCCESS=false
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -e "${BLUE}尝试 $RETRY_COUNT/$MAX_RETRIES...${NC}"
        
        if poetry install --no-interaction --no-ansi --no-root; then
            INSTALL_SUCCESS=true
            break
        else
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}安装失败，2秒后重试...${NC}"
                sleep 2
            fi
        fi
    done
    
    if [ "$INSTALL_SUCCESS" = false ]; then
        echo -e "${RED}错误: 依赖安装失败（已重试 $MAX_RETRIES 次）${NC}"
        echo -e "${RED}请检查网络连接和 Poetry 配置${NC}"
        exit 1
    fi
    
    # 验证关键依赖是否安装成功
    echo -e "${BLUE}验证关键依赖...${NC}"
    if ! poetry run python -c "import fastapi, sqlalchemy, celery, docker, redis" 2>/dev/null; then
        echo -e "${RED}错误: 关键依赖验证失败！${NC}"
        echo -e "${RED}以下包可能未正确安装: fastapi, sqlalchemy, celery, docker, redis${NC}"
        echo ""
        echo "尝试查看已安装的包："
        poetry show | grep -E "fastapi|sqlalchemy|celery|docker|redis" || true
        exit 1
    fi
    
    echo -e "${GREEN}✓ 关键依赖验证通过${NC}"
    
    # 保存当前哈希值
    echo "$CURRENT_HASH" > "$DEPS_HASH_FILE"
    
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
    echo ""
fi

# 根据环境变量决定启动模式
if [ "$CELERY_WORKER" = "true" ]; then
    # Worker 模式
    echo "=========================================="
    echo "启动 Celery Worker"
    echo "=========================================="
    echo "  - App: app.core.celery_app"
    echo "  - Log Level: info"
    echo "=========================================="
    echo ""
    
    exec poetry run celery -A app.core.celery_app worker --loglevel=info
else
    # Backend 模式（默认）
    echo "=========================================="
    echo "启动开发服务器"
    echo "=========================================="
    echo "  - Host: 0.0.0.0"
    echo "  - Port: 8000"
    echo "  - Reload: Enabled"
    echo "=========================================="
    echo ""
    
    # 启动 uvicorn 开发服务器
    # 使用 exec 确保 uvicorn 成为 PID 1，能正确接收信号
    exec poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
