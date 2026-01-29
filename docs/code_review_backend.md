## 🔴 High Priority (高危问题)

### 1. 安全性 - 硬编码的 JWT 密钥 ⚠️

文件: backend/app/core/config.py

config.pyLines 99-102

SECRET_KEY: str = Field(

​ default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",

​ description="JWT 签名密钥，生产环境必须修改为随机生成的密钥",

)

问题: 默认 SECRET_KEY 是硬编码的，如果生产环境未通过环境变量覆盖，将导致严重的安全风险（JWT 可被伪造）。

建议:

- 移除默认值，改为 Field(..., description="...") 强制从环境变量读取

- 或在启动时检查是否使用默认值并拒绝启动

---

### 2. 时间函数已废弃 🕐

文件: backend/app/core/security.py, backend/app/models/\*.py

security.pyLines 54-54

​ expire = datetime.utcnow() + expires_delta

user.pyLines 42-42

​ default=datetime.utcnow,

问题: datetime.utcnow() 在 Python 3.12+ 已被标记为废弃，应使用 datetime.now(timezone.utc)。

影响:

- 代码在未来版本可能会出现警告或错误

- 时区处理不明确

建议: 全局替换为 datetime.now(timezone.utc)

---

### 3. Session 管理 - 双重 Commit/Rollback 🔄

文件: backend/app/api/deps.py 和各个端点

deps.pyLines 20-35

_async_ _def_ get_db() -> AsyncGenerator[AsyncSession, None]:

"""

获取数据库会话的依赖项.

Yields:

​ AsyncSession: 数据库异步会话

"""

_async_ _with_ async_session_maker() _as_ session:

​ _try_:

​ _yield_ session

​ _await_ session.commit()

​ _except_ Exception:

​ _await_ session.rollback()

​ _raise_

​ _finally_:

​ _await_ session.close()

问题:

1. get_db() 依赖中已经自动处理了 commit()/rollback()

1. 但在端点中又手动调用了 await db.commit()（如 auth.py:58, users.py:56, projects.py:78）

1. 这导致双重提交：

- 端点中先 commit 一次

- 依赖结束时又 commit 一次（无操作，但逻辑混乱）

影响:

- 代码逻辑不清晰，事务边界模糊

- 如果端点中 commit 后发生异常，依赖中的 rollback 不会生效（因为已经 commit 了）

建议:

- 方案 A (推荐): 移除 get_db() 中的自动 commit，让端点显式控制事务

- 方案 B: 移除所有端点中的手动 commit，完全依赖 get_db() 的自动提交

---

### 4. 潜在的 N+1 查询问题 📊

文件: backend/app/api/endpoints/test_executions.py

test_executions.pyLines 164-173

_# 查询测试执行记录 (需要 join project 以检查权限)_

result = _await_ db.execute(

​ select(TestExecution)

​ .join(Project, TestExecution.project_id == Project.id)

​ .where(

​ TestExecution.id == execution_id,

​ Project.owner_id == current_user.id

​ )

)

execution = result.scalar_one_or_none()

问题:

- 使用了 join 但没有使用 joinedload() 或 selectinload()

- 如果后续代码访问 execution.project，会触发额外的 SQL 查询（N+1 问题）

- 虽然当前代码没有访问，但容易在未来引入性能问题

建议: 明确使用 eager loading:

_from_ sqlalchemy.orm _import_ joinedload

result = _await_ db.execute(

select(TestExecution)

.options(joinedload(TestExecution.project))

.join(Project, TestExecution.project_id == Project.id)

.where(...)

)

---

## 🟡 Medium Priority (改进建议)

### 5. 缺少邮箱唯一性约束验证 📧

文件: backend/app/api/endpoints/users.py

users.pyLines 32-59

@router.put("/me", response_model=UserSchema)

_async_ _def_ update_current_user(

user_in: UserUpdate,

current_user: User = Depends(get_current_active_user),

db: AsyncSession = Depends(get_db),

) -> User:

"""更新当前用户信息."""

_# 更新用户名_

_if_ user_in.username is not None:

​ current_user.username = user_in.username

_# 更新密码_

_if_ user_in.password is not None:

​ current_user.hashed_password = get_password_hash(user_in.password)

_await_ db.commit()

_await_ db.refresh(current_user)

_return_ current_user

问题: UserUpdate Schema 不支持更新 email，但如果将来支持，需要先检查邮箱是否已被占用。

建议: 如果支持邮箱修改，需要添加唯一性校验（类似 register 端点）。

---

### 6. 密码哈希可能受时序攻击 ⏱️

文件: backend/app/core/security.py

security.pyLines 15-26

_def_ verify_password(plain_password: str, hashed_password: str) -> bool:

"""

验证明文密码与哈希密码是否匹配.

"""

_return_ pwd_context.verify(plain_password, hashed_password)

问题:

- 在登录逻辑中，先检查用户是否存在，再验证密码

- 攻击者可以通过响应时间差异判断用户是否存在（时序攻击）

位置: auth.py:86-87

_if_ not user or not verify_password(form_data.password, user.hashed_password):

_raise_ HTTPException(...)

建议: 使用 "dummy hash" 策略：

_# 如果用户不存在，也执行一次哈希验证（使用 dummy 值）_

dummy_hash = "$2b$12$dummy_hash_to_prevent_timing_attack"

_if_ not user:

pwd_context.verify("dummy", dummy_hash)

_raise_ HTTPException(...)

_if_ not verify_password(form_data.password, user.hashed_password):

_raise_ HTTPException(...)

---

### 7. 缺少 Database Pool 溢出监控 🏊

文件: backend/app/db/session.py

session.pyLines 17-25

async_engine: AsyncEngine = create_async_engine(

str(settings.DATABASE_URL),

echo=settings.DB_ECHO,

pool_size=settings.DB_POOL_SIZE,

max_overflow=settings.DB_MAX_OVERFLOW,

pool_timeout=settings.DB_POOL_TIMEOUT,

pool_recycle=settings.DB_POOL_RECYCLE,

pool_pre_ping=True, _# 连接前检查连接是否有效_

)

问题:

- 连接池配置正确，但没有监控机制

- 如果连接泄漏或高并发，pool 耗尽会导致服务阻塞

建议:

- 添加连接池状态监控（health check）

- 使用 pool_pre_ping=True 是好的实践 ✅

- 考虑添加日志记录连接池使用情况

---

### 8. SQLAlchemy 关系加载策略不明确 🔗

文件: backend/app/models/\*.py

user.pyLines 52-56

_# Relationship: 用户拥有的项目列表_

projects: Mapped[list["Project"]] = relationship(

​ "Project",

​ back_populates="owner",

​ cascade="all, delete-orphan"

)

问题:

- 没有指定 lazy 加载策略（默认是 select，即惰性加载）

- 如果不小心访问 user.projects，会触发额外查询

建议: 明确指定加载策略:

projects: Mapped[list["Project"]] = relationship(

"Project",

back_populates="owner",

cascade="all, delete-orphan",

lazy="select" _# 或 "selectin" / "joined" / "raise" (禁止加载)_

)

推荐使用 lazy="raise" 强制显式加载，避免意外的 N+1 查询。

---

### 9. Celery 任务错误处理不统一 🔧

文件: backend/app/tasks/\*.py

问题:

- 任务中有大量 try/except，但错误处理方式不统一

- 有些直接返回 dict，有些会更新数据库状态

- 缺少统一的错误日志格式和告警机制

建议:

- 创建统一的任务基类或装饰器处理错误

- 添加 Celery 错误回调 (on_failure, on_retry)

- 集成 Sentry 等错误追踪工具

---

### 10. 数据库查询可以优化 🚀

文件: backend/app/api/endpoints/auth.py

auth.pyLines 38-46

_# 检查邮箱是否已存在_

result = _await_ db.execute(select(User).where(User.email == user_in.email))

existing_user = result.scalar_one_or_none()

_if_ existing_user:

​ _raise_ HTTPException(

​ status_code=status.HTTP_400_BAD_REQUEST,

​ detail="该邮箱已被注册"

​ )

问题:

- 只需要检查存在性，不需要加载整个 User 对象

- 可以使用 exists() 提高性能

建议:

_from_ sqlalchemy _import_ exists

stmt = select(exists().where(User.email == user_in.email))

email_exists = _await_ db.scalar(stmt)

_if_ email_exists:

_raise_ HTTPException(...)

---

### 11. 缺少请求速率限制 🚦

文件: backend/app/api/endpoints/auth.py

问题:

- 登录、注册等敏感接口没有速率限制

- 容易受到暴力破解攻击

建议:

- 集成 slowapi 或 fastapi-limiter

- 对登录接口添加 IP 级别的速率限制（如 5 次/分钟）

---

### 12. Pydantic Schema 配置不一致 📝

文件: backend/app/schemas/\*.py

问题:

- 有些 Schema 使用 model_config = ConfigDict(from_attributes=True)

- 但有些继承的 Schema 没有明确声明

建议: 统一配置，确保所有需要从 ORM 模型转换的 Schema 都有此配置。

---

### 13. 缺少数据库迁移版本控制说明 📚

文件: backend/app/db/base.py

base.pyLines 9-9

_# 注意: 每次新增模型时，必须在此处导入，否则 Alembic 无法自动生成迁移_

问题:

- 只导入了 User 模型，但代码中有 Project, TestCase, TestExecution

- Alembic 可能无法检测到这些模型的变更

建议: 导入所有模型:

_from_ app.models.user _import_ User _# noqa: F401_

_from_ app.models.project _import_ Project _# noqa: F401_

_from_ app.models.test_case _import_ TestCase _# noqa: F401_

_from_ app.models.test_execution _import_ TestExecution _# noqa: F401_

---

## ✅ 代码亮点

1. 异步/同步引擎分离 ✅ (db/session.py)

- 正确区分了 FastAPI (异步) 和 Celery (同步) 的数据库引擎

- 使用 postgresql+asyncpg 和 postgresql+psycopg2

1. 正确使用 SQLAlchemy 2.0 语法 ✅

- 使用 select(), Mapped, mapped_column

- 避免了废弃的 session.query()

1. Pydantic V2 正确使用 ✅

- 使用 model_dump(), model_validate()

- 类型注解完整

1. 连接池配置合理 ✅

- pool_pre_ping=True 确保连接有效性

- 超时、回收等参数配置完善

---

## 📋 优先修复顺序

1. 立即修复 (生产环境安全):

- \#1: SECRET_KEY 硬编码

- \#3: Session 双重提交

1. 短期修复 (1-2 周):

- \#2: 时间函数废弃

- \#4: N+1 查询

- \#13: 数据库迁移

1. 中期优化 (1 个月):

- \#6: 时序攻击

- \#11: 速率限制

- \#9: Celery 错误处理

1. 长期改进:

- \#7-#10: 性能优化

- \#12: 代码规范统一
