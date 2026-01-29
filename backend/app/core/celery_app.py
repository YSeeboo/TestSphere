"""Celery 应用配置."""

import logging
from celery import Celery
from celery.signals import task_failure, task_retry, task_success
from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

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


# ==================== 统一的任务错误处理 ====================

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """
    任务失败时的统一处理器.

    Args:
        sender: 任务实例
        task_id: 任务 ID
        exception: 异常对象
        args: 任务位置参数
        kwargs: 任务关键字参数
        traceback: 回溯信息
        einfo: 异常信息
    """
    logger.error(
        f"Task {sender.name} [{task_id}] failed",
        extra={
            "task_name": sender.name,
            "task_id": task_id,
            "args": args,
            "kwargs": kwargs,
            "exception": str(exception),
            "exception_type": type(exception).__name__,
        },
        exc_info=einfo
    )


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kw):
    """
    任务重试时的统一处理器.

    Args:
        sender: 任务实例
        task_id: 任务 ID
        reason: 重试原因
        einfo: 异常信息
    """
    logger.warning(
        f"Task {sender.name} [{task_id}] is retrying",
        extra={
            "task_name": sender.name,
            "task_id": task_id,
            "reason": str(reason),
        }
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **kw):
    """
    任务成功时的统一处理器.

    Args:
        sender: 任务实例
        result: 任务返回结果
    """
    logger.info(
        f"Task {sender.name} completed successfully",
        extra={
            "task_name": sender.name,
            "result_status": result.get("status") if isinstance(result, dict) else "unknown",
        }
    )
