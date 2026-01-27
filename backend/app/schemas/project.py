"""项目相关的 Pydantic Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    """项目基础 Schema."""

    name: str = Field(..., min_length=1, max_length=255, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    git_url: Optional[str] = Field(None, max_length=500, description="Git 仓库地址")
    git_branch: str = Field(default="main", max_length=100, description="Git 分支名称")


class ProjectCreate(ProjectBase):
    """项目创建 Schema."""

    pass


class ProjectUpdate(BaseModel):
    """项目更新 Schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    git_url: Optional[str] = Field(None, max_length=500, description="Git 仓库地址")
    git_branch: Optional[str] = Field(None, max_length=100, description="Git 分支名称")


class ProjectInDB(ProjectBase):
    """数据库中的项目 Schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="项目ID")
    owner_id: int = Field(..., description="项目所有者ID")
    last_sync_time: Optional[datetime] = Field(None, description="最后同步时间")
    last_sync_status: str = Field(default="Pending", description="最后同步状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ProjectOut(ProjectInDB):
    """项目响应 Schema (对外返回)."""

    pass
