"""FastAPI 依赖注入模块."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import async_session_maker
from app.models.user import User
from app.schemas.token import TokenPayload

# OAuth2 密码流，token URL 指向登录接口
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖项.
    
    Yields:
        AsyncSession: 数据库异步会话
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    从 JWT Token 获取当前用户.
    
    Args:
        db: 数据库会话
        token: JWT Token
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 401 未授权（Token 无效或用户不存在）
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 解码 Token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # 提取用户 ID
    try:
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise credentials_exception
        user_id: int = int(token_data.sub)
    except (JWTError, ValueError, KeyError):
        raise credentials_exception
    
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户.
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前活跃用户
        
    Raises:
        HTTPException: 400 用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    获取当前超级管理员用户.
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前超级管理员用户
        
    Raises:
        HTTPException: 403 权限不足
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要超级管理员权限"
        )
    return current_user
