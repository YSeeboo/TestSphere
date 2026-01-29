"""测试用例模型."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.db.session import Base
from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.project import Project


class TestCase(Base):
    """
    测试用例模型.
    
    Attributes:
        id: 测试用例唯一标识
        project_id: 所属项目ID (外键关联 projects.id)
        file_path: 测试文件路径 (e.g., tests/api/test_login.py)
        name: 测试函数名称 (e.g., test_login_success)
        description: 测试用例描述 (从 docstring 提取)
        nodeid: pytest nodeid (唯一标识, e.g., tests/api/test_login.py::test_login_success)
        markers: pytest markers (JSON 格式存储)
        created_at: 创建时间
        updated_at: 更新时间
        project: 所属项目 (关联到 Project 模型)
    """

    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 测试用例基本信息
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # pytest 相关信息
    nodeid: Mapped[str] = mapped_column(String(1000), nullable=False, unique=False)
    markers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship: 所属项目
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="test_cases",
        lazy="select"  # 明确指定惰性加载策略
    )

    # 复合唯一索引: 同一个项目下的 nodeid 必须唯一
    __table_args__ = (
        Index("ix_test_cases_project_nodeid", "project_id", "nodeid", unique=True),
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<TestCase(id={self.id}, name='{self.name}', nodeid='{self.nodeid}')>"
