from __future__ import annotations

import hashlib

from sqlalchemy import func, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.novel import NovelChapter
from app.schemas.novel import (
    NovelChapterBatchClean,
    NovelChapterBatchDelete,
    NovelChapterBatchResult,
    NovelChapterCreate,
    NovelChapterEventStateUpdate,
    NovelChapterImport,
    NovelChapterPage,
    NovelChapterRead,
    NovelChapterUpdate,
    NovelImportSplitRule,
)
from app.services import project as project_service
from app.utils.novel_import_rules import get_builtin_import_split_rules
from app.utils.novel_parser import ParsedNovelChapter, parse_novel_chapters
from app.utils.time_tools import utc_now


class NovelServiceError(Exception):
    """小说服务层基础异常。"""


class NovelChapterNotFoundError(NovelServiceError):
    """小说章节不存在。"""


class NovelChapterValidationError(NovelServiceError):
    """小说章节请求不合法。"""


async def list_chapters(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    *,
    page: int = 1,
    limit: int = 20,
    search: str = "",
) -> NovelChapterPage:
    """分页获取指定项目下的小说章节。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    conditions = [NovelChapter.project_id == project.id]
    keyword = search.strip()
    if keyword:
        conditions.append(
            or_(
                NovelChapter.chapter.ilike(f"%{keyword}%"),
                NovelChapter.reel.ilike(f"%{keyword}%"),
            )
        )

    count_statement = select(func.count()).select_from(NovelChapter).where(*conditions)
    count_result = await session.exec(count_statement)
    total = int(count_result.one())

    statement = (
        select(NovelChapter)
        .where(*conditions)
        .order_by(NovelChapter.chapter_index, NovelChapter.id)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await session.exec(statement)
    chapters = list(result.all())
    return NovelChapterPage(
        data=[_to_read(chapter) for chapter in chapters],
        total=total,
        page=page,
        limit=limit,
    )


async def get_chapter(
    session: AsyncSession,
    project_public_id: str,
    chapter_id: int,
    current_user_public_id: str,
) -> NovelChapterRead:
    """获取指定项目下的单个小说章节。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    chapter = await _get_chapter_model_or_raise(session, project.id, chapter_id)
    return _to_read(chapter)


async def create_chapter(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: NovelChapterCreate,
) -> NovelChapterRead:
    """创建小说章节。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    now = utc_now()
    chapter_data = payload.chapter_data.strip()
    chapter = NovelChapter(
        project_id=project.id,
        chapter_index=payload.chapter_index,
        reel=payload.reel.strip(),
        chapter=payload.chapter.strip(),
        chapter_data=chapter_data,
        event=payload.event.strip(),
        event_state=_state_for_event(payload.event, payload.event_state),
        error_reason=payload.error_reason,
        crawl_source_key=payload.crawl_source_key.strip(),
        crawl_novel_dirid=payload.crawl_novel_dirid.strip(),
        crawl_chapter_id=payload.crawl_chapter_id,
        crawl_time=payload.crawl_time.strip(),
        crawl_md5=_chapter_content_md5(chapter_data),
        created_at=now,
        updated_at=now,
    )
    session.add(chapter)
    await session.commit()
    await session.refresh(chapter)
    return _to_read(chapter)


async def update_chapter(
    session: AsyncSession,
    project_public_id: str,
    chapter_id: int,
    current_user_public_id: str,
    payload: NovelChapterUpdate,
) -> NovelChapterRead:
    """更新小说章节。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    chapter = await _get_chapter_model_or_raise(session, project.id, chapter_id)
    fields = payload.model_fields_set
    values = payload.model_dump(exclude_unset=True)
    for field_name, value in values.items():
        if field_name == "crawl_md5":
            continue
        if isinstance(value, str):
            value = value.strip()
        setattr(chapter, field_name, value)

    if "event" in fields and "event_state" not in fields:
        chapter.event_state = 1 if chapter.event.strip() else 0
        chapter.error_reason = None
    if "event_state" in fields and chapter.event_state == 0:
        chapter.error_reason = None
    if "chapter_data" in fields:
        chapter.crawl_md5 = _chapter_content_md5(chapter.chapter_data)

    chapter.updated_at = utc_now()
    session.add(chapter)
    await session.commit()
    await session.refresh(chapter)
    return _to_read(chapter)


async def delete_chapter(
    session: AsyncSession,
    project_public_id: str,
    chapter_id: int,
    current_user_public_id: str,
) -> None:
    """删除小说章节。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    chapter = await _get_chapter_model_or_raise(session, project.id, chapter_id)
    await session.delete(chapter)
    await session.commit()


async def batch_delete_chapters(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: NovelChapterBatchDelete,
) -> NovelChapterBatchResult:
    """批量删除小说章节。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    chapters = await _list_chapter_models_by_ids(session, project.id, payload.ids)
    for chapter in chapters:
        await session.delete(chapter)
    await session.commit()
    return NovelChapterBatchResult(affected=len(chapters))


async def import_chapters(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: NovelChapterImport,
) -> list[NovelChapterRead]:
    """解析全文并导入为章节。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    parsed_chapters = _parse_import_payload(payload)
    if not parsed_chapters:
        raise NovelChapterValidationError("No chapter content found")

    start_index = await _next_chapter_index(session, project.id)
    now = utc_now()
    chapters = [
        NovelChapter(
            project_id=project.id,
            chapter_index=start_index + index,
            reel=item.reel,
            chapter=item.chapter,
            chapter_data=item.chapter_data,
            event="",
            event_state=0,
            error_reason=None,
            crawl_md5=_chapter_content_md5(item.chapter_data),
            created_at=now,
            updated_at=now,
        )
        for index, item in enumerate(parsed_chapters)
    ]
    session.add_all(chapters)
    await session.commit()
    for chapter in chapters:
        await session.refresh(chapter)
    return [_to_read(chapter) for chapter in chapters]


def list_import_split_rules() -> list[NovelImportSplitRule]:
    """Return built-in frontend import split rules."""
    return [
        NovelImportSplitRule(
            key=rule.key,
            label=rule.label,
            description=rule.description,
            chapter_pattern=rule.chapter_pattern,
            chapter_flags_list=list(rule.chapter_flags_list),
            reel_pattern=rule.reel_pattern,
            reel_flags_list=list(rule.reel_flags_list),
            builtin=True,
        )
        for rule in get_builtin_import_split_rules()
    ]


def _parse_import_payload(payload: NovelChapterImport) -> list[ParsedNovelChapter]:
    """Return parsed chapters from preview drafts when present, otherwise parse raw text."""
    if payload.chapters:
        parsed_chapters: list[ParsedNovelChapter] = []
        for index, item in enumerate(payload.chapters, start=1):
            chapter = item.chapter.strip()
            chapter_data = item.chapter_data.strip()
            if not chapter or not chapter_data:
                continue
            parsed_chapters.append(
                ParsedNovelChapter(
                    chapter_index=index,
                    reel=item.reel.strip(),
                    chapter=chapter,
                    chapter_data=chapter_data,
                )
            )
        return parsed_chapters
    return parse_novel_chapters(payload.raw_text)


async def clean_chapter(
    session: AsyncSession,
    project_public_id: str,
    chapter_id: int,
    current_user_public_id: str,
) -> NovelChapterRead:
    """清洗单个章节事件。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    chapter = await _get_chapter_model_or_raise(session, project.id, chapter_id)
    _apply_clean_result(chapter)
    chapter.updated_at = utc_now()
    session.add(chapter)
    await session.commit()
    await session.refresh(chapter)
    return _to_read(chapter)


async def batch_clean_chapters(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: NovelChapterBatchClean,
) -> NovelChapterBatchResult:
    """批量清洗章节事件。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    chapters = await _list_chapter_models_by_ids(session, project.id, payload.ids)
    now = utc_now()
    for chapter in chapters:
        _apply_clean_result(chapter)
        chapter.updated_at = now
        session.add(chapter)
    await session.commit()
    return NovelChapterBatchResult(affected=len(chapters))


async def update_event_state(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: NovelChapterEventStateUpdate,
) -> NovelChapterBatchResult:
    """批量更新章节事件状态。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    chapters = await _list_chapter_models_by_ids(session, project.id, payload.ids)
    now = utc_now()
    for chapter in chapters:
        chapter.event_state = payload.event_state
        if payload.event is not None:
            chapter.event = payload.event.strip()
        if payload.error_reason is not None:
            chapter.error_reason = payload.error_reason.strip()
        if payload.event_state == 0:
            chapter.error_reason = None
        chapter.updated_at = now
        session.add(chapter)
    await session.commit()
    return NovelChapterBatchResult(affected=len(chapters))


async def _get_project_with_id(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
):
    """获取项目并确保内部主键存在。"""
    project = await project_service.get_project_or_raise(session, project_public_id, current_user_public_id)
    if project.id is None:
        raise project_service.ProjectNotFoundError("Project not found")
    return project


async def _get_chapter_model_or_raise(
    session: AsyncSession,
    project_id: int,
    chapter_id: int,
) -> NovelChapter:
    """按项目和章节 ID 获取章节模型。"""
    statement = select(NovelChapter).where(
        NovelChapter.project_id == project_id,
        NovelChapter.id == chapter_id,
    )
    result = await session.exec(statement)
    chapter = result.first()
    if chapter is None:
        raise NovelChapterNotFoundError("Novel chapter not found")
    return chapter


async def _list_chapter_models_by_ids(
    session: AsyncSession,
    project_id: int,
    chapter_ids: list[int],
) -> list[NovelChapter]:
    """按项目和 ID 列表获取章节模型。"""
    unique_ids = sorted(set(chapter_ids))
    if not unique_ids:
        return []
    statement = (
        select(NovelChapter)
        .where(
            NovelChapter.project_id == project_id,
            NovelChapter.id.in_(unique_ids),
        )
        .order_by(NovelChapter.chapter_index, NovelChapter.id)
    )
    result = await session.exec(statement)
    return list(result.all())


async def _next_chapter_index(session: AsyncSession, project_id: int) -> int:
    """返回指定项目下一章节序号。"""
    statement = select(func.max(NovelChapter.chapter_index)).where(NovelChapter.project_id == project_id)
    result = await session.exec(statement)
    max_index = result.one()
    return int(max_index or 0) + 1


def _apply_clean_result(chapter: NovelChapter) -> None:
    """生成本地可复现的章节事件清洗结果。"""
    content = chapter.chapter_data.strip()
    if len(content) < 80:
        chapter.event = ""
        chapter.event_state = -1
        chapter.error_reason = "正文字数过少，无法提取有效事件"
        return

    chapter.event = (
        "## 主要事件\n"
        f"- 由「{chapter.chapter}」自动清洗生成\n"
        f"- 共 {len(content)} 字\n\n"
        "## 关键人物\n"
        "- 主角\n\n"
        "## 场景\n"
        "- 自动识别中..."
    )
    chapter.event_state = 1
    chapter.error_reason = None


def _state_for_event(event: str, requested_state: int) -> int:
    """如果请求携带事件内容，默认认为事件已生成。"""
    if event.strip() and requested_state == 0:
        return 1
    return requested_state


def _chapter_content_md5(chapter_data: str) -> str:
    """按最终保存的章节正文计算内容指纹。"""
    return hashlib.md5(chapter_data.encode("utf-8")).hexdigest()


def _to_read(chapter: NovelChapter) -> NovelChapterRead:
    """将数据库模型转换为响应模型。"""
    return NovelChapterRead.model_validate(chapter)
