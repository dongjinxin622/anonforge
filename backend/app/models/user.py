from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlmodel import Field, SQLModel

from app.utils.time_tools import utc_now


class User(SQLModel, table=True):
    """用户表模型。"""
    __tablename__ = "af_user"
    id: int = Field(default=None, sa_column=Column("id", Integer, primary_key=True, autoincrement=True, nullable=False,),)
    public_id: str = Field(default_factory=lambda: str(uuid4()), sa_column=Column("public_id", String(36), unique=True, nullable=False, index=True,),)

    username: str = Field( sa_column=Column("username", String(64), unique=True, nullable=False, index=True,), description="登录用户名，全局唯一。",)
    nickname: str | None = Field(default=None, sa_column=Column("nickname", String(64), nullable=True,), description="用户昵称，用于前端展示。",)
    email: str | None = Field(default=None, sa_column=Column("email", String(255), unique=True, nullable=True, index=True,), description="用户邮箱。",)
    avatar_url: str | None = Field(default=None, sa_column=Column("avatar_url", String(512), nullable=True,), description="用户头像地址。",)
    password_hash: str = Field(sa_column=Column("password_hash", String(255), nullable=False,), description="密码哈希值。",)

    is_superuser: bool = Field(default=False, sa_column=Column("is_superuser", Boolean, nullable=False, default=False,), description="是否为超级管理员。",)

    sort_order: int = Field(default=0, sa_column=Column("sort_order", Integer, nullable=False, default=0, index=True,), description="排序值，数值越小越靠前。",)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column("created_at", DateTime(timezone=True), nullable=False, default=utc_now,),)
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column("updated_at", DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now,),)
    disabled_at: datetime | None = Field(default=None, sa_column=Column("disabled_at", DateTime(timezone=True), nullable=True, index=True,), description="账号禁用时间。",)
    last_login_at: datetime | None = Field(default=None, sa_column=Column("last_login_at", DateTime(timezone=True), nullable=True,), description="最近登录时间。",)

    @property
    def is_disabled(self) -> bool:
        """账号是否已被禁用。"""
        return self.disabled_at is not None

    @property
    def is_active(self) -> bool:
        """账号是否可用。"""
        return self.disabled_at is None

    async def disable(self) -> None:
        """禁用账号。"""
        self.disabled_at = utc_now()

    async def enable(self) -> None:
        """启用账号。"""
        self.disabled_at = None

    async def update_last_login(self) -> None:
        """更新最近登录时间。"""
        self.last_login_at = utc_now()
