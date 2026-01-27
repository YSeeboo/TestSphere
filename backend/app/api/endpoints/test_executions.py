"""测试执行相关 API 端点."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.project import Project
from app.models.test_execution import TestExecution
from app.models.user import User
from app.schemas.test_execution import TestExecutionCreate, TestExecutionOut
from app.tasks.test_execution import run_test_execution

router = APIRouter()


@router.post("/{project_id}/run", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def trigger_test_execution(
    project_id: int,
    execution_in: TestExecutionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int | str]:
    """
    触发测试执行任务.
    
    该接口会创建一条测试执行记录，并异步触发 Celery 任务来执行测试。
    只能触发当前用户拥有的项目的测试。
    
    Args:
        project_id: 项目 ID
        execution_in: 测试执行配置 (env, marker_expression, keyword_expression)
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        dict: 包含 execution_id 和状态信息
        
    Raises:
        HTTPException: 404 项目不存在或无权访问
    """
    # 检查项目是否存在且属于当前用户
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在或无权访问"
        )
    
    # 构建执行配置
    config = {
        "env": execution_in.env,
        "marker_expression": execution_in.marker_expression,
        "keyword_expression": execution_in.keyword_expression,
    }
    
    # 创建测试执行记录
    execution = TestExecution(
        project_id=project_id,
        status="pending",
        trigger_type="manual",
        config=config,
    )
    
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    # 触发异步任务
    task = run_test_execution.delay(execution.id)
    
    return {
        "execution_id": execution.id,
        "task_id": task.id,
        "status": "accepted",
        "message": f"测试执行任务已提交 (ID: {execution.id})",
    }


@router.get("/{execution_id}", response_model=TestExecutionOut)
async def get_test_execution(
    execution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TestExecution:
    """
    获取测试执行详情.
    
    该接口用于查询测试执行的状态和日志，支持前端轮询。
    只能查询当前用户拥有的项目的测试执行记录。
    
    Args:
        execution_id: 测试执行记录 ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        TestExecution: 测试执行详情
        
    Raises:
        HTTPException: 404 测试执行记录不存在或无权访问
    """
    # 查询测试执行记录 (需要 join project 以检查权限)
    result = await db.execute(
        select(TestExecution)
        .join(Project, TestExecution.project_id == Project.id)
        .where(
            TestExecution.id == execution_id,
            Project.owner_id == current_user.id
        )
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试执行记录不存在或无权访问"
        )
    
    return execution
