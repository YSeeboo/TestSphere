## 🔍 Code Review 结果：潜在 Bug 和资源泄漏风险

---

### 🚨 **严重问题**

#### **1. Docker 容器资源泄漏** (`test_execution.py`)

**位置**：第 243-352 行

**问题**：容器清理逻辑不在 `finally` 块中，多种异常场景会导致容器泄漏：

```python
# 当前代码
try:
    container = client.containers.run(...)
    result = container.wait()  # 如果这里抛异常
    logs = container.logs()     # 或者这里抛异常

    # 清理在 try 块内部
    container.remove()
except docker.errors.DockerException:
    # 有清理尝试
    if container:
        container.remove(force=True)
except Exception:
    # 有清理尝试
    if container:
        container.remove(force=True)
```

**风险场景**：

- `container.wait()` 或 `container.logs()` 抛出非 Docker 异常
- 内存溢出、系统信号中断等系统级错误
- 长期运行会产生大量僵尸容器

**修复建议**：

```python
container = None
try:
    container = client.containers.run(...)
    result = container.wait()
    logs = container.logs()
    # ... 处理逻辑 ...
except Exception as e:
    # 异常处理
    pass
finally:
    # 确保容器总是被清理
    if container:
        try:
            container.remove(force=True)
            logger.info(f"容器已清理: {container.short_id}")
        except Exception as e:
            logger.error(f"容器清理失败: {e}")
```

---

#### **2. 容器 `wait()` 无超时限制** (`test_execution.py`)

**位置**：第 272 行

```272:272:backend/app/tasks/test_execution.py
result = container.wait()
```

**问题**：

- `wait()` 没有设置超时参数，容器内进程 hang 会导致任务无限阻塞
- Celery `task_time_limit=3600` 到期时会强制杀死 Worker 进程，`finally` 块不会执行
- 容器不会被清理，状态卡在 "running"

**修复建议**：

```python
# 设置超时（比 Celery soft_time_limit 稍短）
result = container.wait(timeout=2700)  # 45 分钟
```

---

#### **3. 临时执行目录永久泄漏** (`test_execution.py`)

**位置**：第 181-202 行

```181:202:backend/app/tasks/test_execution.py
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

**问题**：

- 每次执行创建 `/tmp/atp_runs/{execution_id}` 目录
- 执行完成后没有清理逻辑
- 长期运行会占满磁盘空间

**修复建议**：

```python
finally:
    # 清理执行目录
    if run_path and run_path.exists():
        try:
            shutil.rmtree(run_path)
            logger.info(f"已清理执行目录: {run_path}")
        except Exception as e:
            logger.warning(f"清理执行目录失败: {e}")

    db.close()
```

---

### ⚠️ **中等风险问题**

#### **4. Git 仓库目录无清理机制** (`sync_project.py`)

**位置**：第 82-119 行

```82:119:backend/app/tasks/sync_project.py
repo_path = REPOS_ROOT / str(project_id)

# 确保根目录存在
REPOS_ROOT.mkdir(parents=True, exist_ok=True)

logger.info(f"Git 仓库路径: {repo_path}")

if repo_path.exists():
    # 目录存在，执行 pull 操作
    logger.info(f"仓库已存在，执行 git pull")
    try:
        repo = git.Repo(repo_path)
        origin = repo.remotes.origin

        # 切换到指定分支
        if project.git_branch:
            logger.info(f"切换到分支: {project.git_branch}")
            repo.git.checkout(project.git_branch)

        # 拉取最新代码
        origin.pull()
        logger.info("Git pull 成功")
    except git.GitCommandError as e:
        logger.error(f"Git pull 失败: {e}")
        raise Exception(f"Git pull 失败: {e}")
else:
    # 目录不存在，执行 clone 操作
    logger.info(f"仓库不存在，执行 git clone")
    try:
        repo = git.Repo.clone_from(
            project.git_url,
            repo_path,
            branch=project.git_branch or "main",
        )
        logger.info("Git clone 成功")
    except git.GitCommandError as e:
        logger.error(f"Git clone 失败: {e}")
        raise Exception(f"Git clone 失败: {e}")
```

**问题**：

- `/tmp/atp_repos/{project_id}` 目录会持续增长
- 被删除的项目仍然占用磁盘空间
- 没有定期清理或 LRU 机制

**建议**：

- 添加定时清理任务（删除 N 天未访问的仓库）
- 或在项目删除时清理对应目录

---

#### **5. Pytest JSON 报告文件泄漏** (`sync_project.py`)

**位置**：第 125 行

```125:125:backend/app/tasks/sync_project.py
report_path = repo_path / "pytest_report.json"
```

**问题**：

- 报告文件创建后没有清理
- 每次同步覆盖，但如果中途失败，旧文件残留

**修复建议**：

```python
finally:
    # 清理临时文件
    if report_path and report_path.exists():
        try:
            report_path.unlink()
        except Exception as e:
            logger.warning(f"清理报告文件失败: {e}")

    db.close()
```

---

#### **6. 状态卡在 "running" 或 "Syncing"**

**test_execution.py** (第 206 行)：

```206:211:backend/app/tasks/test_execution.py
logger.info(f"更新测试执行 {execution_id} 状态为 running")
execution.status = "running"
execution.logs = f"[{datetime.utcnow().isoformat()}] 开始执行测试\n"
execution.logs += f"[{datetime.utcnow().isoformat()}] 代码源: {repo_path}\n"
execution.logs += f"[{datetime.utcnow().isoformat()}] 执行目录: {run_path}\n"
execution.updated_at = datetime.utcnow()
```

**sync_project.py** (第 78 行)：

```78:79:backend/app/tasks/sync_project.py
project.last_sync_status = "Syncing"
db.commit()
```

**风险场景**：

- Worker 进程被强制 kill (OOM Killer, SIGKILL)
- 系统重启、服务器崩溃
- Celery 配置错误导致任务丢失

**现状**：虽然有最外层 try-except，但系统级错误会绕过 Python 异常处理

**建议**：

- 添加定时任务，检测并重置超时的 "running"/"Syncing" 状态
- 或使用 Celery 的 `after_return` 信号确保状态更新

---

### ✅ **无问题的部分**

1. **数据库 Session 使用正确**：
   - 使用同步 `SessionLocal()`，与 Celery 同步任务匹配
   - 在 `finally` 块中正确关闭 Session

2. **异常处理覆盖全面**：
   - Git 操作、Docker 操作、Pytest 执行都有 try-except
   - 最外层有兜底异常处理

3. **无异步/同步混用问题**：
   - 所有代码都是同步的，没有错误调用 `await`

---

### 📋 **优先级修复建议**

| 优先级 | 问题               | 影响         | 修复难度 |
| ------ | ------------------ | ------------ | -------- |
| 🔴 P0  | Docker 容器泄漏    | 生产环境故障 | 低       |
| 🔴 P0  | 容器 wait() 无超时 | 任务卡死     | 低       |
| 🔴 P0  | 临时目录泄漏       | 磁盘占满     | 低       |
| 🟡 P1  | 状态卡在 "running" | 数据不一致   | 中       |
| 🟡 P1  | Git 仓库目录泄漏   | 磁盘占满     | 中       |
| 🟢 P2  | JSON 报告文件泄漏  | 磁盘空间浪费 | 低       |
