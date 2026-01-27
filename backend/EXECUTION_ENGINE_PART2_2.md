# 执行引擎 Part 2.2 - Docker 容器化执行

## 概述
本文档记录了执行引擎 Part 2.2 的实现，包括命令构建器和 Docker 调度核心。

## Part 2.2.1 - 命令构建器

### 文件结构
```
backend/app/worker/
├── __init__.py
└── utils.py          # 命令构建工具
```

### 核心功能: `build_test_command()`

**位置**: `backend/app/worker/utils.py`

**功能**: 构建 Docker 容器内部的测试执行命令

**参数**:
- `params` (dict): 参数字典
  - `marker` (str, optional): pytest marker 标记，如 "smoke"
  - `keyword` (str, optional): pytest 关键字过滤，如 "login"

**返回**: 完整的 bash 命令字符串

**实现逻辑**:
1. 基础依赖安装命令（使用清华镜像源）
2. 构建 pytest 命令
3. 根据参数拼接 marker 和 keyword 过滤条件
4. 自动追加 `--junitxml=report.xml` 报告输出
5. 正确转义特殊字符（引号）
6. 返回完整的 `bash -c "..."` 格式命令

**示例**:
```python
# 无过滤条件
build_test_command({})
# 输出: bash -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && pytest --junitxml=report.xml"

# 带 marker
build_test_command({"marker": "smoke"})
# 输出: bash -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && pytest -m \"smoke\" --junitxml=report.xml"

# 带 keyword
build_test_command({"keyword": "login"})
# 输出: bash -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && pytest -k \"login\" --junitxml=report.xml"

# 组合条件
build_test_command({"marker": "smoke", "keyword": "login"})
# 输出: bash -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && pytest -m \"smoke\" -k \"login\" --junitxml=report.xml"
```

## Part 2.2.2 - Docker 调度核心

### 修改文件
- `backend/app/tasks/test_execution.py`

### 核心改动

#### 1. 导入依赖
```python
import docker
from app.worker.utils import build_test_command
```

#### 2. 执行流程

**原流程** (Part 2.1):
1. 获取执行记录
2. 检查代码源目录
3. 准备执行目录并复制代码
4. 更新状态为 'running'
5. 模拟测试执行 (sleep 5 秒)
6. 更新状态为 'success'

**新流程** (Part 2.2):
1. 获取执行记录
2. 检查代码源目录
3. 准备执行目录并复制代码
4. 更新状态为 'running'
5. **Docker 容器执行** ⬅️ 新增
   - 构建测试命令
   - 连接 Docker 守护进程
   - 启动容器并执行测试
   - 等待容器完成
   - 获取容器日志
   - 清理容器
6. 根据退出码更新状态 (success/failed)

#### 3. Docker 执行详情

```python
# 构建测试命令
cmd = build_test_command(execution.config)

# 连接 Docker
client = docker.from_env()

# 运行容器
container = client.containers.run(
    image="python:3.11-slim",
    command=cmd,
    volumes={str(run_path): {'bind': '/app', 'mode': 'rw'}},
    working_dir="/app",
    detach=True,
    remove=False
)

# 等待容器执行完成
result = container.wait()
exit_code = result.get('StatusCode', -1)

# 获取容器日志
logs = container.logs().decode('utf-8', errors='replace')

# 删除容器
container.remove()

# 根据退出码更新状态
if exit_code == 0:
    execution.status = "success"
else:
    execution.status = "failed"
```

#### 4. 异常处理

实现了三层异常处理：

**第一层**: 命令构建异常
```python
try:
    cmd = build_test_command(config)
except Exception as e:
    execution.status = "failed"
    execution.logs += f"构建测试命令失败: {e}"
    db.commit()
    return {"status": "failed", ...}
```

**第二层**: Docker 执行异常
```python
try:
    # Docker 执行逻辑
    ...
except docker.errors.DockerException as docker_error:
    execution.status = "failed"
    execution.logs += f"Docker 错误: {docker_error}"
    db.commit()
    # 清理容器
    if container:
        container.remove(force=True)
    return {"status": "failed", ...}
```

**第三层**: 其他执行异常
```python
except Exception as exec_error:
    execution.status = "failed"
    execution.logs += f"执行错误: {exec_error}"
    db.commit()
    # 清理容器
    if container:
        container.remove(force=True)
    return {"status": "failed", ...}
```

**外层兜底**: 任务级异常处理（原有）
```python
except Exception as e:
    # 更新执行状态为失败
    if execution:
        execution.status = "failed"
        execution.logs += f"错误: {str(e)}"
        db.commit()
    return {"status": "failed", ...}
```

#### 5. 日志记录

执行过程中详细记录：
- 配置信息
- 执行命令
- Docker 连接状态
- 容器 ID
- 容器执行进度
- 退出码
- 容器输出日志（完整）
- 执行结果（成功/失败）

日志格式示例：
```
[2026-01-27T10:30:00.000000] 开始执行测试
[2026-01-27T10:30:00.100000] 代码源: /tmp/atp_repos/1
[2026-01-27T10:30:00.200000] 执行目录: /tmp/atp_runs/123
[2026-01-27T10:30:00.300000] 配置信息:
  - Config: {'marker': 'smoke', 'keyword': 'login'}
[2026-01-27T10:30:00.400000] 执行命令: bash -c "pip install ... && pytest -m \"smoke\" -k \"login\" --junitxml=report.xml"
[2026-01-27T10:30:00.500000] Docker 连接成功
[2026-01-27T10:30:00.600000] 启动 Docker 容器...
[2026-01-27T10:30:01.000000] 容器 ID: abc123def
[2026-01-27T10:30:01.100000] 等待容器执行完成...
[2026-01-27T10:30:15.000000] 容器执行完成
[2026-01-27T10:30:15.100000] 退出码: 0

============================================================
容器输出日志:
============================================================
(pytest 输出内容...)
============================================================

[2026-01-27T10:30:15.200000] ✅ 测试执行成功
```

## 技术要点

### 1. Docker SDK 使用
- 使用 `docker.from_env()` 连接 Docker 守护进程
- 使用 `client.containers.run()` 启动容器
- 使用 `container.wait()` 等待容器完成
- 使用 `container.logs()` 获取容器输出
- 使用 `container.remove()` 清理容器

### 2. 卷挂载
```python
volumes={str(run_path): {'bind': '/app', 'mode': 'rw'}}
```
- 将宿主机的执行目录挂载到容器的 `/app` 目录
- 读写模式，允许容器生成报告文件

### 3. 命令转义
- 正确处理 shell 命令中的引号
- 使用 `\\"` 转义内部引号
- 确保命令在 bash -c 中正确执行

### 4. 容器清理
- 正常情况下使用 `container.remove()` 删除容器
- 异常情况下使用 `container.remove(force=True)` 强制删除
- 确保不会留下僵尸容器

## 依赖要求

已在 `pyproject.toml` 中包含：
```toml
[tool.poetry.dependencies]
docker = "^7.0.0"
celery = "^5.3.0"
```

## 测试验证

### 命令构建器测试
创建了 `backend/test_command_builder.py` 进行单元测试：
- ✅ 基础命令（无参数）
- ✅ 带 marker 参数
- ✅ 带 keyword 参数
- ✅ 同时带 marker 和 keyword
- ✅ 特殊字符转义

### Docker 执行测试
需要满足以下前置条件：
1. Docker 守护进程正在运行
2. 有 `python:3.11-slim` 镜像（或能拉取）
3. 执行目录包含有效的 Python 测试项目
4. 项目包含 `requirements.txt`

## 后续优化方向

1. **镜像优化**
   - 预构建包含常用依赖的自定义镜像
   - 减少每次执行时的依赖安装时间

2. **资源限制**
   - 添加 CPU 和内存限制
   - 添加执行超时控制

3. **并发控制**
   - 限制同时运行的容器数量
   - 实现任务队列优先级

4. **报告解析**
   - 解析 `report.xml` (JUnit XML)
   - 提取测试用例结果统计
   - 存储到数据库

5. **日志优化**
   - 实现日志流式输出
   - 支持实时查看执行进度

## 总结

Part 2.2 实现了完整的 Docker 容器化测试执行流程：
- ✅ 命令构建器：灵活构建 pytest 执行命令
- ✅ Docker 调度：在隔离容器中执行测试
- ✅ 异常处理：多层异常捕获，确保状态一致性
- ✅ 日志记录：详细记录执行过程和结果
- ✅ 容器清理：避免资源泄漏

执行引擎已具备生产环境运行的基础能力！
