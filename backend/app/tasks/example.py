"""示例 Celery 任务.

演示如何使用同步数据库连接和 Celery 任务。
"""

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from sqlalchemy import text


@celery_app.task(name="example.health_check")
def health_check_task() -> dict[str, str]:
    """
    健康检查任务示例.
    
    演示如何在 Celery 任务中使用同步数据库连接。
    
    Returns:
        dict: 包含状态信息的字典
    """
    try:
        # 使用同步 Session
        with SessionLocal() as db:
            # 执行简单的数据库查询
            result = db.execute(text("SELECT 1"))
            result.scalar()
            
        return {
            "status": "ok",
            "message": "Database connection successful",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}",
        }


@celery_app.task(name="example.add_numbers")
def add_numbers(a: int, b: int) -> int:
    """
    简单的加法任务示例.
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        int: 两数之和
    """
    return a + b
