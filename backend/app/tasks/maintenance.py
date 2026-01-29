"""维护任务.

负责清理资源和恢复异常状态。
"""

import logging
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select, or_

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.test_execution import TestExecution
from app.models.project import Project

# 配置日志
logger = logging.getLogger(__name__)

# 定义目录路径常量
REPOS_BASE_DIR = Path("/tmp/atp_repos")
RUNS_BASE_DIR = Path("/tmp/atp_runs")


@celery_app.task(name="worker.reset_stuck_statuses")
def reset_stuck_statuses() -> dict[str, Any]:
    """
    重置卡住的状态.

    检测并重置超时的 "running" 和 "Syncing" 状态，防止 Worker 进程被强制 kill 后
    状态永久卡住。

    超时阈值:
    - 测试执行 (running): 3600 秒 (1 小时，匹配 Celery task_time_limit)
    - 项目同步 (Syncing): 600 秒 (10 分钟)

    Returns:
        dict: 包含重置结果的字典
            - status: "success"
            - reset_executions: 重置的测试执行数量
            - reset_projects: 重置的项目数量
    """
    logger.info("开始检查卡住的状态")

    db = SessionLocal()
    reset_executions_count = 0
    reset_projects_count = 0

    try:
        # ==================== 1. 重置卡住的测试执行 ====================
        # 查找状态为 "running" 且超过 1 小时未更新的执行记录
        execution_timeout = datetime.now(timezone.utc) - timedelta(hours=1)

        result = db.execute(
            select(TestExecution).where(
                TestExecution.status == "running",
                TestExecution.updated_at < execution_timeout
            )
        )
        stuck_executions = result.scalars().all()

        for execution in stuck_executions:
            logger.warning(
                f"检测到卡住的测试执行: ID={execution.id}, "
                f"最后更新时间={execution.updated_at}"
            )

            execution.status = "failed"
            execution.logs += (
                f"\n[{datetime.now(timezone.utc).isoformat()}] "
                f"⚠️ 执行超时，自动标记为失败 (Worker 可能被强制终止)\n"
            )
            execution.updated_at = datetime.now(timezone.utc)
            reset_executions_count += 1

        # ==================== 2. 重置卡住的项目同步 ====================
        # 查找状态为 "Syncing" 且超过 10 分钟未更新的项目
        sync_timeout = datetime.now(timezone.utc) - timedelta(minutes=10)

        result = db.execute(
            select(Project).where(
                Project.last_sync_status == "Syncing",
                or_(
                    Project.last_sync_time < sync_timeout,
                    Project.last_sync_time.is_(None)
                )
            )
        )
        stuck_projects = result.scalars().all()

        for project in stuck_projects:
            logger.warning(
                f"检测到卡住的项目同步: ID={project.id}, "
                f"最后同步时间={project.last_sync_time}"
            )

            project.last_sync_status = "Failed"
            project.last_sync_time = datetime.now(timezone.utc)
            reset_projects_count += 1

        db.commit()

        logger.info(
            f"状态重置完成: 测试执行={reset_executions_count}, "
            f"项目同步={reset_projects_count}"
        )

        return {
            "status": "success",
            "reset_executions": reset_executions_count,
            "reset_projects": reset_projects_count,
        }

    except Exception as e:
        logger.exception(f"重置卡住状态失败: {e}")
        db.rollback()

        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        db.close()


@celery_app.task(name="worker.cleanup_old_repos")
def cleanup_old_repos(days: int = 30) -> dict[str, Any]:
    """
    清理旧的 Git 仓库目录.

    删除超过指定天数未访问的 Git 仓库目录，释放磁盘空间。
    同时清理数据库中已删除项目的仓库。

    Args:
        days: 保留天数，默认 30 天

    Returns:
        dict: 包含清理结果的字典
            - status: "success" | "failed"
            - cleaned_repos: 清理的仓库数量
            - freed_space_mb: 释放的磁盘空间 (MB)
    """
    logger.info(f"开始清理 {days} 天前的旧仓库")

    db = SessionLocal()
    cleaned_count = 0
    freed_space = 0

    try:
        if not REPOS_BASE_DIR.exists():
            logger.info("仓库根目录不存在，无需清理")
            return {
                "status": "success",
                "cleaned_repos": 0,
                "freed_space_mb": 0,
            }

        # 获取所有现存项目的 ID
        result = db.execute(select(Project.id))
        active_project_ids = {str(pid) for pid in result.scalars().all()}

        # 遍历仓库目录
        for repo_dir in REPOS_BASE_DIR.iterdir():
            if not repo_dir.is_dir():
                continue

            project_id = repo_dir.name

            # 检查是否是已删除项目的仓库
            if project_id not in active_project_ids:
                logger.info(f"发现已删除项目的仓库: {project_id}")

                try:
                    # 计算目录大小
                    dir_size = sum(
                        f.stat().st_size for f in repo_dir.rglob('*') if f.is_file()
                    )
                    freed_space += dir_size

                    # 删除目录
                    shutil.rmtree(repo_dir)
                    logger.info(f"已删除仓库目录: {repo_dir}")
                    cleaned_count += 1

                except Exception as e:
                    logger.error(f"删除仓库目录 {repo_dir} 失败: {e}")
                    continue

            else:
                # 检查目录的最后访问时间
                try:
                    last_access_time = datetime.fromtimestamp(
                        repo_dir.stat().st_atime, tz=timezone.utc
                    )
                    cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

                    if last_access_time < cutoff_time:
                        logger.info(
                            f"发现长期未使用的仓库: {project_id}, "
                            f"最后访问={last_access_time}"
                        )

                        # 计算目录大小
                        dir_size = sum(
                            f.stat().st_size for f in repo_dir.rglob('*')
                            if f.is_file()
                        )
                        freed_space += dir_size

                        # 删除目录
                        shutil.rmtree(repo_dir)
                        logger.info(f"已删除仓库目录: {repo_dir}")
                        cleaned_count += 1

                except Exception as e:
                    logger.error(f"检查/删除仓库目录 {repo_dir} 失败: {e}")
                    continue

        freed_space_mb = freed_space / (1024 * 1024)

        logger.info(
            f"仓库清理完成: 清理数量={cleaned_count}, "
            f"释放空间={freed_space_mb:.2f} MB"
        )

        return {
            "status": "success",
            "cleaned_repos": cleaned_count,
            "freed_space_mb": round(freed_space_mb, 2),
        }

    except Exception as e:
        logger.exception(f"清理旧仓库失败: {e}")

        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        db.close()


@celery_app.task(name="worker.cleanup_old_run_dirs")
def cleanup_old_run_dirs(hours: int = 24) -> dict[str, Any]:
    """
    清理旧的执行目录.

    删除超过指定小时数的执行目录 (可能是清理失败遗留的)。
    正常情况下，执行目录应该在 finally 块中被清理。

    Args:
        hours: 保留小时数，默认 24 小时

    Returns:
        dict: 包含清理结果的字典
            - status: "success" | "failed"
            - cleaned_dirs: 清理的目录数量
            - freed_space_mb: 释放的磁盘空间 (MB)
    """
    logger.info(f"开始清理 {hours} 小时前的旧执行目录")

    cleaned_count = 0
    freed_space = 0

    try:
        if not RUNS_BASE_DIR.exists():
            logger.info("执行目录根目录不存在，无需清理")
            return {
                "status": "success",
                "cleaned_dirs": 0,
                "freed_space_mb": 0,
            }

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # 遍历执行目录
        for run_dir in RUNS_BASE_DIR.iterdir():
            if not run_dir.is_dir():
                continue

            try:
                # 检查目录的修改时间
                last_modified_time = datetime.fromtimestamp(
                    run_dir.stat().st_mtime, tz=timezone.utc
                )

                if last_modified_time < cutoff_time:
                    logger.info(
                        f"发现过期的执行目录: {run_dir.name}, "
                        f"最后修改={last_modified_time}"
                    )

                    # 计算目录大小
                    dir_size = sum(
                        f.stat().st_size for f in run_dir.rglob('*')
                        if f.is_file()
                    )
                    freed_space += dir_size

                    # 删除目录
                    shutil.rmtree(run_dir)
                    logger.info(f"已删除执行目录: {run_dir}")
                    cleaned_count += 1

            except Exception as e:
                logger.error(f"删除执行目录 {run_dir} 失败: {e}")
                continue

        freed_space_mb = freed_space / (1024 * 1024)

        logger.info(
            f"执行目录清理完成: 清理数量={cleaned_count}, "
            f"释放空间={freed_space_mb:.2f} MB"
        )

        return {
            "status": "success",
            "cleaned_dirs": cleaned_count,
            "freed_space_mb": round(freed_space_mb, 2),
        }

    except Exception as e:
        logger.exception(f"清理旧执行目录失败: {e}")

        return {
            "status": "failed",
            "error": str(e),
        }
