# ATP 快速启动指南

本指南帮助您快速启动 ATP（自动化测试平台）的后端和前端服务。

## 📋 前置要求

- Docker & Docker Compose
- Python 3.11+ (后端开发)
- Poetry (后端开发)
- Node.js 18+ (前端开发)
- npm/pnpm/yarn (前端开发)

## 🚀 快速启动

### 1. 启动基础设施（PostgreSQL + Redis）

```bash
# 在项目根目录执行
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 2. 配置后端环境

```bash
cd backend

# 复制环境变量配置文件
cp .env.example .env

# 安装依赖
poetry install
```

### 3. 启动后端服务

```bash
# 方式 1: 使用 Poetry
poetry run python -m app.main

# 方式 2: 使用 uvicorn（推荐开发环境）
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动前端服务

在新终端中：

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 5. 验证服务

访问以下地址验证服务是否正常：

**后端服务**:

- **根路径**: http://localhost:8000/
- **健康检查**: http://localhost:8000/api/v1/health
- **API 文档**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

**前端服务**:

- **应用首页**: http://localhost:5173/

## 🔍 健康检查端点

| 端点                       | 说明         | 用途                        |
| -------------------------- | ------------ | --------------------------- |
| `GET /api/v1/health`       | 完整健康检查 | 检查数据库和 Redis 连接状态 |
| `GET /api/v1/health/ready` | 就绪检查     | Kubernetes readiness probe  |
| `GET /api/v1/health/live`  | 存活检查     | Kubernetes liveness probe   |

## 📦 服务端口

| 服务        | 端口 | 说明           |
| ----------- | ---- | -------------- |
| Frontend    | 5173 | Vue 3 前端应用 |
| Backend API | 8000 | FastAPI 应用   |
| PostgreSQL  | 5432 | 数据库         |
| Redis       | 6379 | 缓存/消息队列  |

## 🛠️ 常用命令

### Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 停止并删除数据卷（⚠️ 会删除数据）
docker-compose down -v

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f postgres
docker-compose logs -f redis
```

### 数据库连接

```bash
# 使用 psql 连接数据库
docker exec -it atp_postgres psql -U atp_user -d atp_db

# 使用 redis-cli 连接 Redis
docker exec -it atp_redis redis-cli
```

### 后端开发

```bash
cd backend

# 安装依赖
poetry install

# 添加新依赖
poetry add package-name

# 运行测试
poetry run pytest

# 代码格式化
poetry run black app/

# 代码检查
poetry run ruff check app/

# 类型检查
poetry run mypy app/
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 类型检查
npm run type-check

# 代码检查
npm run lint
```

## 📁 项目结构

```
apt_platform/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── main.py         # FastAPI 应用入口
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库
│   │   ├── models/         # SQLAlchemy 模型
│   │   └── schemas/        # Pydantic 模型
│   ├── pyproject.toml      # Poetry 依赖配置
│   └── Dockerfile
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── api/            # API 接口定义
│   │   ├── components/     # 可复用组件
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── utils/          # 工具函数
│   │   ├── views/          # 页面组件
│   │   └── main.ts         # 应用入口
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml       # Docker Compose 配置
├── docs/                    # 文档
└── QUICKSTART.md           # 本文件
```

## 🔧 环境变量说明

关键环境变量（`.env` 文件）：

```bash
# 应用配置
DEBUG=True                    # 开发模式
API_V1_PREFIX=/api/v1        # API 前缀

# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=atp_user
POSTGRES_PASSWORD=atp_password
POSTGRES_DB=atp_db

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 📝 开发规范

详见项目根目录的 `.cursorrules` 文件。

### 关键规范

✅ **严格类型提示**: 所有函数必须有类型注解  
✅ **异步优先**: 所有 I/O 操作使用 async/await  
✅ **SQLAlchemy 2.0**: 使用 `select()`, `AsyncSession`  
✅ **Pydantic V2**: 使用 `model_dump()`, `model_validate()`  
✅ **清晰注释**: 复杂逻辑使用中文注释

## 🐛 故障排查

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
docker-compose ps postgres

# 查看 PostgreSQL 日志
docker-compose logs postgres

# 测试连接
docker exec -it atp_postgres psql -U atp_user -d atp_db -c "SELECT 1;"
```

### Redis 连接失败

```bash
# 检查 Redis 是否运行
docker-compose ps redis

# 查看 Redis 日志
docker-compose logs redis

# 测试连接
docker exec -it atp_redis redis-cli ping
```

### 端口被占用

```bash
# 查看端口占用情况
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# 修改 docker-compose.yml 中的端口映射
# 例如: "15432:5432" 将 PostgreSQL 映射到 15432
```

## 📚 参考文档

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2 文档](https://docs.pydantic.dev/latest/)
- [Poetry 文档](https://python-poetry.org/docs/)

## 📞 获取帮助

如遇问题，请查看：

1. 项目 README: `backend/README.md`
2. PRD 文档: `docs/PRD_v0.1.0.md`
3. 前端设计: `docs/Frontend_Design_v0.1.0.md`
