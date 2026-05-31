# 用户系统参考范本

> 来源项目：`e:\projects\case_one` | 分支：`feature/visual-style` | 提取日期：2026-05-23
>
> 适用范围：需要用户注册、登录认证、个人资料管理的单用户/非多人协作项目。可直接以此为蓝本裁剪或照搬。

---

## 一、技术栈（仅用户系统相关）

| 层级 | 组件 | 说明 |
|------|------|------|
| 后端框架 | FastAPI (Python 3.x) | 异步 HTTP，Starlette + Pydantic |
| ORM | SQLModel | SQLAlchemy + Pydantic 融合，模型即 Schema |
| 数据库 | PostgreSQL / SQLite | 异步驱动 asyncpg / aiosqlite |
| 迁移 | Alembic | 自动生成 DDL 迁移 |
| 缓存 | Redis | 存储 Token，实现主动吊销 |
| 密码 | bcrypt + SHA-256 | 两级哈希 |
| 认证 | JWT (HS256) | Access + Refresh 双令牌 |
| 图片 | Pillow | 头像裁剪缩放 |
| 前端 | Vue 3 + Vite + TS | Composition API |
| UI | Element Plus 2 | 组件库 |
| HTTP | Axios 1 | 拦截器自动刷新 Token |
| 路由 | Vue Router 5 | 导航守卫 |

---

## 二、后端目录结构（用户系统核心文件）

```
backend/
├── app/
│   ├── main.py                   # 应用入口：注册中间件、路由、启动事件
│   ├── core/
│   │   ├── config.py             # Settings dataclass，从 .env 读取全部配置
│   │   └── database.py           # 异步引擎 + 会话工厂 + Redis 客户端
│   ├── middlewares/
│   │   └── common.py             # JWT 认证中间件、请求耗时中间件
│   ├── models/
│   │   ├── base.py               # ★ BaseModel 基类（public_id、时间戳、软删除）
│   │   └── user.py               # User 模型
│   ├── routers/
│   │   ├── base.py               # ★ BaseView 类视图 + @route 装饰器
│   │   ├── api.py                # 根路由聚合 + /api/health
│   │   └── user.py               # 用户端点
│   ├── schemas/
│   │   └── user.py               # 请求/响应 DTO
│   ├── services/
│   │   └── user.py               # 业务逻辑层
│   ├── utils/
│   │   ├── jwt_tools.py          # JWT 创建/解码/刷新/吊销
│   │   ├── string_tools.py       # 密码哈希 + 数据库 URL 构建
│   │   └── time_tools.py         # utc_now()
│   └── tests/
│       ├── base.py               # 测试基类
│       ├── test_user_model.py
│       ├── test_user_service.py
│       └── test_user_router.py
└── run.py                        # uvicorn 启动
```

---

## 三、核心设计模式

### 3.1 BaseModel 基类 —— 所有表的公共字段

**文件**：[backend/app/models/base.py](../backend/app/models/base.py)

```python
class BaseModel(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    public_id: str = Field(default_factory=lambda: str(uuid4()), max_length=36, unique=True, index=True)
    sort_order: int = Field(default=0, index=True)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True),
                                  sa_column_kwargs={"onupdate": utc_now})
    disabled_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), index=True)

    @property
    def is_disabled(self) -> bool:
        return self.disabled_at is not None

    async def disable(self) -> None:
        self.disabled_at = utc_now()

    async def enable(self) -> None:
        self.disabled_at = None
```

**设计要点**：
- `id` 内部自增，`public_id`（UUID）对外暴露，防止遍历
- `disabled_at` 实现软删除，不物理删除数据
- `created_at` / `updated_at` 自动维护，`updated_at` 通过 `onupdate` 自动刷新

### 3.2 BaseView 路由模式 —— 统一端点注册

**文件**：[backend/app/routers/base.py](../backend/app/routers/base.py)

通过 `BaseView` 类 + `@route` 装饰器统一管理路由和中间件依赖：

```python
class BaseView:
    def __init__(self, prefix: str, tags: list[str], dependencies: list | None = None):
        self.router = APIRouter(prefix=prefix, tags=tags, dependencies=dependencies or [])

def route(view: BaseView, path: str, method: str, **kwargs):
    """装饰器：将函数注册到 view.router 上"""
```

用法示例：`@route(user_view, "/login", "POST", response_model=UserLoginResponse)`

### 3.3 分层架构 —— Router → Service → Model

```
Router (HTTP 层) → 解析请求、调用 Service、返回响应
Service (业务层) → 业务逻辑、数据校验、数据库操作
Model (数据层)   → 表定义、字段约束
Schema (DTO 层)  → 请求参数校验、响应结构定义
```

**Router 不直接操作数据库**，全部通过 Service 函数完成。Router 只做三件事：提取参数、调用 Service、构造响应。

---

## 四、用户数据模型

**文件**：[backend/app/models/user.py](../backend/app/models/user.py)

表名 `af_user`，继承 `BaseModel`：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `username` | `str(64)` | UNIQUE, INDEX | 登录用户名 |
| `nickname` | `str(64)` \| None | | 展示昵称 |
| `email` | `str(255)` \| None | UNIQUE, INDEX | 邮箱 |
| `avatar_url` | `str(512)` \| None | | 头像地址 |
| `password_hash` | `str(255)` | NOT NULL | bcrypt+sha256 |
| `is_superuser` | `bool` | 默认 False | 管理员标记 |
| `last_login_at` | `datetime(tz)` \| None | | 最近登录 |

```python
class User(BaseModel, table=True):
    __tablename__ = "af_user"

    username: str = Field(sa_column=Column(String(64), unique=True, nullable=False, index=True))
    nickname: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))
    email: str | None = Field(default=None, sa_column=Column(String(255), unique=True, nullable=True, index=True))
    avatar_url: str | None = Field(default=None, sa_column=Column(String(512), nullable=True))
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    is_superuser: bool = Field(default=False)
    last_login_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    async def update_last_login(self) -> None:
        self.last_login_at = utc_now()
```

---

## 五、认证系统

### 5.1 密码加密

**文件**：[backend/app/utils/string_tools.py](../backend/app/utils/string_tools.py)

```
原始密码 → SHA-256 → bcrypt 加盐 → 存入 password_hash
```

```python
def hash_password(raw: str) -> str:
    return bcrypt.hashpw(sha256(raw).hexdigest().encode(), bcrypt.gensalt()).decode()

def verify_password(raw: str, hashed: str) -> bool:
    return bcrypt.checkpw(sha256(raw).hexdigest().encode(), hashed.encode())
```

### 5.2 JWT 令牌系统

**文件**：[backend/app/utils/jwt_tools.py](../backend/app/utils/jwt_tools.py)

**双令牌设计**：

| 令牌 | 默认有效期 | 用途 |
|------|-----------|------|
| Access Token | 9000s (2.5h) | 业务请求鉴权 |
| Refresh Token | 604800s (7d) | 无感刷新 Access Token |

**JWT Payload 结构**：
```json
{
  "sub": "用户 public_id",
  "username": "登录用户名",
  "type": "access | refresh",
  "jti": "UUID 唯一标识",
  "iat": 1700000000,
  "exp": 1700009000
}
```

**四个核心函数**：

| 函数 | 作用 | 行号 |
|------|------|------|
| `_create_token()` | 生成单个 JWT，同时写入 Redis | 55 |
| `create_login_tokens()` | 登录时生成 access + refresh 两个令牌 | 85 |
| `decode_token()` | 解析 JWT 并检查 Redis 中是否被吊销 | 115 |
| `create_access_token_from_refresh_token()` | 用 refresh token 换取新 access token | 135 |
| `revoke_token()` | 从 Redis 删除，实现登出 | 165 |

**Redis 存储格式**：`{prefix}{jti}` → `{"public_id":"...", "token_type":"access", "expires_at":1700009000}`，TTL 等于 JWT 过期时间。

**关键设计**：JWT 本身是无状态的，但通过在 Redis 中存储 jti，实现了**主动吊销**能力——登出时从 Redis 删除对应 key，即使 JWT 未过期也会被 `decode_token()` 拒绝。

### 5.3 认证中间件

**文件**：[backend/app/middlewares/common.py](../backend/app/middlewares/common.py)

```python
async def jwt_auth_middleware(request: Request, credentials: HTTPAuthorizationCredentials | None) -> None:
    # 1. 提取 Bearer token，缺失 → 401
    # 2. decode_token() 校验签名 + Redis 存在性
    # 3. 验证 type == "access"
    # 4. 通过 → 注入 request.state.current_user_public_id
```

使用方式：

```python
# 需认证的端点
@route(user_view, "/me", "GET", dependencies=[Depends(jwt_auth_middleware)])
# 无需认证的端点
@route(user_view, "/login", "POST")  # 不加依赖
```

### 5.4 API 端点一览

**文件**：[backend/app/routers/user.py](../backend/app/routers/user.py)，前缀 `/api/users`

| 方法 | 路径 | 认证 | 功能 | 适用场景 |
|------|------|------|------|---------|
| POST | `/login` | 无 | 登录，返回 tokens | 所有项目 |
| POST | `/refresh-token` | 无 | 刷新 access token | 所有项目 |
| GET | `/me` | JWT | 当前用户资料 | 所有项目 |
| PUT | `/me/profile` | JWT | 修改个人资料 | 需要用户设置页 |
| PUT | `/me/password` | JWT | 修改密码 | 需要用户设置页 |
| POST | `/me/avatar/upload` | JWT | 上传头像 | 需要头像功能 |
| GET | `/` | JWT | 用户列表 | 需要管理功能 |
| POST | `/` | JWT | 创建用户 | 需要管理功能/开放注册 |
| GET | `/{public_id}` | JWT | 用户详情 | 需要用户信息展示 |
| PUT | `/{public_id}` | JWT | 更新用户 | 需要管理功能 |
| PATCH | `/{public_id}/disable` | JWT | 禁用用户 | 需要管理功能 |
| DELETE | `/{public_id}` | JWT | 删除用户 | 需要管理功能 |
| POST | `/register` | 无 | 注册用户(可扩展) | 开放注册的项目 |

### 5.5 登录流程（完整调用链）

```
POST /api/users/login { username, password }
  → Router: login()
    → Service: get_user_by_username() 查用户
    → Service: verify_password() 校验密码
    → Service: user.update_last_login()
    → jwt_tools: create_login_tokens() 生成双令牌
    → 返回 { access_token, refresh_token, expires_in, user }
```

---

## 六、用户信息服务层

**文件**：[backend/app/services/user.py](../backend/app/services/user.py)

### 6.1 函数职责对照

| 函数 | 类型 | 说明 |
|------|------|------|
| `get_user_by_username` | 查询 | 按用户名查单个用户 |
| `get_user_by_email` | 查询 | 按邮箱查单个用户 |
| `get_user_by_public_id` | 查询 | 按 public_id 查，返回 None |
| `get_user_or_raise` | 查询 | 按 public_id 查，不存在抛 `UserNotFoundError` |
| `ensure_unique_username` | 校验 | 用户名冲突抛 `UserNameConflictError` |
| `ensure_unique_email` | 校验 | 邮箱冲突抛 `UserEmailConflictError` |
| `create_user` | 命令 | 创建用户（含唯一性检查 + 密码哈希） |
| `update_user` | 命令 | 管理员更新任意用户 |
| `disable_user` | 命令 | 软删除（设 disabled_at） |
| `delete_user` | 命令 | 硬删除 |
| `get_current_user` | 查询 | 获取当前登录用户 |
| `update_current_user_profile` | 命令 | 当前用户更新自己的资料 |
| `update_current_user_password` | 命令 | 当前用户改密码（需验证旧密码） |
| `update_current_user_avatar` | 命令 | 更新头像 URL |
| `upload_current_user_avatar` | 命令 | 上传头像文件（PIL 处理） |
| `ensure_default_admin` | 启动引导 | 确保至少有一个管理员 |

### 6.2 异常体系

```python
class UserServiceError(Exception): ...        # 基础异常
class UserNotFoundError(UserServiceError): ... # 用户不存在
class UserNameConflictError(UserServiceError): ... # 用户名冲突
class UserEmailConflictError(UserServiceError): ... # 邮箱冲突
class UserPasswordMismatchError(UserServiceError): ... # 密码不匹配
class UserAvatarInvalidError(UserServiceError): ... # 头像不合法
```

### 6.3 头像上传流程

**文件**：[user.py:256-307](../backend/app/services/user.py#L256)

```
UploadFile → 校验 Content-Type (仅 PNG/JPEG/JPG)
          → 校验大小 (≤5MB)
          → PIL.Image.open() 打开
          → 取宽高最小值，居中裁剪为正方形
          → LANCZOS 缩放到 256×256
          → RGBA/LA 模式 → 白底 RGB 转换
          → JPEG q=88 保存到 data/oss/avatars/{public_id}_{timestamp}.jpg
          → 更新 user.avatar_url = "/oss/avatars/{filename}"
```

### 6.4 默认管理员引导

**文件**：[user.py:310-338](../backend/app/services/user.py#L310)

应用启动时自动调用（在 `main.py` 的 `lifespan` 中注册）：

```
启动 → 查是否有 is_superuser=True 的用户
  → 有 → 跳过
  → 没有 → 查是否有用户名为 .env 中配置的用户
    → 有 → 提升为管理员
    → 没有 → 用 .env 中的用户名密码新建管理员
```

---

## 七、前端认证机制

### 7.1 路由守卫

**文件**：[frontend/src/routes/index.ts](../frontend/src/routes/index.ts)

```typescript
router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (to.path !== '/login' && !token) return '/login'    // 未登录 → 登录页
  if (to.path === '/login' && token) return '/project'    // 已登录 → 主页
  if (to.path === '/' && token) return '/project'         // 根路径 → 主页
})
```

### 7.2 Axios 拦截器 —— 自动 Token 刷新

**文件**：[frontend/src/request/index.ts](../frontend/src/request/index.ts)

**请求拦截器**：
```
每个请求出发前 → 从 localStorage 读取 access_token → 附加 Authorization: Bearer {token}
```

**响应拦截器（Token 自动刷新）**：
```
收到 401 响应
  → 检查 detail 是否包含 "access token"
  → 是 → 取 refresh_token → POST /api/users/refresh-token
    → 成功 → 更新 localStorage 中的 access_token → 重试原请求
    → 失败 → 清除所有凭据 → 跳转 /login
  → 否 → 直接 reject
```

**并发刷新去重**：多个请求同时 401 时，通过模块级 `refreshTokenRequest` Promise 变量缓存，只发一次刷新请求，其余共享同一个 Promise 结果。

```typescript
let refreshTokenRequest: Promise<string> | null = null

const refreshAccessToken = (refreshToken: string) => {
  if (!refreshTokenRequest) {
    refreshTokenRequest = axios.post('/api/users/refresh-token', { refresh_token: refreshToken })
      .then(({ data }) => { ... return data.access_token })
      .finally(() => { refreshTokenRequest = null })
  }
  return refreshTokenRequest
}
```

### 7.3 前端页面结构

```
Login.vue         — 登录页（无鉴权）
Settings.vue      — 设置面板（个人资料 + 密码修改 + 头像上传裁剪 + 注销）
App.vue           — 根组件，仅含 <router-view>
```

### 7.4 前端的 Token 存储

所有凭据存在 `localStorage`：

| Key | 值 |
|-----|---|
| `access_token` | JWT access token |
| `refresh_token` | JWT refresh token |
| `token_type` | "bearer" |
| `expires_in` | access token 有效期 |
| `user` | 用户信息 JSON |

注销时调用 `clearAuthStorage()` 清除全部并跳转登录页。

---

## 八、配置项参考（.env）

用户系统相关的关键配置：

```ini
# 数据库
DB_DRIVER=postgresql+asyncpg      # 或 sqlite+aiosqlite
DB_USER=case_one
DB_PASSWORD=xxx
DB_HOST=localhost
DB_PORT=5432
DB_NAME=case_one

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_SECONDS=9000       # 2.5 小时
REFRESH_TOKEN_EXPIRE_SECONDS=604800    # 7 天

# 默认管理员（首次启动自动创建）
USER_DEFAULT_ADMIN_NAME=admin
USER_DEFAULT_ADMIN_PASSWORD=xxx
```

**文件**：[backend/app/core/config.py](../backend/app/core/config.py) — 所有配置通过 `Settings` dataclass 集中管理，从 `.env` 读取。

---

## 九、测试模式

**文件**：[backend/app/tests/](../backend/app/tests/)

### 9.1 测试基类

```python
class EnvTestBase:
    """提供异步 session、测试客户端等公共 fixture"""
```

### 9.2 用户相关测试文件

| 文件 | 覆盖 |
|------|------|
| `test_user_model.py` | User 模型字段、继承、方法 |
| `test_user_service.py` | 所有 Service 函数：CRUD、校验、密码、头像 |
| `test_user_router.py` | 所有 HTTP 端点：状态码、响应结构、鉴权 |

### 9.3 测试技术栈

- **pytest** — 测试框架
- **anyio** — 异步支持
- **httpx AsyncClient + ASGITransport** — FastAPI 内存测试客户端
- **SQLite** — 测试数据库（无需外部依赖）

---

## 十、迁移到新项目的裁剪指南

### 最小可用集（只需登录认证）

必须保留的文件：

```
backend/
├── app/core/config.py, database.py
├── app/models/base.py, user.py
├── app/schemas/user.py (精简到 UserCreate / UserLogin / UserRead / UserLoginResponse)
├── app/services/user.py (精简到 create_user / get_user_by_username / get_current_user)
├── app/utils/jwt_tools.py, string_tools.py, time_tools.py
├── app/middlewares/common.py
├── app/routers/base.py, user.py
└── app/main.py
```

可删除：
- `update_current_user_avatar` / `upload_current_user_avatar` — 如果不需要头像
- `update_current_user_password` — 如果不需要改密码
- `ensure_default_admin` — 如果用其他方式初始化管理员
- `disable_user` / `delete_user` — 如果不需要用户管理

### 标准集（登录 + 资料管理 + 头像）

在最小集基础上保留：
- 完整的 `services/user.py`
- 头像上传逻辑
- `Settings.vue` 前端组件

### 完整集（登录 + 资料 + 管理后台）

在标准集基础上保留：
- 用户 CRUD 全部端点
- 禁用/启用/删除功能

### 前端裁剪

| 需求 | 保留文件 |
|------|---------|
| 仅登录 | `Login.vue` + `request/index.ts` + `routes/index.ts` |
| 登录 + 用户中心 | 上述 + `Settings.vue` + `api/user.ts` |
| 不需要自动刷新 | 删除 `request/index.ts` 中的响应拦截器，仅保留请求拦截器 |

---

## 十一、核心设计决策总结

| 决策 | 说明 | 收益 |
|------|------|------|
| `public_id` (UUID) 对外 | 内部 `id` 自增，对外只用 UUID | 防遍历，隐藏用户量 |
| 软删除 (`disabled_at`) | 禁用不删行 | 数据可恢复，审计友好 |
| JWT + Redis 双存储 | JWT 无状态 + Redis 可吊销 | 兼顾性能和安全 |
| bcrypt + SHA-256 | 先 SHA-256 再 bcrypt | 防彩虹表 + 抗暴力 |
| Service 层独立 | Router 不直接操作 DB | 可测试、可复用 |
| 异常体系分层 | 自定义 `UserServiceError` 子类 | 精确错误处理 |
| 登录返回双令牌 | Access 短 + Refresh 长 | 安全与体验平衡 |
| Axios 拦截器自动刷新 | 401 → 刷 token → 重试 | 用户无感 |
| 启动引导管理员 | `ensure_default_admin()` | 新部署开箱即用 |
