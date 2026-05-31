from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


EVENT_STATES = {-1, 0, 1}


def to_camel(value: str) -> str:
    """将 snake_case 字段名转换为 camelCase。"""
    parts = value.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


SCHEMA_CONFIG = ConfigDict(populate_by_name=True, alias_generator=to_camel)
READ_SCHEMA_CONFIG = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)


class NovelChapterBase(BaseModel):
    """小说章节请求基础字段。"""

    model_config = SCHEMA_CONFIG

    chapter_index: int = Field(default=1, ge=1, le=9999)
    reel: str = Field(default="", max_length=120)
    chapter: str = Field(min_length=1, max_length=255)
    chapter_data: str = Field(min_length=1)
    event: str = Field(default="")
    event_state: int = Field(default=0)
    error_reason: str | None = None
    crawl_source_key: str = Field(default="", max_length=64)
    crawl_novel_dirid: str = Field(default="", max_length=120)
    crawl_chapter_id: int | None = None
    crawl_time: str = Field(default="", max_length=64)
    crawl_md5: str = Field(default="", max_length=64)

    @field_validator("event_state")
    @classmethod
    def validate_event_state(cls, value: int) -> int:
        if value not in EVENT_STATES:
            raise ValueError("event_state must be -1, 0 or 1")
        return value


class NovelChapterCreate(NovelChapterBase):
    """创建小说章节请求。"""


class NovelChapterUpdate(BaseModel):
    """更新小说章节请求。"""

    model_config = SCHEMA_CONFIG

    chapter_index: int | None = Field(default=None, ge=1, le=9999)
    reel: str | None = Field(default=None, max_length=120)
    chapter: str | None = Field(default=None, min_length=1, max_length=255)
    chapter_data: str | None = Field(default=None, min_length=1)
    event: str | None = None
    event_state: int | None = None
    error_reason: str | None = None
    crawl_source_key: str | None = Field(default=None, max_length=64)
    crawl_novel_dirid: str | None = Field(default=None, max_length=120)
    crawl_chapter_id: int | None = None
    crawl_time: str | None = Field(default=None, max_length=64)
    crawl_md5: str | None = Field(default=None, max_length=64)

    @field_validator("event_state")
    @classmethod
    def validate_event_state(cls, value: int | None) -> int | None:
        if value is not None and value not in EVENT_STATES:
            raise ValueError("event_state must be -1, 0 or 1")
        return value


class NovelChapterRead(NovelChapterBase):
    """小说章节响应。"""

    model_config = READ_SCHEMA_CONFIG

    id: int
    public_id: str
    project_id: int
    sort_order: int
    created_at: datetime
    updated_at: datetime
    disabled_at: datetime | None


class NovelChapterPage(BaseModel):
    """小说章节分页响应。"""

    data: list[NovelChapterRead]
    total: int
    page: int
    limit: int


class NovelChapterImportItem(BaseModel):
    """全文导入时前端预览得到的单章草稿。"""

    model_config = SCHEMA_CONFIG

    reel: str = Field(default="", max_length=120)
    chapter: str = Field(min_length=1, max_length=255)
    chapter_data: str = Field(min_length=1)


class NovelChapterImport(BaseModel):
    """全文导入请求。"""

    model_config = SCHEMA_CONFIG

    raw_text: str = ""
    chapters: list[NovelChapterImportItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_import_source(self) -> "NovelChapterImport":
        if not self.raw_text.strip() and not self.chapters:
            raise ValueError("raw_text or chapters is required")
        return self


class NovelImportSplitRule(BaseModel):
    """Built-in chapter split rule returned to the frontend import dialog."""

    model_config = SCHEMA_CONFIG

    key: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=120)
    description: str = Field(default="")
    chapter_pattern: str = Field(default="")
    chapter_flags_list: list[str] = Field(default_factory=list)
    reel_pattern: str = Field(default="")
    reel_flags_list: list[str] = Field(default_factory=list)
    builtin: bool = True


class NovelChapterBatchDelete(BaseModel):
    """批量删除章节请求。"""

    ids: list[int] = Field(min_length=1)


class NovelChapterBatchClean(BaseModel):
    """批量清洗章节请求。"""

    ids: list[int] = Field(min_length=1)


class NovelChapterEventStateUpdate(BaseModel):
    """批量更新事件状态请求。"""

    model_config = SCHEMA_CONFIG

    ids: list[int] = Field(min_length=1)
    event_state: int
    event: str | None = None
    error_reason: str | None = None

    @field_validator("event_state")
    @classmethod
    def validate_event_state(cls, value: int) -> int:
        if value not in EVENT_STATES:
            raise ValueError("event_state must be -1, 0 or 1")
        return value


class NovelChapterBatchResult(BaseModel):
    """批量操作结果。"""

    affected: int
