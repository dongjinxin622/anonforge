from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project import ProjectMemberRole, ProjectVideoMode


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="项目名称")
    intro: str = Field(default="", max_length=2000, description="项目简介")
    project_type: str = Field(default="novel_to_video", description="项目类型")
    content_type: str = Field(default="novel", description="内容来源类型")
    art_style: str = Field(default="3D_chinese_traditional", description="艺术风格")
    director_manual: str = Field(default="", description="导演风格")
    video_ratio: str = Field(default="9:16", description="视频比例")
    image_model: str = Field(default="", description="生图模型")
    video_model: str = Field(default="", description="视频模型")
    image_quality: str = Field(default="standard", description="图片质量")
    mode: ProjectVideoMode = Field(default=ProjectVideoMode.TEXT, description="视频生成模式")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    intro: str | None = None
    project_type: str | None = None
    content_type: str | None = None
    art_style: str | None = None
    director_manual: str | None = None
    video_ratio: str | None = None
    image_model: str | None = None
    video_model: str | None = None
    image_quality: str | None = None
    mode: ProjectVideoMode | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    owner_id: str
    my_role: ProjectMemberRole | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    disabled_at: datetime | None


class ProjectMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    user_public_id: str
    role: ProjectMemberRole
    joined_at: datetime


class ProjectMemberInvite(BaseModel):
    user_public_id: str = Field(min_length=1, max_length=36, description="被邀请用户的公开标识")
    role: ProjectMemberRole = Field(default=ProjectMemberRole.VIEWER, description="邀请加入后的项目角色")