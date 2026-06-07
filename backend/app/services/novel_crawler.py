from __future__ import annotations

import asyncio
from concurrent.futures import ProcessPoolExecutor
import json
import os
import re
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import quote

import httpx

from app.models.novel import NovelCrawlSource
from app.schemas.novel import CrawlChapterDraft, CrawlSearchResult


HTTP_TIMEOUT = httpx.Timeout(20.0, connect=10.0)
HTTP_METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}
CHAPTER_COROUTINES_PER_PROCESS = 8
MAX_CRAWL_PROCESSES = 4


class NovelCrawlerError(Exception):
    """小说 HTTP 爬取基础异常。"""


class NovelCrawlerConfigError(NovelCrawlerError):
    """小说来源配置缺失或不合法时抛出。"""


def extract_json_path_values(data: Any, path: str) -> list[Any]:
    """按来源配置支持的简化 JSONPath 提取值。"""
    tokens = _parse_json_path(path)
    if not tokens:
        return []

    values = [data]
    for token in tokens:
        next_values: list[Any] = []
        for value in values:
            if token == "*":
                if isinstance(value, list):
                    next_values.extend(value)
                elif isinstance(value, dict):
                    next_values.extend(value.values())
                continue
            if isinstance(token, int):
                if isinstance(value, list) and -len(value) <= token < len(value):
                    next_values.append(value[token])
                continue
            if isinstance(value, dict) and token in value:
                next_values.append(value[token])
        values = next_values
        if not values:
            break
    return values


async def search_books(
    source: NovelCrawlSource,
    query: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[CrawlSearchResult]:
    """通过配置好的 HTTP 来源搜索小说。"""
    if not source.search_url_template.strip():
        raise NovelCrawlerConfigError("search_url_template is required")

    context = {"q": query.strip(), "keyword": query.strip(), "sort": query.strip()}
    if client is not None:
        data = await _request_json(
            client,
            source.api_search_method,
            source.search_url_template,
            source.api_search_headers,
            source.api_search_body,
            context,
        )
        return _parse_search_results(source, data)

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as owned_client:
        data = await _request_json(
            owned_client,
            source.api_search_method,
            source.search_url_template,
            source.api_search_headers,
            source.api_search_body,
            context,
        )
        return _parse_search_results(source, data)


async def fetch_book_detail(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    *,
    client: httpx.AsyncClient | None = None,
) -> CrawlSearchResult:
    """获取选中小说详情，并合并配置字段。"""
    if not source.api_book_url.strip():
        return book

    context = _book_context(book)
    if client is not None:
        data = await _request_json(
            client,
            source.api_book_method,
            source.api_book_url,
            source.api_book_headers,
            source.api_book_body,
            context,
        )
        return _merge_book_detail(source, book, data)

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as owned_client:
        data = await _request_json(
            owned_client,
            source.api_book_method,
            source.api_book_url,
            source.api_book_headers,
            source.api_book_body,
            context,
        )
        return _merge_book_detail(source, book, data)


async def fetch_chapter_count(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    *,
    client: httpx.AsyncClient | None = None,
) -> int:
    """返回选中小说的章节总数。"""
    metas = await fetch_chapter_metas(source, book, client=client)
    if metas:
        return len(metas)
    return max(book.lastchapterid, 0)


async def fetch_chapter_metas(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    """获取并标准化章节列表元数据。"""
    if not source.api_chapter_list_url.strip():
        return _fallback_chapter_metas(book)

    context = _book_context(book)
    if client is not None:
        data = await _request_json(
            client,
            source.api_chapter_list_method,
            source.api_chapter_list_url,
            source.api_chapter_list_headers,
            source.api_chapter_list_body,
            context,
        )
        metas = _parse_chapter_metas(source, book, data)
        return metas or _fallback_chapter_metas(book)

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as owned_client:
        data = await _request_json(
            owned_client,
            source.api_chapter_list_method,
            source.api_chapter_list_url,
            source.api_chapter_list_headers,
            source.api_chapter_list_body,
            context,
        )
        metas = _parse_chapter_metas(source, book, data)
        return metas or _fallback_chapter_metas(book)


async def fetch_chapters(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    start_chapter: int,
    end_chapter: int,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[CrawlChapterDraft]:
    """爬取指定范围内的章节正文。"""
    metas = _slice_chapter_metas(await fetch_chapter_metas(source, book, client=client), start_chapter, end_chapter)
    if not metas:
        return []
    if client is not None:
        return await _fetch_chapters_from_metas(source, book, metas, client=client)

    chapters = [chapter async for chapter in crawl_chapters_parallel(source, book, metas)]
    return sorted(chapters, key=lambda chapter: chapter.key)


async def stream_chapters(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    start_chapter: int,
    end_chapter: int,
    *,
    client: httpx.AsyncClient | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """以 NDJSON 兼容字典流式返回爬取进度。"""
    if client is not None:
        metas = _slice_chapter_metas(await fetch_chapter_metas(source, book, client=client), start_chapter, end_chapter)
        async for event in _stream_chapter_events(source, book, metas, start_chapter, end_chapter, client):
            yield event
        return

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as owned_client:
        metas = _slice_chapter_metas(
            await fetch_chapter_metas(source, book, client=owned_client),
            start_chapter,
            end_chapter,
        )
        async for event in _stream_chapter_events(source, book, metas, start_chapter, end_chapter, owned_client):
            yield event


async def _stream_chapter_events(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    metas: list[dict[str, Any]],
    start_chapter: int,
    end_chapter: int,
    client: httpx.AsyncClient,
) -> AsyncIterator[dict[str, Any]]:
    total = len(metas)
    yield {"type": "start", "total": total, "startChapter": start_chapter, "endChapter": end_chapter}
    completed = 0
    async for chapter in _stream_chapters_from_metas(
        source,
        book,
        metas,
        client=client,
        concurrency=MAX_CRAWL_PROCESSES * CHAPTER_COROUTINES_PER_PROCESS,
    ):
        completed += 1
        yield {
            "type": "chapter",
            "completed": completed,
            "total": total,
            "chapter": chapter.model_dump(mode="json", by_alias=True),
        }
    yield {"type": "done", "completed": completed, "total": total}


async def crawl_chapters_parallel(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    metas: list[dict[str, Any]],
) -> AsyncIterator[CrawlChapterDraft]:
    """多进程爬取章节详情，每个进程内并发运行协程。"""
    if not metas:
        return

    workers = min(MAX_CRAWL_PROCESSES, os.cpu_count() or 1, len(metas))
    if workers <= 1:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            for chapter in await _fetch_chapters_from_metas(source, book, metas, client=client):
                yield chapter
        return

    loop = asyncio.get_running_loop()
    source_data = _dump_source(source)
    book_data = book.model_dump(mode="json")
    chunks = _partition_metas(metas, workers)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            loop.run_in_executor(
                executor,
                _crawl_chapter_batch_worker,
                source_data,
                book_data,
                chunk,
                CHAPTER_COROUTINES_PER_PROCESS,
            )
            for chunk in chunks
        ]
        for future in futures:
            for item in await future:
                yield CrawlChapterDraft.model_validate(item)


def _crawl_chapter_batch_worker(
    source_data: dict[str, Any],
    book_data: dict[str, Any],
    metas: list[dict[str, Any]],
    concurrency: int,
) -> list[dict[str, Any]]:
    source = NovelCrawlSource(**source_data)
    book = CrawlSearchResult.model_validate(book_data)
    return asyncio.run(_crawl_chapter_batch_worker_async(source, book, metas, concurrency))


async def _crawl_chapter_batch_worker_async(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    metas: list[dict[str, Any]],
    concurrency: int,
) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        chapters = await _fetch_chapters_from_metas(source, book, metas, client=client, concurrency=concurrency)
        return [chapter.model_dump(mode="json") for chapter in chapters]


async def _fetch_chapters_from_metas(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    metas: list[dict[str, Any]],
    *,
    client: httpx.AsyncClient,
    concurrency: int = CHAPTER_COROUTINES_PER_PROCESS,
) -> list[CrawlChapterDraft]:
    semaphore = asyncio.Semaphore(max(concurrency, 1))

    async def fetch_one(meta: dict[str, Any]) -> CrawlChapterDraft:
        async with semaphore:
            return await _fetch_chapter_detail(source, book, meta, client=client)

    return list(await asyncio.gather(*(fetch_one(meta) for meta in metas)))


async def _stream_chapters_from_metas(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    metas: list[dict[str, Any]],
    *,
    client: httpx.AsyncClient,
    concurrency: int,
) -> AsyncIterator[CrawlChapterDraft]:
    if not metas:
        return

    semaphore = asyncio.Semaphore(max(concurrency, 1))

    async def fetch_one(meta: dict[str, Any]) -> CrawlChapterDraft:
        async with semaphore:
            return await _fetch_chapter_detail(source, book, meta, client=client)

    tasks = [asyncio.create_task(fetch_one(meta)) for meta in metas]
    try:
        for task in asyncio.as_completed(tasks):
            yield await task
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()


async def _fetch_chapter_detail(
    source: NovelCrawlSource,
    book: CrawlSearchResult,
    meta: dict[str, Any],
    *,
    client: httpx.AsyncClient,
) -> CrawlChapterDraft:
    data: Any = {}
    if source.api_chapter_url.strip():
        data = await _request_json(
            client,
            source.api_chapter_method,
            source.api_chapter_url,
            source.api_chapter_headers,
            source.api_chapter_body,
            {**_book_context(book), **_chapter_context(meta)},
        )

    name = _first_text(data, source.api_chapter_name_path) or str(meta.get("chaptername") or "")
    text = _first_text(data, source.api_chapter_content_path) or str(meta.get("txt") or "")
    update_time = _first_text(data, source.api_chapter_time_path) or str(meta.get("time") or "")
    md5 = _first_text(data, source.api_chapter_md5_path) or str(meta.get("md5") or "")
    chapter_id = _to_int(meta.get("chapterid"), int(meta.get("ordinal") or 0))
    return CrawlChapterDraft(
        key=int(meta.get("ordinal") or chapter_id),
        novelDirid=book.dirid,
        chapterid=chapter_id,
        chaptername=name or f"第{meta.get('ordinal')}章",
        time=update_time,
        txt=text,
        md5=md5,
        event="",
        eventState=0,
        errorReason=None,
    )


async def _request_json(
    client: httpx.AsyncClient,
    method: str,
    url_template: str,
    headers_raw: str,
    body_raw: str,
    context: dict[str, Any],
) -> Any:
    method = (method or "GET").strip().upper()
    url = _render_template(url_template, context, encode_url_values=True)
    headers = _parse_json_mapping(headers_raw, context)
    body = _parse_json_body(body_raw, context) if method in HTTP_METHODS_WITH_BODY and body_raw.strip() else None
    response = await client.request(method, url, headers=headers, json=body)
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as exc:
        raise NovelCrawlerError("crawl source did not return valid JSON") from exc


def _parse_search_results(source: NovelCrawlSource, data: Any) -> list[CrawlSearchResult]:
    ids = extract_json_path_values(data, source.api_search_book_id_path)
    titles = extract_json_path_values(data, source.api_search_book_title_path)
    count = max(
        len(ids),
        len(titles),
        len(extract_json_path_values(data, source.api_search_book_url_path)),
        0,
    )
    books: list[CrawlSearchResult] = []
    for index in range(count):
        raw_id = _nth(ids, index)
        title = _to_text(_nth(titles, index))
        dirid = _to_text(raw_id) or _to_text(_nth(extract_json_path_values(data, source.api_search_book_url_path), index))
        if not dirid and not title:
            continue
        books.append(
            CrawlSearchResult(
                dirid=dirid,
                id=_to_int(raw_id, index + 1),
                full=_to_text(_nth(extract_json_path_values(data, source.api_search_book_update_status_path), index)),
                title=title,
                author=_to_text(_nth(extract_json_path_values(data, source.api_search_book_author_path), index)),
                cover=_to_text(_nth(extract_json_path_values(data, source.api_search_book_cover_path), index)),
                lastchapter=_to_text(_nth(extract_json_path_values(data, source.api_search_book_last_chapter_path), index)),
                lastchapterid=_to_int(_nth(extract_json_path_values(data, source.api_search_book_last_chapter_id_path), index)),
                lastupdate=_to_text(_nth(extract_json_path_values(data, source.api_search_book_last_update_path), index)),
                sortname=_to_text(_nth(extract_json_path_values(data, source.api_search_book_category_path), index)),
                intro=_to_text(_nth(extract_json_path_values(data, source.api_search_book_intro_path), index)),
                sourceKey=source.key,
            )
        )
    return books


def _merge_book_detail(source: NovelCrawlSource, book: CrawlSearchResult, data: Any) -> CrawlSearchResult:
    source_book_id = _first_text(data, source.api_book_id_path) or book.dirid
    return CrawlSearchResult(
        dirid=source_book_id,
        id=_to_int(source_book_id, book.id),
        full=_first_text(data, source.api_book_update_status_path) or book.full,
        title=_first_text(data, source.api_book_title_path) or book.title,
        author=_first_text(data, source.api_book_author_path) or book.author,
        cover=_first_text(data, source.api_book_cover_path) or book.cover,
        lastchapter=_first_text(data, source.api_book_last_chapter_path) or book.lastchapter,
        lastchapterid=_to_int(_first_value(data, source.api_book_last_chapter_id_path), book.lastchapterid),
        lastupdate=_first_text(data, source.api_book_last_update_path) or book.lastupdate,
        sortname=_first_text(data, source.api_book_category_path) or book.sortname,
        intro=_first_text(data, source.api_book_intro_path) or book.intro,
        sourceKey=book.source_key or source.key,
    )


def _parse_chapter_metas(source: NovelCrawlSource, book: CrawlSearchResult, data: Any) -> list[dict[str, Any]]:
    ids = extract_json_path_values(data, source.api_chapter_list_id_path)
    names = extract_json_path_values(data, source.api_chapter_list_name_path)
    times = extract_json_path_values(data, source.api_chapter_list_time_path)
    texts = extract_json_path_values(data, source.api_chapter_list_content_path)
    md5s = extract_json_path_values(data, source.api_chapter_list_md5_path)
    count = max(len(ids), len(names), len(texts), 0)
    metas: list[dict[str, Any]] = []
    for index in range(count):
        chapter_id = _to_int(_nth(ids, index), index + 1)
        metas.append(
            {
                "ordinal": index + 1,
                "novel_dirid": book.dirid,
                "chapterid": chapter_id,
                "chaptername": _to_text(_nth(names, index)) or f"第{index + 1}章",
                "time": _to_text(_nth(times, index)),
                "txt": _to_text(_nth(texts, index)),
                "md5": _to_text(_nth(md5s, index)),
            }
        )
    return metas


def _fallback_chapter_metas(book: CrawlSearchResult) -> list[dict[str, Any]]:
    return [
        {
            "ordinal": index,
            "novel_dirid": book.dirid,
            "chapterid": index,
            "chaptername": f"第{index}章",
            "time": "",
            "txt": "",
            "md5": "",
        }
        for index in range(1, max(book.lastchapterid, 0) + 1)
    ]


def _slice_chapter_metas(
    metas: list[dict[str, Any]],
    start_chapter: int,
    end_chapter: int,
) -> list[dict[str, Any]]:
    start = max(start_chapter, 1)
    end = max(end_chapter, start)
    return metas[start - 1 : end]


def _first_value(data: Any, path: str) -> Any:
    values = extract_json_path_values(data, path)
    return values[0] if values else None


def _first_text(data: Any, path: str) -> str:
    return _to_text(_first_value(data, path))


def _nth(values: list[Any], index: int) -> Any:
    if not values:
        return None
    if index < len(values):
        return values[index]
    if len(values) == 1:
        return values[0]
    return None


def _parse_json_path(path: str) -> list[str | int]:
    raw = path.strip()
    if not raw:
        return []
    if raw.startswith("$"):
        raw = raw[1:]
    tokens: list[str | int] = []
    index = 0
    while index < len(raw):
        char = raw[index]
        if char == ".":
            index += 1
            continue
        if char == "[":
            end = raw.find("]", index)
            if end < 0:
                raise NovelCrawlerConfigError(f"invalid JSON path: {path}")
            content = raw[index + 1 : end].strip().strip("'\"")
            if content == "*":
                tokens.append("*")
            elif re.fullmatch(r"-?\d+", content):
                tokens.append(int(content))
            else:
                tokens.append(content)
            index = end + 1
            continue
        end = index
        while end < len(raw) and raw[end] not in ".[":
            end += 1
        tokens.append(raw[index:end])
        index = end
    return [token for token in tokens if token != ""]


def _render_template(template: str, context: dict[str, Any], *, encode_url_values: bool) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = _to_text(context.get(key, ""))
        return quote(value, safe="") if encode_url_values else value

    return re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", replace, template)


def _parse_json_mapping(raw: str, context: dict[str, Any]) -> dict[str, str]:
    if not raw.strip():
        return {}
    rendered = _render_template(raw, context, encode_url_values=False)
    data = json.loads(rendered)
    if not isinstance(data, dict):
        raise NovelCrawlerConfigError("request headers must be a JSON object")
    return {str(key): _to_text(value) for key, value in data.items()}


def _parse_json_body(raw: str, context: dict[str, Any]) -> Any:
    rendered = _render_template(raw, context, encode_url_values=False)
    return json.loads(rendered)


def _book_context(book: CrawlSearchResult) -> dict[str, Any]:
    return {
        "id": book.id or book.dirid,
        "bookid": book.dirid or book.id,
        "dirid": book.dirid or book.id,
        "title": book.title,
        "sourceKey": book.source_key,
        "source_key": book.source_key,
    }


def _chapter_context(meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "chapterid": meta.get("chapterid", ""),
        "chapter_id": meta.get("chapterid", ""),
        "chapter": meta.get("chapterid", ""),
        "chaptername": meta.get("chaptername", ""),
        "index": meta.get("ordinal", ""),
    }


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        text = _to_text(value)
        match = re.search(r"\d+", text)
        return int(match.group(0)) if match else default


def _partition_metas(metas: list[dict[str, Any]], workers: int) -> list[list[dict[str, Any]]]:
    chunk_size = max((len(metas) + workers - 1) // workers, 1)
    return [metas[index : index + chunk_size] for index in range(0, len(metas), chunk_size)]


def _dump_source(source: NovelCrawlSource) -> dict[str, Any]:
    return {
        field: getattr(source, field)
        for field in (
            "key",
            "name",
            "base_url",
            "desc",
            "builtin",
            "source_type",
            "scope",
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
    }
