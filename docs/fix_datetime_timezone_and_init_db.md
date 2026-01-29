# 修复 DateTime 时区问题和数据库初始化

## 问题描述

执行 `docker compose down -v` 后，数据库被清空，导致表不存在：
```
asyncpg.exceptions.UndefinedTableError: relation "users" does not exist
```

## 原因

1. **时区问题**（已修复）：模型中使用 `datetime.now(timezone.utc)` 创建带时区的 datetime，但数据库列定义为 `TIMESTAMP WITHOUT TIME ZONE`。
2. **数据库被清空**：`docker compose down -v` 删除了所有数据卷，包括数据库数据。

## 已完成的修复

### 1. 修复模型文件中的 DateTime 列

在以下文件中，所有 `DateTime` 列都添加了 `timezone=True` 参数：
- `backend/app/models/user.py`
- `backend/app/models/project.py`
- `backend/app/models/test_case.py`
- `backend/app/models/test_execution.py`

**修改示例**:
```python
# 修复前
created_at: Mapped[datetime] = mapped_column(
    DateTime,
    default=lambda: datetime.now(timezone.utc),
    nullable=False
)

# 修复后
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),  # ✅ 添加 timezone=True
    default=lambda: datetime.now(timezone.utc),
    nullable=False
)
```

### 2. 创建数据库初始化脚本

已创建 `backend/scripts/init_db.py` 脚本，用于：
- 创建所有数据库表
- 创建初始管理员和测试用户

## 🚀 立即修复步骤

### 方法 A：在 Docker 容器内初始化（推荐）

```bash
# 1. 进入后端容器
docker exec -it apt_backend bash

# 2. 运行初始化脚本
python scripts/init_db.py

# 3. 退出容器
exit
```

### 方法 B：在宿主机上初始化（如果本地有 Python 环境）

```bash
cd /Users/ycb/workspace/apt_platform/backend

# 激活虚拟环境
source .venv/bin/activate

# 运行初始化脚本
python scripts/init_db.py
```

## 初始化后的账号信息

脚本会创建以下账号：

| 角色 | 邮箱 | 密码 | 权限 |
|------|------|------|------|
| 管理员 | admin@example.com | admin123 | 超级管理员 |
| 测试用户 | test@example.com | test123 | 普通用户 |

## 验证修复

初始化完成后，尝试以下操作：

### 1. 登录测试

在前端登录页面使用以下账号登录：
- 邮箱: `test@example.com`
- 密码: `test123`

### 2. 创建项目并运行测试

登录后：
1. 创建一个新项目
2. 配置 Git 仓库（如果有）
3. 尝试运行测试

应该不再出现时区错误或表不存在的错误。

## 如果初始化脚本失败

### 问题 1：找不到 scripts 目录

```bash
# 在容器内创建目录
docker exec -it apt_backend mkdir -p /app/scripts

# 将脚本复制到容器
docker cp backend/scripts/init_db.py apt_backend:/app/scripts/
```

### 问题 2：权限问题

```bash
# 给脚本添加执行权限
docker exec -it apt_backend chmod +x /app/scripts/init_db.py
```

### 问题 3：手动执行 SQL（最后手段）

如果脚本无法运行，可以手动修改数据库列类型：

```bash
# 1. 进入 PostgreSQL 容器
docker exec -it apt_postgres psql -U postgres -d atp_db

# 2. 如果表存在，修改列类型
ALTER TABLE users
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
  ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;

ALTER TABLE projects
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
  ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE,
  ALTER COLUMN last_sync_time TYPE TIMESTAMP WITH TIME ZONE;

ALTER TABLE test_cases
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
  ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;

ALTER TABLE test_executions
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
  ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;

# 3. 退出
\q
```

然后使用初始化脚本创建初始用户。

## 预防措施

### 避免数据丢失

以后重启容器时，**不要使用 `-v` 参数**：

```bash
# ❌ 错误：会删除数据
docker compose down -v

# ✅ 正确：保留数据
docker compose down

# 重启
docker compose up -d
```

### 定期备份数据库

```bash
# 备份数据库
docker exec apt_postgres pg_dump -U postgres atp_db > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i apt_postgres psql -U postgres atp_db < backup_20260129.sql
```

## 技术说明

### 为什么需要 timezone=True？

PostgreSQL 有两种时间戳类型：
- `TIMESTAMP WITHOUT TIME ZONE` - 不存储时区信息
- `TIMESTAMP WITH TIME ZONE` - 存储时区信息

当 Python 代码使用 `datetime.now(timezone.utc)` 创建**带时区的 datetime** 对象时，必须将其存储到 `TIMESTAMP WITH TIME ZONE` 列中。

SQLAlchemy 通过 `DateTime(timezone=True)` 参数来指定使用 `TIMESTAMP WITH TIME ZONE`。

### 修复影响范围

所有涉及时间戳的操作都已修复：
- 用户注册/更新
- 项目创建/更新/同步
- 测试用例创建/更新
- 测试执行创建/更新

---

**修复时间**：2026-01-29
**修复人员**：Claude Sonnet 4.5
