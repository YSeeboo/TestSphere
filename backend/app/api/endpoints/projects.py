"""项目相关 API 端点."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from app.schemas.test_case import TestCaseListResponse, TestCaseOut
from app.tasks.sync_project import sync_project_test_cases

router = APIRouter()


@router.get("/", response_model=list[ProjectOut])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    """
    获取当前登录用户的所有项目.
    
    Args:
        skip: 跳过记录数
        limit: 返回记录数上限
        current_user: 当前用户 (通过 JWT Token 验证)
        db: 数据库会话
        
    Returns:
        list[Project]: 当前用户的项目列表
    """
    result = await db.execute(
        select(Project)
        .where(Project.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    
    return list(projects)


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    创建新项目.
    
    项目的 owner_id 自动设置为当前登录用户的 ID.
    
    Args:
        project_in: 项目创建信息
        current_user: 当前用户 (通过 JWT Token 验证)
        db: 数据库会话
        
    Returns:
        Project: 创建的项目信息
    """
    # 创建新项目，owner_id 自动设为 current_user.id
    project = Project(
        name=project_in.name,
        description=project_in.description,
        git_url=project_in.git_url,
        git_branch=project_in.git_branch,
        owner_id=current_user.id
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    根据 ID 获取项目信息.
    
    只能获取当前用户拥有的项目.
    
    Args:
        project_id: 项目 ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Project: 项目信息
        
    Raises:
        HTTPException: 404 项目不存在或无权访问
    """
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
    
    return project


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    更新项目信息.
    
    只能更新当前用户拥有的项目.
    
    Args:
        project_id: 项目 ID
        project_in: 项目更新信息
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Project: 更新后的项目信息
        
    Raises:
        HTTPException: 404 项目不存在或无权访问
    """
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
    
    # 更新项目字段
    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.git_url is not None:
        project.git_url = project_in.git_url
    if project_in.git_branch is not None:
        project.git_branch = project_in.git_branch
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    删除项目.
    
    只能删除当前用户拥有的项目 (必须检查 project.owner_id == current_user.id).
    
    Args:
        project_id: 项目 ID
        current_user: 当前用户
        db: 数据库会话
        
    Raises:
        HTTPException: 404 项目不存在或无权访问
    """
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
    
    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    触发项目同步任务.
    
    该接口会异步触发 Celery 任务来同步项目的测试用例:
    1. 从 Git 仓库拉取最新代码
    2. 使用 pytest 收集测试用例
    3. 将测试用例信息保存到数据库
    
    只能同步当前用户拥有的项目.
    
    Args:
        project_id: 项目 ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        dict: 包含任务 ID 和状态信息
        
    Raises:
        HTTPException: 404 项目不存在或无权访问
        HTTPException: 400 项目未配置 Git 仓库
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
    
    # 检查是否配置了 Git 仓库
    if not project.git_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目未配置 Git 仓库地址"
        )
    
    # 触发异步任务
    task = sync_project_test_cases.delay(project_id)
    
    return {
        "task_id": task.id,
        "status": "accepted",
        "message": f"项目 {project.name} 的同步任务已提交"
    }


@router.get("/{project_id}/test-cases", response_model=TestCaseListResponse)
async def get_project_test_cases(
    project_id: int,
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TestCaseListResponse:
    """
    获取项目的测试用例列表 (分页).
    
    该接口会返回指定项目下的所有测试用例，支持分页查询。
    只能获取当前用户拥有的项目的测试用例。
    
    Args:
        project_id: 项目 ID
        limit: 每页数量 (默认 20，最大 100)
        offset: 偏移量 (默认 0)
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        TestCaseListResponse: 测试用例列表和总数
        
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
    
    # 查询测试用例总数
    count_result = await db.execute(
        select(func.count(TestCase.id)).where(TestCase.project_id == project_id)
    )
    total = count_result.scalar_one()
    
    # 查询测试用例列表
    test_cases_result = await db.execute(
        select(TestCase)
        .where(TestCase.project_id == project_id)
        .order_by(TestCase.id.desc())
        .offset(offset)
        .limit(limit)
    )
    test_cases = test_cases_result.scalars().all()
    
    # 转换为 Pydantic 模型
    items = [TestCaseOut.model_validate(tc) for tc in test_cases]
    
    return TestCaseListResponse(items=items, total=total)
