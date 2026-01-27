# Pytest 测试用例收集与解析

## 功能概述

本模块实现了从 Git 仓库拉取代码后，自动收集 Pytest 测试用例并入库的功能。

## 实现细节

### 1. Pytest 收集命令

```bash
poetry run pytest --collect-only -q --json-report --json-report-file=report.json
```

**参数说明**:
- `--collect-only`: 只收集测试用例，不执行
- `-q`: 静默模式，减少输出
- `--json-report`: 启用 JSON 报告插件
- `--json-report-file=report.json`: 指定报告文件名

**超时设置**: 60 秒

### 2. 依赖要求

目标 Git 仓库需要满足以下条件:
1. 是一个 **Poetry 项目** (包含 `pyproject.toml` 和 `poetry.lock`)
2. 已安装 `pytest` 和 `pytest-json-report` 依赖

如果目标仓库不是 Poetry 项目，可以修改命令为:
```python
cmd = ["pytest", "--collect-only", "-q", "--json-report", f"--json-report-file={report_file.name}"]
```

### 3. JSON 报告格式

`pytest-json-report` 生成的报告格式 (示例):

```json
{
  "collectors": [
    {
      "nodeid": "tests/api/test_login.py::test_login_success",
      "doc": "测试登录成功场景",
      "markers": [
        {"name": "api", "args": [], "kwargs": {}},
        {"name": "smoke", "args": [], "kwargs": {}}
      ]
    }
  ]
}
```

**字段说明**:
- `nodeid`: Pytest 唯一标识符 (格式: `文件路径::类名::函数名`)
- `doc`: 函数的 docstring
- `markers`: Pytest 标记列表

### 4. 数据库 Upsert 逻辑

```python
# 查询: WHERE project_id = ? AND nodeid = ?
existing = db.execute(
    select(TestCase).where(
        TestCase.project_id == project_id,
        TestCase.nodeid == nodeid
    )
).scalar_one_or_none()

if existing:
    # 更新现有记录
    existing.file_path = file_path_part
    existing.name = name_part
    existing.description = description
    existing.markers = markers_json
    existing.updated_at = datetime.utcnow()
else:
    # 插入新记录
    new_test_case = TestCase(...)
    db.add(new_test_case)
```

### 5. Marker 过滤

系统会自动过滤掉 Pytest 内置 marker:
- `asyncio`
- `parametrize`
- `skipif`
- `skip`
- `xfail`
- `filterwarnings`

只保留用户自定义的 marker (如 `@pytest.mark.api`, `@pytest.mark.smoke`)。

### 6. 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| Pytest 收集超时 (>60s) | 更新项目状态为 "Failed"，返回错误信息 |
| 报告文件不存在 | 抛出 FileNotFoundError，更新状态为 "Failed" |
| JSON 解析失败 | 捕获 JSONDecodeError，更新状态为 "Failed" |
| 单个测试用例解析失败 | 记录错误日志，继续处理下一个 |

## 使用示例

```python
from app.worker.tasks import sync_project_test_cases

# 触发同步任务 (异步执行)
result = sync_project_test_cases.delay(project_id=1)

# 等待结果
task_result = result.get()
# {
#   "status": "success",
#   "message": "同步成功，共同步 15 个测试用例",
#   "test_cases_count": 15
# }
```

## 注意事项

1. **权限问题**: 确保 Celery Worker 有权限访问 Git 仓库 (私有仓库需配置 SSH Key 或 Token)
2. **磁盘空间**: Git 仓库会存储在 `/tmp/atp_repos/{project_id}/`，注意清理
3. **Poetry 依赖**: 目标仓库必须已安装 `pytest-json-report` 插件
4. **网络问题**: Git clone/pull 可能因网络问题失败，建议配置重试机制

## 后续优化

1. 支持非 Poetry 项目 (自动检测 `pyproject.toml` 是否存在)
2. 添加任务重试机制 (Celery 的 `autoretry_for`)
3. 定期清理旧的 Git 仓库缓存
4. 支持增量同步 (只更新变更的测试用例)
