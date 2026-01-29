# Worker 资源泄漏和状态管理修复

## 修复时间

2026-01-29

## 问题总结

根据 `code_review_worker.md` 的分析，Worker 任务存在以下 6 个问题：

### 🔴 P0 (严重问题)

1. **Docker 容器资源泄漏** - 容器清理逻辑不在 finally 块中
2. **容器 wait() 无超时** - 可能导致任务无限阻塞
3. **临时执行目录永久泄漏** - `/tmp/atp_runs/` 目录不断增长

### 🟡 P1 (中等风险)

4. **状态卡在 "running" 或 "Syncing"** - Worker 进程被强制 kill 后状态不更新
5. **Git 仓库目录无清理机制** - `/tmp/atp_repos/` 目录持续增长

### 🟢 P2 (低风险)

6. **Pytest JSON 报告文件泄漏** - 报告文件创建后不清理

---

## 修复详情

### ✅ 修复 1: Docker 容器资源泄漏

**修改文件**: `backend/app/tasks/test_execution.py`

**问题描述**:
容器清理代码在 try 块内部，如果 `container.wait()` 或 `container.logs()` 抛出非 Docker 异常，容器不会被清理。

**修复方案**:
1. 在函数开始处初始化 `container = None`
2. 移除 try/except 块中的容器清理代码
3. 在 finally 块中添加容器清理逻辑

**修改内容**:

```python
# 函数开始处初始化
@celery_app.task(name="worker.run_test_execution", bind=True)
def run_test_execution(self, execution_id: int) -> dict[str, Any]:
    db = SessionLocal()
    execution: TestExecution | None = None
    container = None  # ✅ 新增
    run_path: Path | None = None  # ✅ 新增

    try:
        # ... 执行逻辑 ...
        container = client.containers.run(...)
        result = container.wait(timeout=2700)
        logs = container.logs()

        # ❌ 移除：原来在这里的 container.remove()
        # 注意：容器清理已移至 finally 块，确保总是被执行

    except docker.errors.DockerException as docker_error:
        # ... 异常处理 ...
        # ❌ 移除：原来在这里的 container.remove(force=True)
        # 容器清理已移至 finally 块

    except Exception as exec_error:
        # ... 异常处理 ...
        # ❌ 移除：原来在这里的 container.remove(force=True)
        # 容器清理已移至 finally 块

    finally:
        # ✅ 新增：确保容器总是被清理
        if container:
            try:
                container.remove(force=True)
                logger.info(f"容器已清理: {container.short_id}")
            except Exception as e:
                logger.error(f"容器清理失败: {e}")

        # ✅ 新增：清理执行目录（修复 3）
        if run_path and run_path.exists():
            try:
                shutil.rmtree(run_path)
                logger.info(f"已清理执行目录: {run_path}")
            except Exception as e:
                logger.warning(f"清理执行目录失败: {e}")

        db.close()
```

**影响**:
- 无论任何异常场景，容器都会被清理
- 防止长期运行产生大量僵尸容器
- 生产环境稳定性大幅提升

---

### ✅ 修复 2: 容器 wait() 无超时限制

**修改文件**: `backend/app/tasks/test_execution.py:272`

**问题描述**:
`container.wait()` 没有设置超时参数，如果容器内进程 hang，任务会无限阻塞。Celery `task_time_limit=3600` 到期时会强制杀死 Worker 进程，finally 块不会执行。

**修复方案**:
设置超时时间为 2700 秒（45 分钟），比 Celery `soft_time_limit=3000` 稍短，确保有时间执行清理逻辑。

**修改内容**:

```python
# 修复前
result = container.wait()

# 修复后
result = container.wait(timeout=2700)  # 45 分钟
```

**影响**:
- 防止任务无限阻塞
- 确保 finally 块能正常执行
- 超时后会抛出异常，进入异常处理流程

---

### ✅ 修复 3: 临时执行目录永久泄漏

**修改文件**: `backend/app/tasks/test_execution.py:181-202`

**问题描述**:
每次执行创建 `/tmp/atp_runs/{execution_id}` 目录，执行完成后没有清理逻辑，长期运行会占满磁盘空间。

**修复方案**:
在 finally 块中添加执行目录清理逻辑（已在修复 1 中实现）。

**修改内容**:
见修复 1 的 finally 块。

**影响**:
- 执行完成后立即清理临时目录
- 防止磁盘空间被占满
- 即使任务失败也会清理

---

### ✅ 修复 4: 状态卡在 "running" 或 "Syncing"

**新增文件**: `backend/app/tasks/maintenance.py`

**问题描述**:
Worker 进程被强制 kill (OOM Killer, SIGKILL) 或系统重启时，测试执行状态会永久卡在 "running"，项目同步状态会永久卡在 "Syncing"。

**修复方案**:
创建定期维护任务 `reset_stuck_statuses`，检测并重置超时的状态。

**新增代码**:

```python
@celery_app.task(name="worker.reset_stuck_statuses")
def reset_stuck_statuses() -> dict[str, Any]:
    """
    重置卡住的状态.

    超时阈值:
    - 测试执行 (running): 3600 秒 (1 小时)
    - 项目同步 (Syncing): 600 秒 (10 分钟)
    """
    db = SessionLocal()

    try:
        # 1. 重置卡住的测试执行
        execution_timeout = datetime.now(timezone.utc) - timedelta(hours=1)

        stuck_executions = db.execute(
            select(TestExecution).where(
                TestExecution.status == "running",
                TestExecution.updated_at < execution_timeout
            )
        ).scalars().all()

        for execution in stuck_executions:
            execution.status = "failed"
            execution.logs += (
                f"\n[{datetime.now(timezone.utc).isoformat()}] "
                f"⚠️ 执行超时，自动标记为失败 (Worker 可能被强制终止)\n"
            )
            execution.updated_at = datetime.now(timezone.utc)

        # 2. 重置卡住的项目同步
        sync_timeout = datetime.now(timezone.utc) - timedelta(minutes=10)

        stuck_projects = db.execute(
            select(Project).where(
                Project.last_sync_status == "Syncing",
                or_(
                    Project.last_sync_time < sync_timeout,
                    Project.last_sync_time.is_(None)
                )
            )
        ).scalars().all()

        for project in stuck_projects:
            project.last_sync_status = "Failed"
            project.last_sync_time = datetime.now(timezone.utc)

        db.commit()

    finally:
        db.close()
```

**Celery Beat 配置**:

```python
# backend/app/core/celery_app.py
celery_app.conf.beat_schedule = {
    "reset-stuck-statuses": {
        "task": "worker.reset_stuck_statuses",
        "schedule": crontab(minute="*/5"),  # 每 5 分钟执行一次
        "options": {"expires": 240},
    },
}
```

**影响**:
- 每 5 分钟自动检查并恢复卡住的状态
- 防止状态永久不一致
- 用户体验改善，不会看到永久 "运行中" 的任务

---

### ✅ 修复 5: Git 仓库目录无清理机制

**新增文件**: `backend/app/tasks/maintenance.py`

**问题描述**:
`/tmp/atp_repos/{project_id}` 目录会持续增长，被删除的项目仍然占用磁盘空间，没有定期清理或 LRU 机制。

**修复方案**:
创建定期维护任务 `cleanup_old_repos`，清理已删除项目的仓库和长期未使用的仓库。

**新增代码**:

```python
@celery_app.task(name="worker.cleanup_old_repos")
def cleanup_old_repos(days: int = 30) -> dict[str, Any]:
    """
    清理旧的 Git 仓库目录.

    删除超过指定天数未访问的 Git 仓库目录，释放磁盘空间。
    同时清理数据库中已删除项目的仓库。

    Args:
        days: 保留天数，默认 30 天
    """
    db = SessionLocal()
    cleaned_count = 0
    freed_space = 0

    try:
        # 获取所有现存项目的 ID
        active_project_ids = {
            str(pid) for pid in
            db.execute(select(Project.id)).scalars().all()
        }

        # 遍历仓库目录
        for repo_dir in REPOS_BASE_DIR.iterdir():
            if not repo_dir.is_dir():
                continue

            project_id = repo_dir.name

            # 检查是否是已删除项目的仓库
            if project_id not in active_project_ids:
                # 计算并删除
                dir_size = sum(
                    f.stat().st_size for f in repo_dir.rglob('*')
                    if f.is_file()
                )
                freed_space += dir_size
                shutil.rmtree(repo_dir)
                cleaned_count += 1

            else:
                # 检查目录的最后访问时间
                last_access_time = datetime.fromtimestamp(
                    repo_dir.stat().st_atime, tz=timezone.utc
                )
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

                if last_access_time < cutoff_time:
                    # 计算并删除
                    dir_size = sum(
                        f.stat().st_size for f in repo_dir.rglob('*')
                        if f.is_file()
                    )
                    freed_space += dir_size
                    shutil.rmtree(repo_dir)
                    cleaned_count += 1

        freed_space_mb = freed_space / (1024 * 1024)

        return {
            "status": "success",
            "cleaned_repos": cleaned_count,
            "freed_space_mb": round(freed_space_mb, 2),
        }

    finally:
        db.close()
```

**Celery Beat 配置**:

```python
# backend/app/core/celery_app.py
celery_app.conf.beat_schedule = {
    "cleanup-old-repos": {
        "task": "worker.cleanup_old_repos",
        "schedule": crontab(hour=2, minute=0),  # 每天凌晨 2 点
        "args": (30,),  # 清理 30 天前的仓库
        "options": {"expires": 3600},
    },
}
```

**影响**:
- 自动清理已删除项目的仓库
- 自动清理 30 天未使用的仓库
- 防止磁盘空间无限增长

---

### ✅ 修复 6: Pytest JSON 报告文件泄漏

**修改文件**: `backend/app/tasks/sync_project.py`

**问题描述**:
`pytest_report.json` 文件创建后没有清理，每次同步覆盖，但如果中途失败，旧文件残留。

**修复方案**:
在 finally 块中添加报告文件清理逻辑。

**修改内容**:

```python
# 函数开始处初始化
@celery_app.task(name="worker.sync_project_test_cases", bind=True)
def sync_project_test_cases(self, project_id: int) -> dict[str, Any]:
    db = SessionLocal()
    project: Project | None = None
    report_path: Path | None = None  # ✅ 新增

    try:
        # ... 执行逻辑 ...
        report_path = repo_path / "pytest_report.json"

        # ... pytest 执行和报告解析 ...

    finally:
        # ✅ 新增：清理临时报告文件
        if report_path and report_path.exists():
            try:
                report_path.unlink()
                logger.info(f"已清理报告文件: {report_path}")
            except Exception as e:
                logger.warning(f"清理报告文件失败: {e}")

        db.close()
```

**影响**:
- 防止报告文件累积
- 同步完成后立即清理
- 即使任务失败也会清理

---

## 额外的安全网：清理遗留执行目录

**新增任务**: `cleanup_old_run_dirs`

虽然修复 3 已经在 finally 块中清理执行目录，但作为额外的安全网，我们添加了定期清理任务，处理可能因极端情况（如系统崩溃）遗留的目录。

```python
@celery_app.task(name="worker.cleanup_old_run_dirs")
def cleanup_old_run_dirs(hours: int = 24) -> dict[str, Any]:
    """
    清理旧的执行目录.

    删除超过指定小时数的执行目录。
    正常情况下，执行目录应该在 finally 块中被清理。
    """
    # ... 实现逻辑 ...
```

**Celery Beat 配置**:

```python
celery_app.conf.beat_schedule = {
    "cleanup-old-run-dirs": {
        "task": "worker.cleanup_old_run_dirs",
        "schedule": crontab(hour=3, minute=0),  # 每天凌晨 3 点
        "args": (24,),  # 清理 24 小时前的目录
        "options": {"expires": 3600},
    },
}
```

---

## 修改文件列表

### 修改的文件

1. **backend/app/tasks/test_execution.py**
   - 添加 `container` 和 `run_path` 初始化
   - 为 `container.wait()` 添加超时参数
   - 移除 try/except 块中的容器清理代码
   - 在 finally 块中添加容器和目录清理逻辑

2. **backend/app/tasks/sync_project.py**
   - 添加 `report_path` 初始化
   - 在 finally 块中添加报告文件清理逻辑

3. **backend/app/core/celery_app.py**
   - 添加 `from celery.schedules import crontab` 导入
   - 添加 `beat_schedule` 配置，定义 3 个定期维护任务

### 新增的文件

4. **backend/app/tasks/maintenance.py** (新文件)
   - `reset_stuck_statuses()` - 重置卡住的状态
   - `cleanup_old_repos()` - 清理旧的 Git 仓库
   - `cleanup_old_run_dirs()` - 清理遗留的执行目录

---

## Celery Beat 定时任务总览

启动 Celery Beat 需要运行以下命令：

```bash
celery -A app.core.celery_app beat --loglevel=info
```

已配置的定时任务：

| 任务名称 | 执行频率 | 功能 | 超时时间 |
|---------|---------|------|---------|
| reset-stuck-statuses | 每 5 分钟 | 重置超时的 running/Syncing 状态 | 4 分钟 |
| cleanup-old-repos | 每天凌晨 2 点 | 清理 30 天未使用的 Git 仓库 | 1 小时 |
| cleanup-old-run-dirs | 每天凌晨 3 点 | 清理 24 小时前的执行目录 | 1 小时 |

---

## 测试建议

### 1. 测试容器清理

```python
# 1. 模拟容器执行失败
def test_container_cleanup_on_failure():
    # 执行一个必定失败的测试
    result = run_test_execution.apply(args=[invalid_execution_id])

    # 检查容器是否被清理
    client = docker.from_env()
    containers = client.containers.list(all=True, filters={"status": "exited"})
    assert len(containers) == 0  # 应该没有遗留容器

# 2. 模拟容器超时
def test_container_timeout():
    # 执行一个会超时的测试 (容器内运行 sleep 3600)
    result = run_test_execution.apply(args=[timeout_execution_id])

    # 应该在 45 分钟后超时并清理容器
    assert result.status == "failed"
```

### 2. 测试目录清理

```bash
# 执行测试前检查目录
ls /tmp/atp_runs/

# 执行测试
curl -X POST http://localhost:8000/api/test-executions

# 执行完成后检查目录（应该被清理）
ls /tmp/atp_runs/
```

### 3. 测试状态恢复

```bash
# 1. 启动一个长时间运行的测试
# 2. 强制杀死 Worker 进程
kill -9 $(pgrep -f celery)

# 3. 等待 5 分钟，让 reset_stuck_statuses 执行
# 4. 检查数据库中执行状态是否被重置为 "failed"
```

### 4. 测试仓库清理

```bash
# 1. 创建一个测试项目并同步
# 2. 删除该项目
# 3. 手动运行清理任务
celery -A app.core.celery_app call worker.cleanup_old_repos

# 4. 检查 /tmp/atp_repos/ 目录，已删除项目的目录应该被清理
```

---

## 监控建议

### 1. 容器监控

```bash
# 定期检查僵尸容器
docker ps -a --filter "status=exited" --filter "name=atp"

# 检查容器数量
docker ps -a | grep atp | wc -l
```

### 2. 磁盘空间监控

```bash
# 检查临时目录占用
du -sh /tmp/atp_runs/
du -sh /tmp/atp_repos/

# 监控磁盘使用率
df -h /tmp
```

### 3. 任务状态监控

```sql
-- 检查长时间 running 的执行
SELECT id, status, created_at, updated_at
FROM test_executions
WHERE status = 'running'
  AND updated_at < NOW() - INTERVAL '1 hour';

-- 检查长时间 Syncing 的项目
SELECT id, name, last_sync_status, last_sync_time
FROM projects
WHERE last_sync_status = 'Syncing'
  AND last_sync_time < NOW() - INTERVAL '10 minutes';
```

---

## 部署步骤

### 1. 更新代码

```bash
git pull origin main
```

### 2. 重启 Celery Worker

```bash
# 停止现有 Worker
pkill -f "celery.*worker"

# 启动新 Worker
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

### 3. 启动 Celery Beat

```bash
# 如果之前没有运行 Beat
celery -A app.core.celery_app beat --loglevel=info

# 或使用 systemd (推荐)
sudo systemctl start celery-beat
```

### 4. 验证定时任务

```bash
# 检查 Beat 日志
tail -f /var/log/celery/beat.log

# 应该看到以下任务被调度
# [2026-01-29 00:00:00] Scheduler: Sending due task reset-stuck-statuses
# [2026-01-29 02:00:00] Scheduler: Sending due task cleanup-old-repos
# [2026-01-29 03:00:00] Scheduler: Sending due task cleanup-old-run-dirs
```

---

## 回滚计划

如果修复导致问题，可以回滚到之前的版本：

```bash
# 1. 回滚代码
git revert <commit_hash>

# 2. 重启服务
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

**注意**：回滚后仍需要手动清理可能遗留的容器和目录：

```bash
# 清理容器
docker rm -f $(docker ps -aq --filter "name=atp")

# 清理目录
rm -rf /tmp/atp_runs/*
rm -rf /tmp/atp_repos/*  # 注意：会删除所有仓库，需要重新同步
```

---

## 总结

本次修复解决了 Worker 任务中的所有 6 个资源泄漏和状态管理问题：

### ✅ 已修复

- **P0 (严重)**：Docker 容器泄漏、容器超时、临时目录泄漏
- **P1 (中等)**：状态卡住、Git 仓库泄漏
- **P2 (低风险)**：报告文件泄漏

### 🎯 修复效果

- **资源管理**：所有临时资源（容器、目录、文件）都在 finally 块中确保清理
- **超时控制**：容器执行有明确的超时限制，防止无限阻塞
- **状态恢复**：定期任务自动检测并恢复异常状态
- **空间优化**：定期清理旧资源，防止磁盘占满

### 📊 预期改进

- **稳定性**：消除资源泄漏导致的生产环境故障
- **可靠性**：状态永久卡住的问题不再发生
- **可维护性**：磁盘空间自动管理，减少人工干预

---

**修复完成时间**：2026-01-29
**修复人员**：Claude Sonnet 4.5
