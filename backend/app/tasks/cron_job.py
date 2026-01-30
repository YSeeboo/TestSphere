"""Cron 定时任务调度."""

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from croniter import croniter, CroniterBadCronError, CroniterBadDateError
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.cron_job import CronJob
from app.models.test_execution import TestExecution
from app.tasks.test_execution import run_test_execution

logger = logging.getLogger(__name__)

TIMEZONE = ZoneInfo("Asia/Shanghai")


@celery_app.task(name="worker.check_and_trigger_cron_jobs")
def check_and_trigger_cron_jobs() -> dict[str, Any]:
    """
    检查并触发到期的 Cron 任务.

    每分钟执行一次，找到到期的任务并创建测试执行记录。
    """
    logger.info("开始检查 Cron 任务")

    db = SessionLocal()
    triggered = 0
    skipped = 0
    invalid = 0

    try:
        now = datetime.now(TIMEZONE)
        result = db.execute(select(CronJob).where(CronJob.is_active.is_(True)))
        jobs = result.scalars().all()

        for job in jobs:
            try:
                next_run_at = job.next_run_at
                if next_run_at and next_run_at.tzinfo is None:
                    next_run_at = next_run_at.replace(tzinfo=TIMEZONE)

                if next_run_at is None:
                    job.next_run_at = croniter(job.cron_expression, now).get_next(datetime)
                    skipped += 1
                    continue

                if now < next_run_at:
                    skipped += 1
                    continue

                config = {
                    "env": job.env,
                    "marker_expression": job.marker_expression,
                    "keyword_expression": job.keyword_expression,
                }
                execution = TestExecution(
                    project_id=job.project_id,
                    status="pending",
                    trigger_type="scheduled",
                    config=config,
                )
                db.add(execution)
                db.flush()

                run_test_execution.delay(execution.id)

                job.last_run_at = now
                job.next_run_at = croniter(job.cron_expression, now).get_next(datetime)
                triggered += 1

            except (CroniterBadCronError, CroniterBadDateError) as e:
                logger.warning(f"Cron 表达式无效 (id={job.id}): {e}")
                invalid += 1
            except Exception as e:
                logger.exception(f"触发 Cron 任务失败 (id={job.id}): {e}")
                invalid += 1

        db.commit()

        return {
            "status": "success",
            "triggered": triggered,
            "skipped": skipped,
            "invalid": invalid,
        }

    except Exception as e:
        logger.exception(f"检查 Cron 任务失败: {e}")
        db.rollback()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
