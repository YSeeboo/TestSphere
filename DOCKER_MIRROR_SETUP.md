# Docker 镜像源配置指南 (macOS)

## 问题描述
Docker 无法从 Docker Hub 拉取镜像，出现超时错误：
```
failed to fetch anonymous token: Get "https://auth.docker.io/token?...": dial tcp [...]:443: i/o timeout
```

## 解决方案

### 方案 1: 配置 Docker Desktop 镜像加速器（推荐）

1. **打开 Docker Desktop**
   - 点击菜单栏的 Docker 图标
   - 选择 "Settings" (设置)

2. **配置镜像源**
   - 点击左侧 "Docker Engine"
   - 在 JSON 配置中添加以下内容：

```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

3. **应用并重启**
   - 点击 "Apply & Restart" 按钮
   - 等待 Docker 重启完成

4. **验证配置**
```bash
docker info | grep -A 5 "Registry Mirrors"
```

### 方案 2: 使用国内镜像仓库（已在 Dockerfile 中配置）

Dockerfile 已更新为使用阿里云镜像仓库作为备选方案。

### 方案 3: 手动拉取镜像

如果配置镜像源后仍有问题，可以尝试手动拉取：

```bash
# 清理 Docker 缓存
docker system prune -f

# 手动拉取基础镜像
docker pull python:3.11-slim
docker pull postgres:15-alpine
docker pull redis:7-alpine

# 然后再启动服务
docker-compose up -d
```

## 常用国内 Docker 镜像源

| 镜像源 | 地址 | 说明 |
|--------|------|------|
| 中科大 | https://docker.mirrors.ustc.edu.cn | 稳定性好 |
| 网易 | https://hub-mirror.c.163.com | 速度快 |
| 百度云 | https://mirror.baidubce.com | 可靠 |
| 阿里云 | https://registry.cn-hangzhou.aliyuncs.com | 需要登录 |

## 验证步骤

1. **检查 Docker 是否运行**
```bash
docker ps
```

2. **测试镜像拉取**
```bash
docker pull python:3.11-slim
```

3. **启动项目**
```bash
cd /Users/ycb/workspace/apt_platform
docker-compose up -d
```

4. **查看日志**
```bash
docker-compose logs -f backend
```

## 故障排除

### 如果镜像源配置后仍然超时

1. **检查网络连接**
```bash
ping docker.mirrors.ustc.edu.cn
```

2. **尝试其他镜像源**
   - 在 Docker Desktop 设置中更换不同的镜像源
   - 或者使用阿里云容器镜像服务（需要注册账号）

3. **使用代理**
   如果有 VPN 或代理，可以在 Docker Desktop 中配置：
   - Settings → Resources → Proxies
   - 配置 HTTP/HTTPS 代理

### 如果 Docker Desktop 无法启动

```bash
# 重置 Docker Desktop
# 注意：这会清除所有容器和镜像
rm -rf ~/Library/Containers/com.docker.docker
rm -rf ~/.docker

# 重新启动 Docker Desktop
```

## 下一步

配置完成后，运行：
```bash
docker-compose up -d
```

如果遇到其他问题，请查看：
- `docker-compose logs` - 查看所有服务日志
- `docker-compose ps` - 查看服务状态
