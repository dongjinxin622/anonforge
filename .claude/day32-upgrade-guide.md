# Day32 升级指南 —— 详细新增内容报告

> 生成时间：2026-05-22  
> 对比基准：case_one 项目 `feature/user` 分支 (commit fd84dbd)  
> 范本来源：`E:\AI智能体课程\AI agent\day32\代码\code`

---

## 一、总览

day32 范本在一次完整开发迭代中新增了 **5 大功能模块**：

| 模块 | 变更类型 | 涉及文件数 |
|------|----------|-----------|
| 用户个人设置（个人资料 / 密码 / 头像上传） | 新增 | 6 |
| Token 自动刷新机制 | 新增 | 3 |
| 导演手册文件系统管理（CRUD） | 新增 | 4 |
| 自动化测试套件 | 新增 | 10 |
| 数据库迁移工具（Alembic） | 新增 | 5 |

---

## 二、后端新增内容

### 2.1 用户个人设置服务 (`backend/app/services/user.py`)

**文件规模**：198 行 → 338 行（+140 行）

**新增异常类**：

```python
class UserPasswordMismatchError(UserServiceError):
    """当前密码校验失败异常。"""

class UserAvatarInvalidError(UserServiceError):
    """头像文件格式或内容不合法异常。"""
```

**新增函数（5 个）**：

| 函数 | 用途 | 技术要点 |
|------|------|----------|
| `get_user_by_email()` | 按邮箱查询用户 | 用于邮箱唯一性校验 |
| `get_current_user()` | 获取当前登录用户 | 调用 `get_user_or_raise` |
| `update_current_user_profile()` | 更新当前用户个人资料 | 仅允许修改 username / nickname / email，校验唯一性 |
| `update_current_user_password()` | 修改当前用户密码 | 先校验旧密码 (`verify_password`)，再哈希新密码 |
| `update_current_user_avatar()` | 更新头像 URL | 直接写入 `avatar_url` 字段 |
| `upload_current_user_avatar()` | 上传并处理头像图片 | **Pillow 图像处理**：居中裁剪 1:1 → 缩放 256×256 → RGBA 转 RGB → JPEG 存储 |

**头像上传核心逻辑**：

```
1. 校验 Content-Type（仅允许 PNG/JPEG/JPG）
2. 校验文件大小（≤ 5MB）
3. Pillow 打开图片 → 中心裁剪为正方形
4. 缩放至 256×256（LANCZOS 重采样）
5. RGBA/LA 模式 → 白底转换 RGB
6. 存储至 data/oss/avatars/{public_id}_{timestamp}.jpg
7. 写入 avatar_url = /oss/avatars/{filename}
```

**新增依赖**：`pip install Pillow`（已在 requirements.txt 中）

---

### 2.2 用户 Schema 扩展 (`backend/app/schemas/user.py`)

**文件规模**：82 行 → 151 行（+69 行）

**新增 Schema（5 个）**：

```python
from pydantic import AliasChoices  # 新增导入

class UserProfileUpdate(BaseModel):
    """当前登录用户个人资料更新模型。"""
    username: str | None = Field(default=None, min_length=3, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=255)

class UserPasswordUpdate(BaseModel):
    """当前登录用户密码修改模型。"""
    # 使用 AliasChoices 同时支持 snake_case 和 camelCase
    old_password: str = Field(validation_alias=AliasChoices("old_password", "oldPassword"))
    new_password: str = Field(validation_alias=AliasChoices("new_password", "newPassword"))
    confirm_password: str = Field(validation_alias=AliasChoices("confirm_password", "confirmPassword"))

    @model_validator(mode="after")
    def validate_new_password(self) -> "UserPasswordUpdate":
        if self.new_password != self.confirm_password:
            raise ValueError("新密码与确认密码不一致")
        if self.old_password == self.new_password:
            raise ValueError("新密码不能与当前密码相同")
        return self

class UserAvatarUpdate(BaseModel):
    """当前登录用户头像更新模型。"""
    avatar_url: str | None = Field(
        validation_alias=AliasChoices("avatar_url", "avatarUrl")
    )

class TokenRefreshRequest(BaseModel):
    """刷新 access token 请求。"""
    refresh_token: str = Field(
        validation_alias=AliasChoices("refresh_token", "refreshToken")
    )

class TokenRefreshResponse(BaseModel):
    """刷新 access token 响应。"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
```

**设计要点**：
- `AliasChoices` 使得 API 同时接受 `old_password` 和 `oldPassword`，兼容前端 camelCase 习惯
- `UserPasswordUpdate` 内置 `model_validator` 做新密码一致性校验
- `TokenRefreshRequest/Response` 为 token 自动刷新机制提供类型定义

---

### 2.3 导演手册 Schema (`backend/app/schemas/project.py`)

**文件规模**：132 行 → 180 行（+48 行）

**新增 Schema（5 个）**—— 结构上完全镜像视觉风格（VisualStyle）设计：

```python
class DirectorManualFileRead(BaseModel):
    """导演手册 Markdown 文件读取结果。"""
    path: str
    content: str
    size_bytes: int = Field(ge=0)

class DirectorManualFileWrite(BaseModel):
    """导演手册 Markdown 文件写入请求。"""
    path: str = Field(default="", max_length=255)
    content: str = Field(default="")

    @field_validator("path")
    @classmethod
    def validate_markdown_path(cls, value: str) -> str:
        if value and not value.lower().endswith(".md"):
            raise ValueError("导演手册文件必须是 .md 文件")
        return value

class DirectorManualImageRead(BaseModel):
    """导演手册图片读取结果。"""
    filename: str
    path: str
    url: str
    size_bytes: int = Field(ge=0)

class DirectorManualImageWrite(BaseModel):
    """导演手册图片写入请求。"""
    filename: str = Field(default="", max_length=120)
    data: str  # base64 数据

class DirectorManualRead(BaseModel):
    """导演手册完整读取结果。"""
    manual_path: str
    name: str = Field(default="")
    files: list[DirectorManualFileRead] = Field(default_factory=list)
    images: list[DirectorManualImageRead] = Field(default_factory=list)
```

---

### 2.4 导演手册服务层 (`backend/app/services/project.py`)

**文件规模**：~920 行 → ~1400+ 行（新增约 500 行）

**新增异常类**：

```python
class DirectorManualNotFoundError(ProjectServiceError):
    """导演手册不存在异常。"""

class DirectorManualValidationError(ProjectServiceError):
    """导演手册参数校验异常。"""
```

**新增服务函数（10+ 个）**—— 镜像视觉风格的设计：

| 函数 | 用途 |
|------|------|
| `list_director_manuals()` | 列出所有导演手册目录 |
| `read_director_manual_file()` | 读取单个 Markdown 文件 |
| `write_director_manual_file()` | 创建 / 覆盖 Markdown 文件 |
| `delete_director_manual_file()` | 删除 Markdown 文件（需超管） |
| `get_director_manual_image_path()` | 获取图片文件系统路径 |
| `write_director_manual_image()` | 创建 / 覆盖图片（base64 解码） |
| `delete_director_manual_image()` | 删除图片 |

加上内部辅助函数（`_director_manual_root`、`_director_manual_dir`、`_validate_manual_path` 等），总计约 **15 个新增函数**。

**关键设计**：
- 路径安全校验正则：`^[A-Za-z0-9][A-Za-z0-9_-]{0,119}$`
- 图片仅允许 `.png` 扩展名
- 自动生成默认 README.md（`_write_default_readme_if_needed`）
- 文件写入操作在超管权限下执行

**配置支持**：
```python
# backend/app/core/config.py（day31 已添加）
director_manual_root: str = "./data/skills/director_manual"
```

---

### 2.5 用户路由扩展 (`backend/app/routers/user.py`)

**文件规模**：246 行 → 401 行（+155 行）

**新增导入**：
```python
import jwt
from fastapi import File, UploadFile
from app.utils.jwt_tools import create_access_token_from_refresh_token
```

**新增端点（6 个）**：

| 方法 | 路径 | 功能 | 鉴权 |
|------|------|------|------|
| `GET` | `/users/me` | 获取当前登录用户信息 | JWT |
| `PUT` | `/users/me/profile` | 更新当前用户个人资料 | JWT |
| `PUT` | `/users/me/password` | 修改当前用户密码 | JWT |
| `PUT` | `/users/me/avatar` | 更新当前用户头像 URL | JWT |
| `POST` | `/users/me/avatar/upload` | 上传头像图片文件 | JWT |
| `POST` | `/users/refresh-token` | 使用 refresh token 换取新 access token | 无（仅 duration 中间件） |

**设计要点**：
- 所有 `/me/*` 端点从 JWT token 中提取 `current_user_public_id`，用户只能修改自己的数据
- `POST /refresh-token` 不需要 JWT 鉴权（因为正是 access token 过期才需要刷新），仅记录请求耗时
- 头像上传使用 `UploadFile` + `multipart/form-data`

**中间件常量提取**：
```python
USER_ROUTE_MIDDLEWARES = [
    Depends(common.jwt_auth_middleware),
    Depends(common.request_duration_middleware),
]
```

---

### 2.6 导演手册路由 (`backend/app/routers/project.py`)

**文件规模**：674 行 → 839 行（+165 行）

**新增端点（7 个）**：

| 方法 | 路径 | 功能 | 鉴权 |
|------|------|------|------|
| `GET` | `/projects/director-manuals` | 列出所有导演手册 | JWT |
| `GET` | `/projects/director-manuals/{manual_path}/files/{file_path}` | 读取手册文件 | JWT |
| `PUT` | `/projects/director-manuals/{manual_path}/files/{file_path}` | 写入手册文件 | JWT |
| `DELETE` | `/projects/director-manuals/{manual_path}/files/{file_path}` | 删除手册文件 | JWT（超管） |
| `GET` | `/projects/director-manuals/{manual_path}/images/{filename}` | 获取手册图片 | **无鉴权**（FileResponse） |
| `PUT` | `/projects/director-manuals/{manual_path}/images/{filename}` | 写入手册图片 | JWT |
| `DELETE` | `/projects/director-manuals/{manual_path}/images/{filename}` | 删除手册图片 | JWT |

> 图片 GET 端点不需要 JWT 鉴权，原因是 `FileResponse` 直接返回文件内容，需要能被 `<img src>` 和 CSS `url()` 直接引用。

---

### 2.7 测试套件（全新）(`backend/app/tests/`)

**共 8 个文件**，覆盖配置、数据库、健康检查、用户模型、用户服务、用户路由、项目服务。

#### 2.7.1 测试基础设施 (`tests/base.py`)

```python
class EnvTestBase:
    """环境变量驱动的测试基类。"""
    def set_env(self, monkeypatch, values: dict[str, str]) -> None:
        """批量设置环境变量。"""

    def reload_modules(self, *modules) -> tuple:
        """重新加载模块以应用新环境变量。"""

class ApiTestBase:
    """API 接口测试基类。"""
    def create_client(self) -> TestClient:
        """创建 FastAPI TestClient。"""
```

**核心机制**：通过 `monkeypatch.setenv` + `importlib.reload` 实现不同测试使用不同的数据库配置（SQLite 内存 / 临时文件），无需修改实际环境变量。

#### 2.7.2 配置测试 (`tests/test_config.py`)

验证 `Settings` dataclass 正确读取环境变量并进行类型转换（`PORT` → int 等）。

#### 2.7.3 数据库引擎测试 (`tests/test_database.py`)

验证在设置 `DB_ENGINE=sqlite` + `DB_DRIVER=aiosqlite` 后：
- 引擎 URL 的 `drivername` 为 `sqlite+aiosqlite`
- `async_session_maker.class_` 是 `AsyncSession`
- `get_session` 是异步生成器函数

#### 2.7.4 健康检查测试 (`tests/test_health.py`)

```python
class TestMainApi(ApiTestBase):
    def test_health_endpoint_returns_ok(self) -> None:
        with self.create_client() as client:
            response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

#### 2.7.5 用户模型测试 (`tests/test_user_model.py`)

验证 `User` 模型的状态方法：
- `disable()` → `disabled_at` 非空，`is_disabled` 为 True，`is_active` 为 False
- `enable()` → `disabled_at` 为空，`is_disabled` 为 False，`is_active` 为 True
- `update_last_login()` → `last_login_at` 非空

#### 2.7.6 用户服务测试 (`tests/test_user_service.py`)

- **CRUD 全流程测试**：创建 → 查询 → 更新 → 禁用 → 列表 → 删除
- **默认管理员测试**：验证 `ensure_default_admin()` 在空数据库时创建 admin，已有管理员时跳过，admin 用户存在时升级为超管

#### 2.7.7 用户路由测试 (`tests/test_user_router.py`)

- **完整 CRUD 集成测试**：通过 `httpx.AsyncClient` + `ASGITransport` 测试实际 HTTP 端点
- **登录成功测试**：验证返回 access_token、refresh_token、user 信息
- **登录失败测试**：密码错误返回 401，用户被禁用返回 403
- 使用 SQLite 临时文件作为测试数据库，环境变量注入

#### 2.7.8 项目服务测试 (`tests/test_project_service.py`)

- **成员邮箱 JOIN 测试**：验证 `list_project_members` 返回 `ProjectMemberRead`（含 `user_email`）
- **视觉风格集成测试**：通过 HTTP 端点测试视觉风格的完整 CRUD 流程
- 验证 `list_visual_styles`、`get_visual_style_image_path` 等功能

**测试技术栈**：
```
pytest + pytest-asyncio (anyio)
httpx.AsyncClient + ASGITransport（异步 HTTP 测试）
sqlite+aiosqlite（测试数据库隔离）
monkeypatch（环境变量注入）
```

**新建配置文件**：

`backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = app/tests
```

`backend/requirements.txt` 新增依赖：
```
pytest>=8.0
pytest-asyncio>=0.24
httpx>=0.27
aiosqlite>=0.20
Pillow>=10.0
```

---

### 2.8 数据库迁移工具 Alembic（全新）(`backend/alembic/`)

**文件清单**：

| 文件 | 用途 |
|------|------|
| `alembic.ini` | Alembic 主配置（数据库 URL 由 env.py 动态注入） |
| `env.py` | 迁移环境：从 `app.core.config` 读取配置，动态拼接数据库 URL，设置 `target_metadata = SQLModel.metadata` |
| `script.py.mako` | 迁移脚本模板（Mako 模板引擎） |
| `versions/3c78bc78cf88_create_user_table.py` | 用户表创建迁移（`af_user`） |
| `versions/b17a735cfd65_create_project_table.py` | 项目表创建迁移（早期版本） |
| `versions/56edd77febb5_create_project_table.py` | 项目表创建迁移（最终版本，含 `af_project` + `af_project_member`） |

**使用方式**：
```bash
cd backend
alembic upgrade head      # 执行所有迁移
alembic downgrade -1      # 回滚一个版本
alembic revision --autogenerate -m "描述"  # 自动生成迁移
```

**设计要点**：
- `env.py` 不做硬编码数据库 URL，而是从 `app.core.config.settings` 动态读取
- 兼容 PostgreSQL 和 SQLite
- `target_metadata = SQLModel.metadata` 支持自动生成（autogenerate）

---

## 三、前端新增内容

### 3.1 用户 API 扩展 (`frontend/src/api/user.ts`)

**文件规模**：24 行 → 89 行（+65 行）

**新增接口类型**：

```typescript
export interface UserRecord {
  public_id: string
  username: string
  nickname: string | null
  email: string | null
  avatar_url: string | null
  sort_order: number
  is_superuser: boolean
  disabled_at: string | null
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface UserProfileUpdatePayload {
  username?: string
  nickname?: string | null
  email?: string | null
}

export interface UserPasswordUpdatePayload {
  old_password: string
  new_password: string
  confirm_password: string
}
```

**新增 API 函数（6 个）**：

| 函数 | 端点 | 用途 |
|------|------|------|
| `getCurrentUserApi()` | `GET /users/me` | 获取当前用户 |
| `updateCurrentUserProfileApi()` | `PUT /users/me/profile` | 更新个人资料 |
| `updateCurrentUserPasswordApi()` | `PUT /users/me/password` | 修改密码 |
| `updateCurrentUserAvatarApi()` | `PUT /users/me/avatar` | 更新头像 URL |
| `uploadCurrentUserAvatarApi()` | `POST /users/me/avatar/upload` | 上传头像文件（FormData） |
| `updateUserApi()` | `PUT /users/{public_id}` | 管理员更新用户 |

---

### 3.2 导演手册 API (`frontend/src/api/project.ts`)

**文件规模**：138 行 → 163 行（+25 行）

**新增接口类型**：

```typescript
export interface DirectorManualFileRecord {
  path: string
  content: string
  size_bytes: number
}

export interface DirectorManualImageRecord {
  filename: string
  path: string
  url: string
  size_bytes: number
}

export interface DirectorManualRecord {
  manual_path: string
  name: string
  files: DirectorManualFileRecord[]
  images: DirectorManualImageRecord[]
}
```

**新增 API 函数**：

```typescript
export const listDirectorManualsApi = () =>
  request.get<DirectorManualRecord[]>('/projects/director-manuals')
```

---

### 3.3 Token 自动刷新拦截器 (`frontend/src/request/index.ts`)

**文件规模**：18 行 → 108 行（+90 行）

这是前端最重要的架构升级之一。完整实现了 **无感知 token 刷新** 机制。

**核心逻辑**：

```
请求拦截器：
  → 从 localStorage 读取 access_token，附加到 Authorization 头

响应拦截器（错误处理）：
  → 收到 401 错误？
    → 是鉴权路由（login / refresh-token）？→ 直接拒绝
    → 已经重试过？→ 直接拒绝
    → 错误消息不含 "access token"？→ 直接拒绝
    → 有 refresh_token？
      → 是：调用 refreshAccessToken()
        → 成功 → 更新 localStorage → 重试原请求
        → 失败 → 清除凭据 → 跳转登录页
      → 否：清除凭据 → 拒绝
```

**并发刷新去重**：

```typescript
let refreshTokenRequest: Promise<string> | null = null

const refreshAccessToken = (refreshToken: string) => {
  if (!refreshTokenRequest) {
    refreshTokenRequest = axios
      .post<TokenRefreshResult>('/api/users/refresh-token', { refresh_token: refreshToken })
      .then(({ data }) => {
        localStorage.setItem('access_token', data.access_token)
        return data.access_token
      })
      .finally(() => { refreshTokenRequest = null })
  }
  return refreshTokenRequest
}
```

**设计要点**：
- 多个并发请求同时遇到 401 时，只发起一次 refresh 请求（`refreshTokenRequest` Promise 复用）
- 刷新成功后自动重试原请求（`_retry` 标记防止无限循环）
- 刷新失败时清除所有凭据并跳转到登录页
- 登录 / 刷新接口本身不触发刷新逻辑（防止死循环）

---

### 3.4 设置对话框组件（全新）(`frontend/src/components/Settings.vue`)

**文件规模**：1238 行（模板 225 行 + 脚本 470 行 + 样式 543 行）

一个完整的暗色主题设置对话框，包含 **3 个功能面板**：

#### 面板一：个人资料（Profile）

- 表单字段：用户名、昵称、邮箱
- 头像显示：有头像时显示图片，无头像时显示用户名首字母
- **头像上传**：
  - 文件类型校验（PNG/JPEG/JPG）
  - 文件大小校验（≤ 5MB）
  - 客户端裁剪工具（Pointer Events 实现拖拽移动 + 右下角缩放）
  - Canvas 裁剪渲染 → JPEG blob → `FormData` 上传
- 头像渐变圆形背景（金色到紫色渐变）

#### 面板二：修改密码（Password）

- 旧密码、新密码、确认密码三个字段
- **密码强度指示器**（4 级）：
  - 1 级（红）：长度 ≥ 8
  - 2 级（橙）：含大小写字母
  - 3 级（黄）：含数字
  - 4 级（绿）：含特殊字符
- 客户端校验：新密码与确认密码一致性、新旧密码不能相同

#### 面板三：注销登录（Logout）

- 显示当前用户信息（头像、昵称、用户名、邮箱）
- 显示最后登录时间和当前设备信息
- 注销确认对话框（`ElMessageBox.confirm`）
- 注销后清除所有 localStorage 凭据并跳转到登录页

**技术亮点**：

1. **自定义头像裁剪工具**：
   - 使用 Pointer Events API 实现拖拽（`pointerdown` → `pointermove` → `pointerup`）
   - 9 宫格辅助线（CSS `background-image` linear-gradient）
   - Canvas 渲染裁剪区域为 JPEG blob
   - 支持触摸设备（`touch-action: none`）

2. **暗色主题样式系统**：
   - 完整的 Element Plus 组件深度定制（`:deep()` + 全局 class 覆盖）
   - 毛玻璃效果（`rgba` 半透明 + `backdrop-filter`）
   - 蓝色主色调（`#2563eb`）
   - 响应式布局（移动端侧边栏切换为横向滚动）

3. **`defineModel` 双向绑定**：
   ```typescript
   const visible = defineModel<boolean>({ default: false })
   ```
   父组件可直接使用 `v-model="settingsVisible"` 控制显示。

---

### 3.5 全局样式 (`frontend/src/style.css`)

```css
html, body {
  margin: 0;
  padding: 0;
}
```

极简的全局 reset，消除浏览器默认边距。

---

### 3.6 项目页面升级 (`frontend/src/pages/Project.vue`)

**文件规模**：1171 行 → 2707 行（+1536 行）

**新增功能**：

1. **设置弹窗集成**：
   ```vue
   <Settings v-model="settingsVisible" />
   ```
   侧边栏"设置"按钮现在打开 Settings 组件而非显示"即将开放"。

2. **导演手册选择器**：
   - 在项目创建 / 编辑对话框中，`director_manual` 字段从纯文本输入变为**可视化卡片选择器**
   - 每个导演风格显示概念图缩略图（背景图 URL）
   - 点击卡片选中，支持放大预览（`el-dialog` 嵌套）
   - 数据来源于 `listDirectorManualsApi()` 接口

3. **新增导入**：
   ```typescript
   import Settings from '../components/Settings.vue'
   import { listDirectorManualsApi, type DirectorManualRecord } from '@/api/project'
   ```

4. **新增状态和方法**：
   - `settingsVisible` ref
   - `directorStylePresets`、`directorStylesLoading`
   - `loadDirectorManuals()`、`getDirectorStyleBackground()`、`openDirectorPreview()`
   - `activeDirectorStyleLabel` computed

---

### 3.7 路由守卫升级 (`frontend/src/routes/index.ts`)

day32 的路由文件与 case_one 当前版本 **完全相同**（均已有路由守卫），无需变更。

---

## 四、数据文件新增

### 4.1 导演手册数据 (`data/skills/director_manual/`)

**12 个导演风格类别**，每个类别包含完整的手册文件：

```
director_manual/
├── Comedy_humor/          # 喜剧幽默
├── Coming_of_age/         # 成长青春
├── Family_warmth/         # 家庭温情
├── Historical_epic/       # 历史史诗
├── Horror_supernatural/   # 恐怖超自然
├── Hot_blooded_action/    # 热血动作
├── Mystery_thriller/      # 悬疑惊悚
├── Psychological_drama/   # 心理剧情
├── Scifi_post_apocalypse/ # 科幻末日
├── Sweet_romance_novel/   # 甜宠言情
├── Urban_workplace_drama/ # 都市职场
└── Xianxia_fantasy/       # 仙侠奇幻
```

每个类别目录结构：
```
{Category}/
├── README.md                                  # 风格说明
├── director_manual/
│   ├── director_planning_narrative.md          # 导演规划叙事
│   └── director_storyboard_table_narrative.md  # 分镜表叙事
└── images/
    ├── concept_image_prompt.md                 # 概念图生成提示词
    └── director_concept.png                    # 导演概念图
```

### 4.2 头像样例 (`data/oss/avatars/`)

```
avatars/
└── 5819119d-86f7-4122-8320-ec5321f0e5d9_1778680555.jpg
```

预置的头像样例文件，用户上传头像时也会生成到此目录。

---

## 五、变更影响分析

### 5.1 需要新增的依赖

**后端 Python 包**（`backend/requirements.txt`）：
```
pytest>=8.0
pytest-asyncio>=0.24
httpx>=0.27
aiosqlite>=0.20
Pillow>=10.0
alembic>=1.14
```

### 5.2 需要新增的配置文件

| 文件 | 位置 |
|------|------|
| `pytest.ini` | `backend/pytest.ini` |
| `alembic.ini` | `backend/alembic.ini` |

### 5.3 需要新增的目录

| 目录 | 用途 |
|------|------|
| `backend/app/tests/` | 测试文件 |
| `backend/alembic/` | 数据库迁移 |
| `data/skills/director_manual/` | 导演手册数据 |
| `data/oss/avatars/` | 用户头像存储 |

### 5.4 需要修改的现有文件清单

| 文件 | 变更幅度 |
|------|----------|
| `backend/app/schemas/user.py` | +69 行（新增 5 个 Schema） |
| `backend/app/schemas/project.py` | +48 行（新增 5 个 Schema） |
| `backend/app/services/user.py` | +140 行（新增 6 个函数 + 2 个异常类） |
| `backend/app/services/project.py` | +500 行（导演手册全套 CRUD） |
| `backend/app/routers/user.py` | +155 行（新增 6 个端点） |
| `backend/app/routers/project.py` | +165 行（新增 7 个端点） |
| `frontend/src/api/user.ts` | +65 行（新增 6 个 API 函数 + 3 个接口） |
| `frontend/src/api/project.ts` | +25 行（新增 3 个接口 + 1 个 API 函数） |
| `frontend/src/request/index.ts` | +90 行（Token 刷新拦截器） |
| `frontend/src/pages/Project.vue` | +1536 行（设置弹窗 + 导演手册选择器） |

### 5.5 无需修改的文件

以下文件 day32 与 case_one **内容一致**，无需变更：
- `backend/app/core/config.py`、`database.py`、`main.py`
- `backend/app/models/project.py`、`user.py`
- `backend/app/middlewares/common.py`
- `backend/app/utils/jwt_tools.py`、`string_tools.py`、`time_tools.py`
- `backend/app/routers/base.py`、`api.py`
- `backend/app/models/base.py`
- `frontend/src/pages/Login.vue`（行数和结构相同）
- `frontend/src/main.ts`、`App.vue`
- `frontend/src/routes/index.ts`（已含路由守卫）

---

## 六、技术学习要点

### 6.1 AliasChoices 字段别名

```python
from pydantic import AliasChoices

class UserPasswordUpdate(BaseModel):
    old_password: str = Field(
        validation_alias=AliasChoices("old_password", "oldPassword")
    )
```

Pydantic v2 的 `AliasChoices` 允许一个字段接受多个名称，同时兼容 Python snake_case 和前端 camelCase 的传参习惯。

### 6.2 Token 自动刷新模式

前端使用 **axios 响应拦截器 + Promise 去重** 实现无感知 token 刷新：
- 多个并发请求同时 401 时，只发一个 refresh 请求
- 刷新成功后重放原请求
- 刷新失败清除凭据并跳转登录

### 6.3 Pillow 图像处理链

```
上传文件 → BytesIO → Image.open → 居中裁剪(1:1) → 
缩放(256×256 LANCZOS) → RGBA白底转换 → JPEG存储
```

### 6.4 monkipatch + importlib.reload 测试模式

```python
class EnvTestBase:
    def set_env(self, monkeypatch, values):
        for k, v in values.items():
            monkeypatch.setenv(k, v)

    def reload_modules(self, *modules):
        return tuple(importlib.reload(m) for m in modules)
```

每次测试使用独立的 SQLite 临时文件，通过环境变量注入隔离，避免测试间相互影响。

### 6.5 Alembic 动态数据库 URL

```python
# env.py
from app.core.config import settings
from app.utils.string_tools import build_database_url

database_url = build_database_url(...)
config.set_main_option("sqlalchemy.url", database_url)
```

不在 `alembic.ini` 中硬编码数据库连接，而是从应用配置动态读取，兼容多环境。

### 6.6 SQLModel + Alembic 自动迁移

```python
target_metadata = SQLModel.metadata  # 关键：指向所有模型
```

只需要 `from app.models import *`，Alembic 就能自动发现所有 SQLModel 表定义，`--autogenerate` 时会自动对比数据库现状和模型定义，生成迁移脚本。

### 6.7 客户端图片裁剪（Pointer Events）

使用原生 Pointer Events API 而非第三方裁剪库：
- `pointerdown` 开始拖拽 → `pointermove` 更新位置/大小 → `pointerup` 结束
- 全局事件监听（`document.addEventListener`）确保鼠标移出裁剪框后仍可跟踪
- Canvas 裁剪渲染为 JPEG blob 后上传

### 6.8 文件系统管理模式的复用

导演手册（DirectorManual）和视觉风格（VisualStyle）采用 **完全相同的架构模式**：
- 相同的 Schema 结构（FileRead/Write、ImageRead/Write、Read）
- 相同的路由模式（list + CRUD file + CRUD image）
- 相同的服务层设计（路径校验 → 文件操作 → 错误映射）

这种模式可复用于任何"文件系统级别的资源管理"场景。

---

## 七、升级优先级建议

| 优先级 | 模块 | 理由 |
|--------|------|------|
| P0 | Token 自动刷新（`request/index.ts`） | 影响用户体验，token 过期后需手动重新登录 |
| P0 | 用户设置 API（`services/user.py` 等） | Settings 组件依赖此后端 |
| P1 | 用户设置 UI（`Settings.vue`） | 提供完整的用户自助管理能力 |
| P1 | 测试套件（`tests/`） | 保障代码质量，防止回归 |
| P2 | 导演手册管理（前后端全套） | 业务功能增强，Project.vue 中已有 UI 集成 |
| P2 | Alembic 迁移 | 数据库版本管理，生产环境必需 |
| P3 | `style.css` | 极简改动，可随时添加 |