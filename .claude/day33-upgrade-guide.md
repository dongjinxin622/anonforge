# Day33 升级报告：大模型服务 Provider 适配器系统

## 一、新增内容概览

本次升级引入了一套完整的 **大模型服务 Provider 适配器管理系统**，允许用户通过文件系统级 CRUD 管理多个 AI 厂商的服务配置、模型列表和代码适配器。这是从"单一项目管理系统"到"AI 多模型调度平台"的关键架构扩展。

### 新增文件清单

| 层级 | 文件路径 | 用途 |
|------|---------|------|
| 核心基类 | `backend/app/core/base_provider.py` | Provider 适配器抽象基类，定义统一接口 |
| 配置管理 | `backend/app/services/provider.py` | Provider 配置文件 CRUD、AST 解析、原子写入、加密保护 |
| 运行时调度 | `backend/app/services/provider_runtime.py` | 运行时动态加载、创建实例、统一调度 |
| 数据模型 | `backend/app/schemas/provider.py` | Pydantic Schema 定义（ProviderConfig、ProviderModel 等） |
| API 路由 | `backend/app/routers/provider.py` | RESTful API 接口（10个端点） |
| 密钥工具 | `backend/app/utils/secret_tools.py` | HMAC-SHA256 可逆加解密，保护 API Key |
| 厂商适配器 | `backend/app/providers/klingai.py` | KlingAI（快手可灵）视频生成适配器 |
| 厂商适配器 | `backend/app/providers/moluo.py` | 墨落中转站 OpenAI 兼容适配器 |
| 厂商适配器 | `backend/app/providers/qwen.py` | 通义千问适配器 |
| 厂商适配器 | `backend/app/providers/volcengine.py` | 火山引擎 Ark 适配器 |
| 模板 | `data/provider_template.py` | 自定义服务脚手架模板 |
| 文档示例 | `docs/demo/provider_adapter_demo.py` | 适配器架构演示代码 |
| 前端 API | `frontend/src/api/modelProvider.ts` | 前端 Provider API 类型定义与调用 |
| 前端组件 | `frontend/src/components/ProviderCodeWebEditor.vue` | CodeMirror Python 代码编辑器组件 |

### 修改的既有文件

| 文件 | 变化 |
|------|------|
| `backend/app/routers/api.py` | 新增 `provider_router` 注册 |
| `backend/app/core/config.py` | 新增 `provider_template_path` 配置项 |
| `backend/app/core/database.py` | 移除 Redis 导入（改为在其他位置导入） |
| `backend/app/main.py` | 新增 OSS 静态资源挂载 `/oss`；重构 lifespan 函数 |

---

## 二、架构设计分析

### 2.1 整体架构图

```
┌──────────────────────────────────────────────────────────────┐
│                     前端 (Vue 3 + Element Plus)              │
│  ┌────────────────────┐  ┌─────────────────────────────────┐│
│  │ modelProvider.ts   │  │ ProviderCodeWebEditor.vue       ││
│  │ (API 类型+调用)    │  │ (CodeMirror Python 编辑器)      ││
│  └────────────────────┘  └─────────────────────────────────┘│
└───────────────────────────────┬──────────────────────────────┘
                                │ HTTP REST API
┌───────────────────────────────┴──────────────────────────────┐
│                     后端 (FastAPI)                            │
│                                                               │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────────┐│
│  │ Router       │  │ Service          │  │ Runtime         ││
│  │ provider.py  │→ │ provider.py      │  │ provider_       ││
│  │ (10端点)     │  │ (文件级CRUD)     │  │ runtime.py      ││
│  └──────────────┘  └──────────────────┘  │ (动态加载调度)  ││
│                     ┌──────────────────┐  └─────────────────┘│
│                     │ Schema           │                      │
│                     │ provider.py      │                      │
│                     │ (Pydantic模型)   │                      │
│                     └──────────────────┘                      │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ BaseProvider (ABC)                                       ││
│  │  └─ Text  ── generate_text()                            ││
│  │  └─ Image ── generate_image()                           ││
│  │  └─ Video ── generate_video()                           ││
│  │  └─ TTS   ── generate_tts()                             ││
│  └────────────┬──────────────┬──────────────┬───────────────┘│
│               │              │              │                  │
│  ┌────────────┴──┐ ┌────────┴──────┐ ┌─────┴──────────┐     │
│  │ klingai.py    │ │ moluo.py      │ │ volcengine.py  │     │
│  │ qwen.py       │ │ (自定义...)   │ │                 │     │
│  └───────────────┘ └───────────────┘ └─────────────────┘     │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ app/providers/  (文件系统级配置存储)                      ││
│  │  每个 .py = 一个厂商服务，内含 PROVIDER_CONFIG 字面量     ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计模式

**1. 文件系统级配置存储（零数据库依赖）**

Provider 配置不存储在数据库中，而是以 Python 源文件形式存放在 `app/providers/` 目录。每个厂商对应一个 `.py` 文件，其中以 `PROVIDER_CONFIG = {...}` 字面量声明配置。这是核心创新点：

- 配置即代码：PROVIDER_CONFIG 是 Python 字面量字典，AST 解析读取、替换写入
- 无需额外数据库表：配置随代码一同版本管理
- 动态扩展：新增厂商只需新增一个 `.py` 文件

**2. AST 解析 + 原子写入的安全编辑机制**

`provider.py` 服务层不通过 `import` 导入模块读取配置，而是使用 `ast.literal_eval()` 直接解析源文件中的 `PROVIDER_CONFIG` 字面量。写入时：

- 使用 AST 定位 `PROVIDER_CONFIG` 节点的行范围
- 用 `pformat` 生成新配置的 Python 字面量替换
- 先编译验证语法合法性，再原子写入（临时文件 → rename）
- 写入前自动备份为 `.bak` 文件

**3. 适配器基类抽象（策略模式）**

`BaseProvider` 是抽象基类，定义四种能力类型：
- `Text` → `generate_text()`
- `Image` → `generate_image()`
- `Video` → `generate_video()`
- `TTS` → `generate_tts()`

每个厂商的 `.py` 文件可以包含多个适配器类（如 moluo.py 同时包含 Text/Image/Video/TTS），通过 `provider_key` + `model_type` 双键定位。

**4. 运行时动态加载**

`provider_runtime.py` 使用 `importlib.import_module` + `importlib.reload` 动态加载和热重载 Provider 模块，支持配置修改后无需重启服务即可生效。

**5. 密钥加密保护**

`secret_tools.py` 实现了基于 HMAC-SHA256 的可逆加密方案：
- 加密：随机 nonce + XOR 流密码 + HMAC tag → `enc:v1:` 前缀 Base64 编码
- 解密：验证 HMAC tag → XOR 流密码逆向还原
- 所有 password 类型输入值在返回客户端前自动加密，API Key 不会以明文暴露

---

## 三、关键技术要点

### 3.1 Provider 配置文件结构

每个 Provider 文件的核心是 `PROVIDER_CONFIG` 字面量字典，结构如下：

```python
PROVIDER_CONFIG = {
    "key": "moluo",              # 服务唯一标识（匹配文件名）
    "protocol": "openai",        # 协议类型（openai/qwen/volcengine等）
    "version": "2.0",            # 协议版本
    "name": "墨落中转站",         # 显示名称
    "description": "...",        # 描述
    "decs_url": "...",           # 文档链接
    "icon": "data:image/...",    # 图标（Base64 或 URL）
    "inputs": [...],             # 可编辑输入项（apiKey/baseUrl等）
    "input_values": {...},       # 输入值（password类型加密存储）
    "base_url": "...",           # API 请求基础地址
    "enabled": True,             # 是否启用
    "sort_order": 0,             # 排序权重
    "models": [...],             # 可用模型列表
    "url": "...",                # 服务主页地址
}
```

### 3.2 API 端点设计（10个）

| 方法 | 路径 | 用途 | 权限 |
|------|------|------|------|
| GET | `/providers/template` | 获取空白模板 | 需登录 |
| POST | `/providers/template` | 根据配置生成模板 | 需超级管理员 |
| GET | `/providers/` | 列出所有 Provider 配置 | 需登录 |
| POST | `/providers/` | 创建新 Provider 文件 | 需登录 |
| POST | `/providers/models/fetch` | 远端拉取模型列表 | 需登录 |
| GET | `/providers/{key}` | 获取配置+源码 | 需登录 |
| PUT | `/providers/{key}/config` | 更新配置（保留代码） | 需登录 |
| PUT | `/providers/{key}/inputs` | 只更新输入值 | 需登录 |
| PUT | `/providers/{key}/code` | 更新源码 | 需登录 |
| DELETE | `/providers/{key}` | 删除（备份后） | 需超级管理员 |

### 3.3 远端模型列表自动获取

`fetch_provider_models()` 可以用临时凭据调用厂商 `/models` 端点，自动发现可用模型：
- 支持 OpenAI 兼容协议的 `/v1/models` 格式
- 自动推断模型类型（text/image/video/tts）基于 model_id 关键词
- 解密加密的 API Key 用于请求
- 不写入配置文件，仅返回发现结果供用户选择

### 3.4 前端集成要点

- `modelProvider.ts`：完整的 TypeScript 类型定义和 API 调用函数，与后端 Schema 精确对齐
- `ProviderCodeWebEditor.vue`：基于 `vue-codemirror` + `@codemirror/lang-python` + `oneDark` 主题的在线 Python 代码编辑器，支持双向绑定 (`v-model`)
- 前端尚未创建独立的 Provider 管理页面（目前仅有 API 层和编辑器组件，缺少页面路由和视图）

### 3.5 OSS 静态资源挂载

`main.py` 新增了 `/oss` 静态资源挂载，将配置的 OSS 本地目录暴露为静态文件 URL，用于头像等用户上传文件的直接访问。

---

## 四、已包含的厂商适配器

| 厂商 | 文件 | 协议 | 模型能力 | 特点 |
|------|------|------|----------|------|
| 墨落中转站 | `moluo.py` | openai | Text/Image/Video/TTS | OpenAI 兼容中转站，包含 GPT-5.5/gpt-image-2 等 |
| 通义千问 | `qwen.py` | qwen | Text/Image | 阿里通义系列，含多种文本和图像模型 |
| 火山引擎 | `volcengine.py` | volcengine | Text/Image/Video/TTS | 豆包系列 + Seedance 视频，含大量历史版本模型 |
| KlingAI | `klingai.py` | klingai | Video | 快手可灵 AI 视频生成 |

---

## 五、架构评价与建议

### 优势

1. **零数据库依赖**：文件系统级存储避免了新的数据库表和迁移，配置随代码版本管理
2. **热重载能力**：运行时通过 `importlib.reload` 实现配置变更无需重启
3. **安全设计完善**：API Key 加密存储、路径安全校验（防逃逸）、原子写入
4. **扩展性极好**：新增厂商只需添加一个 `.py` 文件，无需修改核心代码
5. **AST 安全解析**：只使用 `literal_eval`，不执行任意代码

### 不足与待完善

1. **缺少前端页面**：API 层和编辑器组件就绪，但缺少 Provider 管理页面（列表/详情/创建表单）
2. **适配器实际调用未实现**：所有厂商的 `generate_*` 方法都抛出 `NotImplementedError`，仅声明了接口
3. **并发安全**：文件级操作使用 `threading.RLock`，但在异步 FastAPI 中可能不够充分（建议改为 asyncio Lock）
4. **测试覆盖不足**：新增模块缺少对应的单元测试文件
5. **密钥加密方案偏轻量**：HMAC-SHA256 + XOR 流密码是非标准加密方案，生产环境建议迁移到 Fernet 或 AES-GCM

---

## 六、对当前项目的影响

本次新增的 Provider 系统是完全独立的模块，不影响既有功能：

- 新增路由 `/providers/*` 不与现有 `/projects/*`、`/users/*` 冲突
- OSS 静态资源挂载是新增功能，不影响既有接口
- `config.py` 仅新增 `provider_template_path` 配置项
- 数据库无新表，无迁移影响