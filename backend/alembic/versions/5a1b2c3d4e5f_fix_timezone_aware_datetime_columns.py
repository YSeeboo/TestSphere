"""fix timezone aware datetime columns

Revision ID: 5a1b2c3d4e5f
Revises: 4630cd7126cf
Create Date: 2026-01-29 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a1b2c3d4e5f'
down_revision: Union[str, None] = '4630cd7126cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    修改所有 DateTime 列为 TIMESTAMP WITH TIME ZONE.

    这是为了修复 timezone-aware datetime 对象与数据库列类型不匹配的问题。
    """
    # 修改 users 表
    op.alter_column('users', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=False)
    op.alter_column('users', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=False)

    # 修改 projects 表
    op.alter_column('projects', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=False)
    op.alter_column('projects', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=False)
    op.alter_column('projects', 'last_sync_time',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=True)

    # 修改 test_cases 表
    op.alter_column('test_cases', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=False)
    op.alter_column('test_cases', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=False)

    # 修改 test_executions 表
    op.alter_column('test_executions', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=False)
    op.alter_column('test_executions', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=False)


def downgrade() -> None:
    """
    回退: 将所有 TIMESTAMP WITH TIME ZONE 改回 TIMESTAMP WITHOUT TIME ZONE.
    """
    # 回退 test_executions 表
    op.alter_column('test_executions', 'updated_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=False)
    op.alter_column('test_executions', 'created_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=False)

    # 回退 test_cases 表
    op.alter_column('test_cases', 'updated_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=False)
    op.alter_column('test_cases', 'created_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=False)

    # 回退 projects 表
    op.alter_column('projects', 'last_sync_time',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.alter_column('projects', 'updated_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=False)
    op.alter_column('projects', 'created_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=False)

    # 回退 users 表
    op.alter_column('users', 'updated_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=False)
    op.alter_column('users', 'created_at',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=False)
