from __future__ import annotations

from sqlalchemy import exists, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project, ProjectMember, ProjectMemberRole
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.utils.time_tools import utc_now


class ProjectServiceError(Exception):
    """项目服务层基础异常。"""


class ProjectNotFoundError(ProjectServiceError):
    """项目不存在异常。"""


class ProjectAccessDeniedError(ProjectServiceError):
    """当前用户无权访问项目异常。"""


class ProjectMemberNotFoundError(ProjectServiceError):
    """项目成员不存在异常。"""


class ProjectMemberConflictError(ProjectServiceError):
    """项目成员已存在异常。"""


async def get_project_by_id(
    session: AsyncSession,
    project_id: int,
    current_user_public_id: str,
) -> Project | None:
    """按内部主键查询单个项目。"""
    project = await _get_project_by_id(session, project_id)
    if project is None:
        return None
    await _ensure_project_access(session, project, current_user_public_id)
    return project


async def _get_project_by_id(
    session: AsyncSession,
    project_id: int,
) -> Project | None:
    """按内部主键查询单个项目，不做权限过滤。"""
    statement = select(Project).where(Project.id == project_id)
    result = await session.exec(statement)
    return result.first()


async def get_project_by_public_id(
    session: AsyncSession,
    public_id: str,
    current_user_public_id: str,
) -> Project | None:
    """按公开 ID 查询单个项目。"""
    project = await _get_project_by_public_id(session, public_id)
    if project is None:
        return None
    await _ensure_project_access(session, project, current_user_public_id)
    return project


async def _get_project_by_public_id(
    session: AsyncSession,
    public_id: str,
) -> Project | None:
    """按公开 ID 查询单个项目，不做权限过滤。"""
    statement = select(Project).where(Project.public_id == public_id)
    result = await session.exec(statement)
    return result.first()


async def get_project_or_raise(
    session: AsyncSession,
    public_id: str,
    current_user_public_id: str,
) -> Project:
    """按公开 ID 获取项目，不存在时抛出业务异常。"""
    project = await _get_project_by_public_id(session, public_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")
    await _ensure_project_access(session, project, current_user_public_id)
    return project


async def list_projects(session: AsyncSession, current_user_public_id: str) -> list[Project]:
    """获取当前用户可访问的项目列表。"""
    return await _list_accessible_projects(session, current_user_public_id, select(Project))


async def search_projects_by_name(
    session: AsyncSession,
    current_user_public_id: str,
    name: str,
) -> list[Project]:
    """按项目名搜索当前用户可访问的项目列表。"""
    statement = select(Project)
    keyword = name.strip()
    if keyword:
        statement = statement.where(Project.name.ilike(f"%{keyword}%"))
    return await _list_accessible_projects(session, current_user_public_id, statement)


async def search_projects_by_member(
    session: AsyncSession,
    current_user_public_id: str,
    member_public_id: str,
) -> list[Project]:
    """按项目成员搜索当前用户可访问的项目列表。"""
    statement = select(Project).where(
        or_(
            Project.owner_id == member_public_id,
            _project_has_member_condition(member_public_id),
        )
    )
    return await _list_accessible_projects(session, current_user_public_id, statement)


async def search_project_member_candidates(
    session: AsyncSession,
    project_public_id: str,
    keyword: str,
    current_user_public_id: str,
) -> list[User]:
    """按用户名或邮箱搜索可邀请加入项目的用户。"""
    project = await get_project_or_raise(session, project_public_id, current_user_public_id)
    if project.id is None:
        raise ProjectNotFoundError("Project not found")

    search_keyword = keyword.strip()
    if not search_keyword:
        return []

    statement = (
        select(User)
        .where(
            or_(
                User.username.ilike(f"%{search_keyword}%"),
                User.email.ilike(f"%{search_keyword}%"),
            ),
            User.public_id != project.owner_id,
            ~exists().where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_public_id == User.public_id,
            ),
        )
        .order_by(User.sort_order, User.id)
    )
    result = await session.exec(statement)
    return list(result.all())


async def create_project(session: AsyncSession, owner_public_id: str, payload: ProjectCreate) -> Project:
    """创建项目，并自动把创建者加入 owner 成员。"""
    await _get_current_user_or_raise(session, owner_public_id)

    now = utc_now()
    project = Project(
        **payload.model_dump(),
        owner_id=owner_public_id,
        disabled_at=None,
        created_at=now,
        updated_at=now,
    )
    session.add(project)
    await session.flush()

    if project.id is None:
        raise ProjectServiceError("Project id was not generated")

    owner_member = ProjectMember(
        project_id=project.id,
        user_public_id=owner_public_id,
        role=ProjectMemberRole.OWNER,
        joined_at=now,
    )
    session.add(owner_member)
    await session.commit()
    await session.refresh(project)
    return project


async def update_project(
    session: AsyncSession,
    public_id: str,
    payload: ProjectUpdate,
    current_user_public_id: str,
) -> Project:
    """更新项目基础信息。"""
    project = await get_project_or_raise(session, public_id, current_user_public_id)

    for field_name in payload.model_fields_set:
        value = getattr(payload, field_name)
        if value is not None:
            setattr(project, field_name, value)

    project.updated_at = utc_now()
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def disable_project(
    session: AsyncSession,
    public_id: str,
    current_user_public_id: str,
) -> Project:
    """禁用项目。"""
    project = await get_project_or_raise(session, public_id, current_user_public_id)
    await project.disable()
    project.updated_at = utc_now()
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def enable_project(
    session: AsyncSession,
    public_id: str,
    current_user_public_id: str,
) -> Project:
    """启用项目。"""
    project = await get_project_or_raise(session, public_id, current_user_public_id)
    await project.enable()
    project.updated_at = utc_now()
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def delete_project(
    session: AsyncSession,
    public_id: str,
    current_user_public_id: str,
) -> None:
    """删除项目及其成员关系。"""
    project = await get_project_or_raise(session, public_id, current_user_public_id)
    if project.id is None:
        raise ProjectNotFoundError("Project not found")

    members = await _list_project_members_by_project_id(session, project.id)
    for member in members:
        await session.delete(member)

    await session.delete(project)
    await session.commit()


async def get_project_member(
    session: AsyncSession,
    project_id: int,
    user_public_id: str,
    current_user_public_id: str,
) -> ProjectMember | None:
    """按项目内部主键和用户公开 ID 查询成员关系。"""
    project = await _get_project_by_id(session, project_id)
    if project is None:
        return None
    await _ensure_project_access(session, project, current_user_public_id)
    return await _get_project_member(session, project_id, user_public_id)


async def _get_project_member(
    session: AsyncSession,
    project_id: int,
    user_public_id: str,
) -> ProjectMember | None:
    """按项目内部主键和用户公开 ID 查询成员关系，不做权限过滤。"""
    statement = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_public_id == user_public_id,
    )
    result = await session.exec(statement)
    return result.first()


async def get_project_member_or_raise(
    session: AsyncSession,
    project_id: int,
    user_public_id: str,
    current_user_public_id: str,
) -> ProjectMember:
    """获取项目成员，不存在时抛出业务异常。"""
    member = await get_project_member(session, project_id, user_public_id, current_user_public_id)
    if member is None:
        raise ProjectMemberNotFoundError("Project member not found")
    return member


async def list_project_members(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
) -> list[ProjectMember]:
    """按项目公开 ID 获取项目成员列表。"""
    project = await get_project_or_raise(session, project_public_id, current_user_public_id)
    if project.id is None:
        raise ProjectNotFoundError("Project not found")
    return await _list_project_members_by_project_id(session, project.id)


async def add_project_member(
    session: AsyncSession,
    project_public_id: str,
    user_public_id: str,
    role: ProjectMemberRole,
    current_user_public_id: str,
) -> ProjectMember:
    """新增项目成员。"""
    project = await get_project_or_raise(session, project_public_id, current_user_public_id)
    if project.id is None:
        raise ProjectNotFoundError("Project not found")

    existing_member = await _get_project_member(session, project.id, user_public_id)
    if existing_member is not None:
        raise ProjectMemberConflictError("Project member already exists")

    member = ProjectMember(
        project_id=project.id,
        user_public_id=user_public_id,
        role=role,
        joined_at=utc_now(),
    )
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return member


async def invite_project_member(
    session: AsyncSession,
    project_public_id: str,
    user_public_id: str,
    role: ProjectMemberRole,
    current_user_public_id: str,
) -> ProjectMember:
    """邀请用户加入项目。"""
    await _get_user_by_public_id_or_raise(session, user_public_id)
    return await add_project_member(
        session,
        project_public_id,
        user_public_id,
        role,
        current_user_public_id,
    )


async def update_project_member_role(
    session: AsyncSession,
    project_public_id: str,
    user_public_id: str,
    role: ProjectMemberRole,
    current_user_public_id: str,
) -> ProjectMember:
    """更新项目成员角色。"""
    project = await get_project_or_raise(session, project_public_id, current_user_public_id)
    if project.id is None:
        raise ProjectNotFoundError("Project not found")

    member = await get_project_member_or_raise(
        session,
        project.id,
        user_public_id,
        current_user_public_id,
    )
    member.role = role
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return member


async def remove_project_member(
    session: AsyncSession,
    project_public_id: str,
    user_public_id: str,
    current_user_public_id: str,
) -> None:
    """移除项目成员。"""
    project = await get_project_or_raise(session, project_public_id, current_user_public_id)
    if project.id is None:
        raise ProjectNotFoundError("Project not found")

    member = await get_project_member_or_raise(
        session,
        project.id,
        user_public_id,
        current_user_public_id,
    )
    await session.delete(member)
    await session.commit()


async def _list_project_members_by_project_id(
    session: AsyncSession,
    project_id: int,
) -> list[ProjectMember]:
    """按项目内部主键获取项目成员列表。"""
    statement = (
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.id)
    )
    result = await session.exec(statement)
    return list(result.all())


async def _get_current_user_or_raise(session: AsyncSession, current_user_public_id: str) -> User:
    """获取当前用户，不存在时按项目访问拒绝处理。"""
    statement = select(User).where(User.public_id == current_user_public_id)
    result = await session.exec(statement)
    user = result.first()
    if user is None:
        raise ProjectAccessDeniedError("Project access denied")
    return user


async def _get_user_by_public_id_or_raise(session: AsyncSession, public_id: str) -> User:
    """获取用户，不存在时按成员不存在处理。"""
    statement = select(User).where(User.public_id == public_id)
    result = await session.exec(statement)
    user = result.first()
    if user is None:
        raise ProjectMemberNotFoundError("User not found")
    return user


async def _ensure_project_access(
    session: AsyncSession,
    project: Project,
    current_user_public_id: str,
) -> None:
    """确认当前用户是否可访问指定项目。"""
    current_user = await _get_current_user_or_raise(session, current_user_public_id)
    if current_user.is_superuser or project.owner_id == current_user_public_id:
        return
    if project.id is not None and await _get_project_member(session, project.id, current_user_public_id):
        return
    raise ProjectAccessDeniedError("Project access denied")


async def _list_accessible_projects(
    session: AsyncSession,
    current_user_public_id: str,
    statement,
) -> list[Project]:
    """执行项目列表查询，并按当前用户权限收敛结果集。"""
    current_user = await _get_current_user_or_raise(session, current_user_public_id)
    if not current_user.is_superuser:
        statement = statement.where(_project_related_to_user_condition(current_user_public_id))

    statement = statement.distinct().order_by(Project.sort_order, Project.id)
    result = await session.exec(statement)
    return list(result.all())


def _project_related_to_user_condition(user_public_id: str):
    """返回项目与用户相关的 SQL 条件。"""
    return or_(
        Project.owner_id == user_public_id,
        _project_has_member_condition(user_public_id),
    )


def _project_has_member_condition(user_public_id: str):
    """返回项目包含指定成员的 SQL 条件。"""
    return exists().where(
        ProjectMember.project_id == Project.id,
        ProjectMember.user_public_id == user_public_id,
    )