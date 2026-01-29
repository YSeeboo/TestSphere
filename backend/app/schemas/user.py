"""用户相关的 Pydantic Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """用户基础 Schema."""

    email: EmailStr = Field(..., description="用户邮箱")
    username: str = Field(..., min_length=2, max_length=100, description="用户名")
    is_active: bool = Field(default=True, description="是否激活")
    is_superuser: bool = Field(default=False, description="是否超级管理员")


class UserCreate(BaseModel):
    """用户注册 Schema."""

    email: EmailStr = Field(..., description="用户邮箱")
    username: str = Field(..., min_length=2, max_length=100, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    """用户登录 Schema."""

    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """用户更新 Schema."""

    email: Optional[EmailStr] = Field(None, description="用户邮箱")
    username: Optional[str] = Field(None, min_length=2, max_length=100, description="用户名")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="新密码")


class UserInDB(UserBase):
    """数据库中的用户 Schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class User(UserInDB):
    """用户响应 Schema (对外返回)."""

    pass
