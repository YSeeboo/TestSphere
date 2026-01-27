# Docker 配置说明

## 问题：Docker Hub 连接超时

如果遇到 `dial tcp ... i/o timeout` 错误，说明无法连接到 Docker Hub。

## 解决方案

### 1. 配置 Docker 镜像加速器（推荐）

#### macOS

1. 打开 Docker Desktop
2. 点击右上角齿轮图标 -> Settings
3. 选择 Docker Engine
4. 在 JSON 配置中添加：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

5. 点击 "Apply & Restart"

#### Linux

创建或编辑 `/etc/docker/daemon.json`:

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 2. 验证配置

```bash
docker info | grep -A 5 "Registry Mirrors"
```

应该显示配置的镜像源。

### 3. 重新构建

```bash
# 清理旧的构建缓存
docker-compose down
docker system prune -f

# 重新构建
docker-compose up -d --build
```

## 方案 2: 本地开发（不使用 Docker）

如果 Docker 网络问题无法解决，可以直接在本地运行：

### 1. 启动数据库和 Redis

```bash
# 只启动基础服务
docker-compose up -d postgres redis
```

### 2. 本地运行 Backend

```bash
cd backend

# 安装依赖
poetry install

# 运行数据库迁移
poetry run alembic upgrade head

# 启动 FastAPI
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 本地运行 Celery Worker

在另一个终端：

```bash
cd backend

# 启动 Worker
poetry run celery -A app.core.celery_app worker --loglevel=info
```

## 方案 3: 使用已有镜像

如果已经拉取过 `python:3.11-slim` 镜像：

```bash
# 查看本地镜像
docker images | grep python

# 如果存在，直接构建
docker-compose build --no-cache worker
docker-compose up -d worker
```

## 常见问题

### Q: 镜像加速器配置后仍然超时？

A: 尝试以下方法：
1. 检查网络代理设置
2. 尝试其他镜像源
3. 使用本地开发模式（方案 2）

### Q: 如何查看构建日志？

```bash
docker-compose build worker
docker-compose logs -f worker
```

### Q: 如何完全重新构建？

```bash
docker-compose down -v
docker system prune -a -f
docker-compose up -d --build
```
