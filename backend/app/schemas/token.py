"""Token 相关的 Pydantic Schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """JWT Token 响应 Schema."""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")


class TokenPayload(BaseModel):
    """JWT Token Payload Schema."""

    sub: Optional[int] = Field(None, description="用户ID")
    exp: Optional[int] = Field(None, description="过期时间戳")
    iat: Optional[int] = Field(None, description="签发时间戳")
