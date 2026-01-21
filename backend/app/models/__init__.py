"""数据库模型模块."""

# 导入所有模型，供外部使用
from app.models.base import Base, User

__all__ = ["Base", "User"]
