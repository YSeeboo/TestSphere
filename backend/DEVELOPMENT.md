# ATP Backend 开发指南

本文档介绍 ATP Backend 的开发环境配置、依赖管理和常见问题解决方案。

## 目录

- [开发环境架构](#开发环境架构)
- [快速开始](#快速开始)
- [依赖管理](#依赖管理)
- [开发工作流](#开发工作流)
- [生产环境部署](#生产环境部署)
- [常见问题](#常见问题)

## 开发环境架构

ATP Backend 采用**开发/生产环境分离**的 Docker 配置策略：

### 开发环境特性

- **Dockerfile**: `Dockerfile.dev`
- **启动脚本**: `dev-entrypoint.sh`
- **特点**:
  - ✅ 代码通过 Volume 挂载，支持热重载
  - ✅ 自动检测依赖变化并安装
  - ✅ 无需手动重建镜像
  - ✅ 快速迭代开发

### 生产环境特性

- **Dockerfile**: `Dockerfile`
- **Docker Compose**: `docker-compose.prod.yml`
- **特点**:
  - ✅ 依赖固定在镜像中
  - ✅ 无 Volume 挂载，代码打包在镜像内
  - ✅ 多进程部署（uvicorn workers, celery concurrency）
  - ✅ 自动重启策略

## 快速开始

### 1. 首次启动

```bash
# 在项目根目录下
docker-compose up

# 或后台运行
docker-compose up -d
```

首次启动时，容器会自动：
1. 检测 `pyproject.toml` 和 `poetry.lock`
2. 安装所有 Python 依赖
3. 启动 uvicorn 开发服务器（带热重载）

### 2. 查看日志

```bash
# 查看 backend 日志
docker-compose logs -f backend

# 查看 worker 日志
docker-compose logs -f worker
```

### 3. 停止服务

```bash
docker-compose down
```

## 依赖管理

### 添加新依赖

#### 方法 1: 使用 poetry add（推荐）

```bash
# 在宿主机上（需要安装 Poetry）
cd backend
poetry add <package-name>

# 重启容器，自动安装新依赖
docker-compose restart backend
```

#### 方法 2: 手动编辑 pyproject.toml

```bash
# 1. 编辑 backend/pyproject.toml，添加依赖
vim backend/pyproject.toml

# 2. 重启容器，自动检测并安装
docker-compose restart backend
```

### 依赖同步原理

开发环境的智能启动脚本 (`dev-entrypoint.sh`) 会：

1. 计算 `pyproject.toml` 和 `poetry.lock` 的哈希值
2. 与上次启动时的哈希值对比
3. 如果发现变化，自动执行 `poetry install`
4. 保存新的哈希值，避免重复安装

**示例输出**：

```
==========================================
ATP Backend Development Environment
==========================================
检测到依赖文件变化，需要重新安装依赖...
  - pyproject.toml 或 poetry.lock 已更新

==========================================
安装 Python 依赖...
==========================================
执行 poetry install...
Installing dependencies from lock file
...
✓ 依赖安装完成
```

### 更新依赖版本

```bash
# 更新所有依赖到最新兼容版本
cd backend
poetry update

# 更新特定依赖
poetry update <package-name>

# 重启容器
docker-compose restart backend
```

## 开发工作流

### 日常开发

1. **启动开发环境**
   ```bash
   docker-compose up -d
   ```

2. **编写代码**
   - 代码变化会自动触发热重载
   - 无需重启容器

3. **添加新依赖**
   ```bash
   cd backend
   poetry add <package>
   docker-compose restart backend
   ```

4. **查看日志**
   ```bash
   docker-compose logs -f backend
   ```

### 数据库迁移

```bash
# 生成迁移文件
docker-compose exec backend poetry run alembic revision --autogenerate -m "描述"

# 执行迁移
docker-compose exec backend poetry run alembic upgrade head

# 回滚迁移
docker-compose exec backend poetry run alembic downgrade -1
```

### 进入容器调试

```bash
# 进入 backend 容器
docker-compose exec backend bash

# 进入 worker 容器
docker-compose exec worker bash

# 在容器内执行 Python
docker-compose exec backend poetry run python
```

### 运行测试

```bash
# 在容器内运行测试
docker-compose exec backend poetry run pytest

# 运行特定测试文件
docker-compose exec backend poetry run pytest tests/test_auth.py

# 运行带覆盖率的测试
docker-compose exec backend poetry run pytest --cov=app tests/
```

## 生产环境部署

### 构建生产镜像

```bash
# 构建镜像
docker-compose -f docker-compose.prod.yml build

# 查看镜像
docker images | grep atp
```

### 启动生产环境

```bash
# 设置生产环境密码（推荐）
export POSTGRES_PASSWORD=your_secure_password

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps
```

### 生产环境与开发环境的区别

| 特性 | 开发环境 | 生产环境 |
|------|---------|---------|
| Dockerfile | `Dockerfile.dev` | `Dockerfile` |
| Volume 挂载 | ✅ 代码挂载 | ❌ 代码打包在镜像 |
| 热重载 | ✅ 启用 | ❌ 禁用 |
| 依赖安装 | 启动时自动检测 | 构建时固定 |
| Uvicorn Workers | 1 (单进程) | 4 (多进程) |
| Celery Concurrency | 默认 | 4 |
| 重启策略 | 无 | `unless-stopped` |

## 常见问题

### Q1: ModuleNotFoundError: No module named 'xxx'

**原因**: 添加了新依赖但容器未安装。

**解决方案**:
```bash
# 方法 1: 重启容器（推荐）
docker-compose restart backend

# 方法 2: 手动安装
docker-compose exec backend poetry install

# 方法 3: 重建容器
docker-compose up -d --force-recreate backend
```

### Q2: 依赖安装很慢

**原因**: 网络问题或首次安装依赖较多。

**解决方案**:
- 已配置阿里云镜像源，通常速度较快
- 首次安装需要时间，后续启动会很快
- 可以查看安装进度：`docker-compose logs -f backend`

### Q3: 容器启动失败

**排查步骤**:

1. 查看日志
   ```bash
   docker-compose logs backend
   ```

2. 检查端口占用
   ```bash
   lsof -i :8000
   ```

3. 检查依赖文件
   ```bash
   ls -la backend/pyproject.toml backend/poetry.lock
   ```

4. 重建容器
   ```bash
   docker-compose down
   docker-compose up --build
   ```

### Q4: 热重载不工作

**原因**: Volume 挂载配置问题。

**检查**:
```bash
# 确认 docker-compose.yml 中有正确的 volume 配置
grep -A 2 "volumes:" docker-compose.yml

# 应该看到:
# volumes:
#   - ./backend:/app
```

### Q5: 如何清理所有数据重新开始

```bash
# 停止并删除所有容器、网络、卷
docker-compose down -v

# 删除镜像（可选）
docker-compose down --rmi all -v

# 重新启动
docker-compose up -d
```

### Q6: Worker 容器无法访问 Docker

**原因**: Docker socket 未正确挂载。

**检查**:
```bash
# 确认 docker-compose.yml 中 worker 服务有以下配置
grep -A 5 "worker:" docker-compose.yml | grep docker.sock

# 应该看到:
# - /var/run/docker.sock:/var/run/docker.sock
```

### Q7: 生产环境如何更新代码

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose -f docker-compose.prod.yml build

# 3. 重启服务（滚动更新）
docker-compose -f docker-compose.prod.yml up -d

# 4. 查看状态
docker-compose -f docker-compose.prod.yml ps
```

## 性能优化建议

### 开发环境

1. **使用 .dockerignore**
   - 避免将不必要的文件复制到容器
   - 减少 Volume 挂载的文件数量

2. **定期清理**
   ```bash
   # 清理未使用的镜像
   docker image prune -a
   
   # 清理未使用的卷
   docker volume prune
   ```

### 生产环境

1. **使用多阶段构建**（未来优化）
2. **启用 Gunicorn + Uvicorn Workers**（已配置）
3. **配置 Celery 并发数**（已配置为 4）
4. **使用 Redis 缓存**（已集成）

## 故障排查

### 依赖安装失败

**症状**: 容器启动时报错 `ModuleNotFoundError: No module named 'xxx'`

**原因**: 
- 依赖未正确安装
- 哈希文件失效导致跳过安装
- 网络问题导致安装中断

**解决方案**:

#### 方法 1: 强制重新安装依赖（推荐）

```bash
# 设置环境变量强制安装
FORCE_INSTALL_DEPS=true docker-compose up -d backend

# 或者在 .env 文件中添加
echo "FORCE_INSTALL_DEPS=true" >> .env
docker-compose up -d backend

# 安装成功后记得移除环境变量
sed -i '' '/FORCE_INSTALL_DEPS/d' .env  # macOS
# 或
sed -i '/FORCE_INSTALL_DEPS/d' .env     # Linux
```

#### 方法 2: 手动进入容器安装

```bash
# 1. 启动容器（即使失败也会保留）
docker-compose up -d

# 2. 进入容器
docker-compose exec backend bash

# 3. 手动安装依赖
poetry install --no-interaction --no-ansi --no-root

# 4. 验证关键包
poetry show docker celery fastapi

# 5. 退出并重启
exit
docker-compose restart backend
```

#### 方法 3: 清理并重建

```bash
# 完全清理（会删除所有数据）
docker-compose down -v

# 删除哈希文件
rm -f backend/.deps_hash

# 重新启动
docker-compose up -d
```

### Cursor 调试最佳实践

在使用 Cursor 进行 Docker 调试时，为避免卡死问题：

#### 1. 使用分离模式启动

```bash
# 使用 -d 后台运行，避免阻塞终端
docker-compose up -d

# 然后查看日志
docker-compose logs -f backend
```

#### 2. 分步骤操作

```bash
# 不要一次性执行多个命令，分步进行：

# 步骤 1: 停止服务
docker-compose stop backend

# 步骤 2: 修改代码或配置
# ... 进行修改 ...

# 步骤 3: 启动服务
docker-compose start backend

# 步骤 4: 查看日志
docker-compose logs -f backend
```

#### 3. 使用调试模式

```bash
# 启用详细日志输出
DEBUG=true docker-compose up backend
```

#### 4. 监控容器状态

```bash
# 在另一个终端窗口实时监控
watch -n 2 'docker-compose ps'
```

#### 5. 快速重启技巧

```bash
# 只重启 backend，不影响数据库
docker-compose restart backend

# 查看最近 50 行日志
docker-compose logs --tail=50 backend
```

### 依赖更新工作流

#### 添加新依赖

```bash
# 方法 1: 在宿主机上（需要安装 Poetry）
cd backend
poetry add <package-name>

# 方法 2: 在容器中添加
docker-compose exec backend poetry add <package-name>

# 重启容器自动安装
docker-compose restart backend
```

#### 更新现有依赖

```bash
# 更新所有依赖
docker-compose exec backend poetry update

# 更新特定依赖
docker-compose exec backend poetry update <package-name>

# 重启容器
docker-compose restart backend
```

### 性能优化建议

#### 1. 持久化 Poetry 缓存

已在 `docker-compose.yml` 中配置：

```yaml
volumes:
  - backend_poetry_cache:/root/.cache/pypoetry
```

这样可以：
- 避免重复下载依赖包
- 加快容器重启速度
- 减少网络流量

#### 2. 使用国内镜像源

已在 `Dockerfile.dev` 中配置：

```dockerfile
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
```

#### 3. 定期清理

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的卷（谨慎使用）
docker volume prune
```

## 相关文档

- [Poetry 官方文档](https://python-poetry.org/docs/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [Celery 官方文档](https://docs.celeryq.dev/)

## 技术支持

如遇到问题，请：

1. 查看本文档的**故障排查**部分
2. 查看容器日志：`docker-compose logs -f backend`
3. 启用调试模式：`DEBUG=true docker-compose up backend`
4. 检查 GitHub Issues
5. 联系开发团队

---

**最后更新**: 2026-01-27
