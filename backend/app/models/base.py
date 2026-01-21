"""模型基类模块 - 导入所有模型供 Alembic 使用."""

from app.db.session import Base
from app.models.user import User

# 导出所有模型，供 Alembic 自动检测使用
__all__ = ["Base", "User"]
