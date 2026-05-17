from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserBase(BaseModel):
    """用户基础资料。"""

    username: str = Field(min_length=3, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=512)
    sort_order: int = Field(default=0)
    is_superuser: bool = Field(default=False)


class UserCreate(UserBase):
    """创建用户请求模型。"""

    password: str = Field(min_length=6, max_length=128)
    repassword: str = Field(min_length=6, max_length=128)

    @model_validator(mode="after")
    def validate_passwords_match(self) -> "UserCreate":
        if self.password != self.repassword:
            raise ValueError("两次输入的密码不一致")
        return self

class UserUpdate(BaseModel):
    """更新用户请求模型。"""

    username: str | None = Field(default=None, min_length=3, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=512)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    sort_order: int | None = None
    is_superuser: bool | None = None
    disabled_at: datetime | None = None


class UserRead(BaseModel):
    """用户响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    public_id: str
    username: str
    nickname: str | None
    email: str | None
    avatar_url: str | None
    sort_order: int
    is_superuser: bool
    disabled_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    """用户登录请求。"""
    username: str = Field(min_length=1, max_length=50, description="用户名")
    password: str = Field(min_length=8, max_length=128, description="密码")


class LoginUserInfo(BaseModel):
    """登录成功后返回的用户信息。"""

    public_id: str
    username: str
    nickname: str | None = None


class UserLoginResponse(BaseModel):
    """用户登录响应。"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: LoginUserInfo