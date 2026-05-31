# Day34 升级报告：小说内容管理与创作工作流系统

## 一、新增内容概览

本次升级在 Day33（大模型 Provider 适配器系统）基础上，引入了完整的 **小说内容管理** 和 **AI 创作工作流前端**，标志着平台从"工具配置层"向"业务创作层"的关键跃迁。核心新增四大模块：**小说章节管理系统**、**导演/视觉风格管理系统**、**小说爬虫源配置系统**和**三个核心创作前端页面**。

### 新增文件清单

| 层级 | 文件路径 | 用途 |
|------|---------|------|
| 数据模型 | `backend/app/models/novel.py` | NovelChapter 数据模型，管理小说章节与事件清洗 |
| 数据校验 | `backend/app/schemas/novel.py` | Pydantic Schema（章节 CRUD + 导入 + 清洗 + 批量操作） |
| API 路由 | `backend/app/routers/novel.py` | 10 个 RESTful 端点，以项目为命名空间 |
| 业务逻辑 | `backend/app/services/novel.py` | 章节 CRUD、全文解析导入、事件清洗引擎 |
| 解析工具 | `backend/app/utils/novel_parser.py` | 正则引擎智能拆解中英文卷/章标题 |
| 导入规则 | `backend/app/utils/novel_import_rules.py` | 4 套内置章节拆分规则（中文/英文/古典/混合） |
| 数据库迁移 | `backend/alembic/versions/131aa939f05d_add_novel_table.py` | af_novel_chapter 建表迁移 |
| 前端页面 | `frontend/src/pages/Novel.vue` | 小说管理页面（1908 行） |
| 前端页面 | `frontend/src/pages/Script.vue` | 剧本管理页面（3349 行） |
| 前端页面 | `frontend/src/pages/Original.vue` | 短剧/原创内容页面（3039 行） |
| 前端组件 | `frontend/src/components/DirectorStyleDialog.vue` | 导演风格管理对话框（1143 行） |
| 前端组件 | `frontend/src/components/VisualStyleDialog.vue` | 视觉风格管理对话框（1146 行） |
| 前端组件 | `frontend/src/components/MarkdownEditor.vue` | Markdown 编辑器封装（258 行） |
| 前端工具 | `frontend/src/utils/markdownEditorConfig.ts` | 编辑器工具栏配置 |
| 前端 API | `frontend/src/api/novel.ts` | 小说 API 类型定义与调用（含爬虫 API） |
| 测试 | `backend/app/tests/test_novel_parser.py` | 章节解析器单元测试 |
| 测试 | `backend/app/tests/test_novel_service.py` | 小说服务层单元测试 |

### 修改的既有文件

| 文件 | 变化内容 |
|------|---------|
| `backend/app/models/project.py` | 新增大量项目配置字段（模型选择、画幅、画质等） |
| `backend/app/schemas/project.py` | 新增视觉风格/导演手册全套 Schema（读写/图片） |
| `backend/app/routers/project.py` | 新增视觉风格和导演手册 CRUD 端点（约 20 个） |
| `backend/app/services/project.py` | 新增视觉风格和导演手册的文件系统级管理（1100+ 行） |
| `backend/app/routers/api.py` | 新增 `novel_router` 注册 |
| `backend/app/models/__init__.py` | 新增 NovelChapter 导出 |
| `frontend/src/routes/index.ts` | 新增 `/novel`、`/script`、`/original` 路由 |
| `frontend/src/pages/Project.vue` | 集成模型选择、导演/视觉风格选择 |
| `frontend/src/components/Settings.vue` | 面板导航新增小说/剧本/短剧入口 |
| `frontend/src/api/project.ts` | 新增视觉风格、导演手册 API |
| `backend/app/providers/moluo.py` | 适配器代码更新 |
| `backend/requirements.txt` | 新增依赖项 |
| `frontend/package.json` | 新增 md-editor-v3 等依赖 |

---

## 二、架构设计分析

### 2.1 整体架构图（Day33 + Day34 完整版）

```
┌──────────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3 + Element Plus)                   │
│                                                                    │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐               │
│  │ Novel.vue   │ │ Script.vue   │ │ Original.vue │               │
│  │ (小说管理)  │ │ (剧本管理)   │ │ (短剧管理)   │               │
│  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘               │
│         │                │                │                        │
│  ┌──────┴──────┐ ┌──────┴───────┐ ┌──────┴───────┐               │
│  │ novel.ts    │ │ project.ts   │ │ Markdown     │               │
│  │ (API 层)    │ │ (API 层)     │ │ Editor       │               │
│  └──────┬──────┘ └──────┬───────┘ └──────────────┘               │
│         │                │                                        │
│  ┌──────┴──────┐ ┌──────┴──────────────────────┐                 │
│  │ Director    │ │ VisualStyleDialog.vue       │                 │
│  │ StyleDialog │ │ (视觉风格管理)              │                 │
│  │ (导演风格)  │ └─────────────────────────────┘                 │
│  └─────────────┘                                                  │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ HTTP REST API
┌────────────────────────────────┴─────────────────────────────────┐
│                       后端 (FastAPI)                                │
│                                                                    │
│  ┌──────────────────┐  ┌────────────────────┐                     │
│  │ Novel Router     │  │ Project Router     │                     │
│  │ (10 端点)        │  │ (项目+风格+手册)    │                     │
│  │ /projects/{id}/  │  │ /projects/         │                     │
│  │   novels/        │  │ /projects/visual-  │                     │
│  │                  │  │   styles/          │                     │
│  │  ├─ CRUD 章节    │  │ /projects/director-│                     │
│  │  ├─ 全文导入     │  │   manuals/         │                     │
│  │  ├─ 事件清洗     │  └────────────────────┘                     │
│  │  ├─ 批量操作     │                                            │
│  │  └─ 爬虫集成     │                                            │
│  └────────┬─────────┘                                            │
│           │                                                       │
│  ┌────────┴─────────┐  ┌─────────────────────┐                   │
│  │ Novel Service    │  │ Project Service     │                   │
│  │ (章节+清洗+解析) │  │ (项目+视觉+导演)     │                   │
│  └────────┬─────────┘  └──────────┬──────────┘                   │
│           │                       │                               │
│  ┌────────┴─────────┐  ┌──────────┴──────────┐                   │
│  │ novel_parser.py  │  │ File System         │                   │
│  │ (智能章节拆分)   │  │ (data/skills/)      │                   │
│  │ novel_import_    │  │ art_list/           │                   │
│  │ rules.py         │  │ director_manual/    │                   │
│  └──────────────────┘  └─────────────────────┘                   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ af_novel_chapter 表（数据库）                                  │ │
│  │  ├─ 章节基础信息（卷次/标题/正文/序号）                          │ │
│  │  ├─ 事件清洗结果（event/event_state/error_reason）              │ │
│  │  ├─ 爬虫溯源信息（crawl_source_key/crawl_md5/...）              │ │
│  │  └─ 外键关联 project_id → af_project                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计模式

#### 1. 小说章节的事件清洗架构

系统引入了一套 **章节事件清洗流水线**，这是将原始小说文本结构化为可被 AI 模型消费的事件的关键中间层：

```
原始小说正文 (chapter_data)
    │
    ▼
事件清洗引擎 (_apply_clean_result)
    │
    ├─ 字数检查 (< 80 字 → 标记为失败)
    │
    ▼
结构化事件文档 (event, Markdown 格式)
    │
    ├─ 主要事件
    ├─ 关键人物
    └─ 场景描述
    │
    ▼
下游 AI 模型消费（生成分镜、剧本、视频提示词）
```

清洗状态管理使用三态机：`0` 待清洗 → `1` 成功 → `-1` 失败（附错误原因）。

#### 2. 智能章节拆分引擎（novel_parser.py）

`parse_novel_chapters()` 实现了多模式正则匹配，能自动识别以下格式：

| 格式类型 | 示例 | 正则策略 |
|---------|------|---------|
| 中文卷+章混合行 | `第十二集 第一章 标题` | INLINE_REEL_CHAPTER_PATTERN |
| 纯数字+标题 | `八 虎啸龙吟` | BARE_NUMBER_TITLE_PATTERN |
| 纯数字（两行） | `八\n虎啸龙吟` | BARE_NUMBER_ONLY_PATTERN + next_line |
| 标准章节标题 | `第一章 少年归来` | CHAPTER_PATTERN |
| 标准卷标题 | `第一卷` / `Book 1` | REEL_PATTERN / EN_REEL_PATTERN |
| 前言/序 | `序章` / `序言` | PREFACE_PATTERN |
| 英文章节 | `Chapter 10 The End` | EN_CHAPTER_PATTERN |

#### 3. 全文导入的双通道设计

导入支持两种模式：
- **原始文本通道**：用户粘贴全文 → 后端自动解析拆分 → 逐章入库
- **前端预览通道**：前端先拆分预览 → 用户确认/编辑 → 提交章节草稿列表

两通道通过 `NovelChapterImport` Schema 的 `raw_text` 和 `chapters` 字段互斥校验实现。

#### 4. 视觉风格和导演手册的文件系统级管理

与 Day33 Provider 系统的文件系统存储模式一致，视觉风格和导演手册使用目录级管理：

```
data/skills/
├── art_list/                  # 视觉风格根目录
│   ├── 3D_chinese_traditional/
│   │   ├── README.md
│   │   └── images/
│   │       ├── character_turnaround_sheet.png
│   │       ├── landscape_four_states_sheet.png
│   │       └── scene_character_in_landscape.png
│   ├── cyberpunk_photoreal/
│   └── ... (共 50+ 种视觉风格)
│
└── director_manual/           # 导演手册根目录
    ├── Xianxia_fantasy/
    │   ├── README.md
    │   ├── director_manual/
    │   │   ├── director_planning_narrative.md
    │   │   └── director_storyboard_table_narrative.md
    │   └── images/
    │       └── director_concept.png
    └── ... (共 16 种导演风格)
```

每个风格目录的标准结构为：
- `README.md` — 风格描述（第一行 `#` 标题作为展示名称）
- `images/` — 3 张标准图片（人物转面图 / 场景四视图 / 人物场景融合图）

#### 5. 小说爬虫源配置系统

`novel.ts` 前端 API 层定义了完整的爬虫源配置类型，支持两种爬取模式：

- **规则模式** (`sourceType: "rule"`)：基于 CSS 选择器的网页解析，配置搜索/列表/详情页选择器
- **API 模式** (`sourceType: "api"`)：基于 HTTP API 的结构化抓取，支持 JSONPath

此外支持 SSE 流式章节抓取（`/crawl/chapters/stream`），实现大章节量的实时进度反馈。

#### 6. Markdown 编辑器集成

`MarkdownEditor.vue` 封装了 `md-editor-v3` 库，提供：
- 工具栏定制（加粗/标题/代码/表格等 19 个工具）
- 主题切换（暗色/亮色/跟随系统）
- 全屏预览弹窗
- 粘贴媒体过滤防止意外插入

---

## 三、关键技术要点

### 3.1 Novel 章节 API 端点设计（10 个）

| 方法 | 路径 | 用途 | 说明 |
|------|------|------|------|
| GET | `/projects/{id}/novels` | 分页列表 | 支持 search 关键词搜索 |
| POST | `/projects/{id}/novels` | 创建章节 | 正文自动计算 crawl_md5 |
| POST | `/projects/{id}/novels/import` | 全文导入 | 120 秒超时，支持 raw_text/chapters 双通道 |
| GET | `/projects/{id}/novels/import-split-rules` | 获取拆分规则 | 返回 4 套内置规则 |
| POST | `/projects/{id}/novels/batch-delete` | 批量删除 | 返回 affected 计数 |
| POST | `/projects/{id}/novels/batch-clean` | 批量清洗事件 | 120 秒超时 |
| POST | `/projects/{id}/novels/event-state` | 批量更新状态 | 手动修正清洗结果 |
| PUT | `/projects/{id}/novels/{chapter_id}` | 更新章节 | 正文变更时重新计算 MD5 |
| DELETE | `/projects/{id}/novels/{chapter_id}` | 删除章节 | 返回 204 |
| POST | `/projects/{id}/novels/{chapter_id}/clean` | 单章清洗 | 120 秒超时 |

所有端点均挂载在项目公开 ID 下，确保项目级权限隔离。

### 3.2 项目模型扩展字段

Day34 对 `af_project` 表新增了大量 AI 创作相关配置字段：

| 字段 | 类型 | 默认值 | 用途 |
|------|------|-------|------|
| `text_model` | varchar(100) | "" | 默认文本生成模型 |
| `image_model` | varchar(100) | "" | 默认图像生成模型 |
| `video_model` | varchar(100) | "" | 默认视频生成模型 |
| `tts_model` | varchar(100) | "" | 默认语音生成模型 |
| `image_quality` | varchar(50) | "standard" | 默认图像质量档位 |
| `art_style` | varchar(100) | "3D_chinese_traditional" | 视觉风格选择 |
| `director_manual` | varchar(4000) | "" | 导演叙事风格选择 |
| `video_ratio` | varchar(20) | "9:16" | 默认视频画幅比例 |
| `content_type` | varchar(50) | "novel" | 源内容类型 |
| `mode` | enum | "text" | 视频生成模式（6 种） |

支持 6 种视频生成模式：`text` / `singleImage` / `multiReference` / `startEndRequired` / `endFrameOptional` / `startFrameOptional`。

### 3.3 NovelChapter 数据模型详解

```python
class NovelChapter(BaseModel, table=True):
    __tablename__ = "af_novel_chapter"

    project_id: int       # FK → af_project.id
    chapter_index: int    # 章节序号 (1-9999)
    reel: str             # 卷次标题 (≤120字符)
    chapter: str          # 章节标题 (≤255字符, 索引)
    chapter_data: str     # 章节正文 (TEXT, 无长度限制)
    event: str            # 清洗后的事件内容 (TEXT)
    event_state: int      # 清洗状态：0待清洗/1成功/-1失败 (索引)
    error_reason: str     # 清洗失败原因
    # --- 爬虫溯源字段 ---
    crawl_source_key: str      # 来源标识
    crawl_novel_dirid: str     # 来源小说 ID
    crawl_chapter_id: int      # 来源章节 ID
    crawl_time: str            # 来源发布时间
    crawl_md5: str             # 来源正文 MD5（去重依据）
```

`crawl_md5` 的自动计算确保了章节内容去重的可靠性，正文内容变更时自动更新。

### 3.4 内置章节拆分规则（4 套）

| 规则 Key | 标签 | 匹配范围 |
|---------|------|---------|
| `zh-mixed` | 中文章节（默认） | 「第X章」「第X回」「第X节」「序章」，按「第X卷/部/集/册」归类 |
| `zh-chapter` | 仅「第 X 章」 | 严格只匹配「第X章」 |
| `zh-hui` | 仅「第 X 回」 | 古典小说常见格式 |
| `en-chapter` | Chapter N（英文） | 识别「Chapter 1」「Chapter II」，大小写不敏感 |

### 3.5 爬虫系统设计

爬虫系统采用 **源配置 → 搜索 → 拉取章节 → 导入** 四步流水线：

```
1. 配置爬虫源 (CrawlSourcePayload)
   ├─ 规则模式: CSS 选择器链
   └─ API 模式: URL + JSONPath/Headers/Body

2. 搜索小说 (searchCrawlBooksApi)
   └─ 返回 CrawlSearchResult[]

3. 拉取章节 (CrawlChapterFetchPayload)
   ├─ 普通模式: POST → 返回全量 CrawlChapterDraft[]
   └─ 流式模式: SSE → CrawlChapterStreamEvent (实时进度)

4. 导入章节 (importCrawlChaptersApi)
   └─ 返回 CrawlImportResult {created, updated, skipped, chapters}
```

漂流式抓取的 SSE 接口提供实时进度反馈（start → chapter × N → done/error），适合大章节量场景。

---

## 四、前端三大创作页面详解

### 4.1 Novel.vue — 小说管理页面

核心工作区，提供完整的章节生命周期管理：

**功能矩阵：**
- 📋 **章节列表**：分页展示、按标题搜索、多选操作
- ➕ **新建章节**：手动创建单章，填入卷/章标题和正文
- 📥 **全文导入**：粘贴或上传全文 → 选择拆分规则 → 预览 → 导入
- 🕷️ **小说爬取**：配置爬虫源 → 搜索小说 → 选择章节范围 → 爬取
- 🧹 **事件清洗**：单章/批量清洗，生成结构化事件文档
- 🗑️ **批量操作**：批量删除、批量清洗、批量状态更新
- 📝 **内联编辑**：直接在列表中编辑章节正文（Markdown）
- 🔗 **侧栏导航**：项目 / 小说 / 任务 / 文档 / 设置

### 4.2 Script.vue — 剧本管理页面

用于管理 AI 生成的剧本素材，支持：
- 剧本 CRUD、导入/导出
- 排序（按创建时间/名称/更新日期）
- 关联项目和资产的展示
- 分镜预览面板

### 4.3 Original.vue — 短剧页面

用于管理短剧方向，创新功能：
- 🎲 **灵感模板系统**：预设一句话创意模板，点击切换
- ➕ **自定义模板**：用户可添加自己的灵感模板
- 📝 **从一句话到短剧方案**：输入创意 → 生成短剧方向、分集节奏、资产列表
- 🎬 **资产预览**：角色/场景/道具列表

### 4.4 DirectorStyleDialog / VisualStyleDialog

两个管理对话框组件提供了风格目录的完整 CRUD 界面：
- 创建/编辑风格目录
- 上传管理图片（Base64 编码传输）
- Markdown 文件编辑
- 图片拖拽排序

---

## 五、扩展的视觉风格库

Day34 附带了一个庞大的视觉风格资产库，位于 `data/skills/art_list/`：

| 分类 | 风格数量 | 代表风格 |
|------|---------|---------|
| 2D 动画 | 10 | 赛璐璐动画、赛博朋克动漫、水墨仙侠、日式电影感、韩漫风格 |
| 3D 渲染 | 4 | Q版卡通、国风仙侠动漫、风格化渲染 |
| 古典艺术 | 8 | 埃及壁画、巴洛克、拜占庭马赛克、文艺复兴、洛可可 |
| 现代设计 | 7 | 包豪斯几何、构成主义、立体主义、极简主义、波普艺术 |
| 未来主义 | 6 | 赛博朋克写实、蒸汽朋克、柴油朋克、原子朋克、太阳朋克 |
| 特殊效果 | 8 | 像素艺术、黏土定格、剪纸、水彩、油画、素描 |
| 写实风格 | 3 | 纪录片写实、现代商用真人、数字绘画 |

每个风格包含标准三件套：`character_turnaround_sheet.png`、`landscape_four_states_sheet.png`、`scene_character_in_landscape.png`。

导演手册库（`data/skills/director_manual/`）包含 16 种叙事风格：仙侠奇幻、都市职场、悬疑惊悚、热血动作、甜宠言情、喜剧幽默、科幻末日、恐怖超自然、历史史诗、心理剧情、家庭温情、成长故事等。

---

## 六、新增测试覆盖

| 测试文件 | 测试范围 |
|---------|---------|
| `test_novel_parser.py` | 章节解析器各种格式的正确拆分 |
| `test_novel_service.py` | 小说服务层 CRUD 和清洗逻辑 |

---

## 七、架构评价与建议

### 优势

1. **创作工作流完整**：从小说导入 → 事件清洗 → 剧本 → 短剧，形成完整的 AI 辅助内容创作流水线
2. **智能解析引擎**：章节拆分支持中英文混合、古典格式、纯数字标题等灵活场景
3. **爬虫系统专业**：规则+API 双模式、SSE 流式抓取、MD5 去重，具备生产级抓取能力
4. **风格库即插即用**：50+ 视觉风格 + 16 种导演手册，开箱即用的 AI 创作配置
5. **事件清洗中间层**：将非结构化小说文本转换为结构化事件文档，为下游 AI 模型提供标准化输入
6. **一致性设计**：视觉风格/导演手册采用与 Provider 系统相同的文件系统级管理模式

### 不足与待完善

1. **事件清洗为占位实现**：当前 `_apply_clean_result` 只是一个模板生成器，实际清洗逻辑尚未接入 AI 模型，生成的是固定格式的占位内容
2. **爬虫后端未完整实现**：前端 API 层已定义了完整的爬虫类型和接口，但后端 `novel.py` 路由中未见对应的爬虫端点实现（仅有小说章节 CRUD）
3. **Script.vue / Original.vue 数据模型缺失**：两个前端页面的后端数据模型和 API 尚未实现，当前只能展示 UI 框架
4. **前端页面过大**：Script.vue（3349 行）和 Original.vue（3039 行）单体组件过大，建议拆分为子组件
5. **并发清洗未使用队列**：批量清洗是同步循环处理，大量章节时可能阻塞
6. **清洗结果未被下游消费**：Novel.vue 清洗完事件后，Script.vue 和 Original.vue 没有直接的数据通路消费这些事件

### 对当前项目的影响

- 新增数据库表 `af_novel_chapter`（不影响既有表）
- 新增路由挂载在 `/projects/{id}/novels` 下（与现有路由无冲突）
- 新增路由 `/projects/visual-styles/*` 和 `/projects/director-manuals/*`
- 项目模型新增字段仅扩展现有表，不影响既有查询
- Provider 系统（Day33）继续独立运行，本模块通过项目配置字段引用 Provider 模型名称

---

## 八、与 Day33 的集成关系

Day33 定义的 Provider 系统（大模型适配器）与 Day34 的创作工作流形成了上下游关系：

```
Day33: Provider 系统                     Day34: 创作工作流
┌──────────────────────┐              ┌──────────────────────┐
│ 墨落 / 千问 / 火山 / │              │ 小说导入              │
│ 可灵                 │              │   ↓                  │
│                      │  ──选择模型──→│ 事件清洗 (待 AI 增强) │
│ text_model ◄─────────│              │   ↓                  │
│ image_model ◄────────│              │ 剧本管理              │
│ video_model ◄────────│              │   ↓                  │
│ tts_model ◄──────────│              │ 短剧方案              │
└──────────────────────┘              └──────────────────────┘
```

项目配置中的 `text_model`、`image_model`、`video_model`、`tts_model` 字段引用的是 Provider 系统中的模型名称，形成配置到执行的完整链路。当前这条链路的 AI 调用部分（即事件清洗和剧本生成的实际 AI 调用）仍为占位实现，是后续迭代的关键待办项。
