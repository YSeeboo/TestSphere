# Celery 配置说明

## 概述

本项目已配置 Celery 用于处理后台异步任务。Celery Worker 使用同步数据库连接（psycopg2），避免与 AsyncIO 冲突。

## 架构

- **FastAPI (API 服务)**: 使用 `AsyncEngine` + `AsyncSession` (asyncpg)
- **Celery Worker**: 使用 `Engine` + `SessionLocal` (psycopg2)
- **Broker & Backend**: Redis

## 文件结构

```
backend/
├── app/
│   ├── core/
│   │   └── celery_app.py          # Celery 应用实例
│   ├── db/
│   │   └── session.py              # 数据库会话 (异步 + 同步)
│   └── tasks/
│       ├── __init__.py
│       └── example.py              # 示例任务
└── docker-compose.yml              # 包含 worker 服务
```

## 依赖安装

确保已安装以下依赖（已在 `pyproject.toml` 中配置）:

```bash
cd backend
poetry install
```

关键依赖:
- `celery`: 任务队列
- `psycopg2-binary`: 同步 PostgreSQL 驱动
- `redis`: Redis 客户端

## 使用方法

### 1. 启动服务

使用 Docker Compose 启动所有服务:

```bash
docker-compose up -d
```

这将启动:
- `postgres`: PostgreSQL 数据库
- `redis`: Redis 服务
- `backend`: FastAPI 应用
- `worker`: Celery Worker

### 2. 创建任务

在 `app/tasks/` 目录下创建任务文件:

```python
# app/tasks/my_tasks.py
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from sqlalchemy import select
from app.models.user import User

@celery_app.task(name="my_tasks.process_user")
def process_user(user_id: int) -> dict:
    """处理用户数据的后台任务."""
    with SessionLocal() as db:
        user = db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # 执行业务逻辑
        # ...
        
        db.commit()
        return {"status": "success", "user_id": user_id}
```

### 3. 在 API 中调用任务

```python
# app/api/endpoints/users.py
from fastapi import APIRouter
from app.tasks.my_tasks import process_user

router = APIRouter()

@router.post("/users/{user_id}/process")
async def trigger_process(user_id: int):
    """触发后台任务处理用户."""
    # 异步调用任务
    task = process_user.delay(user_id)
    
    return {
        "task_id": task.id,
        "status": "Task submitted"
    }

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态."""
    from app.core.celery_app import celery_app
    task = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
```

## 本地开发

### 启动 Worker (不使用 Docker)

```bash
cd backend
poetry run celery -A app.core.celery_app worker --loglevel=info
```

### 查看任务列表

```bash
poetry run celery -A app.core.celery_app inspect registered
```

### 监控任务

使用 Flower (需要额外安装):

```bash
poetry add flower
poetry run celery -A app.core.celery_app flower
```

访问 http://localhost:5555

## 配置说明

### Celery 配置 (`app/core/celery_app.py`)

- **broker**: Redis URL (从 `settings.REDIS_URL` 读取)
- **backend**: Redis URL (存储任务结果)
- **task_time_limit**: 3600 秒 (1 小时)
- **task_soft_time_limit**: 3000 秒 (50 分钟)
- **worker_prefetch_multiplier**: 4 (预取任务数)

### 数据库配置 (`app/db/session.py`)

- **async_engine**: 供 FastAPI 使用 (postgresql+asyncpg)
- **sync_engine**: 供 Celery Worker 使用 (postgresql+psycopg2)
- **SessionLocal**: 同步会话工厂，在 Celery 任务中使用

## 注意事项

1. **不要在 Celery 任务中使用 AsyncSession**: Worker 运行在同步环境中，必须使用 `SessionLocal`
2. **任务应该是幂等的**: 任务可能会重试，确保多次执行结果一致
3. **使用 context manager**: 使用 `with SessionLocal() as db:` 确保连接正确关闭
4. **任务超时**: 长时间运行的任务应该设置合理的 `time_limit`
5. **错误处理**: 在任务中添加适当的异常处理和日志记录

## 测试

测试示例任务:

```python
# 在 Python shell 中
from app.tasks.example import health_check_task, add_numbers

# 同步执行
result = health_check_task()
print(result)

# 异步执行
task = add_numbers.delay(10, 20)
print(f"Task ID: {task.id}")
print(f"Result: {task.get()}")  # 等待任务完成并获取结果
```

## 故障排查

### Worker 无法连接数据库

检查环境变量是否正确设置:
```bash
docker-compose logs worker
```

### 任务未被发现

确保任务模块在 `app/tasks/` 目录下，并且 `celery_app.autodiscover_tasks()` 配置正确。

### Redis 连接失败

检查 Redis 服务是否运行:
```bash
docker-compose ps redis
```
