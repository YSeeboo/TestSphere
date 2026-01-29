# JWT 密钥安全配置指南

## 概述

本文档说明如何正确配置 ATP 平台的 JWT 密钥，以确保系统安全。

## 问题背景

**修复前的问题**：
- `SECRET_KEY` 有硬编码的默认值
- 如果开发者忘记设置环境变量，生产环境会使用不安全的默认密钥
- 攻击者可以伪造 JWT Token，造成严重的安全风险

## 修复方案

### 1. 配置要求

**强制要求**：
- ✅ `SECRET_KEY` 必须通过环境变量设置（不再提供默认值）
- ✅ 密钥长度必须至少 32 字符
- ✅ 系统启动时会自动检测并拒绝不安全的示例密钥
- ✅ 生产环境（`DEBUG=False`）会强制检查密钥强度

### 2. 本地开发环境配置

#### 步骤 1: 生成安全密钥

使用以下任一命令生成随机密钥：

```bash
# 方式 1: 使用 Python (推荐)
python -c "import secrets; print(secrets.token_hex(32))"

# 方式 2: 使用 OpenSSL
openssl rand -hex 32
```

示例输出：
```
5be3f4acfed5cdd5c71373923ebfae8bd98d778b75beea4344177f925c61ed1a
```

#### 步骤 2: 配置 .env 文件

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，将生成的密钥设置到 `SECRET_KEY`：

```env
# JWT 认证配置
SECRET_KEY=5be3f4acfed5cdd5c71373923ebfae8bd98d778b75beea4344177f925c61ed1a
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 步骤 3: 验证配置

启动后端服务，系统会自动验证密钥：

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

如果配置正确，您会看到：
```
INFO:     Application startup complete.
```

### 3. 生产环境配置

#### 推荐方式 1: Kubernetes Secrets

```yaml
# kubernetes/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: atp-backend-secrets
  namespace: atp
type: Opaque
stringData:
  SECRET_KEY: "your-production-secret-key-here"
```

在 Deployment 中引用：

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atp-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        image: atp-backend:latest
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: atp-backend-secrets
              key: SECRET_KEY
```

#### 推荐方式 2: Docker Secrets

```bash
# 创建密钥
echo "your-production-secret-key-here" | docker secret create atp_secret_key -

# docker-compose.yml
services:
  backend:
    image: atp-backend:latest
    secrets:
      - atp_secret_key
    environment:
      SECRET_KEY_FILE: /run/secrets/atp_secret_key

secrets:
  atp_secret_key:
    external: true
```

#### 推荐方式 3: 环境变量（云平台）

对于 AWS ECS、Azure Container Instances 等：

```bash
# 通过平台界面或 CLI 设置环境变量
aws ecs create-task-definition \
  --container-definitions '[{
    "name": "atp-backend",
    "environment": [
      {
        "name": "SECRET_KEY",
        "value": "your-production-secret-key-here"
      }
    ]
  }]'
```

### 4. 安全最佳实践

#### ✅ 应该做的

1. **密钥管理**
   - 使用专业的密钥管理服务（如 AWS Secrets Manager、HashiCorp Vault）
   - 每个环境使用不同的密钥（开发、测试、生产）
   - 定期轮换密钥（建议每 90 天）

2. **访问控制**
   - 限制能访问密钥的人员和系统
   - 使用最小权限原则
   - 记录密钥访问日志

3. **传输和存储**
   - 密钥传输时使用加密通道（HTTPS、SSH）
   - 不要在日志中输出密钥
   - 不要在错误消息中暴露密钥

#### ❌ 不应该做的

1. **永远不要**：
   - ❌ 将 `.env` 文件提交到 Git
   - ❌ 在代码中硬编码密钥
   - ❌ 通过邮件或即时消息发送密钥明文
   - ❌ 在公开渠道（如论坛、Issues）分享密钥
   - ❌ 在多个项目中重用同一个密钥

2. **避免**：
   - ⚠️ 使用简单或可预测的密钥（如 "secret123"）
   - ⚠️ 使用太短的密钥（少于 32 字符）
   - ⚠️ 在生产环境使用示例密钥

### 5. 安全检查机制

系统内置了以下安全检查：

#### 启动时检查

```python
# 自动检测以下不安全的密钥并拒绝启动
INSECURE_KEYS = {
    "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
    "your-secret-key-here",
    "secret",
    "changeme",
}
```

如果检测到不安全的密钥，系统会报错：

```
ValueError: 检测到不安全的 SECRET_KEY！
请在环境变量中设置安全的密钥。
生成新密钥的命令: python -c 'import secrets; print(secrets.token_hex(32))'
或使用 openssl: openssl rand -hex 32
```

#### 生产环境强制检查

在生产环境（`DEBUG=False`）下：
- 强制要求密钥长度 ≥ 32 字符
- 如果不满足，启动时会报错并拒绝运行

### 6. 故障排查

#### 问题 1: 启动时报错 "Field required"

**错误信息**：
```
ValidationError: 1 validation error for Settings
SECRET_KEY
  Field required
```

**原因**：未设置 `SECRET_KEY` 环境变量

**解决方案**：
1. 检查 `.env` 文件是否存在
2. 确认 `.env` 文件中有 `SECRET_KEY` 配置
3. 如果使用 Docker，确认环境变量正确传递

#### 问题 2: 报错 "检测到不安全的 SECRET_KEY"

**原因**：使用了示例密钥或常见的不安全密钥

**解决方案**：
```bash
# 生成新的安全密钥
python -c "import secrets; print(secrets.token_hex(32))"

# 更新 .env 文件中的 SECRET_KEY
```

#### 问题 3: 生产环境报错 "密钥长度不足"

**错误信息**：
```
ValueError: 生产环境的 SECRET_KEY 长度必须至少 32 字符，当前长度: 16
```

**解决方案**：
生成更长的密钥（至少 32 字符 = 64 个十六进制字符）

### 7. 密钥轮换

定期更换密钥可以降低密钥泄露的风险：

#### 轮换步骤

1. **准备新密钥**：
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **零停机轮换（推荐）**：
   - 短时间内同时支持新旧密钥
   - 逐步迁移用户 Token
   - 移除旧密钥

3. **直接轮换**：
   - 更新环境变量
   - 重启服务
   - 所有用户需要重新登录

#### 轮换脚本示例

```bash
#!/bin/bash
# rotate_secret_key.sh

# 生成新密钥
NEW_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# 更新 Kubernetes Secret
kubectl create secret generic atp-backend-secrets \
  --from-literal=SECRET_KEY=$NEW_KEY \
  --dry-run=client -o yaml | kubectl apply -f -

# 滚动更新 Deployment
kubectl rollout restart deployment/atp-backend

echo "密钥轮换完成"
```

### 8. 相关文件

修复涉及的文件：

1. **`backend/app/core/config.py`**
   - 移除硬编码的默认值
   - 添加安全验证逻辑

2. **`backend/.env.example`**
   - 添加 JWT 配置示例
   - 添加安全警告

3. **`backend/.env`**（新创建）
   - 包含生成的安全密钥
   - 已添加到 `.gitignore`

4. **`backend/README.md`**
   - 添加密钥生成说明
   - 更新环境变量表格

## 参考资料

- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

## 更新历史

- **2026-01-29**: 初始版本 - 修复硬编码 JWT 密钥安全问题
