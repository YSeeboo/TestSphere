#!/usr/bin/env python3
"""初始化数据库脚本.

创建所有表并添加初始数据。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.security import get_password_hash
from app.db.session import async_engine, async_session_maker, Base
from app.models.user import User
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.test_execution import TestExecution


async def init_db():
    """初始化数据库."""

    print("=" * 60)
    print("ATP 数据库初始化")
    print("=" * 60)

    # 1. 创建所有表
    print("\n📊 创建数据库表...")
    async with async_engine.begin() as conn:
        # 删除所有现有表（谨慎：会删除所有数据）
        await conn.run_sync(Base.metadata.drop_all)
        print("  ✓ 已删除现有表")

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        print("  ✓ 已创建所有表")

    # 2. 创建初始用户
    print("\n👤 创建初始用户...")
    async with async_session_maker() as session:
        # 检查是否已有用户
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()

        if user_count == 0:
            # 创建管理员用户
            admin_user = User(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
            )
            session.add(admin_user)

            # 创建测试用户
            test_user = User(
                email="test@example.com",
                username="test_user",
                hashed_password=get_password_hash("test123"),
                is_active=True,
                is_superuser=False,
            )
            session.add(test_user)

            await session.commit()
            print("  ✓ 已创建管理员用户: admin@example.com (密码: admin123)")
            print("  ✓ 已创建测试用户: test@example.com (密码: test123)")
        else:
            print(f"  ℹ️  数据库已有 {user_count} 个用户，跳过创建")

    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    print("\n📝 可以使用以下账号登录：")
    print("  • 管理员: admin@example.com / admin123")
    print("  • 测试用户: test@example.com / test123")
    print()


async def main():
    """主函数."""
    try:
        await init_db()
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 关闭引擎
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
