"""Cron 任务相关 API 端点."""

from datetime import datetime
from zoneinfo import ZoneInfo

from croniter import croniter, CroniterBadCronError, CroniterBadDateError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.cron_job import CronJob
from app.models.project import Project
from app.models.test_execution import TestExecution
from app.models.user import User
from app.schemas.cron_job import CronJobCreate, CronJobOut, CronJobUpdate
from app.tasks.test_execution import run_test_execution

router = APIRouter()


async def _get_project_or_404(
    project_id: int, current_user: User, db: AsyncSession
) -> Project:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在或无权访问",
        )
    return project


@router.get("/projects/{project_id}/cron-jobs", response_model=list[CronJobOut])
async def list_cron_jobs(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[CronJob]:
    await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(CronJob).where(CronJob.project_id == project_id).order_by(CronJob.id.desc())
    )
    return list(result.scalars().all())


@router.post(
    "/projects/{project_id}/cron-jobs",
    response_model=CronJobOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_cron_job(
    project_id: int,
    payload: CronJobCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CronJob:
    await _get_project_or_404(project_id, current_user, db)

    job = CronJob(
        project_id=project_id,
        name=payload.name,
        cron_expression=payload.cron_expression,
        is_active=payload.is_active,
        env=payload.env,
        marker_expression=payload.marker_expression,
        keyword_expression=payload.keyword_expression,
    )
    if payload.is_active:
        try:
            now = datetime.now(ZoneInfo("Asia/Shanghai"))
            job.next_run_at = croniter(payload.cron_expression, now).get_next(datetime)
        except (CroniterBadCronError, CroniterBadDateError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cron 表达式无效",
            ) from None
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.put("/projects/{project_id}/cron-jobs/{job_id}", response_model=CronJobOut)
async def update_cron_job(
    project_id: int,
    job_id: int,
    payload: CronJobUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CronJob:
    await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(CronJob).where(
            CronJob.id == job_id,
            CronJob.project_id == project_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务不存在",
        )

    if payload.name is not None:
        job.name = payload.name
    if payload.cron_expression is not None:
        job.cron_expression = payload.cron_expression
        if job.is_active:
            try:
                now = datetime.now(ZoneInfo("Asia/Shanghai"))
                job.next_run_at = croniter(payload.cron_expression, now).get_next(datetime)
            except (CroniterBadCronError, CroniterBadDateError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cron 表达式无效",
                ) from None
        else:
            job.next_run_at = None
    if payload.is_active is not None:
        was_active = job.is_active
        job.is_active = payload.is_active
        if payload.is_active and not was_active:
            try:
                now = datetime.now(ZoneInfo("Asia/Shanghai"))
                job.next_run_at = croniter(job.cron_expression, now).get_next(datetime)
            except (CroniterBadCronError, CroniterBadDateError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cron 表达式无效",
                ) from None
        if not payload.is_active:
            job.next_run_at = None
    if payload.env is not None:
        job.env = payload.env
    if payload.marker_expression is not None:
        job.marker_expression = payload.marker_expression
    if payload.keyword_expression is not None:
        job.keyword_expression = payload.keyword_expression

    await db.commit()
    await db.refresh(job)
    return job


@router.delete("/projects/{project_id}/cron-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cron_job(
    project_id: int,
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(CronJob).where(
            CronJob.id == job_id,
            CronJob.project_id == project_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务不存在",
        )

    await db.delete(job)
    await db.commit()


@router.post("/projects/{project_id}/cron-jobs/{job_id}/run", response_model=dict)
async def run_cron_job_now(
    project_id: int,
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int | str]:
    await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(CronJob).where(
            CronJob.id == job_id,
            CronJob.project_id == project_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务不存在",
        )

    config = {
        "env": job.env,
        "marker_expression": job.marker_expression,
        "keyword_expression": job.keyword_expression,
    }
    execution = TestExecution(
        project_id=project_id,
        status="pending",
        trigger_type="scheduled",
        config=config,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    task = run_test_execution.delay(execution.id)

    return {
        "id": execution.id,
        "execution_id": execution.id,
        "task_id": task.id,
        "status": "accepted",
        "message": f"定时任务已触发 (ID: {job.id})",
    }
