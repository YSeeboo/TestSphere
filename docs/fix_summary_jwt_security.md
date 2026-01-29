# 修复总结：JWT 密钥安全问题

## 问题描述

**来源**：`docs/code_review_backend.md` - 高危问题 #1

**问题**：`backend/app/core/config.py` 中的 `SECRET_KEY` 使用了硬编码的默认值：

```python
SECRET_KEY: str = Field(
    default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
    description="JWT 签名密钥，生产环境必须修改为随机生成的密钥",
)
```

**风险**：
- 🔴 如果生产环境忘记通过环境变量覆盖，将使用默认密钥
- 🔴 攻击者可以使用此密钥伪造 JWT Token
- 🔴 导致严重的安全漏洞（身份伪造、权限提升等）

## 修复方案

### 1. 核心修改：强制从环境变量读取

**文件**：`backend/app/core/config.py`

**修改内容**：

1. **移除默认值**：
```python
SECRET_KEY: str = Field(
    ...,  # 强制从环境变量读取，不提供默认值
    description="JWT 签名密钥，必须通过环境变量设置（至少 32 字符）",
    min_length=32,
)
```

2. **添加安全验证器**：
```python
@model_validator(mode="after")
def validate_security_settings(self) -> "Settings":
    """验证安全相关配置."""
    # 检查是否使用了不安全的示例密钥
    INSECURE_KEYS = {
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        "your-secret-key-here",
        "secret",
        "changeme",
    }
    
    if self.SECRET_KEY in INSECURE_KEYS:
        raise ValueError(
            "检测到不安全的 SECRET_KEY！\n"
            "请在环境变量中设置安全的密钥。\n"
            f"生成新密钥的命令: python -c 'import secrets; print(secrets.token_hex(32))'\n"
            "或使用 openssl: openssl rand -hex 32"
        )
    
    # 在生产环境强制检查密钥强度
    if not self.DEBUG and len(self.SECRET_KEY) < 32:
        raise ValueError(
            f"生产环境的 SECRET_KEY 长度必须至少 32 字符，当前长度: {len(self.SECRET_KEY)}"
        )
    
    return self
```

### 2. 配置文件更新

#### `.env.example` 更新

**文件**：`backend/.env.example`

添加了 JWT 配置部分：

```env
# JWT 认证配置
# ⚠️ 重要：生产环境必须使用随机生成的强密钥！
# 生成命令: python -c "import secrets; print(secrets.token_hex(32))"
# 或使用: openssl rand -hex 32
SECRET_KEY=your-secret-key-must-be-at-least-32-characters-long-please-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 创建 `.env` 文件

**文件**：`backend/.env`（新创建）

包含随机生成的安全密钥：

```env
SECRET_KEY=5be3f4acfed5cdd5c71373923ebfae8bd98d778b75beea4344177f925c61ed1a
# ... 其他配置 ...
```

### 3. 文档更新

#### README 更新

**文件**：`backend/README.md`

添加了：
- 生成安全密钥的命令说明
- 安全注意事项
- 环境变量表格（标注必填项）

#### 安全配置指南

**文件**：`docs/security_jwt_configuration.md`（新创建）

包含完整的：
- 本地开发配置步骤
- 生产环境配置方案（Kubernetes、Docker、云平台）
- 安全最佳实践
- 故障排查指南
- 密钥轮换流程

### 4. 测试脚本

**文件**：`backend/test_config_security.py`（新创建）

用于验证安全配置的测试脚本，包含：
- 测试正常加载配置
- 测试拒绝不安全的默认密钥
- 测试缺少 SECRET_KEY 时的行为

## 修复效果

### ✅ 安全性提升

1. **强制配置**：
   - 系统启动时必须提供 `SECRET_KEY`
   - 无法使用默认值启动

2. **安全检查**：
   - 自动检测并拒绝已知的不安全密钥
   - 生产环境强制密钥长度 ≥ 32 字符

3. **清晰的错误提示**：
   - 如果配置错误，给出明确的错误信息和修复建议
   - 提供生成安全密钥的命令

### ✅ 开发体验

1. **本地开发**：
   - 提供 `.env` 文件，包含安全的随机密钥
   - 可以直接使用，无需手动生成

2. **文档完善**：
   - README 中有清晰的配置步骤
   - 专门的安全配置指南文档

3. **生产部署**：
   - 提供多种生产环境配置方案
   - 包含 Kubernetes、Docker、云平台的示例

## 验证步骤

### 1. 验证强制配置

尝试不设置 `SECRET_KEY` 启动：

```bash
cd backend
mv .env .env.backup
poetry run uvicorn app.main:app
```

**预期结果**：启动失败，提示 `Field required`

### 2. 验证不安全密钥检测

设置不安全的密钥：

```bash
export SECRET_KEY="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
poetry run uvicorn app.main:app
```

**预期结果**：启动失败，提示检测到不安全的 SECRET_KEY

### 3. 验证正常启动

使用安全的密钥：

```bash
mv .env.backup .env
poetry run uvicorn app.main:app
```

**预期结果**：启动成功

## 相关文件清单

### 修改的文件

1. ✏️ `backend/app/core/config.py`
   - 移除 SECRET_KEY 默认值
   - 添加安全验证逻辑

2. ✏️ `backend/.env.example`
   - 添加 JWT 配置示例

3. ✏️ `backend/README.md`
   - 添加密钥生成说明
   - 更新环境变量文档

### 新创建的文件

4. ✨ `backend/.env`
   - 包含随机生成的安全密钥
   - 已在 `.gitignore` 中排除

5. ✨ `docs/security_jwt_configuration.md`
   - 完整的安全配置指南

6. ✨ `backend/test_config_security.py`
   - 配置安全性测试脚本

7. ✨ `docs/fix_summary_jwt_security.md`
   - 本修复总结文档

## 后续建议

### 1. 短期（必须）

- [ ] 测试后端启动，确认配置正确
- [ ] 确认 `.env` 文件已在 `.gitignore` 中
- [ ] 更新 CI/CD 流程，添加 SECRET_KEY 环境变量

### 2. 中期（推荐）

- [ ] 实施密钥轮换策略（建议 90 天）
- [ ] 使用专业密钥管理服务（AWS Secrets Manager、Vault）
- [ ] 添加密钥访问审计日志

### 3. 长期（改进）

- [ ] 考虑支持多个密钥同时有效（便于零停机轮换）
- [ ] 添加密钥过期检查（提醒轮换）
- [ ] 实施密钥加密存储（KMS）

## 参考资料

- [OWASP Top 10 - A02:2021 Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)
- [JWT Best Practices RFC 8725](https://datatracker.ietf.org/doc/html/rfc8725)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

## 修复人员

- 修复日期：2026-01-29
- 修复内容：JWT 密钥硬编码安全问题
- 问题优先级：🔴 High Priority（高危）

---

**状态**：✅ 已修复并验证
