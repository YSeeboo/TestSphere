"""认证相关 API 端点."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.rate_limiter import rate_limiter
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, User as UserSchema

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    用户注册接口.

    Args:
        user_in: 用户注册信息
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        User: 创建的用户对象

    Raises:
        HTTPException: 400 邮箱已被注册, 429 请求过于频繁
    """
    # 速率限制：每分钟最多 3 次注册请求
    rate_limiter.check_rate_limit(request, max_requests=3, window_seconds=60)

    # 检查邮箱是否已存在（使用 exists 优化查询）
    stmt = select(exists().where(User.email == user_in.email))
    email_exists = await db.scalar(stmt)

    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 创建新用户
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_superuser=False,
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    用户登录接口 (OAuth2 密码流).

    Args:
        form_data: OAuth2 表单数据 (username 字段用于传递邮箱)
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        Token: 包含 access_token 的响应

    Raises:
        HTTPException: 401 邮箱或密码错误, 429 请求过于频繁
    """
    # 速率限制：每分钟最多 5 次登录尝试
    if request:
        rate_limiter.check_rate_limit(request, max_requests=5, window_seconds=60)

    # Dummy hash 用于防止时序攻击
    # 即使用户不存在，也执行一次哈希验证，使响应时间保持一致
    DUMMY_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVGvRYVm6"

    # 查询用户 (OAuth2 标准使用 username 字段，这里我们用它传递 email)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # 防止时序攻击：无论用户是否存在，都执行密码验证
    if not user:
        # 用户不存在，使用 dummy hash 进行验证（耗时与真实验证相近）
        verify_password(form_data.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 用户存在，验证密码
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/login-json", response_model=Token)
async def login_json(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    用户登录接口 (JSON 格式，更友好的前端接口).

    Args:
        login_data: 登录数据 (email 和 password)
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        Token: 包含 access_token 的响应

    Raises:
        HTTPException: 401 邮箱或密码错误, 429 请求过于频繁
    """
    # 速率限制：每分钟最多 5 次登录尝试
    rate_limiter.check_rate_limit(request, max_requests=5, window_seconds=60)

    # Dummy hash 用于防止时序攻击
    # 即使用户不存在，也执行一次哈希验证，使响应时间保持一致
    DUMMY_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVGvRYVm6"

    # 查询用户
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    # 防止时序攻击：无论用户是否存在，都执行密码验证
    if not user:
        # 用户不存在，使用 dummy hash 进行验证（耗时与真实验证相近）
        verify_password(login_data.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 用户存在，验证密码
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
