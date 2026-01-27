"""测试用例相关的 Pydantic Schema."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TestCaseBase(BaseModel):
    """测试用例基础 Schema."""
    
    file_path: str = Field(..., description="测试文件路径")
    name: str = Field(..., description="测试函数名称")
    description: str | None = Field(None, description="测试用例描述")
    nodeid: str = Field(..., description="pytest nodeid")
    markers: dict[str, Any] | None = Field(None, description="pytest markers")


class TestCaseOut(TestCaseBase):
    """测试用例输出 Schema."""
    
    id: int = Field(..., description="测试用例 ID")
    project_id: int = Field(..., description="所属项目 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = {
        "from_attributes": True  # Pydantic v2: 支持从 ORM 模型转换
    }


class TestCaseListResponse(BaseModel):
    """测试用例列表响应 Schema."""
    
    items: list[TestCaseOut] = Field(..., description="测试用例列表")
    total: int = Field(..., description="总数")
