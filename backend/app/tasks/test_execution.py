"""测试执行任务.

负责运行测试执行并更新执行状态。
"""

import logging
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import docker
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.test_execution import TestExecution
from app.models.project import Project
from app.worker.utils import build_test_command

# 配置日志
logger = logging.getLogger(__name__)

# 定义目录路径常量
REPOS_BASE_DIR = Path("/tmp/atp_repos")
RUNS_BASE_DIR = Path("/tmp/atp_runs")
STATIC_BASE_DIR = Path("/app/static")
REPORTS_BASE_DIR = STATIC_BASE_DIR / "reports"


def _ensure_directory_exists(directory: Path) -> None:
    """确保目录存在，如果不存在则创建.
    
    Args:
        directory: 目录路径
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"确保目录存在: {directory}")
    except Exception as e:
        logger.error(f"创建目录 {directory} 失败: {e}")
        raise


def _copy_repo_to_run_dir(repo_path: Path, run_path: Path) -> None:
    """将代码仓库复制到执行目录.
    
    Args:
        repo_path: 源代码仓库路径
        run_path: 目标执行目录路径
        
    Raises:
        FileNotFoundError: 如果源代码目录不存在
        Exception: 如果复制过程出现错误
    """
    if not repo_path.exists():
        raise FileNotFoundError(f"源代码目录不存在: {repo_path}")
    
    if not repo_path.is_dir():
        raise ValueError(f"源代码路径不是目录: {repo_path}")
    
    logger.info(f"开始复制代码: {repo_path} -> {run_path}")
    
    # 定义需要忽略的目录/文件
    def ignore_patterns(directory: str, contents: list[str]) -> set[str]:
        """返回需要忽略的文件/目录列表."""
        ignored = set()
        for item in contents:
            # 忽略 .git 目录以加快复制速度
            if item == ".git":
                ignored.add(item)
            # 可以添加其他忽略规则，如 __pycache__, .pyc 等
            elif item == "__pycache__" or item.endswith(".pyc"):
                ignored.add(item)
        return ignored
    
    try:
        # 如果目标目录已存在，先删除
        if run_path.exists():
            logger.warning(f"执行目录已存在，先删除: {run_path}")
            shutil.rmtree(run_path)
        
        # 复制整个目录树
        shutil.copytree(
            src=repo_path,
            dst=run_path,
            ignore=ignore_patterns,
            dirs_exist_ok=False
        )
        
        logger.info(f"代码复制完成: {run_path}")
        
    except Exception as e:
        logger.error(f"复制代码失败: {e}")
        raise


@celery_app.task(name="worker.run_test_execution", bind=True)
def run_test_execution(self, execution_id: int) -> dict[str, Any]:
    """
    执行测试任务.
    
    执行流程 (Part 2.1 版本):
    1. 从数据库获取执行记录
    2. 检查代码源目录是否存在
    3. 准备执行目录并复制代码
    4. 更新状态为 'running'
    5. 模拟测试执行 (sleep 5 秒)
    6. 更新状态为 'success'
    
    后续版本将实现 Docker 容器执行逻辑。
    
    Args:
        execution_id: 测试执行记录 ID
        
    Returns:
        dict: 包含执行结果的字典
            - status: "success" | "failed"
            - message: 结果描述
            - execution_id: 执行记录 ID
    """
    logger.info(f"开始执行测试任务 {execution_id}")

    db = SessionLocal()
    execution: TestExecution | None = None
    container = None
    run_path = None

    try:
        # ==================== 1. 获取执行记录 ====================
        result = db.execute(
            select(TestExecution).where(TestExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        
        if not execution:
            logger.error(f"测试执行记录 {execution_id} 不存在")
            return {
                "status": "failed",
                "message": f"测试执行记录 {execution_id} 不存在",
                "execution_id": execution_id,
            }
        
        # 检查项目是否存在
        project_result = db.execute(
            select(Project).where(Project.id == execution.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            logger.error(f"项目 {execution.project_id} 不存在")
            execution.status = "failed"
            execution.logs = f"项目 {execution.project_id} 不存在"
            execution.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "status": "failed",
                "message": f"项目 {execution.project_id} 不存在",
                "execution_id": execution_id,
            }
        
        # ==================== 2. 检查代码源目录 ====================
        repo_path = REPOS_BASE_DIR / str(project.id)
        
        logger.info(f"检查代码源目录: {repo_path}")
        
        if not repo_path.exists():
            error_msg = (
                f"代码源目录不存在: {repo_path}。"
                f"请先执行项目同步任务 (sync_project) 拉取代码。"
            )
            logger.error(error_msg)
            execution.status = "failed"
            execution.logs = f"[{datetime.now(timezone.utc).isoformat()}] 错误: {error_msg}\n"
            execution.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "status": "failed",
                "message": error_msg,
                "execution_id": execution_id,
            }
        
        # ==================== 3. 准备执行目录并复制代码 ====================
        run_path = RUNS_BASE_DIR / str(execution_id)
        
        logger.info(f"准备执行目录: {run_path}")
        
        # 确保基础目录存在
        _ensure_directory_exists(RUNS_BASE_DIR)
        
        # 复制代码到执行目录
        try:
            _copy_repo_to_run_dir(repo_path, run_path)
        except Exception as e:
            error_msg = f"复制代码到执行目录失败: {e}"
            logger.error(error_msg)
            execution.status = "failed"
            execution.logs = f"[{datetime.now(timezone.utc).isoformat()}] 错误: {error_msg}\n"
            execution.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "status": "failed",
                "message": error_msg,
                "execution_id": execution_id,
            }

        # 确保 Allure 结果目录存在（供 pytest 写入）
        try:
            _ensure_directory_exists(run_path / "allure-results")
        except Exception as e:
            logger.warning(f"创建 Allure 结果目录失败: {e}")
        
        # ==================== 4. 更新状态为 running ====================
        logger.info(f"更新测试执行 {execution_id} 状态为 running")
        execution.status = "running"
        execution.logs = f"[{datetime.now(timezone.utc).isoformat()}] 开始执行测试\n"
        execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 代码源: {repo_path}\n"
        execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 执行目录: {run_path}\n"
        execution.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        # ==================== 5. Docker 容器执行 ====================
        logger.info(f"开始 Docker 容器执行测试")
        
        # 记录配置信息到日志
        config = execution.config or {}
        
        execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 配置信息:\n"
        execution.logs += f"  - Config: {config}\n"
        db.commit()
        
        # 构建测试命令
        try:
            cmd = build_test_command(config)
            if "--alluredir=" not in cmd:
                cmd = cmd.replace(
                    "pytest",
                    "pytest --alluredir=/app/allure-results",
                    1,
                )
            logger.info(f"构建的测试命令: {cmd}")
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 执行命令: {cmd}\n"
            db.commit()
        except Exception as e:
            error_msg = f"构建测试命令失败: {e}"
            logger.error(error_msg)
            execution.status = "failed"
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 错误: {error_msg}\n"
            execution.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "status": "failed",
                "message": error_msg,
                "execution_id": execution_id,
            }
        
        # Docker 容器执行
        container = None
        try:
            # 连接 Docker
            logger.info("连接 Docker 守护进程")
            client = docker.from_env()
            
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] Docker 连接成功\n"
            db.commit()
            
            # 运行容器
            logger.info(f"启动 Docker 容器执行测试")
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 启动 Docker 容器...\n"
            db.commit()
            
            container = client.containers.run(
                image="python:3.11-slim",
                command=cmd,
                volumes={str(run_path): {'bind': '/app', 'mode': 'rw'}},
                working_dir="/app",
                detach=True,
                remove=False  # 不自动删除，我们需要获取日志
            )
            
            logger.info(f"容器已启动: {container.id}")
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 容器 ID: {container.short_id}\n"
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 等待容器执行完成...\n"
            db.commit()
            
            # 等待容器执行完成（设置超时比 Celery soft_time_limit 稍短）
            result = container.wait(timeout=2700)  # 45 分钟
            exit_code = result.get('StatusCode', -1)
            
            logger.info(f"容器执行完成，退出码: {exit_code}")
            
            # 获取容器日志
            logs = container.logs().decode('utf-8', errors='replace')
            
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 容器执行完成\n"
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 退出码: {exit_code}\n"
            execution.logs += f"\n{'='*60}\n"
            execution.logs += f"容器输出日志:\n"
            execution.logs += f"{'='*60}\n"
            execution.logs += logs
            execution.logs += f"\n{'='*60}\n"

            # ==================== 6. 生成 Allure 报告 ====================
            allure_results_dir = run_path / "allure-results"
            report_dir = REPORTS_BASE_DIR / str(execution_id)

            try:
                _ensure_directory_exists(REPORTS_BASE_DIR)

                if not allure_results_dir.exists():
                    execution.logs += (
                        f"[{datetime.now(timezone.utc).isoformat()}] ⚠️ 未找到 Allure 结果目录: "
                        f"{allure_results_dir}\n"
                    )
                else:
                    logger.info(f"生成 Allure 报告: {allure_results_dir} -> {report_dir}")
                    allure_result = subprocess.run(
                        [
                            "allure",
                            "generate",
                            str(allure_results_dir),
                            "-o",
                            str(report_dir),
                            "--clean",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    execution.logs += (
                        f"[{datetime.now(timezone.utc).isoformat()}] "
                        f"Allure 报告生成完成 (退出码: {allure_result.returncode})\n"
                    )
                    if allure_result.stdout:
                        execution.logs += allure_result.stdout + "\n"
                    if allure_result.stderr:
                        execution.logs += allure_result.stderr + "\n"
            except FileNotFoundError:
                execution.logs += (
                    f"[{datetime.now(timezone.utc).isoformat()}] "
                    "❌ 未找到 Allure CLI，请确认容器已安装 allure\n"
                )
            except Exception as e:
                execution.logs += (
                    f"[{datetime.now(timezone.utc).isoformat()}] "
                    f"❌ 生成 Allure 报告失败: {e}\n"
                )

            # ==================== 7. 根据退出码更新状态 ====================
            if exit_code == 0:
                execution.status = "success"
                execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] ✅ 测试执行成功\n"
                logger.info(f"测试执行 {execution_id} 成功完成")
            else:
                execution.status = "failed"
                execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] ❌ 测试执行失败 (退出码: {exit_code})\n"
                logger.warning(f"测试执行 {execution_id} 失败，退出码: {exit_code}")
            
            execution.updated_at = datetime.now(timezone.utc)
            db.commit()
            
        except docker.errors.DockerException as docker_error:
            # Docker 相关错误
            error_msg = f"Docker 执行错误: {docker_error}"
            logger.error(error_msg)

            execution.status = "failed"
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] ❌ Docker 错误: {docker_error}\n"
            execution.updated_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "status": "failed",
                "message": error_msg,
                "execution_id": execution_id,
            }

        except Exception as exec_error:
            # 其他执行错误
            error_msg = f"执行过程错误: {exec_error}"
            logger.error(error_msg)

            execution.status = "failed"
            execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] ❌ 执行错误: {exec_error}\n"
            execution.updated_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "status": "failed",
                "message": error_msg,
                "execution_id": execution_id,
            }
        
        logger.info(f"测试执行 {execution_id} 成功完成")
        
        return {
            "status": "success",
            "message": "测试执行成功",
            "execution_id": execution_id,
        }
        
    except Exception as e:
        logger.exception(f"测试执行 {execution_id} 失败: {e}")
        
        # 更新执行状态为失败
        if execution:
            try:
                execution.status = "failed"
                if execution.logs:
                    execution.logs += f"[{datetime.now(timezone.utc).isoformat()}] 错误: {str(e)}\n"
                else:
                    execution.logs = f"[{datetime.now(timezone.utc).isoformat()}] 错误: {str(e)}\n"
                execution.updated_at = datetime.now(timezone.utc)
                db.commit()
            except Exception as commit_error:
                logger.error(f"更新执行状态失败: {commit_error}")
                db.rollback()
        
        return {
            "status": "failed",
            "message": "测试执行失败",
            "error": str(e),
            "execution_id": execution_id,
        }
        
    finally:
        # 清理 Docker 容器
        if container:
            try:
                container.remove(force=True)
                logger.info(f"容器已清理: {container.short_id}")
            except Exception as e:
                logger.error(f"容器清理失败: {e}")

        # 清理执行目录
        if run_path and run_path.exists():
            try:
                shutil.rmtree(run_path)
                logger.info(f"已清理执行目录: {run_path}")
            except Exception as e:
                logger.warning(f"清理执行目录失败: {e}")

        db.close()
