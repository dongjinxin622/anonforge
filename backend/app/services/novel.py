from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
import json

from sqlalchemy import func, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.novel import NovelChapter, NovelCrawlBook, NovelCrawlSource
from app.schemas.novel import (
    CrawlAnalyzePayload,
    CrawlAnalyzeResult,
    CrawlBookChapterCountResult,
    CrawlBookDetailResult,
    CrawlBookPayload,
    CrawlChapterDraft,
    CrawlChapterFetchPayload,
    CrawlImportPayload,
    CrawlImportResult,
    CrawlSearchPayload,
    CrawlSearchResult,
    CrawlSourceDuplicate,
    CrawlSourcePayload,
    CrawlSourceRead,
    CrawlSourceUpdate,
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
from app.services import novel_crawler
from app.services import project as project_service
from app.utils.novel_import_rules import get_builtin_import_split_rules
from app.utils.novel_parser import ParsedNovelChapter, parse_novel_chapters
from app.utils.time_tools import utc_now


CRAWL_SOURCE_CONFIG_FIELDS = (
    "name",
    "base_url",
    "desc",
    "source_type",
    "search_url_template",
    "api_search_method",
    "api_search_headers",
    "api_search_body",
    "api_search_book_url_path",
    "api_search_book_id_path",
    "api_search_book_title_path",
    "api_search_book_author_path",
    "api_search_book_intro_path",
    "api_search_book_cover_path",
    "api_search_book_category_path",
    "api_search_book_update_status_path",
    "api_search_book_last_chapter_path",
    "api_search_book_last_chapter_id_path",
    "api_search_book_last_update_path",
    "api_book_url",
    "api_book_method",
    "api_book_headers",
    "api_book_body",
    "api_book_title_path",
    "api_book_author_path",
    "api_book_intro_path",
    "api_book_last_chapter_path",
    "api_book_last_chapter_id_path",
    "api_book_last_update_path",
    "api_book_cover_path",
    "api_book_category_path",
    "api_book_update_status_path",
    "api_book_id_path",
    "api_chapter_list_url",
    "api_chapter_list_method",
    "api_chapter_list_headers",
    "api_chapter_list_body",
    "api_chapter_list_id_path",
    "api_chapter_list_name_path",
    "api_chapter_list_time_path",
    "api_chapter_list_content_path",
    "api_chapter_list_md5_path",
    "api_chapter_url",
    "api_chapter_method",
    "api_chapter_headers",
    "api_chapter_body",
    "api_chapter_name_path",
    "api_chapter_content_path",
    "api_chapter_time_path",
    "api_chapter_md5_path",
)


class NovelServiceError(Exception):
    """小说服务层基础异常。"""


class NovelChapterNotFoundError(NovelServiceError):
    """小说章节不存在。"""


class NovelChapterValidationError(NovelServiceError):
    """小说章节请求不合法。"""


class NovelCrawlSourceNotFoundError(NovelServiceError):
    """小说爬取来源不存在，或当前项目不可见。"""


class NovelCrawlSourceValidationError(NovelServiceError):
    """小说爬取来源配置或爬取请求不合法。"""


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
    """返回前端导入弹窗使用的内置章节切分规则。"""
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


async def list_crawl_sources(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
) -> list[CrawlSourceRead]:
    """列出当前项目可见的公共来源和项目私有来源。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    statement = (
        select(NovelCrawlSource)
        .where(
            NovelCrawlSource.disabled_at.is_(None),
            or_(NovelCrawlSource.scope == "public", NovelCrawlSource.project_id == project.id),
        )
        .order_by(NovelCrawlSource.sort_order, NovelCrawlSource.id)
    )
    result = await session.exec(statement)
    return [_to_crawl_source_read(source, project_public_id if source.project_id == project.id else None) for source in result.all()]


async def create_crawl_source(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: CrawlSourcePayload,
) -> CrawlSourceRead:
    """创建项目私有的 API 小说爬取来源。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    await _ensure_crawl_source_key_available(session, payload.key)
    now = utc_now()
    source = NovelCrawlSource(
        project_id=project.id,
        owner_public_id=current_user_public_id,
        key=payload.key.strip(),
        builtin=False,
        scope="private",
        created_at=now,
        updated_at=now,
    )
    _apply_crawl_source_values(source, payload.model_dump())
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return _to_crawl_source_read(source, project_public_id)


async def update_crawl_source(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    key: str,
    payload: CrawlSourceUpdate,
) -> CrawlSourceRead:
    """更新项目私有的小说爬取来源。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    source = await _get_project_crawl_source_or_raise(session, project.id, key)
    _apply_crawl_source_values(source, payload.model_dump(exclude_unset=True))
    source.updated_at = utc_now()
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return _to_crawl_source_read(source, project_public_id)


async def delete_crawl_source(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    key: str,
) -> None:
    """删除项目私有的小说爬取来源。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    source = await _get_project_crawl_source_or_raise(session, project.id, key)
    await session.delete(source)
    await session.commit()


async def duplicate_crawl_source(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    key: str,
    payload: CrawlSourceDuplicate,
) -> CrawlSourceRead:
    """把可见来源复制到当前项目。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    origin = await _get_visible_crawl_source_or_raise(session, project.id, key)
    await _ensure_crawl_source_key_available(session, payload.new_key)
    now = utc_now()
    source = NovelCrawlSource(
        project_id=project.id,
        owner_public_id=current_user_public_id,
        key=payload.new_key.strip(),
        builtin=False,
        scope="private",
        created_at=now,
        updated_at=now,
    )
    values = {field: getattr(origin, field) for field in CRAWL_SOURCE_CONFIG_FIELDS}
    if payload.name:
        values["name"] = payload.name
    _apply_crawl_source_values(source, values)
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return _to_crawl_source_read(source, project_public_id)


async def analyze_crawl_source(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: CrawlAnalyzePayload,
) -> CrawlAnalyzeResult:
    """返回用于手动配置的来源草稿。"""
    await _get_project_with_id(session, project_public_id, current_user_public_id)
    return CrawlAnalyzeResult(
        status="pending",
        source=CrawlSourcePayload(
            key="custom_source",
            name="Custom Source",
            baseUrl=payload.url,
            sourceType="api",
            searchUrlTemplate="",
            builtin=False,
            projectPublicId=project_public_id,
        ),
        message="Source analysis is not automated yet. Please complete the API paths manually.",
    )


async def search_crawl_books(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: CrawlSearchPayload,
) -> list[CrawlSearchResult]:
    """通过选中的小说来源搜索小说。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    source = await _get_visible_crawl_source_or_raise(session, project.id, payload.source_key)
    try:
        return await novel_crawler.search_books(source, payload.query)
    except Exception as exc:
        raise NovelCrawlSourceValidationError(str(exc)) from exc


async def fetch_crawl_book_detail(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: CrawlBookPayload,
) -> CrawlBookDetailResult:
    """获取选中小说详情，并持久化爬取小说快照。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    source = await _get_visible_crawl_source_or_raise(session, project.id, payload.source_key)
    try:
        book = await novel_crawler.fetch_book_detail(source, payload.book)
    except Exception as exc:
        raise NovelCrawlSourceValidationError(str(exc)) from exc
    await _upsert_crawl_book(session, project.id, source.key, book)
    await session.commit()
    return CrawlBookDetailResult(book=book)


async def fetch_crawl_book_chapter_count(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: CrawlBookPayload,
) -> CrawlBookChapterCountResult:
    """获取选中小说的章节总数。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    source = await _get_visible_crawl_source_or_raise(session, project.id, payload.source_key)
    try:
        count = await novel_crawler.fetch_chapter_count(source, payload.book)
    except Exception as exc:
        raise NovelCrawlSourceValidationError(str(exc)) from exc
    book = payload.book.model_copy(update={"lastchapterid": count, "source_key": payload.source_key})
    await _upsert_crawl_book(session, project.id, source.key, book)
    await session.commit()
    return CrawlBookChapterCountResult(book=book, lastchapterid=count)


async def fetch_crawl_chapters(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: CrawlChapterFetchPayload,
) -> list[CrawlChapterDraft]:
    """爬取指定范围内的章节。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    source = await _get_visible_crawl_source_or_raise(session, project.id, payload.source_key)
    try:
        return await novel_crawler.fetch_chapters(source, payload.book, payload.start_chapter, payload.end_chapter)
    except Exception as exc:
        raise NovelCrawlSourceValidationError(str(exc)) from exc


async def build_crawl_chapter_stream(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: CrawlChapterFetchPayload,
) -> AsyncIterator[dict[str, object]]:
    """创建指定章节范围的爬取进度流。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    source = await _get_visible_crawl_source_or_raise(session, project.id, payload.source_key)

    async def generate() -> AsyncIterator[dict[str, object]]:
        completed = 0
        total = max(payload.end_chapter - payload.start_chapter + 1, 0)
        try:
            async for event in novel_crawler.stream_chapters(
                source,
                payload.book,
                payload.start_chapter,
                payload.end_chapter,
            ):
                if event.get("type") == "chapter":
                    completed = int(event.get("completed") or completed)
                    total = int(event.get("total") or total)
                yield event
        except Exception as exc:
            yield {
                "type": "error",
                "detail": str(exc),
                "completed": completed,
                "total": total,
            }

    return generate()


async def import_crawl_chapters(
    session: AsyncSession,
    project_public_id: str,
    current_user_public_id: str,
    payload: CrawlImportPayload,
) -> CrawlImportResult:
    """把已爬取章节导入现有小说章节表。"""
    project = await _get_project_with_id(session, project_public_id, current_user_public_id)
    source = await _get_visible_crawl_source_or_raise(session, project.id, payload.source_key)
    book = payload.book.model_copy(update={"source_key": source.key})
    await _upsert_crawl_book(session, project.id, source.key, book)

    start_index = await _next_chapter_index(session, project.id)
    now = utc_now()
    created = 0
    updated = 0
    skipped = 0
    touched: list[NovelChapter] = []

    for draft in sorted(payload.chapters, key=lambda item: (item.key, item.chapterid)):
        chapter_text = draft.txt.strip()
        chapter_name = draft.chaptername.strip()
        if not chapter_text or not chapter_name:
            skipped += 1
            continue
        existing = await _get_chapter_by_crawl_identity(
            session,
            project.id,
            source.key,
            draft.novel_dirid or book.dirid,
            draft.chapterid,
        )
        if existing is not None:
            if (
                existing.chapter == chapter_name
                and existing.chapter_data == chapter_text
                and existing.event == draft.event.strip()
                and existing.event_state == draft.event_state
            ):
                skipped += 1
                continue
            existing.chapter = chapter_name
            existing.chapter_data = chapter_text
            existing.event = draft.event.strip()
            existing.event_state = draft.event_state
            existing.error_reason = draft.error_reason
            existing.crawl_time = draft.time.strip()
            existing.crawl_md5 = draft.md5.strip() or _chapter_content_md5(chapter_text)
            existing.updated_at = now
            session.add(existing)
            touched.append(existing)
            updated += 1
            continue

        chapter = NovelChapter(
            project_id=project.id,
            chapter_index=start_index + created,
            reel="",
            chapter=chapter_name,
            chapter_data=chapter_text,
            event=draft.event.strip(),
            event_state=draft.event_state,
            error_reason=draft.error_reason,
            crawl_source_key=source.key,
            crawl_novel_dirid=(draft.novel_dirid or book.dirid).strip(),
            crawl_chapter_id=draft.chapterid,
            crawl_time=draft.time.strip(),
            crawl_md5=draft.md5.strip() or _chapter_content_md5(chapter_text),
            created_at=now,
            updated_at=now,
        )
        session.add(chapter)
        touched.append(chapter)
        created += 1

    await session.commit()
    for chapter in touched:
        await session.refresh(chapter)
    return CrawlImportResult(
        created=created,
        updated=updated,
        skipped=skipped,
        chapters=[_to_read(chapter) for chapter in touched],
    )


def _parse_import_payload(payload: NovelChapterImport) -> list[ParsedNovelChapter]:
    """优先返回预览草稿解析结果，否则解析原始文本。"""
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


async def _ensure_crawl_source_key_available(session: AsyncSession, key: str) -> None:
    statement = select(NovelCrawlSource.id).where(NovelCrawlSource.key == key.strip())
    result = await session.exec(statement)
    if result.first() is not None:
        raise NovelCrawlSourceValidationError("Crawl source key already exists")


async def _get_visible_crawl_source_or_raise(
    session: AsyncSession,
    project_id: int,
    key: str,
) -> NovelCrawlSource:
    statement = select(NovelCrawlSource).where(
        NovelCrawlSource.key == key.strip(),
        NovelCrawlSource.disabled_at.is_(None),
        or_(NovelCrawlSource.scope == "public", NovelCrawlSource.project_id == project_id),
    )
    result = await session.exec(statement)
    source = result.first()
    if source is None:
        raise NovelCrawlSourceNotFoundError("Crawl source not found")
    return source


async def _get_project_crawl_source_or_raise(
    session: AsyncSession,
    project_id: int,
    key: str,
) -> NovelCrawlSource:
    statement = select(NovelCrawlSource).where(
        NovelCrawlSource.key == key.strip(),
        NovelCrawlSource.project_id == project_id,
        NovelCrawlSource.disabled_at.is_(None),
    )
    result = await session.exec(statement)
    source = result.first()
    if source is None:
        raise NovelCrawlSourceNotFoundError("Crawl source not found")
    return source


def _apply_crawl_source_values(source: NovelCrawlSource, values: dict[str, object]) -> None:
    for field in CRAWL_SOURCE_CONFIG_FIELDS:
        if field not in values:
            continue
        value = values[field]
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if field.endswith("_method"):
            value = str(value or "GET").upper()
        if field == "source_type":
            value = str(value or "api").lower()
        setattr(source, field, value)


def _to_crawl_source_read(source: NovelCrawlSource, project_public_id: str | None) -> CrawlSourceRead:
    return CrawlSourceRead(
        **{field: getattr(source, field) for field in CRAWL_SOURCE_CONFIG_FIELDS},
        key=source.key,
        builtin=source.builtin,
        projectPublicId=project_public_id,
        id=int(source.id or 0),
        publicId=source.public_id,
        scope=source.scope,
        sortOrder=source.sort_order,
        createdAt=source.created_at,
        updatedAt=source.updated_at,
        disabledAt=source.disabled_at,
    )


async def _upsert_crawl_book(
    session: AsyncSession,
    project_id: int,
    source_key: str,
    book: CrawlSearchResult,
) -> NovelCrawlBook:
    statement = select(NovelCrawlBook).where(
        NovelCrawlBook.project_id == project_id,
        NovelCrawlBook.source_key == source_key,
        NovelCrawlBook.source_book_id == book.dirid,
    )
    result = await session.exec(statement)
    crawl_book = result.first()
    now = utc_now()
    if crawl_book is None:
        crawl_book = NovelCrawlBook(
            project_id=project_id,
            source_key=source_key,
            source_book_id=book.dirid,
            created_at=now,
            updated_at=now,
        )
    crawl_book.source_book_numeric_id = book.id or None
    crawl_book.title = book.title
    crawl_book.author = book.author
    crawl_book.cover_url = book.cover
    crawl_book.category = book.sortname
    crawl_book.update_status = book.full
    crawl_book.intro = book.intro
    crawl_book.last_chapter = book.lastchapter
    crawl_book.last_chapter_id = book.lastchapterid
    crawl_book.last_update = book.lastupdate
    crawl_book.raw_data = json.dumps(book.model_dump(mode="json", by_alias=True), ensure_ascii=False)
    crawl_book.updated_at = now
    session.add(crawl_book)
    return crawl_book


async def _get_chapter_by_crawl_identity(
    session: AsyncSession,
    project_id: int,
    source_key: str,
    novel_dirid: str,
    chapter_id: int,
) -> NovelChapter | None:
    statement = select(NovelChapter).where(
        NovelChapter.project_id == project_id,
        NovelChapter.crawl_source_key == source_key,
        NovelChapter.crawl_novel_dirid == novel_dirid,
        NovelChapter.crawl_chapter_id == chapter_id,
    )
    result = await session.exec(statement)
    return result.first()


def _to_read(chapter: NovelChapter) -> NovelChapterRead:
    """将数据库模型转换为响应模型。"""
    return NovelChapterRead.model_validate(chapter)
