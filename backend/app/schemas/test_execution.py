"""测试执行相关的 Pydantic Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TestExecutionConfig(BaseModel):
    """测试执行配置 Schema."""

    env: Optional[str] = Field(None, description="环境变量配置 (如 staging, production)")
    marker_expression: Optional[str] = Field(None, description="Pytest marker 表达式 (如 -m smoke)")
    keyword_expression: Optional[str] = Field(None, description="Pytest keyword 表达式 (如 -k 'login or logout')")


class TestExecutionCreate(BaseModel):
    """测试执行创建 Schema."""

    env: Optional[str] = Field(None, description="环境变量配置")
    marker_expression: Optional[str] = Field(None, description="Pytest marker 表达式")
    keyword_expression: Optional[str] = Field(None, description="Pytest keyword 表达式")


class TestExecutionOut(BaseModel):
    """测试执行响应 Schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="执行记录ID")
    project_id: int = Field(..., description="项目ID")
    status: str = Field(..., description="执行状态 (pending, running, success, failed)")
    trigger_type: str = Field(..., description="触发类型 (manual, scheduled, webhook)")
    config: Optional[dict] = Field(None, description="执行配置")
    logs: Optional[str] = Field(None, description="执行日志")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
