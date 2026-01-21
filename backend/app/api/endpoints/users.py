"""用户相关 API 端点."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_superuser, get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    获取当前登录用户信息.
    
    Args:
        current_user: 当前用户 (通过 JWT Token 验证)
        
    Returns:
        User: 当前用户信息
    """
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    更新当前用户信息.
    
    Args:
        user_in: 用户更新信息
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        User: 更新后的用户信息
    """
    # 更新用户名
    if user_in.username is not None:
        current_user.username = user_in.username
    
    # 更新密码
    if user_in.password is not None:
        current_user.hashed_password = get_password_hash(user_in.password)
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/{user_id}", response_model=UserSchema)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> User:
    """
    根据 ID 获取用户信息 (需要超级管理员权限).
    
    Args:
        user_id: 用户 ID
        db: 数据库会话
        _: 当前用户 (超级管理员)
        
    Returns:
        User: 用户信息
        
    Raises:
        HTTPException: 404 用户不存在
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user


@router.get("/", response_model=list[UserSchema])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[User]:
    """
    获取用户列表 (需要超级管理员权限).
    
    Args:
        skip: 跳过记录数
        limit: 返回记录数上限
        db: 数据库会话
        _: 当前用户 (超级管理员)
        
    Returns:
        list[User]: 用户列表
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    
    return list(users)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> None:
    """
    删除用户 (需要超级管理员权限).
    
    Args:
        user_id: 用户 ID
        db: 数据库会话
        current_user: 当前用户 (超级管理员)
        
    Raises:
        HTTPException: 400 不能删除自己, 404 用户不存在
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await db.delete(user)
    await db.commit()
