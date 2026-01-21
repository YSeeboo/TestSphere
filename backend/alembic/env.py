"""Alembic 环境配置 - 数据库迁移."""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection

from alembic import context

# 将项目根目录添加到 Python 路径
# 这样可以正确导入 app 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 导入应用配置
from app.core.config import settings
# 导入所有模型的 Base (确保所有模型都被导入)
from app.db.base import Base

# Alembic Config 对象，提供访问 .ini 文件的能力
config = context.config

# 使用应用配置中的数据库 URL，而不是 alembic.ini 中的
# 将异步连接字符串转换为同步版本用于 Alembic
database_url = str(settings.DATABASE_URL)
# 将 postgresql+asyncpg:// 替换为 postgresql://（用于同步迁移）
sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", sync_database_url)

# 设置日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标 metadata，用于自动生成迁移
target_metadata = Base.metadata

# 其他自定义配置
# target_metadata = mymodel.Base.metadata


def run_migrations_offline() -> None:
    """
    在 'offline' 模式下运行迁移.
    
    这种模式下不需要建立数据库连接，只会生成 SQL 脚本。
    配置只需要一个 URL 即可，不需要实际的数据库连接。
    
    调用 context.execute() 来执行 SQL 脚本。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # 比较列类型变化
        compare_server_default=True,  # 比较服务器默认值
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移的核心逻辑."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # 比较列类型变化
        compare_server_default=True,  # 比较服务器默认值
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在 'online' 模式下运行迁移.
    
    这种模式下会创建实际的数据库连接并执行迁移。
    使用同步引擎，因为 Alembic 主要设计用于同步操作。
    """
    from sqlalchemy import engine_from_config
    
    # 创建同步引擎配置
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


# 判断运行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
