from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlmodel import Field

from app.models.base import BaseModel


class NovelChapter(BaseModel, table=True):
    """小说章节表模型。"""

    __tablename__ = "af_novel_chapter"

    project_id: int = Field(
        sa_column=Column("project_id", Integer, ForeignKey("af_project.id"), nullable=False, index=True),
        description="所属项目内部主键。",
    )
    chapter_index: int = Field(
        default=1,
        sa_column=Column("chapter_index", Integer, nullable=False, default=1, index=True),
        description="章节序号。",
    )
    reel: str = Field(
        default="",
        sa_column=Column("reel", String(120), nullable=False, default="", server_default=""),
        description="卷次标题。",
    )
    chapter: str = Field(
        sa_column=Column("chapter", String(255), nullable=False, index=True),
        description="章节标题。",
    )
    chapter_data: str = Field(
        default="",
        sa_column=Column("chapter_data", Text(), nullable=False, default="", server_default=""),
        description="章节正文。",
    )
    event: str = Field(
        default="",
        sa_column=Column("event", Text(), nullable=False, default="", server_default=""),
        description="清洗后的事件内容。",
    )
    event_state: int = Field(
        default=0,
        sa_column=Column("event_state", Integer, nullable=False, default=0, server_default="0", index=True),
        description="事件清洗状态：0 待清洗，1 成功，-1 失败。",
    )
    error_reason: str | None = Field(
        default=None,
        sa_column=Column("error_reason", Text(), nullable=True),
        description="清洗失败原因。",
    )
    crawl_source_key: str = Field(
        default="",
        sa_column=Column("crawl_source_key", String(64), nullable=False, default="", server_default=""),
        description="小说来源唯一标识。",
    )
    crawl_novel_dirid: str = Field(
        default="",
        sa_column=Column("crawl_novel_dirid", String(120), nullable=False, default="", server_default=""),
        description="小说来源小说唯一ID。",
    )
    crawl_chapter_id: int | None = Field(
        default=None,
        sa_column=Column("crawl_chapter_id", Integer, nullable=True),
        description="小说来源章节唯一标识。",
    )
    crawl_time: str = Field(
        default="",
        sa_column=Column("crawl_time", String(64), nullable=False, default="", server_default=""),
        description="小说来源章节发布时间。",
    )
    crawl_md5: str = Field(
        default="",
        sa_column=Column("crawl_md5", String(64), nullable=False, default="", server_default=""),
        description="小说来源正文 MD5。",
    )
