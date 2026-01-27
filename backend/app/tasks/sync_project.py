"""项目同步任务.

负责从 Git 仓库拉取代码并解析 pytest 测试用例入库。
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import git
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.project import Project
from app.models.test_case import TestCase

# 配置日志
logger = logging.getLogger(__name__)

# Git 仓库存储根目录
REPOS_ROOT = Path("/tmp/atp_repos")


@celery_app.task(name="worker.sync_project_test_cases", bind=True)
def sync_project_test_cases(self, project_id: int) -> dict[str, Any]:
    """
    同步项目测试用例任务.
    
    执行流程:
    1. 从数据库获取项目信息
    2. 执行 Git 操作 (clone 或 pull)
    3. 运行 pytest 收集测试用例
    4. 解析 JSON 报告并入库 (Upsert)
    5. 更新项目同步状态
    
    Args:
        project_id: 项目 ID
        
    Returns:
        dict: 包含同步结果的字典
            - status: "success" | "failed"
            - message: 结果描述
            - test_cases_count: 同步的测试用例数量 (成功时)
            - error: 错误信息 (失败时)
    """
    logger.info(f"开始同步项目 {project_id} 的测试用例")
    
    db = SessionLocal()
    project: Project | None = None
    
    try:
        # ==================== 1. 获取项目信息 ====================
        result = db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            logger.error(f"项目 {project_id} 不存在")
            return {
                "status": "failed",
                "message": f"项目 {project_id} 不存在",
            }
        
        if not project.git_url:
            logger.error(f"项目 {project_id} 未配置 Git 仓库地址")
            project.last_sync_status = "Failed"
            db.commit()
            return {
                "status": "failed",
                "message": "项目未配置 Git 仓库地址",
            }
        
        # 更新同步状态为进行中
        project.last_sync_status = "Syncing"
        db.commit()
        
        # ==================== 2. Git 操作 ====================
        repo_path = REPOS_ROOT / str(project_id)
        
        # 确保根目录存在
        REPOS_ROOT.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Git 仓库路径: {repo_path}")
        
        if repo_path.exists():
            # 目录存在，执行 pull 操作
            logger.info(f"仓库已存在，执行 git pull")
            try:
                repo = git.Repo(repo_path)
                origin = repo.remotes.origin
                
                # 切换到指定分支
                if project.git_branch:
                    logger.info(f"切换到分支: {project.git_branch}")
                    repo.git.checkout(project.git_branch)
                
                # 拉取最新代码
                origin.pull()
                logger.info("Git pull 成功")
            except git.GitCommandError as e:
                logger.error(f"Git pull 失败: {e}")
                raise Exception(f"Git pull 失败: {e}")
        else:
            # 目录不存在，执行 clone 操作
            logger.info(f"仓库不存在，执行 git clone")
            try:
                repo = git.Repo.clone_from(
                    project.git_url,
                    repo_path,
                    branch=project.git_branch or "main",
                )
                logger.info("Git clone 成功")
            except git.GitCommandError as e:
                logger.error(f"Git clone 失败: {e}")
                raise Exception(f"Git clone 失败: {e}")
        
        # ==================== 3. Pytest 解析 ====================
        logger.info("开始执行 pytest 收集测试用例")
        
        # JSON 报告输出路径
        report_path = repo_path / "pytest_report.json"
        
        # 构建 pytest 命令
        # --collect-only: 只收集测试用例，不执行
        # -q: 安静模式
        # --json-report: 生成 JSON 报告
        # --json-report-file: 指定报告文件路径
        cmd = [
            "pytest",
            "--collect-only",
            "-q",
            "--json-report",
            f"--json-report-file={report_path.name}",
        ]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
            )
            
            # pytest --collect-only 即使没有测试也会返回 0 或 5 (没有收集到测试)
            # 我们认为这两种情况都是正常的
            if result.returncode not in (0, 5):
                logger.error(f"Pytest 执行失败 (返回码: {result.returncode})")
                logger.error(f"stdout: {result.stdout}")
                logger.error(f"stderr: {result.stderr}")
                raise Exception(f"Pytest 执行失败: {result.stderr}")
            
            logger.info("Pytest 收集成功")
            
        except subprocess.TimeoutExpired:
            logger.error("Pytest 执行超时")
            raise Exception("Pytest 执行超时 (5分钟)")
        except Exception as e:
            logger.error(f"Pytest 执行异常: {e}")
            raise
        
        # ==================== 4. 解析 JSON 报告 ====================
        logger.info(f"开始解析 JSON 报告: {report_path}")
        
        if not report_path.exists():
            logger.error("JSON 报告文件不存在")
            raise Exception("JSON 报告文件不存在")
        
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        
        # 解析测试用例
        test_cases_data = _parse_pytest_report(report_data)
        logger.info(f"解析到 {len(test_cases_data)} 个测试用例")
        
        # ==================== 5. 入库 (Upsert) ====================
        logger.info("开始入库测试用例")
        
        upserted_count = 0
        
        for tc_data in test_cases_data:
            # 根据 project_id + nodeid 查找是否存在
            result = db.execute(
                select(TestCase).where(
                    TestCase.project_id == project_id,
                    TestCase.nodeid == tc_data["nodeid"],
                )
            )
            existing_tc = result.scalar_one_or_none()
            
            if existing_tc:
                # 更新现有测试用例
                existing_tc.file_path = tc_data["file_path"]
                existing_tc.name = tc_data["name"]
                existing_tc.description = tc_data.get("description")
                existing_tc.markers = tc_data.get("markers")
                existing_tc.updated_at = datetime.utcnow()
                logger.debug(f"更新测试用例: {tc_data['nodeid']}")
            else:
                # 创建新测试用例
                new_tc = TestCase(
                    project_id=project_id,
                    file_path=tc_data["file_path"],
                    name=tc_data["name"],
                    description=tc_data.get("description"),
                    nodeid=tc_data["nodeid"],
                    markers=tc_data.get("markers"),
                )
                db.add(new_tc)
                logger.debug(f"创建测试用例: {tc_data['nodeid']}")
            
            upserted_count += 1
        
        # ==================== 6. 更新项目同步状态 ====================
        project.last_sync_time = datetime.utcnow()
        project.last_sync_status = "Success"
        
        db.commit()
        
        logger.info(f"项目 {project_id} 同步完成，共处理 {upserted_count} 个测试用例")
        
        return {
            "status": "success",
            "message": "同步成功",
            "test_cases_count": upserted_count,
        }
        
    except Exception as e:
        logger.exception(f"项目 {project_id} 同步失败: {e}")
        
        # 更新项目同步状态为失败
        if project:
            try:
                project.last_sync_status = "Failed"
                project.last_sync_time = datetime.utcnow()
                db.commit()
            except Exception as commit_error:
                logger.error(f"更新项目状态失败: {commit_error}")
                db.rollback()
        
        return {
            "status": "failed",
            "message": "同步失败",
            "error": str(e),
        }
        
    finally:
        db.close()


def _parse_pytest_report(report_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    解析 pytest-json-report 生成的 JSON 报告.
    
    pytest-json-report 的结构示例:
    {
        "collectors": [
            {
                "nodeid": "",
                "outcome": "passed",
                "result": [
                    {
                        "nodeid": "tests/test_example.py::test_func",
                        "type": "Function",
                        "lineno": 10,
                        "doc": "测试函数的 docstring"
                    }
                ]
            }
        ]
    }
    
    Args:
        report_data: pytest-json-report 生成的 JSON 数据
        
    Returns:
        list[dict]: 解析后的测试用例列表，每个元素包含:
            - nodeid: pytest nodeid
            - file_path: 文件路径
            - name: 测试函数名
            - description: 描述 (从 docstring 提取)
            - markers: markers 信息
    """
    test_cases = []
    
    # 获取 collectors 列表
    collectors = report_data.get("collectors", [])
    
    if not collectors:
        logger.warning("报告中没有 collectors 数据")
        return test_cases
    
    for collector in collectors:
        # 获取收集结果
        result = collector.get("result", [])
        
        if not result:
            continue
        
        for item in result:
            # 只处理测试函数 (type == "Function")
            if item.get("type") != "Function":
                continue
            
            nodeid = item.get("nodeid", "")
            
            if not nodeid:
                logger.warning("测试用例缺少 nodeid，跳过")
                continue
            
            # 从 nodeid 中提取文件路径和函数名
            # nodeid 格式: tests/api/test_login.py::TestClass::test_method
            # 或: tests/api/test_login.py::test_function
            parts = nodeid.split("::")
            file_path = parts[0] if parts else ""
            name = parts[-1] if len(parts) > 1 else ""
            
            # 提取 docstring 作为描述
            description = item.get("doc", "")
            if description:
                # 清理 docstring (去除多余空白)
                description = description.strip()
            
            # 提取 markers
            markers_data = item.get("markers", [])
            markers = None
            if markers_data:
                # markers 是一个列表，每个元素是一个 marker 对象
                # 我们将其转换为字典存储
                markers = {
                    "markers": [
                        {
                            "name": m.get("name", ""),
                            "args": m.get("args", []),
                            "kwargs": m.get("kwargs", {}),
                        }
                        for m in markers_data
                    ]
                }
            
            test_cases.append({
                "nodeid": nodeid,
                "file_path": file_path,
                "name": name,
                "description": description if description else None,
                "markers": markers,
            })
    
    return test_cases
