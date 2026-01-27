"""测试执行记录模型."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project


class TestExecution(Base):
    """
    测试执行记录模型.
    
    Attributes:
        id: 执行记录唯一标识
        project_id: 项目ID (外键关联 projects.id)
        status: 执行状态 (pending, running, success, failed)
        trigger_type: 触发类型 (manual, scheduled, webhook)
        config: 执行配置 (JSON, 包含 env, markers, keywords 等参数)
        logs: 执行日志 (暂存日志文本)
        created_at: 创建时间
        updated_at: 更新时间
        project: 关联的项目
    """

    __tablename__ = "test_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="pending",
        server_default="pending"
    )
    trigger_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="manual",
        server_default="manual"
    )
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )

    # Relationship: 关联的项目
    project: Mapped["Project"] = relationship("Project", back_populates="test_executions")

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<TestExecution(id={self.id}, project_id={self.project_id}, status='{self.status}')>"
