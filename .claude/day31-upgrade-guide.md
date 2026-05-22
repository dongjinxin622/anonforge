# Day31 代码升级说明文档

> 本文档对比 `E:\AI智能体课程\AI agent\day31\code`（新版本）与 `e:\projects\case_one`（当前版本）的差异，详细解释每一项新增/变更功能及其技术要点。

---

## 一、总体概述

day31 版本在现有项目基础上做了以下核心升级：

| 升级方向 | 影响范围 | 代码增量 |
|----------|----------|----------|
| **视觉风格管理系统** | 后端 + 前端 | ~450 行（service 翻倍） |
| **Redis Token 管理增强** | 后端（JWT 工具） | 完善已有功能 |
| **项目成员邮箱展示** | 后端 Schema + 前端 API | 少量改动 |
| **Token 过期时间调整** | .env 配置 | 900 → 9000 秒 |
| **导演手册/视觉风格根目录** | 配置文件 | 2 个新配置项 |
| **启动方式简化** | run.py | 简化 Windows 兼容逻辑 |

---

## 二、新增功能详解

### 2.1 视觉风格管理系统（核心新增）

这是 day31 最重大的新增功能，一套完整的**文件系统级视觉风格管理**能力。

#### 2.1.1 功能概述

允许超级管理员在服务端文件系统中管理"视觉风格"目录，每个风格包含 Markdown 说明文件和参考图片，前端可直接通过 URL 访问图片资源。

#### 2.1.2 新增的后端 Schema

文件：[schemas/project.py](E:\AI智能体课程\AI agent\day31\code\code\backend\app\schemas\project.py)

```python
# 新增 7 个 Schema 类：
VisualStyleFileRead    # Markdown 文件读取结果（path + content + size_bytes）
VisualStyleFileWrite   # Markdown 文件写入请求（path + content，校验 .md 后缀）
VisualStyleImageRead   # 图片读取结果（filename + path + url + size_bytes）
VisualStyleImageWrite  # 图片写入请求（filename + base64 data）
VisualStyleRead        # 风格完整读取（style_path + name + files + images）
VisualStyleCreate      # 创建请求（style_path + name + files + images）
VisualStyleUpdate      # 更新请求（name + files + images + replace_images）
```

**技术要点**：
- `VisualStyleFileWrite.path` 使用 Pydantic `field_validator` 校验 `.md` 后缀，防止非法文件写入
- `VisualStyleImageWrite.data` 接收 base64 编码的图片数据，支持 data URI 前缀
- `VisualStyleUpdate.replace_images` 布尔标记控制是否先清空图片目录再写入，避免残留旧图片

#### 2.1.3 新增的后端 Service 层

文件：[services/project.py](E:\AI智能体课程\AI agent\day31\code\code\backend\app\services\project.py)

新增约 **450 行代码**，包含以下核心函数：

| 函数 | 功能 | 关键技术点 |
|------|------|-----------|
| `list_visual_styles()` | 列出所有视觉风格目录 | `Path.iterdir()` 遍历文件系统 |
| `create_visual_style()` | 创建风格目录及文件/图片 | 目录名正则校验 `STYLE_PATH_PATTERN`，防止路径遍历攻击 |
| `get_visual_style()` | 读取单个风格详情 | 读取 README.md 获取展示名称 |
| `update_visual_style()` | 更新风格文件和图片 | 可选清空图片目录 (`replace_images`) |
| `delete_visual_style()` | 删除整个风格目录 | `shutil.rmtree()` 递归删除 |
| `read_visual_style_file()` | 读取 Markdown 文件 | 路径穿越校验 |
| `write_visual_style_file()` | 写入/覆盖 Markdown 文件 | 文件存在则覆盖，不存在则创建 |
| `delete_visual_style_file()` | 删除 Markdown 文件 | 单文件删除 |
| `get_visual_style_image_path()` | 获取图片的物理路径 | 用于 `FileResponse` 直接返回图片 |
| `write_visual_style_image()` | 写入图片（base64 解码） | `base64.b64decode()` 处理，支持 data URI 前缀自动剥离 |
| `delete_visual_style_image()` | 删除图片 | 单图片文件删除 |

**关键技术要点详解**：

1. **路径安全防护**
   ```python
   STYLE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,119}$")
   ```
   风格目录名必须匹配正则，限制只允许字母数字和 `_-`，防止**目录遍历攻击**（如 `../../etc/passwd`）。

2. **Base64 图片处理**
   ```python
   # 支持两种格式：纯 base64 或 data URI
   if "," in raw:
       raw = raw.split(",", 1)[1]
   image_bytes = base64.b64decode(raw)
   ```

3. **图片 URL 生成**
   ```python
   url = f"/api/projects/visual-styles/{style_path}/images/{filename}"
   ```
   图片通过 FastAPI 端点直接提供，前端可以通过 `FileResponse` 获取，支持 CSS `url()` 引用。

4. **图片扩展名校验**
   ```python
   IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
   ```
   只允许常见图片格式，防止非图片文件被当作图片处理。

#### 2.1.4 新增的 REST API 端点

文件：[routers/project.py](E:\AI智能体课程\AI agent\day31\code\code\backend\app\routers\project.py)

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/projects/visual-styles` | 获取所有视觉风格列表 |
| POST | `/projects/visual-styles` | 创建视觉风格 |
| GET | `/projects/visual-styles/{style_path}` | 获取单个风格详情 |
| PUT | `/projects/visual-styles/{style_path}` | 更新视觉风格 |
| DELETE | `/projects/visual-styles/{style_path}` | 删除视觉风格 |
| GET | `/projects/visual-styles/{style_path}/files/{file_path}` | 读取 Markdown 文件 |
| PUT | `/projects/visual-styles/{style_path}/files/{file_path}` | 写入 Markdown 文件 |
| DELETE | `/projects/visual-styles/{style_path}/files/{file_path}` | 删除 Markdown 文件 |
| GET | `/projects/visual-styles/{style_path}/images/{filename}` | 读取图片（无需 JWT 认证） |
| PUT | `/projects/visual-styles/{style_path}/images/{filename}` | 写入图片 |
| DELETE | `/projects/visual-styles/{style_path}/images/{filename}` | 删除图片 |

**注意**：图片读取端点 **不需要 JWT 中间件**，因为 `FileResponse` 不能携带自定义响应头，且图片 URL 需要被 CSS/HTML 直接引用。

#### 2.1.5 前端新增

文件：[api/project.ts](E:\AI智能体课程\AI agent\day31\code\code\frontend\src\api\project.ts)

```typescript
// 新增接口
export interface VisualStyleFileRecord {
  path: string
  content: string
  size_bytes: number
}

export interface VisualStyleImageRecord {
  filename: string
  path: string
  url: string           // 可直接用于 img src 的 URL
  size_bytes: number
}

export interface VisualStyleRecord {
  style_path: string
  name: string
  files: VisualStyleFileRecord[]
  images: VisualStyleImageRecord[]
}

// 新增 API 函数
export const listVisualStylesApi = () =>
  request.get<VisualStyleRecord[]>('/projects/visual-styles')
```

---

### 2.2 项目成员邮箱展示

#### 变更点

- [schemas/project.py](E:\AI智能体课程\AI agent\day31\code\code\backend\app\schemas\project.py): `ProjectMemberRead` 新增 `user_email: str | None` 字段
- [api/project.ts](E:\AI智能体课程\AI agent\day31\code\code\frontend\src\api\project.ts): `ProjectMemberRecord` 新增 `user_email: string | null` 字段

#### 技术要点

在 service 层查询 `ProjectMember` 时，通过 JOIN `User` 表获取 `email` 字段，填充到响应中。这样前端在展示成员列表时可以直接显示成员邮箱，无需额外请求。

---

### 2.3 Redis Token 管理

#### 2.3.1 架构说明

day31 的 JWT 工具使用 **Redis 作为 Token 缓存层**，实现了以下能力：

```
登录 → 创建 JWT → 缓存到 Redis（key: auth:token:{jti}）
请求 → 解析 JWT → 检查 Redis 中是否存在 → 存在则放行
登出 → 删除 Redis 中的 token → 后续请求被拒绝
```

#### 2.3.2 关键函数

文件：[utils/jwt_tools.py](E:\AI智能体课程\AI agent\day31\code\code\backend\app\utils\jwt_tools.py)

| 函数 | 作用 | 技术要点 |
|------|------|---------|
| `cache_token()` | 登录时将 token 写入 Redis | TTL 设置为 token 过期时间，自动过期清理 |
| `decode_token()` | 解析 JWT 并校验 Redis 状态 | 如果 Redis 中不存在，视为已吊销 |
| `revoke_token()` | 登出时从 Redis 删除 | 实现即时登出 |
| `create_access_token_from_refresh_token()` | 用 refresh token 换新 access token | 校验 refresh token 类型 |

#### 2.3.3 技术要点

1. **JWT + Redis 双校验模式**：JWT 本身有签名和过期时间，Redis 额外提供吊销能力。单独 JWT 无法实现"即时登出"（因为已签发的 token 在过期前始终有效），引入 Redis 后可以通过删除缓存键实现即时吊销。

2. **jti（JWT ID）机制**：每个 token 签发时生成唯一 `jti`（`uuid4().hex`），Redis 键格式为 `auth:token:{jti}`。解码时先验证 JWT 签名，再检查 Redis 中 jti 是否存在。

3. **TTL 自动过期**：Redis 键的过期时间与 JWT 过期时间一致（`ex=ttl_seconds`），过期后自动删除，无需手动清理。

4. **Redis 客户端初始化**：在 [database.py](E:\AI智能体课程\AI agent\day31\code\code\backend\app\core\database.py) 中创建全局 `redis_client`：
   ```python
   redis_client = Redis(
       host=settings.redis_host,
       port=settings.redis_port,
       db=settings.redis_db,
       decode_responses=True,
   )
   ```

---

### 2.4 配置变更

#### 2.4.1 .env 文件

| 配置项 | case_one | day31 | 说明 |
|--------|----------|-------|------|
| `ACCESS_TOKEN_EXPIRE_SECONDS` | 900 | **9000** | Token 有效期从 15 分钟延长到 2.5 小时 |
| `VISUAL_STYLE_ROOT` | 无 | `./data/skills/art_list` | 视觉风格文件根目录 |
| `DIRECTOR_MANUAL_ROOT` | 无 | `./data/skills/director_manual` | 导演手册文件根目录 |

#### 2.4.2 config.py

day31 在 `Settings` 类中新增两个配置字段：

```python
visual_style_root: str = field(default_factory=lambda: os.getenv(
    "VISUAL_STYLE_ROOT", "./data/skills/art_list"))
director_manual_root: str = field(default_factory=lambda: os.getenv(
    "DIRECTOR_MANUAL_ROOT", "./data/skills/director_manual"))
```

---

### 2.5 启动方式变更

#### case_one 版本（显式 SelectorEventLoop）

```python
if sys.platform == "win32":
    loop = asyncio.SelectorEventLoop()
    config = uvicorn.Config("app.main:app", host=settings.host,
                            port=settings.port, loop="asyncio")
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())
else:
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)
```

#### day31 版本（统一 uvicorn.run）

```python
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn
uvicorn.run("app.main:app", host=settings.host, port=settings.port)
```

**技术要点**：
- case_one 使用 `uvicorn.Server` 直接管理事件循环，更底层但也更复杂
- day31 使用 `asyncio.set_event_loop_policy()` 设置 Selector 事件循环策略，然后直接调用 `uvicorn.run()`，更简洁
- 两种方式在功能上等价，day31 的方式是 uvicorn 官方推荐的 Windows 兼容写法

---

## 三、技术要点深度分析

### 3.1 文件系统作为"数据库"的设计模式

视觉风格管理没有使用数据库存储，而是直接操作文件系统。这种设计适用于：

- **内容本身是文件**（Markdown 文档 + 图片）
- **需要直接被前端 URL 访问**（图片通过 `FileResponse` 返回）
- **结构简单**（目录 + 文件，无需复杂查询）

**优缺点**：
- 优点：简单直接，无需额外的数据库表和迁移，适合内容管理类需求
- 缺点：无事务支持，并发写入需自行处理，无版本历史

### 3.2 路径安全防护

风格目录名使用正则 `^[A-Za-z0-9][A-Za-z0-9_-]{0,119}$` 校验，这是防止**路径遍历攻击**的关键措施。

```python
# 攻击者尝试：style_path = "../../etc/passwd"
# 正则校验会拒绝这种输入
STYLE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,119}$")
```

### 3.3 Token 吊销机制的实现原理

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  客户端   │     │  FastAPI │     │  Redis   │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     │  POST /login   │                │
     ├───────────────>│                │
     │                │  SET token:abc │
     │                ├───────────────>│
     │  返回 JWT      │                │
     │<───────────────┤                │
     │                │                │
     │  GET /projects │                │
     │  (Bearer JWT)  │                │
     ├───────────────>│                │
     │                │  GET token:abc │
     │                ├───────────────>│
     │                │  返回 OK       │
     │                │<───────────────┤
     │  200 OK        │                │
     │<───────────────┤                │
     │                │                │
     │  POST /logout  │                │
     ├───────────────>│                │
     │                │  DEL token:abc │
     │                ├───────────────>│
     │  204 No Content│                │
     │<───────────────┤                │
     │                │                │
     │  GET /projects │                │
     │  (同一 JWT)     │                │
     ├───────────────>│                │
     │                │  GET token:abc │
     │                ├───────────────>│
     │                │  返回 nil      │
     │                │<───────────────┤
     │  401 已吊销    │                │
     │<───────────────┤                │
```

### 3.4 Base64 图片上传的处理

```python
def _decode_image_data(raw: str) -> bytes:
    # 支持 "data:image/png;base64,iVBORw0KGgo..." 格式
    if "," in raw:
        raw = raw.split(",", 1)[1]
    return base64.b64decode(raw)
```

这允许前端将图片编码为 base64 字符串后直接通过 JSON 传输，无需使用 multipart/form-data。

---

## 四、文件级差异对比

### 4.1 无变化文件（二进制相同或仅有格式差异）

| 文件 | 状态 |
|------|------|
| `docker/docker-compose.yaml` | 完全相同 |
| `frontend/src/App.vue` | 完全相同 |
| `frontend/src/main.ts` | 完全相同 |
| `frontend/src/pages/Login.vue` | 完全相同 |
| `frontend/src/api/user.ts` | 完全相同 |
| `frontend/src/request/index.ts` | 基本相同（day31 多一行注释） |
| `frontend/src/routes/index.ts` | 基本相同 |
| `backend/app/models/base.py` | 完全相同 |
| `backend/app/models/user.py` | 完全相同 |
| `backend/app/models/project.py` | 完全相同 |
| `backend/app/middlewares/common.py` | 完全相同 |
| `backend/app/routers/api.py` | 基本相同（路由注册顺序不同） |
| `backend/app/routers/base.py` | 完全相同 |
| `backend/app/schemas/user.py` | 完全相同 |
| `backend/app/utils/jwt_tools.py` | 完全相同 |
| `backend/app/utils/string_tools.py` | 略有格式差异 |
| `backend/app/utils/time_tools.py` | 完全相同 |
| `backend/requirements.txt` | 基本相同 |

### 4.2 有实质性变更的文件

| 文件 | 变更内容 | 影响程度 |
|------|---------|---------|
| `.env` | `ACCESS_TOKEN_EXPIRE_SECONDS: 900→9000`；新增 `VISUAL_STYLE_ROOT`、`DIRECTOR_MANUAL_ROOT` | 中 |
| `backend/app/core/config.py` | 新增 `visual_style_root`、`director_manual_root` 字段 | 中 |
| `backend/app/core/database.py` | 导入顺序调整（无功能影响） | 低 |
| `backend/app/main.py` | 简化代码（删除 error handler、调整 lifespan 注释） | 低 |
| `backend/app/routers/project.py` | **新增 10 个视觉风格 REST 端点** | **高** |
| `backend/app/routers/user.py` | 注释更详细，功能不变 | 低 |
| `backend/app/schemas/project.py` | 新增 7 个视觉风格 Schema；`ProjectMemberRead` 新增 `user_email` | **高** |
| `backend/app/services/project.py` | **新增 ~450 行视觉风格管理函数**（行数从 478 → 927） | **高** |
| `backend/run.py` | Windows 启动方式简化 | 中 |
| `frontend/src/api/project.ts` | 新增 3 个视觉风格接口 + `listVisualStylesApi`；`ProjectMemberRecord` 新增 `user_email` | 中 |
| `frontend/src/pages/Project.vue` | 可能存在视觉风格相关 UI 变更 | 中 |
| `frontend/vite.config.ts` | 可能存在代理配置变更 | 低 |
| `frontend/tsconfig.app.json` | 可能新增编译选项 | 低 |

### 4.3 测试差异

| 文件 | case_one | day31 |
|------|----------|-------|
| `test_config.py` | 包含 `REDIS_PORT`/`REDIS_DB` 测试断言 | 无 Redis 测试 |
| `test_project_router.py` | **存在** | 不存在 |
| `test_project_service.py` | CRUD + 权限 + 成员管理 完整测试 | 视觉风格路由测试 |
| `test_user_router.py` | 简化版（含 JWT 认证） | 含登录成功/失败/禁用用户测试 |
| `test_user_service.py` | 基本相同 | 基本相同 |
| `test_user_model.py` | 基本相同 | 基本相同 |

---

## 五、总结

day31 版本的升级围绕**视频制作平台的功能扩展**展开：

1. **视觉风格管理**是最大的新增功能（约 450 行新代码），实现了文件系统级别的风格 CRUD
2. **Redis Token 管理**在现有基础上提供了即时的 token 吊销能力
3. **成员邮箱展示**改善了协作体验
4. **Token 过期时间延长**（15分钟 → 2.5小时）改善了用户体验
5. **启动方式简化**减少了 Windows 兼容代码的复杂度

整体代码量：services/project.py 从 478 行增长到 927 行（+94%），schemas/project.py 从 67 行增加到约 130+ 行，前端 api/project.ts 增加了 4 个接口和 3 个类型定义。