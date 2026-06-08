# Day36 升级报告：AI 驱动的章节事件提取系统

## 一、新增内容概览

本次升级在 Day35（小说爬虫系统）基础上，将 **章节事件清洗从"占位模板"升级为"AI 模型驱动"**，同时构建了支撑 AI 调用的 **模型网关** 和 **提示词技能注册表** 两大基础设施。核心变化：事件清洗终于接入了 Provider 系统。

### 新增文件清单

| 层级 | 文件路径 | 用途 |
|------|---------|------|
| 后端服务 | `backend/app/services/agent_gateway.py` | 模型网关 — 统一入口调用文本生成 |
| 后端服务 | `backend/app/services/prompt_registry.py` | 提示词技能注册表 — 文件系统加载 Markdown 提示词 |

### 扩展的既有文件

| 文件 | 变化内容 | 行数变化 |
|------|---------|---------|
| `backend/app/services/novel.py` | 新增 AI 事件提取、异步清洗队列、清洗进度追踪 | 945 → 1154 (+209) |
| `backend/app/routers/novel.py` | 新增清洗状态查询、异步清洗提交、旧路径兼容 | 622 → 694 (+72) |
| `backend/app/schemas/novel.py` | 新增 NovelChapterCleanStatus 等 Schema | 477 → 493 (+16) |
| `backend/app/core/config.py` | 新增提示词名称、模型超时配置 | +2 配置项 |
| `frontend/src/api/novel.ts` | 新增批量清洗任务管理 API | 418 → 516 (+98) |

### 修改的既有文件

| 文件 | 变化内容 |
|------|---------|
| `backend/app/services/novel.py` | `_apply_clean_result` 保留作为降级方案，新增 `_apply_chapter_event_extraction` 调用 AI 模型 |
| `backend/app/routers/novel.py` | clean_chapter 端点改为异步提交（202 Accepted），新增 `/clean/status` 和 `/clean-status` 端点 |
| `frontend/src/api/novel.ts` | 新增批次清洗任务取消/进度/活跃任务 API |

---

## 二、架构设计分析

### 2.1 整体架构图（Day36 完整版）

```
┌──────────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3 + Element Plus)                   │
│                                                                    │
│  Novel.vue                                                         │
│  ├─ 单章清洗 → POST /{chapter_id}/clean → 202 Accepted            │
│  ├─ 批量清洗 → POST /batch-clean → 后台执行                       │
│  ├─ 清洗进度 → GET /clean/status?ids=1,2,3                        │
│  └─ 任务管理 → GET /batch-clean/jobs/active → 取消/进度           │
└──────────────────────────────┬───────────────────────────────────┘
                               │ HTTP REST API
┌──────────────────────────────┴───────────────────────────────────┐
│                       后端 (FastAPI)                                │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Novel Router (25+ 端点)                                       │ │
│  │  ├─ POST /{chapter_id}/clean  → 提交异步清洗 (NEW)            │ │
│  │  ├─ GET  /clean/status        → 清洗状态查询 (NEW)            │ │
│  │  └─ GET  /clean-status        → 兼容旧前端 (NEW)              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Novel Service（事件清洗流程重构）                              │ │
│  │                                                                │ │
│  │  queue_clean_chapter()                                         │ │
│  │    ├─ 检查章节正文长度 ≥ 300 字                                 │ │
│  │    ├─ 检查项目是否配置文本模型                                  │ │
│  │    └─ 返回章节（立即响应，清洗在后台）                          │ │
│  │                                                                │ │
│  │  submit_clean_chapter_task()  ← 后台任务                       │ │
│  │    ↓                                                            │ │
│  │  _apply_chapter_event_extraction()  ← NEW! AI 驱动             │ │
│  │    ├─ 从项目配置获取 text_model                                │ │
│  │    ├─ 从 PromptRegistry 加载提示词                             │ │
│  │    └─ 通过 ProviderModelGateway 调用 AI 模型                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  新增基础设施层                                                 │ │
│  │                                                                │ │
│  │  ProviderModelGateway (agent_gateway.py)                       │ │
│  │  ├─ generate_text() — 统一文本生成入口                         │ │
│  │  ├─ _extract_text() — 多格式响应自动解析                       │ │
│  │  └─ 支持 OpenAI/千问/墨落等返回格式差异                         │ │
│  │                                                                │ │
│  │  PromptRegistry (prompt_registry.py)                           │ │
│  │  ├─ 从文件系统加载 Markdown 提示词                             │ │
│  │  ├─ 自动索引 skills 目录所有 .md 文件                          │ │
│  │  ├─ 缓存已加载提示词                                           │ │
│  │  └─ 路径安全校验（防目录穿越）                                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  新增配置项 (core/config.py)                                    │ │
│  │                                                                │ │
│  │  CHAPTER_EVENT_EXTRACTION_PROMPT_NAME = "chapter_event_extraction"
│  │  MODEL_REQUEST_TIMEOUT_SECONDS = 180                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计模式

#### 1. 模型网关模式（ProviderModelGateway）

```
调用层（novel.py）         网关层（agent_gateway.py）         Provider 运行时
      │                           │                              │
      │ generate_text(             │                              │
      │   model_id,                │                              │
      │   messages,                │                              │
      │ )                          │                              │
      ├──────────────────────────→│                              │
      │                           │ create_provider_for_model()  │
      │                           ├─────────────────────────────→│
      │                           │         Provider 实例         │
      │                           │←─────────────────────────────│
      │                           │                              │
      │                           │ provider.generate(...)      │
      │                           ├─────────────────────────────→│
      │                           │         raw_output           │
      │                           │←─────────────────────────────│
      │                           │                              │
      │                           │ _extract_text(raw_output)    │
      │                           │ ├─ str → _ensure_text        │
      │                           │ ├─ {output_text} → 提取      │
      │                           │ └─ {choices[0].message.content} │
      │         "提取的文本"       │                              │
      │←──────────────────────────│                              │
```

**解耦价值：**
- 遮罩不同 Provider 返回格式差异
- 统一错误处理（空文本、格式异常）
- 调用层只关心 `model_id` + `messages`，不关心具体 Provider 是谁

#### 2. 提示词技能注册表（PromptRegistry）

```
文件系统：
  data/skills/
  ├── chapter_event_extraction/
  │   └── README.md          ← 被索引为 "chapter_event_extraction"
  ├── director_manual/
  │   └── README.md
  └── custom_skill/
      └── my_prompt.md       ← 被索引为 "my_prompt"

PromptRegistry 工作流程：
  1. 初始化 → 扫描 skills_root 下所有 *.md
  2. 索引规则：
     ├─ README.md → 取父目录名作为 skill key
     └─ 其他 .md  → 取文件名（不含扩展名）作为 skill key
  3. 同名冲突处理：同名 skill 存在多个 .md → 丢弃（避免歧义）
  4. 加载缓存：首次读取 read_text() → 缓存 → 后续调 skill() 走缓存
  5. 路径安全：禁止 ".."、"/"、"\" 字符，禁止越出 skills_root
```

#### 3. AI 事件提取流水线（核心变化）✅

**Day35（占位实现）→ Day36（AI 驱动）**

```
┌─ Day35 占位 ─────────────────────────────────────┐
│                                                    │
│  _apply_clean_result(chapter):                     │
│    生成固定模板：                                   │
│    "## 主要事件"                                    │
│    "- 由「{章节名}」自动清洗生成"                   │
│    "- 共 {字数} 字"                                │
│    "## 关键人物"                                    │
│    "- 主角"                                        │
│    "## 场景"                                       │
│    "- 自动识别中..."                                │
│                                                    │
│    ❌ 全是占位内容，没有实际内容                     │
└────────────────────────────────────────────────────┘

┌─ Day36 AI 驱动 ───────────────────────────────────┐
│                                                    │
│  _apply_chapter_event_extraction(chapter, text_model):
│                                                     │
│    1. 校验: 正文字数 ≥ 300 字                       │
│            项目已配置 text_model                    │
│                                                     │
│    2. 加载提示词:                                   │
│       PromptRegistry.from_settings()               │
│         .skill("chapter_event_extraction")         │
│                                                     │
│    3. 调用 AI 模型:                                 │
│       ProviderModelGateway()                       │
│         .generate_text(                            │
│           model_id=project.text_model,             │
│           messages=[                               │
│             {role:system, content:prompt},         │
│             {role:user, content:chapter_text},     │
│           ]                                        │
│         )                                          │
│                                                     │
│    4. 解析响应:                                     │
│       - 去除 ```json 代码块                         │
│       - JSON.parse → {"events": [...]}             │
│       - 校验：顶层只能有 events 字段                │
│       - 校验：events 必须是数组                     │
│                                                     │
│    5. 写入数据库:                                   │
│       chapter.event = json.dumps({events: [...]})  │
│       chapter.event_state = 1     (=成功)           │
│                                                     │
│    ✅ 真正调用 AI 提取章节事件                       │
└────────────────────────────────────────────────────┘
```

**降级策略：**
- AI 提取失败 → `event_state = -1`，`error_reason` 记录原因
- `_apply_clean_result()` 保留在代码中作为备用（未被删除）

#### 4. 异步清洗模式

```
用户点击"清洗"                   立即返回 202
  │                              ┌──── chapter（event_state=0，待清洗）
  ↓                              │
POST /clean                      │
  │                              └──── 响应中不等待 AI 完成
  ▼
queue_clean_chapter()            submit_clean_chapter_task()
  ├─ 前置校验                     ├─ asyncio.create_task() → 后台运行
  ├─ event_state = 0             └─ _apply_chapter_event_extraction()
  └─ 立即返回
```

**设计理由：**
- AI 调用可能 30-180 秒，HTTP 连接容易超时
- 返回 202 Accepted + 前端轮询 `/clean/status` 获取结果
- 避免 FastAPI worker 被长时间占用

#### 5. 多 Provider 响应格式兼容

```python
def _extract_text(self, raw_output: Any) -> str:
    # 格式 1: 纯字符串
    if isinstance(raw_output, str):
        return raw_output

    # 格式 2: {"output_text": "..."} 或 {"text": "..."}
    if isinstance(raw_output, dict):
        for key in ("output_text", "text"):
            value = raw_output.get(key)
            if isinstance(value, str):
                return value

        # 格式 3: OpenAI 兼容 {"choices": [{"message": {"content": "..."}}]}
        choices = raw_output.get("choices")
        if isinstance(choices, list) and choices:
            choice = choices[0]
            if isinstance(choice, dict):
                message = choice.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"]
                if isinstance(choice.get("text"), str):
                    return choice["text"]
```

兼容的响应格式：
- `千问/墨落` → 返回 `{"output_text": "..."}` 或 `{"text": "..."}`
- `火山引擎` → OpenAI 兼容格式 `{"choices": [...]}`
- `纯文本` → 直接返回字符串

---

## 三、关键技术要点

### 3.1 新增 API 端点

| 方法 | 路径 | 变化 | 说明 |
|------|------|------|------|
| GET | `/clean/status?ids=1,2,3` | **NEW** | 批量查询清洗状态（轻量，不含正文） |
| GET | `/clean-status?ids=1,2,3` | **NEW** | 兼容旧前端路径 |
| POST | `/{chapter_id}/clean` | **CHANGED** | 从同步阻塞 → 202 Accepted 异步提交 |

### 3.2 新增配置项

```python
# core/config.py
chapter_event_extraction_prompt_name: str = "chapter_event_extraction"
# ↑ 指向 data/skills/chapter_event_extraction/README.md

model_request_timeout_seconds: float = 180
# ↑ AI 模型调用超时（秒），默认 3 分钟
```

### 3.3 NovelChapterCleanStatus Schema

```python
class NovelChapterCleanStatus(BaseModel):
    id: int                           # 数据库主键
    publicId: str                     # 公开标识
    chapterIndex: int                 # 章节序号
    reel: str                         # 卷次
    chapter: str                      # 章节标题
    event: str                        # 当前事件内容
    eventState: int                   # 0待清洗/1成功/-1失败
    errorReason: str | None           # 失败原因
    updatedAt: datetime | None        # 更新时间
```

与 `NovelChapterRead` 的区别：**不含 `chapter_data` 字段**，减少响应体积（正文可能很长）。

### 3.4 前端批量清洗任务管理 API

```typescript
// 前端新增 3 个 API 调用

// 1. 取消批次清洗任务
cancelBatchCleanJobApi(projectPublicId, jobPublicId)

// 2. 获取批次清洗任务进度
getBatchCleanJobProgressApi(projectPublicId, jobPublicId)

// 3. 获取项目活跃清洗任务列表
listActiveBatchCleanJobsApi(projectPublicId)
```

### 3.5 事件提取 Prompt 结构

系统通过 PromptRegistry 加载的提示词期望 AI 输出格式：

```json
{
  "events": [
    {
      "description": "事件描述",
      "characters": ["角色1", "角色2"],
      "location": "场景地点",
      "emotion": "情绪基调"
    }
  ]
}
```

校验规则：
- `_parse_chapter_event_payload()` 强制要求顶层只有 `events` 字段
- `events` 必须是数组
- 去除 ```` ```json ```` 代码块包裹

---

## 四、完整事件提取数据流

```
用户点击"清洗"章节
     │
     ▼
前端 POST /projects/{id}/novels/{chapter_id}/clean
     │
     ▼
NovelView.clean_chapter()
     ├─ queue_clean_chapter() → 前置校验 → 返回章节（202 Accepted）
     └─ submit_clean_chapter_task() → 后台执行
             │
             ├─ asyncio.create_task()
             │       │
             │       ▼
             │  _apply_chapter_event_extraction(chapter, text_model)
             │       │
             │       ├─ 1. 获取提示词
             │       │     PromptRegistry.from_settings()
             │       │       .skill("chapter_event_extraction")
             │       │
             │       ├─ 2. 调用模型
             │       │     ProviderModelGateway()
             │       │       .generate_text(
             │       │         model_id=project.text_model,
             │       │         messages=[
             │       │           {role: "system", content: prompt},
             │       │           {role: "user", content: chapter_text}
             │       │         ]
             │       │       )
             │       │
             │       ├─ 3. 解析响应
             │       │     _strip_json_code_fence() → json.loads()
             │       │     _parse_chapter_event_payload() → 校验结构
             │       │
             │       └─ 4. 写入数据库
             │             chapter.event = json.dumps({"events": [...]})
             │             chapter.event_state = 1
             │             session.commit()
             │
             ▼
前端轮询 GET /clean/status?ids={chapter_id}
     │
     ├─ event_state = 0  → "清洗中..."（跳动动画）
     ├─ event_state = 1  → 展示事件列表
     └─ event_state = -1 → 展示错误信息
```

---

## 五、架构评价与建议

### 优势

1. **AI 事件提取终于可用**：从占位模板变为真实的 AI 调用，产出实际可用的事件结构化数据
2. **模型网关解耦**：遮罩各 Provider 返回格式差异，调用层简洁
3. **提示词热更新**：修改 `data/skills/` 下 Markdown 文件即可调整 AI 行为，无需改代码
4. **异步非阻塞**：清洗提交立即返回，后台执行，不阻塞 HTTP worker
5. **多格式兼容**：网关自动识别 3 种常见 AI 响应格式
6. **降级保留**：旧的 `_apply_clean_result` 未删除，保持向后兼容
7. **清洗状态可查**：`NovelChapterCleanStatus` 提供轻量级状态查询

### 不足与待完善

1. **单章清洗而非批量**：`submit_clean_chapter_task` 每次只处理一章，批量清洗场景效率低
2. **无重试机制**：AI 调用失败直接标记为 `-1`，无自动重试
3. **无并发控制**：后台任务没有信号量限制，大量并发清洗可能打爆 Provider
4. **清洗进度未持久化**：后台任务在进程内存中，重启丢失
5. **无清洗任务队列**：未使用 Celery/Redis 等消息队列，任务不可恢复
6. **前端未更新**：Novel.vue 等前端页面未同步更新清洗进度展示逻辑

### 对当前项目的影响

- 新增 2 个服务文件（不影响既有模块）
- 新增 2 个配置项（需在 `.env` 中配置）
- 3 个既有文件变更（server/novel.py, routers/novel.py, schemas/novel.py）
- 数据库表无变化（复用 af_novel_chapter）
- 需要新增 `data/skills/chapter_event_extraction/README.md` 提示词文件

---

## 六、与 Day35 的集成关系

Day35 完成了小说爬虫系统的完整实现，Day36 在此基础上打通了 **AI 调用链路**：

```
Day35: 爬虫系统                        Day36: AI 调用链
┌──────────────────────┐              ┌──────────────────────────┐
│ 爬取小说 → 导入章节   │              │                          │
│                      │              │ ProviderModelGateway     │
│ 章节正文存入          │  ──→  清洗   │   ↓                      │
│ chapter_data 字段     │      (AI)   │ Provider.generate()      │
│                      │              │   ↓                      │
│ event 字段为占位内容   │              │ _extract_text()          │
│ event_state = 1 假值  │              │   ↓                      │
└──────────────────────┘              │ PromptRegistry           │
                                      │   ↓                      │
                                      │ skill(chapter_event)     │
                                      │   ↓                      │
                                      │ event 字段 = 真实事件     │
                                      │ event_state = 1 真实值   │
                                      └──────────────────────────┘
```

---

## 七、待办事项

1. **提示词文件落地**：在 `data/skills/` 下创建 `chapter_event_extraction/README.md`
2. **更新 .env**：添加 `CHAPTER_EVENT_EXTRACTION_PROMPT_NAME`、`MODEL_REQUEST_TIMEOUT_SECONDS`
3. **批量清洗并发控制**：使用 `asyncio.Semaphore` 限制并发 AI 调用数
4. **清洗任务持久化**：使用 Celery/Redis 实现任务队列和断点续洗
5. **前端进度展示更新**：Novel.vue 接入清洗进度查询和轮询更新
6. **自动重试**：AI 调用失败后的指数退避重试
