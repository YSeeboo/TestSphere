"""数据库基类和模型汇总模块 - 供 Alembic 自动发现所有模型."""

# 导入 Base
from app.db.session import Base

# 导入所有模型，确保 Alembic 能够检测到它们
from app.models.user import User  # noqa: F401

# 注意: 每次新增模型时，必须在此处导入，否则 Alembic 无法自动生成迁移

__all__ = ["Base"]
