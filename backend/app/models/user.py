"""用户模型."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.project import Project


class User(Base):
    """
    用户模型.
    
    Attributes:
        id: 用户唯一标识
        email: 用户邮箱 (唯一索引)
        username: 用户名
        hashed_password: 哈希后的密码
        is_active: 是否激活 (默认 True)
        is_superuser: 是否超级管理员 (默认 False)
        created_at: 创建时间
        updated_at: 更新时间
        projects: 用户拥有的项目列表
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
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

    # Relationship: 用户拥有的项目列表
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select"  # 明确指定惰性加载策略
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
