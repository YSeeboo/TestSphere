# Docker 执行引擎使用指南

## 快速开始

### 前置条件

1. **Docker 守护进程运行中**
   ```bash
   # 检查 Docker 是否运行
   docker ps
   
   # 如果未运行，启动 Docker Desktop 或 Docker 服务
   ```

2. **Python 镜像准备**
   ```bash
   # 预拉取镜像（可选，首次运行会自动拉取）
   docker pull python:3.11-slim
   ```

3. **依赖安装**
   ```bash
   cd backend
   poetry install
   ```

## 测试验证

### 1. 测试命令构建器

```bash
cd backend
python test_command_builder.py
```

预期输出：
```
============================================================
测试命令构建器
============================================================

基础命令:
bash -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && pytest --junitxml=report.xml"

带 marker 的命令:
bash -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && pytest -m \"smoke\" --junitxml=report.xml"

...

============================================================
✅ 所有测试通过！
============================================================
```

### 2. 测试 Docker 集成

```bash
cd backend
python test_docker_integration.py
```

预期输出：
```
============================================================
Docker 集成测试套件
============================================================

测试 1: Docker 连接
============================================================
✅ Docker 连接成功
Docker 版本: 24.0.x
API 版本: 1.43

测试 2: 简单容器运行
============================================================
启动测试容器 (python:3.11-slim)...
容器 ID: abc123
等待容器执行完成...
退出码: 0

容器输出:
------------------------------------------------------------
Python 3.11.x
Hello from Docker!
------------------------------------------------------------
✅ 容器已清理

...

============================================================
测试结果汇总
============================================================
Docker 连接          ✅ 通过
简单容器运行         ✅ 通过
命令构建器集成       ✅ 通过
卷挂载功能          ✅ 通过
============================================================
🎉 所有测试通过！Docker 集成正常工作
============================================================
```

## 使用示例

### 通过 API 触发测试执行

1. **创建测试执行记录**

```bash
curl -X POST "http://localhost:8000/api/v1/test-executions/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "trigger_type": "manual",
    "config": {
      "marker": "smoke",
      "keyword": "login"
    }
  }'
```

响应：
```json
{
  "id": 123,
  "project_id": 1,
  "status": "pending",
  "trigger_type": "manual",
  "config": {
    "marker": "smoke",
    "keyword": "login"
  },
  "logs": null,
  "created_at": "2026-01-27T10:00:00",
  "updated_at": "2026-01-27T10:00:00"
}
```

2. **Celery 自动执行**

Celery worker 会自动接收任务并执行：
- 复制代码到执行目录
- 构建测试命令
- 启动 Docker 容器
- 执行测试
- 收集日志和结果
- 更新数据库状态

3. **查询执行结果**

```bash
curl -X GET "http://localhost:8000/api/v1/test-executions/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应：
```json
{
  "id": 123,
  "project_id": 1,
  "status": "success",
  "trigger_type": "manual",
  "config": {
    "marker": "smoke",
    "keyword": "login"
  },
  "logs": "[2026-01-27T10:00:00] 开始执行测试\n[2026-01-27T10:00:01] Docker 连接成功\n...",
  "created_at": "2026-01-27T10:00:00",
  "updated_at": "2026-01-27T10:00:15"
}
```

## 配置参数说明

### `config` 字段

执行配置是一个 JSON 对象，支持以下参数：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `marker` | string | 否 | pytest marker 表达式 | `"smoke"`, `"regression"`, `"smoke and not slow"` |
| `keyword` | string | 否 | pytest 关键字过滤 | `"login"`, `"test_user"` |

### 配置示例

**运行所有测试**:
```json
{
  "config": {}
}
```

**运行 smoke 测试**:
```json
{
  "config": {
    "marker": "smoke"
  }
}
```

**运行包含 login 的测试**:
```json
{
  "config": {
    "keyword": "login"
  }
}
```

**组合条件**:
```json
{
  "config": {
    "marker": "smoke and not slow",
    "keyword": "user or auth"
  }
}
```

## 执行状态说明

| 状态 | 说明 |
|------|------|
| `pending` | 等待执行 |
| `running` | 正在执行 |
| `success` | 执行成功（退出码 0）|
| `failed` | 执行失败（退出码非 0 或异常）|

## 日志格式

执行日志包含以下信息：

```
[时间戳] 开始执行测试
[时间戳] 代码源: /tmp/atp_repos/1
[时间戳] 执行目录: /tmp/atp_runs/123
[时间戳] 配置信息:
  - Config: {'marker': 'smoke'}
[时间戳] 执行命令: bash -c "..."
[时间戳] Docker 连接成功
[时间戳] 启动 Docker 容器...
[时间戳] 容器 ID: abc123
[时间戳] 等待容器执行完成...
[时间戳] 容器执行完成
[时间戳] 退出码: 0

============================================================
容器输出日志:
============================================================
(pytest 执行输出...)
============================================================

[时间戳] ✅ 测试执行成功
```

## 故障排查

### 问题 1: Docker 连接失败

**错误信息**:
```
Docker 执行错误: Error while fetching server API version
```

**解决方案**:
1. 检查 Docker 是否运行: `docker ps`
2. 检查 Docker socket 权限: `ls -l /var/run/docker.sock`
3. 将当前用户添加到 docker 组: `sudo usermod -aG docker $USER`

### 问题 2: 镜像拉取失败

**错误信息**:
```
Docker 执行错误: Unable to find image 'python:3.11-slim' locally
```

**解决方案**:
1. 手动拉取镜像: `docker pull python:3.11-slim`
2. 检查网络连接
3. 配置 Docker 镜像加速器

### 问题 3: 卷挂载权限问题

**错误信息**:
```
Permission denied: '/app/requirements.txt'
```

**解决方案**:
1. 检查执行目录权限: `ls -la /tmp/atp_runs/`
2. 确保目录可读写: `chmod -R 755 /tmp/atp_runs/`

### 问题 4: 容器内依赖安装失败

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement ...
```

**解决方案**:
1. 检查项目的 `requirements.txt` 是否存在
2. 检查依赖版本是否正确
3. 检查网络连接（容器内需要访问 PyPI）

## 性能优化建议

### 1. 使用自定义镜像

创建包含常用依赖的自定义镜像，减少每次安装时间：

```dockerfile
# Dockerfile.test
FROM python:3.11-slim

# 安装常用依赖
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pytest pytest-json-report pytest-html requests

WORKDIR /app
```

构建镜像：
```bash
docker build -t atp-test:latest -f Dockerfile.test .
```

修改任务代码使用自定义镜像：
```python
container = client.containers.run(
    image="atp-test:latest",  # 使用自定义镜像
    ...
)
```

### 2. 添加资源限制

防止测试占用过多资源：

```python
container = client.containers.run(
    image="python:3.11-slim",
    command=cmd,
    volumes={str(run_path): {'bind': '/app', 'mode': 'rw'}},
    working_dir="/app",
    detach=True,
    remove=False,
    # 资源限制
    mem_limit="512m",      # 内存限制 512MB
    cpu_quota=50000,       # CPU 限制 50%
    cpu_period=100000
)
```

### 3. 添加超时控制

防止测试执行时间过长：

```python
import signal

# 设置超时（例如 30 分钟）
timeout_seconds = 1800

def timeout_handler(signum, frame):
    raise TimeoutError("测试执行超时")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(timeout_seconds)

try:
    result = container.wait()
finally:
    signal.alarm(0)  # 取消超时
```

## 下一步

1. **报告解析**: 解析 `report.xml` 文件，提取测试结果
2. **实时日志**: 实现日志流式输出，支持实时查看
3. **并发控制**: 限制同时运行的容器数量
4. **资源监控**: 监控容器资源使用情况
5. **失败重试**: 实现测试失败自动重试机制

## 相关文档

- [EXECUTION_ENGINE_PART2_2.md](./EXECUTION_ENGINE_PART2_2.md) - 技术实现详情
- [TEST_EXECUTION_PART1.md](./TEST_EXECUTION_PART1.md) - Part 1 实现
- [CELERY_SETUP.md](./CELERY_SETUP.md) - Celery 配置指南
- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Docker 环境配置
