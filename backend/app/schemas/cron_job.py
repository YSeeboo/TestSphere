"""Cron 任务相关的 Pydantic Schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CronJobBase(BaseModel):
    """Cron 任务基础字段."""

    name: str = Field(..., description="任务名称")
    cron_expression: str = Field(..., description="Cron 表达式")
    is_active: bool = Field(True, description="是否启用")
    env: Optional[str] = Field(None, description="环境变量配置 (如 staging, production)")
    marker_expression: Optional[str] = Field(None, description="Pytest marker 表达式")
    keyword_expression: Optional[str] = Field(None, description="Pytest keyword 表达式")


class CronJobCreate(CronJobBase):
    """Cron 任务创建 Schema."""


class CronJobUpdate(BaseModel):
    """Cron 任务更新 Schema."""

    name: Optional[str] = Field(None, description="任务名称")
    cron_expression: Optional[str] = Field(None, description="Cron 表达式")
    is_active: Optional[bool] = Field(None, description="是否启用")
    env: Optional[str] = Field(None, description="环境变量配置")
    marker_expression: Optional[str] = Field(None, description="Pytest marker 表达式")
    keyword_expression: Optional[str] = Field(None, description="Pytest keyword 表达式")


class CronJobOut(CronJobBase):
    """Cron 任务响应 Schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="任务ID")
    project_id: int = Field(..., description="项目ID")
    last_run_at: Optional[datetime] = Field(None, description="上次执行时间")
    next_run_at: Optional[datetime] = Field(None, description="下次执行时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
