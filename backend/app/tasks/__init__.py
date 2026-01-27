"""Celery 任务模块.

在此目录下创建任务文件,Celery 会自动发现并注册任务。

示例:
    # app/tasks/example.py
    from app.core.celery_app import celery_app
    
    @celery_app.task
    def example_task(param: str) -> str:
        return f"Task executed with: {param}"
"""

# 导入所有任务以便 Celery 自动发现
from app.tasks.sync_project import sync_project_test_cases
from app.tasks.test_execution import run_test_execution

__all__ = ["sync_project_test_cases", "run_test_execution"]
