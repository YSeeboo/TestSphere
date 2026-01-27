# 执行引擎 Part 2.1 - 基础设施与代码准备

## 实施概述

本文档记录了执行引擎 Part 2.1 的实施内容，主要包括升级 Worker 配置以支持 Docker 操作，并实现代码复制逻辑。

## 实施日期

2026-01-26

## 修改内容

### 1. 依赖管理 (`backend/pyproject.toml`)

✅ **已确认**: Docker Python 客户端依赖已存在
- `docker = "^7.0.0"` - 用于与 Docker 守护进程交互

### 2. Docker Compose 配置 (`docker-compose.yml`)

#### Worker 服务配置更新

**Volume 挂载**:
```yaml
volumes:
  - ./backend:/app                          # 代码热加载
  - /var/run/docker.sock:/var/run/docker.sock  # Docker 守护进程访问
  - /tmp/atp_repos:/tmp/atp_repos              # 代码源目录（持久化/共享）
  - /tmp/atp_runs:/tmp/atp_runs                # 测试执行目录
```

**关键点**:
- `/var/run/docker.sock`: 允许 Worker 容器操作宿主机 Docker（创建/管理测试容器）
- `/tmp/atp_repos`: 项目代码仓库存储，通过 `sync_project` 任务拉取
- `/tmp/atp_runs`: 每次执行的隔离工作目录

### 3. 代码同步任务更新 (`backend/app/tasks/sync_project.py`)

**修改点**:
```python
# 修改前
REPOS_ROOT = Path("/tmp/repos")

# 修改后
REPOS_ROOT = Path("/tmp/atp_repos")
```

确保与 Docker Compose 配置中的目录一致。

### 4. 测试执行任务重构 (`backend/app/tasks/test_execution.py`)

#### 4.1 新增模块导入

```python
import os
import shutil
from pathlib import Path
```

#### 4.2 目录常量定义

```python
REPOS_BASE_DIR = Path("/tmp/atp_repos")  # 代码源目录
RUNS_BASE_DIR = Path("/tmp/atp_runs")    # 执行目录
```

#### 4.3 新增辅助函数

**`_ensure_directory_exists(directory: Path)`**
- 功能: 确保目录存在，不存在则创建
- 参数: 目录路径
- 错误处理: 创建失败时记录日志并抛出异常

**`_copy_repo_to_run_dir(repo_path: Path, run_path: Path)`**
- 功能: 将代码仓库完整复制到执行目录
- 参数:
  - `repo_path`: 源代码仓库路径 (`/tmp/atp_repos/{project_id}`)
  - `run_path`: 目标执行目录路径 (`/tmp/atp_runs/{execution_id}`)
- 特性:
  - 忽略 `.git` 目录（加速复制）
  - 忽略 `__pycache__` 和 `.pyc` 文件
  - 如果目标目录存在则先删除（确保干净环境）
- 错误处理: 验证源目录存在且为有效目录

#### 4.4 执行流程更新

**新的执行流程** (Part 2.1 版本):

```python
1. 从数据库获取执行记录
2. 检查代码源目录是否存在
   - 路径: /tmp/atp_repos/{project_id}
   - 不存在则报错，提示先执行 sync_project 任务
3. 准备执行目录并复制代码
   - 创建执行目录: /tmp/atp_runs/{execution_id}
   - 使用 shutil.copytree 完整复制代码
4. 更新状态为 'running'
   - 记录代码源路径和执行目录到日志
5. 模拟测试执行 (sleep 5 秒)
6. 更新状态为 'success'
```

#### 4.5 关键代码片段

**步骤 2: 检查代码源目录**
```python
repo_path = REPOS_BASE_DIR / str(project.id)
logger.info(f"检查代码源目录: {repo_path}")

if not repo_path.exists():
    error_msg = (
        f"代码源目录不存在: {repo_path}。"
        f"请先执行项目同步任务 (sync_project) 拉取代码。"
    )
    logger.error(error_msg)
    execution.status = "failed"
    execution.logs = f"[{datetime.utcnow().isoformat()}] 错误: {error_msg}\n"
    execution.updated_at = datetime.utcnow()
    db.commit()
    return {
        "status": "failed",
        "message": error_msg,
        "execution_id": execution_id,
    }
```

**步骤 3: 准备执行目录并复制代码**
```python
run_path = RUNS_BASE_DIR / str(execution_id)
logger.info(f"准备执行目录: {run_path}")

# 确保基础目录存在
_ensure_directory_exists(RUNS_BASE_DIR)

# 复制代码到执行目录
try:
    _copy_repo_to_run_dir(repo_path, run_path)
except Exception as e:
    error_msg = f"复制代码到执行目录失败: {e}"
    logger.error(error_msg)
    execution.status = "failed"
    execution.logs = f"[{datetime.utcnow().isoformat()}] 错误: {error_msg}\n"
    execution.updated_at = datetime.utcnow()
    db.commit()
    return {
        "status": "failed",
        "message": error_msg,
        "execution_id": execution_id,
    }
```

**步骤 4: 更新执行日志**
```python
execution.status = "running"
execution.logs = f"[{datetime.utcnow().isoformat()}] 开始执行测试\n"
execution.logs += f"[{datetime.utcnow().isoformat()}] 代码源: {repo_path}\n"
execution.logs += f"[{datetime.utcnow().isoformat()}] 执行目录: {run_path}\n"
execution.updated_at = datetime.utcnow()
db.commit()
```

## 目录结构说明

```
/tmp/
├── atp_repos/           # 代码源目录（通过 sync_project 维护）
│   ├── 1/              # 项目 ID = 1 的代码仓库
│   │   ├── tests/
│   │   ├── pytest.ini
│   │   └── ...
│   ├── 2/              # 项目 ID = 2 的代码仓库
│   └── ...
└── atp_runs/           # 执行目录（每次执行独立）
    ├── 101/           # 执行 ID = 101 的工作目录
    │   ├── tests/
    │   ├── pytest.ini
    │   └── ...
    ├── 102/           # 执行 ID = 102 的工作目录
    └── ...
```

## 安全性与权限

1. **Docker Socket 访问**:
   - Worker 容器通过 `/var/run/docker.sock` 访问宿主机 Docker
   - 这允许 Worker 创建 sibling 容器用于测试执行
   - **注意**: 这是特权操作，生产环境需评估安全风险

2. **目录权限**:
   - `/tmp/atp_repos` 和 `/tmp/atp_runs` 在宿主机上创建
   - Worker 容器以 root 运行（Dockerfile 默认），可访问这些目录
   - 确保 Worker 启动时不会因目录权限报错

## 后续步骤

- [x] Part 2.1: 基础设施与代码准备 ✅
- [ ] Part 2.2: Docker 容器启动与 pytest 执行
- [ ] Part 2.3: 结果收集与日志处理
- [ ] Part 2.4: 清理与错误处理

## 验证步骤

### 1. 重启 Docker Compose 服务

```bash
cd /Users/ycb/workspace/apt_platform
docker-compose down
docker-compose up -d
```

### 2. 验证 Worker 日志

```bash
docker-compose logs -f worker
```

应该看到:
- Worker 成功启动
- 没有目录权限相关错误
- Celery 正常连接到 Redis

### 3. 测试执行流程

1. **首先执行项目同步** (确保代码源存在):
   ```python
   # 通过 API 或直接调用
   from app.tasks.sync_project import sync_project_test_cases
   result = sync_project_test_cases.delay(project_id=1)
   ```

2. **创建测试执行**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/test-executions/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <token>" \
     -d '{
       "project_id": 1,
       "env": "dev",
       "marker_expression": "smoke",
       "keyword_expression": "",
       "config": {}
     }'
   ```

3. **检查执行日志**:
   - 应该看到 "代码源: /tmp/atp_repos/1"
   - 应该看到 "执行目录: /tmp/atp_runs/{execution_id}"

4. **验证目录结构**:
   ```bash
   # 进入 Worker 容器
   docker exec -it atp_worker bash
   
   # 检查目录
   ls -la /tmp/atp_repos/
   ls -la /tmp/atp_runs/
   ```

## 常见问题

### Q1: Worker 启动失败，提示 Docker 权限错误
**解决方案**:
- 确保 Docker 守护进程正在运行
- 检查 `/var/run/docker.sock` 是否存在
- 在 macOS/Windows 上，Docker Desktop 默认共享此 socket

### Q2: 复制代码时报 "源代码目录不存在"
**解决方案**:
- 先执行 `sync_project` 任务拉取代码
- 检查 `/tmp/atp_repos/{project_id}` 是否存在

### Q3: 复制速度慢
**解决方案**:
- 已忽略 `.git` 目录
- 可以考虑使用 `rsync` 或符号链接优化（后续版本）

## 注意事项

1. **目录清理**:
   - 当前版本不自动清理 `/tmp/atp_runs` 中的旧执行目录
   - 建议定期清理（后续实现清理任务）

2. **并发执行**:
   - 每次执行使用独立的目录 (`/tmp/atp_runs/{execution_id}`)
   - 支持多个测试并发执行

3. **代码更新**:
   - 执行时复制的是当前 `/tmp/atp_repos` 中的代码快照
   - 如需最新代码，需先执行 `sync_project` 任务

## 性能优化建议

1. **代码复制优化** (后续版本):
   - 考虑使用 Copy-on-Write (COW) 文件系统
   - 或使用 Docker Volume 的 snapshot 功能

2. **缓存策略** (后续版本):
   - 如果代码未变化，可重用上次的执行目录
   - 通过 Git commit hash 判断代码是否变化

3. **并行处理** (已支持):
   - Celery Worker 可配置多个并发进程
   - 每个执行独立目录，互不影响

## 文件清单

- ✅ `backend/pyproject.toml` (已包含 docker 依赖)
- ✅ `docker-compose.yml` (更新 Worker volumes)
- ✅ `backend/app/tasks/sync_project.py` (更新目录路径)
- ✅ `backend/app/tasks/test_execution.py` (实现代码复制逻辑)

## 代码审查要点

- [x] 类型提示完整
- [x] 异常处理健全
- [x] 日志记录详细
- [x] 符合 .cursorrules 规范
- [x] 使用 Path 对象操作文件路径
- [x] 中文注释清晰
