# 系统架构总览：用户注册、信息管理与项目协作

> 生成时间：2026-05-23 | 分支：`feature/visual-style`

---

## 一、整体技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | **FastAPI** (Python 3.x) | 异步 HTTP 框架，基于 Starlette + Pydantic |
| ORM | **SQLModel** | SQLAlchemy + Pydantic 融合层，同时作为数据库模型和类型校验 |
| 数据库 | **PostgreSQL** (开发) / **SQLite** (测试) | 通过 `aiosqlite` + `asyncpg` 异步驱动 |
| 迁移 | **Alembic** | 5 个迁移版本，覆盖用户表和项目表 |
| 缓存/会话 | **Redis** | Token 存储、吊销列表 |
| 前端框架 | **Vue 3** + Composition API + `<script setup>` | Vite 8 构建，TypeScript 6 |
| UI 组件库 | **Element Plus 2** | 暗色自定义主题 |
| 状态管理 | **Pinia 3** | 轻量级状态管理 |
| HTTP 客户端 | **Axios 1** | 拦截器实现自动 Token 刷新 |
| 路由 | **Vue Router 5** | Web History 模式 + 导航守卫 |
| 密码加密 | **bcrypt + SHA-256** | 加盐哈希 |
| 认证协议 | **JWT (HS256)** | Access Token + Refresh Token 双令牌机制 |
| 图片处理 | **Pillow (PIL)** | 头像裁剪、缩放、格式转换 |
| 容器化 | **Docker Compose** | PostgreSQL 18-alpine + Redis 8.6.3-alpine |

---

## 二、目录结构

```
e:\projects\case_one\
├── backend/
│   ├── app/
│   │   ├── main.py                       # FastAPI 应用入口，注册中间件和路由
│   │   ├── core/
│   │   │   ├── config.py                 # 集中配置（Settings dataclass，从 .env 读取）
│   │   │   └── database.py               # 异步引擎、会话工厂、Redis 客户端
│   │   ├── middlewares/
│   │   │   └── common.py                 # JWT 认证中间件 + 请求耗时中间件
│   │   ├── models/
│   │   │   ├── base.py                   # BaseModel 抽象基类（public_id、时间戳、软删除）
│   │   │   ├── user.py                   # User 模型（af_user 表）
│   │   │   └── project.py                # Project + ProjectMember 模型 + 枚举
│   │   ├── routers/
│   │   │   ├── base.py                   # BaseView 类视图 + @route 装饰器
│   │   │   ├── api.py                    # 根路由聚合 + /api/health 健康检查
│   │   │   ├── user.py                   # 用户相关端点（登录、注册、资料、头像）
│   │   │   └── project.py                # 项目相关端点（CRUD、成员、视觉风格、导演手册）
│   │   ├── schemas/
│   │   │   ├── user.py                   # 用户请求/响应 DTO
│   │   │   └── project.py                # 项目请求/响应 DTO
│   │   ├── services/
│   │   │   ├── user.py                   # 用户业务逻辑（CRUD、密码、头像上传、默认管理员引导）
│   │   │   └── project.py                # 项目业务逻辑（CRUD、成员、视觉风格、导演手册）
│   │   ├── utils/
│   │   │   ├── jwt_tools.py              # JWT 创建/解码/刷新/吊销
│   │   │   ├── string_tools.py           # bcrypt+sha256 密码哈希、数据库 URL 构建
│   │   │   └── time_tools.py             # utc_now() 辅助函数
│   │   └── tests/                        # pytest 测试套件
│   └── run.py                            # Uvicorn 启动脚本
├── frontend/
│   └── src/
│       ├── main.ts                       # Vue 应用入口（Pinia + Router + ElementPlus）
│       ├── App.vue                       # 根组件
│       ├── request/index.ts              # Axios 实例 + 拦截器
│       ├── routes/index.ts               # 路由配置 + 导航守卫
│       ├── api/
│       │   ├── user.ts                   # 用户 API 封装
│       │   └── project.ts                # 项目 API 封装
│       ├── pages/
│       │   ├── Login.vue                 # 登录页面（终端风格 UI）
│       │   └── Project.vue               # 项目仪表盘（卡片、对话框、成员管理）
│       └── components/
│           └── Settings.vue              # 设置面板（资料、密码、头像裁剪、注销）
├── data/
│   ├── oss/avatars/                      # 上传头像存储
│   └── skills/
│       ├── art_list/                     # 视觉风格目录（Markdown + images/）
│       └── director_manual/              # 导演手册目录（Markdown + images/）
└── docker/
    ├── postgres/data/
    └── redis/data/
```

---

## 三、数据模型设计

### 3.1 基础模型 [base.py](../backend/app/models/base.py)

所有实体继承 `BaseModel`，统一提供以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `int` (PK) | 自增主键 |
| `public_id` | `str` (UUID) | 对外公开的唯一标识，索引 |
| `sort_order` | `int` | 排序值，越小越靠前 |
| `created_at` | `datetime(tz)` | 创建时间 |
| `updated_at` | `datetime(tz)` | 最近更新时间，自动更新 |
| `disabled_at` | `datetime(tz)` \| `None` | 软删除标记，非 None 表示已禁用 |

内置方法：`is_disabled`、`is_active`、`disable()`、`enable()`

### 3.2 用户模型 [user.py:12](../backend/app/models/user.py#L12)

表名：`af_user`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `username` | `str(64)` | UNIQUE, INDEX | 登录用户名 |
| `nickname` | `str(64)` \| `None` | - | 展示昵称 |
| `email` | `str(255)` \| `None` | UNIQUE, INDEX | 邮箱 |
| `avatar_url` | `str(512)` \| `None` | - | 头像地址 |
| `password_hash` | `str(255)` | NOT NULL | bcrypt+sha256 哈希 |
| `is_superuser` | `bool` | 默认 False | 超级管理员标记 |
| `last_login_at` | `datetime(tz)` \| `None` | - | 最近登录时间 |

### 3.3 项目模型 [project.py](../backend/app/models/project.py)

**Project**(`af_project`)：name, intro, project_type, content_type, art_style, director_manual, video_ratio, image_model, video_model, image_quality, mode（枚举：text/singleImage/startEndRequired/endFrameOptional/startFrameOptional）, owner_id（FK → `af_user.public_id`）

**ProjectMember**(`af_project_member`)：project_id (FK), user_public_id (FK), role（枚举：owner/admin/manager/editor/viewer）, joined_at

---

## 四、用户认证系统

### 4.1 JWT 令牌机制 [jwt_tools.py](../backend/app/utils/jwt_tools.py)

**双令牌设计**：

| 令牌类型 | 有效期 | 用途 |
|---------|--------|------|
| Access Token | 9000 秒（默认） | 业务请求鉴权 |
| Refresh Token | 604800 秒（默认） | 无感刷新 Access Token |

**核心流程**：

1. **登录** → `create_login_tokens()` 同时生成两个令牌，以 JWT + Redis 双存储
   - JWT Payload：`sub`(public_id), `username`, `type`(access/refresh), `jti`(UUID), `iat`, `exp`
   - Redis：`{prefix}{jti}` → `{public_id, token_type, expires_at}`，TTL 与 JWT 过期时间一致

2. **鉴权** → 中间件 `jwt_auth_middleware` 解析 Bearer token → 调用 `decode_token()` → 校验 JWT 签名 + Redis 中是否存在（未被吊销）→ 验证 `type == "access"` → 注入 `request.state.current_user_public_id`

3. **刷新** → `create_access_token_from_refresh_token()` → 验证 refresh token → 签发新的 access token

4. **吊销** → 从 Redis 删除对应 key，实现登出

### 4.2 密码安全 [string_tools.py](../backend/app/utils/string_tools.py)

- 算法：**bcrypt + SHA-256** 两级哈希
- `hash_password(raw)` → 先 SHA-256 再 bcrypt
- `verify_password(raw, hashed)` → 同样流程后比对

### 4.3 认证中间件 [common.py:37](../backend/app/middlewares/common.py#L37)

```
请求 → HTTPBearer 提取 Token → jwt_auth_middleware 校验
  → 失败：401 "请提供 access token" / "access token 无效或已过期"
  → 成功：注入 request.state.current_user_public_id
```

### 4.4 API 端点汇总 [user.py](../backend/app/routers/user.py)

| 方法 | 路径 | 认证 | 功能 |
|------|------|------|------|
| POST | `/api/users/login` | 无 | 用户登录，返回 tokens + 用户信息 |
| POST | `/api/users/refresh-token` | 无 | 刷新 access token |
| GET | `/api/users/` | JWT | 用户列表 |
| GET | `/api/users/me` | JWT | 获取当前用户资料 |
| PUT | `/api/users/me/profile` | JWT | 更新个人资料（username/nickname/email） |
| PUT | `/api/users/me/password` | JWT | 修改密码（需旧密码验证） |
| PUT | `/api/users/me/avatar` | JWT | 更新头像 URL |
| POST | `/api/users/me/avatar/upload` | JWT | 上传头像文件 |
| GET | `/api/users/{public_id}` | JWT | 用户详情 |
| POST | `/api/users/` | JWT | 创建用户 |
| PUT | `/api/users/{public_id}` | JWT | 更新用户 |
| PATCH | `/api/users/{public_id}/disable` | JWT | 禁用用户 |
| DELETE | `/api/users/{public_id}` | JWT | 删除用户 |

---

## 五、用户信息管理

### 5.1 服务层核心函数 [user.py](../backend/app/services/user.py)

| 函数 | 行号 | 功能 |
|------|------|------|
| `get_user_by_username` | 48 | 按用户名查询 |
| `get_user_by_email` | 55 | 按邮箱查询 |
| `get_user_by_public_id` | 62 | 按公开 ID 查询 |
| `get_user_or_raise` | 69 | 按 ID 查询，不存在抛异常 |
| `ensure_unique_username` | 77 | 用户名唯一性校验 |
| `ensure_unique_email` | 91 | 邮箱唯一性校验 |
| `create_user` | 115 | 创建用户（含唯一性检查） |
| `update_user` | 139 | 更新用户（管理员） |
| `disable_user` | 170 | 软删除用户 |
| `delete_user` | 181 | 硬删除用户 |
| `get_current_user` | 188 | 获取当前登录用户 |
| `update_current_user_profile` | 193 | 当前用户更新资料 |
| `update_current_user_password` | 218 | 当前用户修改密码 |
| `update_current_user_avatar` | 236 | 当前用户更新头像 URL |
| `upload_current_user_avatar` | 256 | 上传并处理头像文件 |
| `ensure_default_admin` | 310 | 启动时确保管理员存在 |

### 5.2 头像上传流程 [user.py:256-307](../backend/app/services/user.py#L256)

```
客户端上传文件 → 校验格式(PNG/JPEG/JPG) → 校验大小(≤5MB)
  → PIL 打开图片 → 居中裁剪为 1:1 正方形 → LANCZOS 缩放到 256×256
  → RGBA 转 RGB（白底）→ 保存为 JPEG(q=88) 到 data/oss/avatars/{public_id}_{timestamp}.jpg
  → 更新用户 avatar_url
```

### 5.3 默认管理员引导 [user.py:310-338](../backend/app/services/user.py#L310)

应用启动时调用 `ensure_default_admin()`：
- 若已有超级管理员 → 跳过
- 若存在同名普通用户 → 提升为管理员
- 否则 → 从 `.env` 配置读取用户名密码创建默认管理员

### 5.4 前端设置面板 [Settings.vue](../frontend/src/components/Settings.vue)

三合一设置面板：
- **个人资料**：编辑 username / nickname / email
- **头像管理**：上传 + 拖拽裁剪 + Canvas 渲染
- **密码修改**：旧密码 + 新密码 + 确认，含强度指示器
- **注销**：清除 localStorage，跳转 `/login`

---

## 六、前端认证机制

### 6.1 路由守卫 [routes/index.ts](../frontend/src/routes/index.ts)

```
未登录访问 /project → 重定向 /login
已登录访问 /login  → 重定向 /project
已登录访问 /       → 重定向 /project
```

### 6.2 Axios 拦截器 [request/index.ts](../frontend/src/request/index.ts)

**请求拦截器**：自动从 localStorage 读取 `access_token`，附加 `Authorization: Bearer {token}`

**响应拦截器**（Token 自动刷新）：
```
收到 401 → 判断 detail 包含 "access token"
  → 从 localStorage 读取 refresh_token
  → POST /api/users/refresh-token 获取新 access_token
  → 更新 localStorage → 重试原请求
  → 刷新失败 → 清除凭据 → 跳转 /login
```

**并发刷新去重**：多个请求同时 401 时，通过 `refreshTokenRequest` Promise 缓存，只发起一次刷新请求。

---

## 七、项目管理与成员协作

### 7.1 API 端点 [project.py](../backend/app/routers/project.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/projects/` | 列出可访问项目 |
| GET | `/api/projects/search/by-name?name=` | 按名称搜索 |
| GET | `/api/projects/search/by-member?member_public_id=` | 按成员搜索 |
| GET | `/api/projects/{public_id}` | 项目详情 |
| POST | `/api/projects/` | 创建项目（自动成为 owner） |
| PUT | `/api/projects/{public_id}` | 更新项目 |
| PATCH | `/api/projects/{public_id}/disable` | 禁用 |
| DELETE | `/api/projects/{public_id}` | 删除（级联删除成员） |
| GET | `/api/projects/{public_id}/members` | 成员列表 |
| GET | `/api/projects/{public_id}/members/candidates?keyword=` | 搜索可邀请用户 |
| POST | `/api/projects/{public_id}/members/invitations` | 邀请成员 |
| POST | `/api/projects/{public_id}/members` | 添加成员 |
| PATCH | `/api/projects/{public_id}/members/{user_public_id}` | 更新角色 |
| DELETE | `/api/projects/{public_id}/members/{user_public_id}` | 移除成员 |

### 7.2 权限模型

- 超级管理员 → 可访问所有项目
- 普通用户 → 仅访问 `owner_id` 为自己的项目 + 作为 `ProjectMember` 的项目
- 通过 `_ensure_project_access()` 进行权限校验

### 7.3 前端项目页面 [Project.vue](../frontend/src/pages/Project.vue)

- **左侧导航**：项目、任务、文档、设置
- **项目卡片网格**：分页、搜索、刷新
- **创建/编辑对话框**：1080px 宽双栏布局，基础信息 + 风格选择器
- **成员管理对话框**：候选人搜索、邀请、角色修改、移除
- **视觉风格选择器**：实时加载，卡片网格展示，图片预览

---

## 八、文件系统级资源管理

### 8.1 视觉风格 [project.py:602-938](../backend/app/services/project.py)

- 存储路径：`data/skills/art_list/{style_path}/`
- 每个风格一个目录，含 `.md` 文件和 `images/` 子目录
- 元数据从 `README.md` 标题行（`# Name`）推断
- 仅超级管理员可创建/更新/删除
- 路径穿越防护：`_ensure_path_inside()` 严格校验

API 端点：`/api/projects/visual-styles`（GET/POST）、`/{style_path}`（GET/PUT/DELETE）、`/{style_path}/files`、`/{style_path}/images`

### 8.2 导演手册 [project.py:940-1174](../backend/app/services/project.py)

- 与视觉风格相同的架构
- 存储路径：`data/skills/director_manual/`
- API 端点：`/api/projects/director-manuals`

### 8.3 图片传输

- 写入：Base64 编码（支持 `data:image/...;base64,` 前缀）
- 读取：支持直接通过 API URL 引用

---

## 九、测试覆盖

| 文件 | 覆盖范围 |
|------|---------|
| [test_config.py](../backend/app/tests/test_config.py) | 配置加载 |
| [test_database.py](../backend/app/tests/test_database.py) | 数据库连接 |
| [test_health.py](../backend/app/tests/test_health.py) | 健康检查端点 |
| [test_user_model.py](../backend/app/tests/test_user_model.py) | 用户模型 |
| [test_user_router.py](../backend/app/tests/test_user_router.py) | 用户 API 端点 |
| [test_user_service.py](../backend/app/tests/test_user_service.py) | 用户服务层 |
| [test_project_router.py](../backend/app/tests/test_project_router.py) | 项目 API 端点 |
| [test_project_service.py](../backend/app/tests/test_project_service.py) | 项目服务层 |

测试框架：**pytest** + **anyio** + **httpx AsyncClient (ASGITransport)**

---

## 十、关键设计决策

1. **public_id 对外隔离**：所有实体内部使用 `id`(int) 自增主键，对外暴露 `public_id`(UUID 字符串)，防止遍历攻击
2. **软删除设计**：通过 `disabled_at` 字段实现，而非物理删除，保留数据可恢复性
3. **双令牌机制**：Access Token 短时效 + Refresh Token 长时效，兼顾安全性与用户体验
4. **Redis 辅助 JWT**：JWT 本身无状态，但通过 Redis 存储实现主动吊销能力（登出即失效）
5. **文件系统 > 数据库**：视觉风格和导演手册采用文件系统管理，而非存入数据库，便于人工编辑和版本管理
6. **BaseView 类视图**：自定义 `@route` 装饰器和类视图模式，统一路由注册和中间件绑定
7. **前后端分离**：Vue SPA + FastAPI RESTful，通过 Axios 拦截器统一处理认证和刷新
