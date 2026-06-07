# Day35 升级报告：小说爬虫系统完整实现

## 一、新增内容概览

本次升级在 Day34（小说内容管理与创作工作流系统）基础上，完成了 **小说爬虫系统的完整后端实现** 和 **两个大型前端对话框组件**，标志着平台具备了生产级的小说内容抓取能力。核心新增三大模块：**完整爬虫后端服务**、**爬虫源配置管理系统**、**前端爬虫/导入对话框**。

### 新增文件清单

| 层级 | 文件路径 | 用途 |
|------|---------|------|
| 爬虫服务 | `backend/app/services/novel_crawler.py` | 完整的 HTTP 爬虫实现（694 行） |
| 数据模型 | `backend/app/models/novel.py` | 新增 NovelCrawlSource、NovelCrawlBook 表 |
| 前端组件 | `frontend/src/components/NovelCrawlDialog.vue` | 小说爬取对话框（4826 行） |
| 前端组件 | `frontend/src/components/NovelImportDialog.vue` | 全文导入对话框（1689 行） |
| 前端工具 | `frontend/src/utils/crawlCache.ts` | 爬虫本地缓存工具 |

### 扩展的既有文件

| 文件 | 变化内容 |
|------|---------|
| `backend/app/services/novel.py` | 新增爬虫源 CRUD、搜索、爬取、导入等 15+ 个服务函数 |
| `backend/app/routers/novel.py` | 新增 10+ 个爬虫相关 API 端点（来源管理、搜索、爬取、流式进度） |
| `backend/app/schemas/novel.py` | 新增爬虫相关 Schema（CrawlSourcePayload、CrawlSearchResult 等） |
| `backend/app/models/__init__.py` | 新增 NovelCrawlSource、NovelCrawlBook 导出 |
| `frontend/src/api/novel.ts` | 新增爬虫 API 类型定义和调用函数 |

---

## 二、架构设计分析

### 2.1 整体架构图（Day35 完整版）

```
┌──────────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3 + Element Plus)                   │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ NovelCrawlDialog.vue (4826 行)                                │ │
│  │  ├─ 来源管理面板（CRUD + 复制 + AI 分析入口）                    │ │
│  │  ├─ 搜索面板（来源选择 + 关键词搜索 + 结果展示）                  │ │
│  │  ├─ 爬取面板（章节范围配置 + 进度条 + SSE 流式接收）              │ │
│  │  └─ 预览面板（章节过滤 + 事件清洗 + 批量导入）                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ NovelImportDialog.vue (1689 行)                               │ │
│  │  ├─ 文件上传（.txt / .docx / .pdf，自动编码识别）                │ │
│  │  ├─ 全文粘贴 + 正则切分规则配置                                 │ │
│  │  ├─ 内容过滤规则（7 个内置 + 自定义正则）                        │ │
│  │  └─ 章节预览 + 批量导入                                        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────┐ ┌──────────────┐                                │
│  │ crawlCache   │ │ novel.ts     │                                │
│  │ (本地缓存)   │ │ (API 层)     │                                │
│  └──────────────┘ └──────┬───────┘                                │
└──────────────────────────┼───────────────────────────────────────┘
                           │ HTTP REST API + SSE Stream
┌──────────────────────────┴───────────────────────────────────────┐
│                       后端 (FastAPI)                                │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Novel Router (20+ 端点)                                        │ │
│  │  ├─ /projects/{id}/novels/              (章节 CRUD)            │ │
│  │  ├─ /projects/{id}/novels/crawl-sources (来源管理)             │ │
│  │  ├─ /projects/{id}/novels/crawl/search  (搜索小说)             │ │
│  │  ├─ /projects/{id}/novels/crawl/book-detail (小说详情)         │ │
│  │  ├─ /projects/{id}/novels/crawl/chapters (爬取章节)            │ │
│  │  ├─ /projects/{id}/novels/crawl/chapters/stream (SSE 流式)     │ │
│  │  └─ /projects/{id}/novels/crawl/import  (导入爬取结果)         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Novel Service                                                  │ │
│  │  ├─ 章节 CRUD + 全文导入 + 事件清洗                            │ │
│  │  ├─ 爬虫源 CRUD（公共/私有 + 复制）                            │ │
│  │  ├─ 搜索/详情/章节爬取（调用 novel_crawler）                    │ │
│  │  └─ 爬取结果导入（去重 + MD5 校验）                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ novel_crawler.py (694 行)                                      │ │
│  │  ├─ JSONPath 字段提取引擎                                      │ │
│  │  ├─ HTTP 请求封装（GET/POST + Headers/Body 模板渲染）           │ │
│  │  ├─ 多进程并行爬取（ProcessPoolExecutor + 协程）                │ │
│  │  └─ SSE 流式进度推送                                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 数据库新增表                                                    │ │
│  │  ├─ af_novel_crawl_source (爬虫源配置，50+ 字段)                │ │
│  │  └─ af_novel_crawl_book (爬取小说快照)                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计模式

#### 1. 爬虫源配置系统（NovelCrawlSource）

爬虫源采用 **配置驱动** 设计，单个源包含 50+ 个配置字段，覆盖完整的爬取流程：

```
爬虫源配置结构：
├─ 基础信息（key/name/baseUrl/desc/scope）
├─ 搜索接口配置
│  ├─ search_url_template（URL 模板，支持 {q} 占位符）
│  ├─ api_search_method/headers/body
│  └─ api_search_book_*_path（JSONPath 字段选择器）
├─ 小说详情接口配置
│  ├─ api_book_url/method/headers/body
│  └─ api_book_*_path（标题/作者/封面/简介等选择器）
├─ 章节列表接口配置
│  ├─ api_chapter_list_url/method/headers/body
│  └─ api_chapter_list_*_path（章节 ID/标题/时间/正文选择器）
└─ 章节详情接口配置
   ├─ api_chapter_url/method/headers/body
   └─ api_chapter_*_path（标题/正文/时间/MD5 选择器）
```

支持两种来源作用域：
- **public**：公共来源，所有项目可见（仅管理员可编辑）
- **private**：项目私有来源，仅创建项目可见

#### 2. JSONPath 字段提取引擎

`novel_crawler.py` 实现了简化但灵活的 JSONPath 解析器：

```python
def extract_json_path_values(data: Any, path: str) -> list[Any]:
    """按来源配置支持的简化 JSONPath 提取值。"""
    # 支持语法：
    # $.data.items[*].title   → 数组展平提取
    # $.data[0].id            → 数组索引
    # $.author                → 简单字段
    # $.*                     → 所有值展平
```

特性：
- 支持 `[*]` 数组展平
- 支持 `[n]` 数组索引（含负数）
- 支持嵌套路径 `$.data.items[*].title`
- 自动处理单值/数组两种返回

#### 3. 多进程并行爬取架构

```
爬取请求（N 章）
    │
    ▼
_partition_metas() ──→ 按 worker 数分片
    │
    ▼
ProcessPoolExecutor (max_workers=4)
    │
    ├─ Worker 1: 章节 1-25 ──→ asyncio.run() ──→ httpx.AsyncClient
    ├─ Worker 2: 章节 26-50 ──→ asyncio.run() ──→ httpx.AsyncClient
    ├─ Worker 3: 章节 51-75 ──→ asyncio.run() ──→ httpx.AsyncClient
    └─ Worker 4: 章节 76-100 ──→ asyncio.run() ──→ httpx.AsyncClient
    │
    ▼
结果合并 ──→ 按章节序号排序返回
```

关键参数：
- `MAX_CRAWL_PROCESSES = 4`：最大进程数
- `CHAPTER_COROUTINES_PER_PROCESS = 8`：每进程并发协程数
- 总并发度：4 × 8 = 32 个并发请求

#### 4. SSE 流式进度推送

```
客户端                          服务端
  │                               │
  │  POST /crawl/chapters/stream  │
  │ ─────────────────────────────→ │
  │                               │
  │  {"type":"start","total":100} │
  │ ←────────────────────────────  │
  │                               │
  │  {"type":"chapter",...}       │
  │ ←────────────────────────────  │
  │  {"type":"chapter",...}       │
  │ ←────────────────────────────  │
  │  ...                          │
  │                               │
  │  {"type":"done","completed":100} │
  │ ←────────────────────────────  │
```

流式事件类型：
- `start`：爬取开始，返回总章节数
- `chapter`：单章完成，返回章节数据
- `done`：爬取完成
- `error`：爬取异常

#### 5. 前端爬虫缓存策略

```typescript
// crawlCache.ts - 本地缓存键设计
const CRAWL_CACHE_PREFIX = 'novel-crawl-cache:v1'

缓存类型：
├─ search:{projectPublicId}:{sourceKey}:{query}
│  └─ 搜索结果缓存（避免重复搜索）
└─ chapters:{projectPublicId}:{sourceKey}:{dirid}:{start}:{end}
   └─ 章节缓存（支持断点续爬）
```

缓存有效期：手动清空或切换来源/小说时自动清理

#### 6. 内容过滤规则引擎

内置 8 个过滤规则，支持自定义扩展：

| 规则 ID | 用途 | 正则模式 |
|--------|------|---------|
| cf-url | 移除 http(s) 网址 | `https?:\/\/[^\s一-龥]+` |
| cf-www | 移除 www 域名 | `www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` |
| cf-ads | 移除广告水印行 | `^.*(笔趣阁\|起点中文\|...).*$` |
| cf-tips | 移除章节尾提示 | `^\s*(?:本章未完.*\|请收藏本站.*).*$` |
| cf-email | 移除邮箱 | `[\w.+-]+@[\w-]+\.[\w.-]+` |
| cf-garbled | 移除乱码字符 | `[� -...]` |
| cf-empty | 合并多余空行 | `\n{3,}` → `\n\n` |
| cf-unicode | 移除特殊符号 | `[¤§©®™°±×÷...]` |

---

## 三、关键技术要点

### 3.1 Novel Crawl API 端点设计（10+ 个）

| 方法 | 路径 | 用途 | 说明 |
|------|------|------|------|
| GET | `/crawl-sources` | 获取来源列表 | 公共 + 项目私有 |
| POST | `/crawl-sources` | 创建来源 | 项目私有来源 |
| PUT | `/crawl-sources/{key}` | 更新来源 | 仅私有来源可编辑 |
| DELETE | `/crawl-sources/{key}` | 删除来源 | 仅私有来源可删除 |
| POST | `/crawl-sources/{key}/duplicate` | 复制来源 | 公共→私有复制 |
| POST | `/crawl-sources/analyze` | AI 分析来源 | 占位实现 |
| POST | `/crawl/search` | 搜索小说 | 返回 CrawlSearchResult[] |
| POST | `/crawl/book-detail` | 获取小说详情 | 持久化到 af_novel_crawl_book |
| POST | `/crawl/book-chapter-count` | 获取章节总数 | 通过章节列表接口 |
| POST | `/crawl/chapters` | 爬取章节 | 多进程并行，返回全量 |
| POST | `/crawl/chapters/stream` | 流式爬取 | SSE 流式进度推送 |
| POST | `/crawl/import` | 导入爬取结果 | 去重 + MD5 校验 |

### 3.2 NovelCrawlSource 数据模型详解

```python
class NovelCrawlSource(BaseModel, table=True):
    __tablename__ = "af_novel_crawl_source"

    # 基础标识
    key: str                  # 全局唯一标识（64字符）
    name: str                 # 显示名称（120字符）
    base_url: str             # 站点 URL（1000字符）
    desc: str                 # 描述（1000字符）
    builtin: bool             # 是否内置来源
    scope: str                # "public" / "private"
    source_type: str          # 固定为 "api"
    sort_order: int           # 排序权重

    # 归属信息
    project_id: int | None    # 私有来源的项目 ID
    owner_public_id: str      # 创建者用户 ID

    # 搜索接口 (15 个字段)
    search_url_template: str
    api_search_method: str    # GET/POST/PUT/PATCH
    api_search_headers: str   # JSON 格式
    api_search_body: str      # JSON 格式
    api_search_book_url_path: str
    api_search_book_id_path: str
    api_search_book_title_path: str
    api_search_book_author_path: str
    api_search_book_intro_path: str
    api_search_book_cover_path: str
    api_search_book_category_path: str
    api_search_book_update_status_path: str
    api_search_book_last_chapter_path: str
    api_search_book_last_chapter_id_path: str
    api_search_book_last_update_path: str

    # 小说详情接口 (13 个字段)
    api_book_url: str
    api_book_method: str
    api_book_headers: str
    api_book_body: str
    api_book_title_path: str
    api_book_author_path: str
    api_book_intro_path: str
    api_book_last_chapter_path: str
    api_book_last_chapter_id_path: str
    api_book_last_update_path: str
    api_book_cover_path: str
    api_book_category_path: str
    api_book_update_status_path: str
    api_book_id_path: str

    # 章节列表接口 (10 个字段)
    api_chapter_list_url: str
    api_chapter_list_method: str
    api_chapter_list_headers: str
    api_chapter_list_body: str
    api_chapter_list_id_path: str
    api_chapter_list_name_path: str
    api_chapter_list_time_path: str
    api_chapter_list_content_path: str
    api_chapter_list_md5_path: str

    # 章节详情接口 (9 个字段)
    api_chapter_url: str
    api_chapter_method: str
    api_chapter_headers: str
    api_chapter_body: str
    api_chapter_name_path: str
    api_chapter_content_path: str
    api_chapter_time_path: str
    api_chapter_md5_path: str
```

### 3.3 NovelCrawlBook 数据模型

```python
class NovelCrawlBook(BaseModel, table=True):
    """爬取小说快照表 - 记录已爬取的小说元信息"""
    __tablename__ = "af_novel_crawl_book"
    __table_args__ = (
        UniqueConstraint("project_id", "source_key", "source_book_id"),
    )

    project_id: int           # 所属项目
    source_key: str           # 来源标识
    source_book_id: str       # 来源站点的小说 ID
    source_book_numeric_id: int | None  # 数字 ID

    # 小说元信息
    title: str                # 标题
    author: str               # 作者
    cover_url: str            # 封面图 URL
    category: str             # 类别
    update_status: str        # 更新状态（连载/完结）
    intro: str                # 简介
    last_chapter: str         # 最新章节标题
    last_chapter_id: int      # 最新章节 ID
    last_update: str          # 最新更新时间
    raw_data: str             # 原始爬取数据（JSON）
```

### 3.4 爬虫流水线设计

```
1. 选择来源 → 2. 搜索小说 → 3. 点击详情 → 4. 获取章节数
                                                      ↓
    ┌─────────────────────────────────────────────────┘
    ▼
5. 配置章节范围（start-end）
    ▼
6. 开始爬取（SSE 流式接收进度）
    ├─ 本地缓存命中 → 直接使用
    └─ 缓存未命中 → 请求服务端 → 多进程并行爬取
    ▼
7. 预览章节列表
    ├─ 过滤正文（应用正则规则）
    ├─ 清洗事件（生成占位事件文档）
    └─ 移除异常章节
    ▼
8. 确认导入 → 写入 af_novel_chapter 表
```

### 3.5 前端 NovelCrawlDialog 组件架构

```
NovelCrawlDialog.vue (4826 行)
├─ 来源管理对话框 (sourceManageVisible)
│  ├─ 来源列表模式 (sourceMode='list')
│  │  ├─ 来源表格（名称/标识/站点/说明/类型/操作）
│  │  └─ 操作按钮（复制/编辑/删除/禁用）
│  ├─ 创建/编辑模式 (sourceMode='create'/'edit')
│  │  ├─ 基础信息表单（key/name/baseUrl/desc）
│  │  ├─ 搜索接口配置（4 个子表单组）
│  │  ├─ 小说详情接口配置
│  │  ├─ 章节列表接口配置
│  │  └─ 章节详情接口配置
│  └─ 复制模式 (sourceMode='duplicate')
│     └─ 新标识/新名称输入
│
└─ 爬取对话框 (modelValue)
   ├─ 步骤 1：搜索小说 (crawlStep=1)
   │  ├─ 来源选择下拉框
   │  ├─ 关键词搜索输入框
   │  ├─ 搜索结果卡片列表
   │  └─ 小说详情加载（点击卡片触发）
   │
   ├─ 步骤 2：爬取章节 (crawlStep=2)
   │  ├─ 选中小说信息展示
   │  ├─ 章节范围配置（start-end）
   │  ├─ 进度条 + 百分比
   │  ├─ 已爬取章节实时列表
   │  └─ 继续爬取按钮（断点续爬）
   │
   └─ 步骤 3：预览入库 (crawlStep=3)
      ├─ 过滤规则面板（8 个内置 + 自定义）
      ├─ 章节表格（多选/排序/预览/过滤/清洗/移除）
      ├─ 章节正文预览弹窗
      └─ 确认导入按钮
```

### 3.6 前端 NovelImportDialog 组件架构

```
NovelImportDialog.vue (1689 行)
├─ 步骤 1：输入内容 (importStep=1)
│  ├─ 文件上传区（拖拽上传）
│  │  ├─ .txt：自动识别 UTF-8/GBK 编码
│  │  ├─ .docx：使用 mammoth 库解析
│  │  └─ .pdf：使用 pdfjs-dist 解析
│  ├─ 全文粘贴区
│  ├─ 章节切分规则配置
│  │  ├─ 预设选择（中文章节/仅第X章/仅第X回/英文Chapter）
│  │  ├─ 自定义正则编辑器
│  │  └─ 卷次正则配置
│  └─ 内容过滤规则
│     ├─ 7 个内置规则
│     ├─ 自定义规则添加
│     └─ 应用/恢复按钮
│
└─ 步骤 2：预览章节 (importStep=2)
   ├─ 章节表格（多选/卷次/标题/字数）
   ├─ 章节正文预览 Popover
   └─ 确认导入按钮
```

---

## 四、新增测试覆盖

| 测试文件 | 测试范围 |
|---------|---------|
| `test_novel_service.py` | 新增爬虫源 CRUD、搜索、爬取、导入测试 |

---

## 五、架构评价与建议

### 优势

1. **完整的爬虫系统**：从来源配置到搜索、爬取、导入，形成完整的内容抓取流水线
2. **生产级并发设计**：多进程 + 协程的混合并发模式，单机可支持 32 并发请求
3. **SSE 流式进度**：大章节量场景下的实时进度反馈，用户体验优秀
4. **灵活的字段选择器**：JSONPath 支持各种复杂的 API 响应结构
5. **本地缓存策略**：搜索结果和章节内容本地缓存，支持断点续爬
6. **内容过滤引擎**：8 个内置规则 + 自定义正则，有效清洗抓取内容
7. **文件上传支持**：.txt/.docx/.pdf 三种格式，自动编码识别

### 不足与待完善

1. **AI 分析入口为占位**：`/crawl-sources/analyze` 接口返回固定草稿，未接入 AI 自动分析
2. **事件清洗为占位**：`_apply_clean_result()` 生成固定格式内容，未接入 AI 模型
3. **来源配置复杂**：50+ 个字段的手动配置对普通用户门槛较高
4. **缺少内置来源**：未提供预配置的常用小说站来源
5. **爬取频率限制**：未实现请求频率控制和重试机制
6. **反爬策略**：缺少 User-Agent 轮换、代理池、Cookie 管理等反爬措施
7. **前端组件过大**：NovelCrawlDialog.vue（4826 行）应拆分为子组件

### 对当前项目的影响

- 新增数据库表 `af_novel_crawl_source` 和 `af_novel_crawl_book`
- 新增路由挂载在 `/projects/{id}/novels/crawl-*` 下
- 项目模型无变化（复用 Day34 的 af_novel_chapter 表）
- Provider 系统（Day33）继续独立运行，爬虫系统独立工作

---

## 六、与 Day34 的集成关系

Day34 定义了小说章节管理系统和爬虫系统的类型定义，Day35 完成了爬虫系统的完整实现：

```
Day34: 定义类型与占位                   Day35: 完整实现
┌──────────────────────────┐          ┌──────────────────────────┐
│ novel.ts API 类型定义     │          │ novel_crawler.py         │
│  ├─ CrawlSourcePayload   │ ──────→  │  ├─ search_books()       │
│  ├─ CrawlSearchResult    │          │  ├─ fetch_book_detail()  │
│  └─ CrawlChapterDraft    │          │  ├─ fetch_chapters()     │
└──────────────────────────┘          │  └─ stream_chapters()    │
                                      └──────────────────────────┘
┌──────────────────────────┐          ┌──────────────────────────┐
│ novel.py 服务层占位       │          │ novel.py 服务层          │
│  └─ 爬虫相关函数待实现    │ ──────→  │  ├─ 15+ 爬虫服务函数     │
└──────────────────────────┘          │  └─ 完整业务逻辑          │
                                      └──────────────────────────┘
┌──────────────────────────┐          ┌──────────────────────────┐
│ Novel.vue 页面           │          │ NovelCrawlDialog.vue     │
│  └─ 爬取按钮占位         │ ──────→  │ NovelImportDialog.vue    │
│                          │          │  └─ 完整爬取/导入界面     │
└──────────────────────────┘          └──────────────────────────┘
```

---

## 七、数据流完整链路

```
用户操作                          前端                          后端                         数据库
   │                              │                             │                             │
   │ 1. 打开爬取对话框             │                             │                             │
   │ ───────────────────────────→ │                             │                             │
   │                              │ GET /crawl-sources          │                             │
   │                              │ ──────────────────────────→ │ SELECT af_novel_crawl_source│
   │                              │                             │ ──────────────────────────→ │
   │ 显示来源列表                  │ ←────────────────────────── │                             │
   │ ←─────────────────────────── │                             │                             │
   │                              │                             │                             │
   │ 2. 选择来源，输入关键词        │                             │                             │
   │ ───────────────────────────→ │ POST /crawl/search          │                             │
   │                              │ ──────────────────────────→ │ HTTP 请求目标站点           │
   │                              │                             │ ──────────────────────────→ │
   │                              │                             │ JSONPath 提取结果           │
   │                              │ ←────────────────────────── │                             │
   │ 显示搜索结果                  │                             │                             │
   │ ←─────────────────────────── │                             │                             │
   │                              │                             │                             │
   │ 3. 点击小说卡片               │ POST /crawl/book-detail     │                             │
   │ ───────────────────────────→ │ ──────────────────────────→ │ HTTP 请求详情页            │
   │                              │                             │ INSERT af_novel_crawl_book  │
   │                              │ ←────────────────────────── │ ──────────────────────────→ │
   │ 显示小说详情                  │                             │                             │
   │ ←─────────────────────────── │                             │                             │
   │                              │                             │                             │
   │ 4. 配置章节范围，开始爬取      │ POST /crawl/chapters/stream │                             │
   │ ───────────────────────────→ │ ──────────────────────────→ │ 多进程并行爬取              │
   │                              │                             │ ──────────────────────────→ │
   │ SSE: {"type":"start",...}    │ ←────────────────────────── │                             │
   │ ←─────────────────────────── │                             │                             │
   │ SSE: {"type":"chapter",...}  │                             │                             │
   │ ←─────────────────────────── │                             │                             │
   │ ...                          │                             │                             │
   │ SSE: {"type":"done",...}     │                             │                             │
   │ ←─────────────────────────── │                             │                             │
   │                              │                             │                             │
   │ 5. 过滤正文，清洗事件         │                             │                             │
   │ ───────────────────────────→ │ 本地正则过滤                │                             │
   │                              │ 本地事件清洗                │                             │
   │                              │                             │                             │
   │ 6. 确认导入                  │ POST /crawl/import          │                             │
   │ ───────────────────────────→ │ ──────────────────────────→ │ 去重校验                   │
   │                              │                             │ INSERT af_novel_chapter     │
   │                              │ ←────────────────────────── │ ──────────────────────────→ │
   │ 导入完成                      │                             │                             │
   │ ←─────────────────────────── │                             │                             │
```

---

## 八、待办事项

1. **AI 来源分析**：实现 `/crawl-sources/analyze` 接口，自动分析目标站点并生成配置
2. **事件清洗 AI 增强**：接入 Provider 系统，实现真正的事件提取
3. **内置来源库**：提供常用小说站的预配置来源
4. **反爬策略**：实现 User-Agent 轮换、请求频率控制、代理池
5. **前端组件拆分**：将 NovelCrawlDialog.vue 拆分为来源管理、搜索、爬取、预览等子组件
6. **爬取任务队列**：使用 Celery/Redis 实现异步爬取任务
