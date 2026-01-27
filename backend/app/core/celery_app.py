"""Celery 应用配置."""

from celery import Celery
from app.core.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "atp",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 任务最大执行时间 1 小时
    task_soft_time_limit=3000,  # 任务软超时 50 分钟
    worker_prefetch_multiplier=4,  # Worker 预取任务数
    worker_max_tasks_per_child=1000,  # Worker 执行多少任务后重启
)

# 自动发现任务
# 当你在 app/tasks/ 目录下创建任务模块时，Celery 会自动发现它们
celery_app.autodiscover_tasks(["app.tasks"])
