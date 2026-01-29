"""项目模型."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.test_case import TestCase
    from app.models.test_execution import TestExecution


class Project(Base):
    """
    项目模型.
    
    Attributes:
        id: 项目唯一标识
        name: 项目名称
        description: 项目描述
        owner_id: 项目所有者ID (外键关联 users.id)
        git_url: Git 仓库地址
        git_branch: Git 分支名称
        last_sync_time: 最后同步时间
        last_sync_status: 最后同步状态 (Pending/Success/Failed)
        created_at: 创建时间
        updated_at: 更新时间
        owner: 项目所有者 (关联到 User 模型)
        test_cases: 项目关联的测试用例列表
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Git 同步相关字段
    git_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    git_branch: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        default="main",
        server_default="main"
    )
    last_sync_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="Pending",
        server_default="Pending"
    )
    
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

    # Relationship: 项目所有者
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
        lazy="select"  # 明确指定惰性加载策略
    )

    # Relationship: 项目的测试用例
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select"  # 明确指定惰性加载策略
    )

    # Relationship: 项目的测试执行记录
    test_executions: Mapped[list["TestExecution"]] = relationship(
        "TestExecution",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select"  # 明确指定惰性加载策略
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<Project(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"
