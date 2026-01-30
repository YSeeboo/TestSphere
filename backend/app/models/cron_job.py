"""定时任务 (Cron) 模型."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.project import Project


class CronJob(Base):
    """
    定时任务模型.

    Attributes:
        id: 任务唯一标识
        project_id: 关联项目 ID
        name: 任务名称
        cron_expression: Cron 表达式 (如 "0 2 * * *")
        is_active: 是否启用
        last_run_at: 上次执行时间
        next_run_at: 下次执行时间
        created_at: 创建时间
        updated_at: 更新时间
    """

    __tablename__ = "cron_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    env: Mapped[str | None] = mapped_column(String(50), nullable=True)
    marker_expression: Mapped[str | None] = mapped_column(String(200), nullable=True)
    keyword_expression: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="cron_jobs",
        lazy="select",
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return (
            f"<CronJob(id={self.id}, project_id={self.project_id}, "
            f"name='{self.name}', cron='{self.cron_expression}')>"
        )
