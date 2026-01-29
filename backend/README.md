# ATP Backend

自动化测试平台（Automated Test Platform）后端服务。

## 技术栈

- **Python**: 3.11+
- **Web 框架**: FastAPI 0.109+
- **数据库**: PostgreSQL 15 + SQLAlchemy 2.0 (Async)
- **缓存**: Redis 7
- **依赖管理**: Poetry

## 快速开始

### 1. 安装依赖

```bash
cd backend
poetry install
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

**⚠️ 重要：生成安全的 JWT 密钥**

在 `.env` 文件中，您必须设置一个安全的 `SECRET_KEY`。使用以下命令生成：

```bash
# 使用 Python（推荐）
python -c "import secrets; print(secrets.token_hex(32))"

# 或使用 OpenSSL
openssl rand -hex 32
```

将生成的密钥复制到 `.env` 文件中的 `SECRET_KEY` 字段。

**安全说明**：
- ✅ `SECRET_KEY` 必须至少 32 字符
- ✅ 必须通过环境变量设置，不能使用默认值
- ✅ 生产环境会检测并拒绝不安全的示例密钥
- ⚠️ 切勿将 `.env` 文件提交到版本控制系统

### 3. 启动基础设施

在项目根目录启动 PostgreSQL 和 Redis：

```bash
docker-compose up -d
```

### 4. 运行应用

```bash
poetry run python -m app.main
```

或使用 uvicorn：

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/                 # API 路由
│   │   ├── __init__.py
│   │   └── endpoints/       # API 端点
│   │       ├── __init__.py
│   │       └── health.py    # 健康检查
│   ├── core/                # 核心配置
│   │   ├── __init__.py
│   │   └── config.py        # 应用配置
│   ├── db/                  # 数据库
│   │   ├── __init__.py
│   │   └── session.py       # 数据库会话
│   ├── models/              # SQLAlchemy 模型
│   │   └── __init__.py
│   └── schemas/             # Pydantic 模型
│       └── __init__.py
├── pyproject.toml           # Poetry 依赖配置
├── .env.example             # 环境变量示例
└── README.md
```

## API 端点

### 健康检查

- `GET /api/v1/health` - 完整健康检查（数据库 + Redis）
- `GET /api/v1/health/ready` - 就绪检查（Kubernetes readiness probe）
- `GET /api/v1/health/live` - 存活检查（Kubernetes liveness probe）

## 开发规范

详见项目根目录的 `.cursorrules` 文件。

### 关键规范

- ✅ 使用严格类型提示
- ✅ 使用 async/await 处理所有 I/O 操作
- ✅ SQLAlchemy 2.0 语法（`select()`, `AsyncSession`）
- ✅ Pydantic V2 语法（`model_dump()`, `model_validate()`）
- ✅ 清晰的中文注释

## 环境变量

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `APP_NAME` | 应用名称 | ATP Backend | ❌ |
| `DEBUG` | 调试模式 | False | ❌ |
| `SECRET_KEY` | JWT 签名密钥 | 无 | ✅ |
| `ALGORITHM` | JWT 算法 | HS256 | ❌ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | 30 | ❌ |
| `POSTGRES_HOST` | PostgreSQL 主机 | localhost | ❌ |
| `POSTGRES_PORT` | PostgreSQL 端口 | 5432 | ❌ |
| `POSTGRES_USER` | PostgreSQL 用户 | atp_user | ❌ |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | atp_password | ❌ |
| `POSTGRES_DB` | PostgreSQL 数据库 | atp_db | ❌ |
| `REDIS_HOST` | Redis 主机 | localhost | ❌ |
| `REDIS_PORT` | Redis 端口 | 6379 | ❌ |

**注意事项**：
- ✅ 标记为必填的变量必须在 `.env` 中设置
- `SECRET_KEY` 必须至少 32 字符，且不能使用不安全的示例值
- 生产环境部署时，建议使用 Kubernetes Secrets 或其他密钥管理服务

## 许可证

MIT
