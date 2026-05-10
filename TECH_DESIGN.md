# FileFinder — 技术设计文档 (TECH_DESIGN)

> 版本：v1.1
> 关联文档：PRD.md、RESEARCH.md、AGENTS.md
> 更新日期：2026-05-10

---

## 1. 技术栈选择

### 1.1 技术选型总览

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (GUI)                             │
│                       PySide6 ≥ 6.5.0                        │
│              跨平台桌面应用框架 + Qt 控件库                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ Qt 信号槽 / Signal 调用
┌─────────────────────────▼───────────────────────────────────┐
│                      后端 (业务逻辑)                          │
│                         Python 3.10+                         │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │ 文件名搜索器  │ 内容搜索引擎  │  文件解析器  │             │
│  │ name_searcher│content_searcher│ file_parser │             │
│  └──────────────┴──────────────┴──────────────┘             │
│  ┌──────────────┐                                           │
│  │ 搜索调度引擎  │                                           │
│  │search_engine │                                           │
│  └──────────────┘                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      数据层 (SQLite)                         │
│     文件索引缓存 + 搜索历史 + 用户设置 + 内存缓存             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 前端：PySide6

| 项目 | 选择 | 说明 |
|------|------|------|
| **框架** | PySide6 | Qt 官方 Python 绑定，LGPL 许可证更宽松 |
| **版本** | ≥ 6.5.0 | 支持 Qt6 的现代特性 |

**选择理由：**
- Qt 官方维护，许可证宽松（LGPL），适合开源项目
- 信号槽机制便于解耦 UI 和业务逻辑（`Signal` / `Slot`）
- 内置样式系统支持主题切换
- 系统托盘、多窗口等桌面特性完善
- 与 PyQt6 API 几乎相同，可按需切换

### 1.3 后端：Python 3.10+

| 组件 | 选择 | 说明 |
|------|------|------|
| **核心语言** | Python 3.10+ | 开发效率高，生态丰富 |
| **正则引擎** | re | 标准库，P1 阶段支持正则搜索 |
| **文件遍历** | os.scandir + os.walk | 标准库，Python 3.10+ 优化 |
| **多线程** | concurrent.futures + QThread | ThreadPoolExecutor 并发搜索 + QThread 后台扫描 |
| **编码检测** | charset-normalizer | 自动检测文件编码 |
| **文件监控** | QFileSystemWatcher | Qt 内置，目录变化自动同步索引 |

### 1.4 数据库：SQLite

| 项目 | 选择 | 说明 |
|------|------|------|
| **数据库** | SQLite 3 | Python 内置（sqlite3 模块），无需安装 |
| **访问方式** | 原生 SQL | 避免额外依赖，轻量级 |
| **缓存策略** | 内存缓存（SearchCache） | 启动时全表加载到内存，搜索在内存中过滤 |

**数据库用途：**
- 文件索引缓存（核心表，持久化存储）
- 搜索历史记录
- 用户设置持久化

**SQLite PRAGMA 优化（已实现）：**

```python
PRAGMA journal_mode=WAL          # Write-Ahead Logging，读写不互斥
PRAGMA synchronous=NORMAL        # 平衡安全性和性能
PRAGMA cache_size=-16000         # 16MB 页缓存
PRAGMA mmap_size=67108864        # 64MB 内存映射
PRAGMA temp_store=MEMORY         # 临时表存内存
```

### 1.5 文档解析库

| 格式 | 库 | 阶段 | 说明 |
|------|------|------|------|
| **纯文本/代码** | 标准库 + charset-normalizer | ✅ P0 | 32 种文本/代码扩展名 |
| **PDF** | PyMuPDF (fitz) | 🔄 P1 | 提取 PDF 文本内容，速度快 |
| **Word (.docx)** | python-docx | 🔄 P1 | 读取 .docx 文档文本 |
| **Excel (.xlsx)** | openpyxl | 🔄 P1 | 读取 .xlsx 单元格文本 |
| **PowerPoint** | python-pptx | 🔄 P1 | 读取 .pptx 文本 |

### 1.6 打包工具

| 工具 | 选择 | 说明 |
|------|------|------|
| **打包** | PyInstaller | 成熟稳定，兼容性好 |
| **备选** | Nuitka | 编译为 C，性能更好，但配置复杂 |

---

## 2. 项目结构

### 2.1 目录结构（当前实际结构）

```
filefinder/
│
├── main.py                      # 程序入口
│                                  # - 设置工作目录
│                                  # - 创建 QApplication
│                                  # - 创建主窗口
│                                  # - 启动事件循环
│
├── config.py                    # 配置管理
│                                  # - load_config() / save_config()
│                                  # - 默认配置与用户配置深度合并
│                                  # - 配置存储: ~/.filefinder/config.json
│
├── constants.py                 # 常量定义
│                                  # - 文件扩展名分类集合（TEXT/CODE/DOCUMENT 等）
│                                  # - FILE_TYPE_CATEGORIES 分类映射
│                                  # - 搜索参数常量（DEBOUNCE_MS/MAX_WORKERS/BATCH_SIZE）
│
├── requirements.txt             # 依赖清单
│
├── models/                     # 数据模型层
│   ├── __init__.py
│   ├── file_item.py             # FileItem: 文件名、路径、大小、时间、类型
│   │                            #   - size_display / modified_date / file_type 计算属性
│   │                            #   - FILE_TYPE_MAP: 60+ 扩展名 → 类型分类
│   ├── search_query.py          # SearchQuery: 搜索条件封装
│   │                            #   - has_name_query / has_content_query / has_query
│   ├── search_result.py         # SearchResult + ContentMatch
│   │                            #   - score 评分属性（名称*10 + 内容*5）
│   └── search_history.py        # SearchHistory: 搜索历史记录
│
├── core/                       # 核心业务逻辑层
│   ├── __init__.py
│   ├── name_searcher.py         # 文件名搜索引擎
│   │                            #   - fuzzy_match() / wildcard_match()
│   │                            #   - _calculate_name_relevance() 评分
│   │                            #   - search_by_name() 主搜索
│   │
│   ├── content_searcher.py      # 文件内容搜索引擎
│   │                            #   - Signal: progress_updated / result_found / search_completed
│   │                            #   - _collect_files() 文件收集
│   │                            #   - _search_file() 单文件搜索
│   │                            #   - _search_batch() 批量搜索
│   │                            #   - search() ThreadPoolExecutor 并发入口
│   │
│   ├── file_parser.py          # 文件解析器（注册表模式）
│   │                            #   - FileParser(ABC) 抽象基类
│   │                            #   - TextParser 纯文本解析器（P0，32 种格式）
│   │                            #   - ParserRegistry 解析器注册表
│   │
│   └── search_engine.py        # 搜索调度引擎
│                                #   - search() 统一搜索入口
│                                #   - 联合搜索：名称 ∩ 内容 取交集
│                                #   - cancel() 取消搜索
│
├── database/                   # 数据访问层
│   ├── __init__.py
│   ├── db_manager.py           # 数据库管理器（单例模式）
│   │                            #   - SearchCache 内存缓存
│   │                            #   - insert_file_batch() 批量插入
│   │                            #   - search_files() 搜索
│   │                            #   - _sync_directory() 增量同步
│   │
│   ├── history_dao.py          # 搜索历史 DAO
│   │                            #   - add_history() / get_histories() / clear_histories()
│   │
│   └── settings_dao.py         # 设置 DAO
│                                #   - save_setting() / load_setting()
│
├── ui/                         # 用户界面层
│   ├── __init__.py
│   ├── main_window.py          # 主窗口（2718 行，需重构）
│   │                            #   - WelcomePage: 首次启动引导
│   │                            #   - ScanProgressDialog: 扫描进度
│   │                            #   - ScanWorker(QThread): 扫描工作线程
│   │                            #   - SearchWorker(QThread): 搜索工作线程
│   │                            #   - SearchScopePanel: 搜索范围面板
│   │                            #   - _ScopeSelectionDialog: 目录选择对话框
│   │                            #   - MainWindow: 主窗口
│   │
│   ├── widgets/                # UI 组件
│   │   ├── __init__.py
│   │   ├── search_bar.py       # 搜索栏（双输入框 + 模式切换 + 动画按钮）
│   │   ├── result_list.py      # 结果列表（自定义 ResultItemWidget + SVG 图标）
│   │   ├── filter_bar.py       # 筛选栏（9 大类型按钮 + 扫描管理）
│   │   └── preview_panel.py    # 预览面板（P1 待实现内容预览）
│   │
│   └── dialogs/                # 对话框
│       ├── __init__.py
│       └── settings_dialog.py  # 设置对话框
│
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── encoding.py             # 编码检测工具
│   │                            #   - detect_file_encoding(): BOM + charset_normalizer
│   │                            #   - read_text_file(): 安全读取文本
│   │
│   ├── path_helper.py          # 路径处理工具
│   │                            #   - normalize_path() / get_file_info()
│   │                            #   - is_binary_file() / get_all_drives()
│   │
│   └── thread_helper.py        # 线程工具
│                                #   - Debouncer: 防抖器（300ms）
│
├── data/                       # 运行时数据
│   └── filefinder.db           # SQLite 数据库文件
│
└── icons/                      # 图标资源
    ├── doctype/                # 文件类型图标（SVG，60+ 种）
    └── *.svg                   # UI 图标
```

### 2.2 模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                            │                                 │
│              ┌─────────────┴─────────────┐                   │
│              ▼                           ▼                   │
│        MainWindow                  (TrayIcon P2)             │
│              │                                               │
│    ┌────────┼────────┬──────────┐                           │
│    ▼        ▼        ▼          ▼                           │
│ SearchBar ResultList FilterBar PreviewPanel                  │
│    │        │        │                                      │
│    └────────┼────────┘                                      │
│             ▼                                                │
│      SearchEngine                                            │
│             │                                                │
│    ┌────────┼────────┐                                      │
│    ▼        ▼        ▼                                      │
│ NameSearcher ContentSearcher                                 │
│    │        │                                               │
│    │        ▼                                               │
│    │    ParserRegistry                                      │
│    │        │                                               │
│    │    ┌───┴───┐                                           │
│    │    ▼       ▼                                           │
│    │ TextParser (P1: PDFParser/DocxParser/XlsxParser)       │
│    │        │                                               │
│    ▼        ▼                                               │
│  DatabaseManager                                             │
│    │    │    │                                               │
│    ▼    ▼    ▼                                               │
│ SearchCache HistoryDAO SettingsDAO                           │
│    │                                                         │
│    ▼                                                         │
│  SQLite (file_index_cache / search_history / settings)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型

### 3.1 核心数据模型（当前实现）

#### FileItem — 文件条目

```python
@dataclass
class FileItem:
    """单个文件的信息模型"""
    path: str                    # 完整文件路径
    name: str                    # 文件名（不含路径）
    extension: str               # 文件扩展名（如 '.txt'）
    size: int                    # 文件大小（字节）
    modified_time: datetime      # 修改时间
    created_time: datetime       # 创建时间
    is_directory: bool = False   # 是否为目录
    item_count: int = 0          # 目录内文件数

    @property
    def size_display(self) -> str:
        """返回人类可读的文件大小（B/KB/MB/GB）"""

    @property
    def modified_date(self) -> str:
        """返回格式化的修改日期 YYYY-MM-DD HH:MM"""

    @property
    def item_count_display(self) -> str:
        """返回目录项数显示 'N 项'"""

    @property
    def file_type(self) -> str:
        """返回文件类型分类（document/code/image/video/audio/archive/other）"""
```

#### SearchQuery — 搜索查询

```python
@dataclass
class SearchQuery:
    """搜索条件模型"""
    name_query: Optional[str] = None       # 文件名关键词
    name_mode: str = 'fuzzy'               # 'fuzzy' | 'exact' | 'wildcard'
    name_case_sensitive: bool = False       # 是否区分大小写
    content_query: Optional[str] = None    # 内容关键词
    content_mode: str = 'keyword'          # 'keyword' (P0) | 'regex' (P1)
    content_case_sensitive: bool = False    # 是否区分大小写
    file_types: List[str] = field(default_factory=list)
    exclude_file_types: List[str] = field(default_factory=list)
    size_min: Optional[int] = None         # P1: 最小文件大小
    size_max: Optional[int] = None         # P1: 最大文件大小
    date_from: Optional[datetime] = None   # P1: 修改日期范围起
    date_to: Optional[datetime] = None     # P1: 修改日期范围止
    include_dirs: List[str] = field(default_factory=list)
    exclude_dirs: List[str] = field(default_factory=list)
    max_results: int = 1000

    @property
    def has_name_query(self) -> bool: ...
    @property
    def has_content_query(self) -> bool: ...
    @property
    def has_query(self) -> bool: ...
```

#### SearchResult / ContentMatch — 搜索结果

```python
@dataclass
class ContentMatch:
    """内容匹配片段"""
    line_number: int             # 行号
    line_content: str            # 该行内容
    match_start: int             # 匹配起始位置
    match_end: int               # 匹配结束位置
    context_before: List[str] = field(default_factory=list)  # 前文（最多3行）
    context_after: List[str] = field(default_factory=list)   # 后文（最多3行）

@dataclass
class SearchResult:
    """搜索结果模型"""
    file_item: FileItem          # 对应的文件条目
    match_reason: str            # 'name' | 'content' | 'both'
    content_matches: List[ContentMatch] = field(default_factory=list)
    name_match_score: int = 0

    @property
    def score(self) -> int:
        """综合评分：名称匹配 * 10 + 内容匹配数 * 5"""
```

#### SearchHistory — 搜索历史

```python
@dataclass
class SearchHistory:
    """搜索历史记录"""
    id: int
    name_query: Optional[str]
    content_query: Optional[str]
    created_at: datetime
    result_count: int = 0
```

### 3.2 数据库表设计（当前实现）

#### 表：file_index_cache（文件索引缓存 — 核心表）

```sql
CREATE TABLE file_index_cache (
    path            TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    name_stem       TEXT,              -- 不含扩展名的文件名（用于搜索）
    extension       TEXT,
    size            INTEGER,
    modified_time   REAL,              -- Unix 时间戳
    is_directory    INTEGER DEFAULT 0,
    item_count      INTEGER DEFAULT 0,
    indexed_at      REAL DEFAULT (julianday('now'))
);

CREATE INDEX idx_index_name ON file_index_cache(name);
CREATE INDEX idx_index_ext ON file_index_cache(extension);
CREATE INDEX idx_index_size ON file_index_cache(size);
CREATE INDEX idx_index_modified ON file_index_cache(modified_time);
CREATE INDEX idx_index_name_stem ON file_index_cache(name_stem);
```

#### 表：search_history（搜索历史）

```sql
CREATE TABLE search_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name_query      TEXT,
    content_query   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result_count    INTEGER DEFAULT 0
);

CREATE INDEX idx_history_created ON search_history(created_at DESC);
```

#### 表：settings（用户设置）

```sql
CREATE TABLE settings (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 配置数据结构

```python
# ~/.filefinder/config.json
{
    "general": {
        "theme": "system",
        "language": "zh_CN",
        "auto_start": false,
        "minimize_to_tray": true,
        "global_shortcut": "Ctrl+Alt+F"
    },
    "search": {
        "default_dirs": [],
        "scanned_dirs": [],
        "exclude_dirs": [
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\$Recycle.Bin"
        ],
        "exclude_extensions": [".dll", ".exe", ".sys", ".obj", ".lib", ".pdb"],
        "case_sensitive": false,
        "max_results": 1000,
        "content_max_size_mb": 10
    },
    "ui": {
        "window_width": 900,
        "window_height": 600,
        "preview_panel_width": 350,
        "show_status_bar": true
    }
}
```

---

## 4. 关键技术点

### 4.1 文件名搜索：SQLite 索引 + 内存缓存

#### 架构设计

借鉴 Everything 的文件名索引思路，FileFinder 实现了「一次扫描，终生复用」的文件名搜索方案：

```
┌─────────────────────────────────────────────────────────────┐
│                    文件名搜索架构                             │
│                                                             │
│  1. 首次扫描                                                │
│     ScanWorker(QThread) 遍历目录                            │
│     │                                                      │
│     ▼                                                      │
│  2. 持久化索引                                              │
│     DatabaseManager.insert_file_batch()                     │
│     SQLite file_index_cache 表                              │
│     │  500 条/批写入                                        │
│     │  PRAGMA WAL + 16MB 缓存                               │
│     ▼                                                      │
│  3. 内存缓存                                                │
│     SearchCache: 启动时全表加载到内存                        │
│     │  self._entries 列表                                   │
│     │  threading.Lock 线程安全                              │
│     ▼                                                      │
│  4. 搜索执行                                                │
│     name_searcher.search_by_name()                          │
│     │  内存缓存过滤 → 数据库获取完整行                       │
│     │  fuzzy_match / exact_match / wildcard_match           │
│     │  _calculate_name_relevance() 评分排序                 │
│     ▼                                                      │
│  5. 索引维护                                                │
│     QFileSystemWatcher 监控目录变化                         │
│     _sync_directory() 增量同步                              │
└─────────────────────────────────────────────────────────────┘
```

**名称相关性评分算法：**

| 匹配情况 | 得分 | 示例（搜索 "main"） |
|----------|------|---------------------|
| 完全匹配 | 100 + pattern_len | `main.py` |
| 前缀匹配 | 80 + pattern_len | `main_window.py` |
| 单词边界匹配 | 60 + pattern_len | `my_main.py` |
| 普通子串匹配 | 40 + pattern_len | `remain.py` |
| 不匹配 | 0 | `config.py` |

### 4.2 文件内容搜索：多线程并发 + 解析器注册表

#### 当前架构（P0 实时扫描模式）

```
┌─────────────────────────────────────────────────────────────┐
│                    内容搜索架构（P0）                         │
│                                                             │
│  1. 文件收集                                                │
│     _collect_files(directory, query)                        │
│     ├─ os.walk 遍历目录                                     │
│     ├─ 跳过排除目录 (node_modules, .git)                    │
│     ├─ 跳过排除扩展名 (.dll, .exe)                          │
│     ├─ 按类型过滤（如只搜索 .txt）                          │
│     └─ 按大小过滤（跳过 >10MB 文件）                        │
│     │                                                      │
│     ▼                                                      │
│  2. 并发搜索                                                │
│     ThreadPoolExecutor(max_workers=4)                       │
│     │                                                      │
│     ├─ Worker 1: 搜索文件 1-100                             │
│     ├─ Worker 2: 搜索文件 101-200                          │
│     ├─ Worker 3: 搜索文件 201-300                           │
│     └─ Worker 4: 搜索文件 301-400                          │
│     │                                                      │
│     ▼                                                      │
│  3. 单文件搜索流程                                          │
│     _search_file(file_path, query)                          │
│     ├─ ParserRegistry.parse() → 提取文本                   │
│     ├─ re.search() 关键词匹配                              │
│     ├─ 提取 ContentMatch（行号+上下文）                     │
│     └─ 每文件最多 10 处匹配                                 │
│     │                                                      │
│     ▼                                                      │
│  4. 结果通知                                                │
│     Signal: result_found / search_completed                 │
│     UI 线程安全更新                                         │
└─────────────────────────────────────────────────────────────┘
```

#### 未来架构（P2 倒排索引模式，借鉴 AnyTXT）

AnyTXT Searcher 的核心性能优势在于其**倒排索引 + 流式匹配**架构。P2 阶段将引入类似设计：

```
┌─────────────────────────────────────────────────────────────┐
│                内容搜索架构（P2 目标）                        │
│                                                             │
│  1. 索引构建（后台异步）                                    │
│     IndexBuilder(QThread)                                   │
│     ├─ 遍历文件 → ParserRegistry.parse()                   │
│     ├─ 文本分词 → 构建倒排索引                              │
│     │   term → [file_path, line_number, position]           │
│     ├─ 存储到 SQLite content_index 表                      │
│     └─ 增量更新：仅处理变化的文件                           │
│                                                             │
│  2. mmap 流式搜索（借鉴 AnyTXT）                            │
│     ├─ 小文件（<1MB）：mmap 整体映射                        │
│     ├─ 大文件（1-10MB）：mmap 分块映射 + 流式匹配           │
│     └─ 超大文件（>10MB）：跳过内容搜索                      │
│                                                             │
│  3. 查询执行                                                │
│     ├─ 倒排索引查询 → 候选文件集                            │
│     ├─ 布尔查询：AND / OR / NOT 组合                        │
│     └─ 实时扫描回退：索引未覆盖时降级为 P0 模式             │
│                                                             │
│  4. 结果排序                                                │
│     ├─ TF-IDF 相关性评分                                    │
│     ├─ 字段加权（标题 > 正文 > 页脚）                       │
│     └─ 时间衰减排序                                        │
└─────────────────────────────────────────────────────────────┘
```

**AnyTXT 关键设计借鉴点：**

| AnyTXT 设计 | 借鉴意义 | FileFinder 实施方案 |
|-------------|----------|---------------------|
| **mmap 内存映射** | 避免数据拷贝，大文件不一次性加载到内存 | P2: 使用 `mmap.mmap()` 替代 `open().read()` |
| **流式匹配** | 边读边搜，不等待全文加载完毕 | P2: 分块读取 + 正则搜索，找到匹配即返回 |
| **倒排索引** | 词项 → 文件映射，搜索复杂度从 O(N) 降为 O(1) | P2: SQLite 存储倒排索引，支持增量更新 |
| **增量索引** | 只更新变化的文件，避免全量重建 | 已部分实现（QFileSystemWatcher），P2 增强 |
| **多编码容错** | UTF-8 优先 + 非法编码容错 | 已实现：BOM 检测 + charset_normalizer + errors='replace' |

### 4.3 文件编码自动检测

```python
# utils/encoding.py — 当前实现
def detect_file_encoding(file_path: str) -> str:
    """
    自动检测文件编码
    优先级：BOM 检测 > charset_normalizer > UTF-8 回退
    """
    # 1. 快速检查 BOM（前 4 字节）
    with open(file_path, 'rb') as f:
        raw = f.read(4)
        if raw.startswith(b'\xff\xfe'): return 'utf-16-le'
        if raw.startswith(b'\xfe\xff'): return 'utf-16-be'
        if raw.startswith(b'\xef\xbb\xbf'): return 'utf-8-sig'

    # 2. charset_normalizer 统计检测
    result = charset_normalizer.from_path(file_path)
    best_match = result.best()
    if best_match:
        return best_match.encoding

    # 3. 默认回退 UTF-8
    return 'utf-8'

def read_text_file(file_path: str, max_size_mb: int = 10) -> Optional[str]:
    """安全读取文本文件，超过大小限制返回 None"""
    if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
        return None
    encoding = detect_file_encoding(file_path)
    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        return f.read()
```

### 4.4 文件解析器注册表模式

```python
# core/file_parser.py — 当前实现
class FileParser(ABC):
    """解析器抽象基类"""
    @abstractmethod
    def can_parse(self, file_path: str) -> bool: ...
    @abstractmethod
    def parse(self, file_path: str) -> Optional[str]: ...

class TextParser(FileParser):
    """纯文本解析器（P0，支持 32 种文本/代码格式）"""
    TEXT_EXTS = {'.txt', '.md', '.log', '.csv', '.json', '.xml',
                 '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml',
                 '.py', '.js', '.ts', '.html', '.css', '.java',
                 '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php',
                 '.sh', '.bat', '.ps1', '.sql', '.vue', '.env',
                 '.gitignore', '.rtf'}

    def can_parse(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.TEXT_EXTS

    def parse(self, file_path: str) -> Optional[str]:
        return read_text_file(file_path)

class ParserRegistry:
    """解析器注册表 — 可扩展架构"""
    def __init__(self):
        self._parsers: List[FileParser] = [TextParser()]

    def parse(self, file_path: str) -> Optional[str]:
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser.parse(file_path)
        return None
```

**P1 扩展计划：**

```python
# P1: 添加文档格式解析器
class PDFParser(FileParser):
    """PDF 解析器（PyMuPDF）"""
    def can_parse(self, file_path): return file_path.lower().endswith('.pdf')
    def parse(self, file_path):
        import fitz
        doc = fitz.open(file_path)
        text = '\n'.join(page.get_text() for page in doc)
        doc.close()
        return text

class DocxParser(FileParser):
    """Word 解析器（python-docx）"""
    def can_parse(self, file_path): return file_path.lower().endswith('.docx')
    def parse(self, file_path):
        from docx import Document
        doc = Document(file_path)
        return '\n'.join(para.text for para in doc.paragraphs)

class XlsxParser(FileParser):
    """Excel 解析器（openpyxl）"""
    def can_parse(self, file_path): return file_path.lower().endswith('.xlsx')
    def parse(self, file_path):
        from openpyxl import load_workbook
        wb = load_workbook(file_path, read_only=True)
        texts = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                texts.extend(str(cell) for cell in row if cell)
        return '\n'.join(texts)

# 注册到 ParserRegistry
registry = ParserRegistry()
registry._parsers.extend([PDFParser(), DocxParser(), XlsxParser()])
```

### 4.5 搜索调度引擎

```python
# core/search_engine.py — 当前实现
class SearchEngine:
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        统一搜索入口，支持三种模式：
        1. 仅名称搜索 → name_searcher.search_by_name()
        2. 仅内容搜索 → ContentSearcher.search()
        3. 联合搜索 → 名称 ∩ 内容 取交集
        """
        if query.has_name_query and query.has_content_query:
            # 联合搜索：取交集
            name_results = name_searcher.search_by_name(query)
            content_results = content_searcher.search(query)
            name_paths = {r.file_item.path for r in name_results}
            results = [r for r in content_results if r.file_item.path in name_paths]
            # 补充名称匹配信息
            ...
        elif query.has_name_query:
            results = name_searcher.search_by_name(query)
        elif query.has_content_query:
            results = content_searcher.search(query)

        # 按 score 降序排列，截取 max_results
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:query.max_results]
```

### 4.6 防抖搜索（Debounce）

```python
# utils/thread_helper.py — 当前实现
class Debouncer(QObject):
    """防抖器：延迟执行，等待用户停止输入"""
    def __init__(self, delay_ms: int = 300, parent=None):
        super().__init__(parent)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute)

    def trigger(self, callback, *args, **kwargs):
        self._callback = callback
        self._timer.stop()
        self._timer.start(self._delay_ms)

    def _execute(self):
        self._callback(*self._args, **self._kwargs)
```

### 4.7 文件系统监控与增量同步

```python
# ui/main_window.py — 当前实现
# 使用 QFileSystemWatcher 监控目录变化
self._watcher = QFileSystemWatcher()
self._watcher.directoryChanged.connect(self._sync_directory)

def _sync_directory(self, dir_path: str):
    """增量同步：比较数据库索引与实际文件系统差异"""
    db_entries = db_manager.search_files('*', dir_path)
    actual_files = set()
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            actual_files.add(os.path.join(root, f))

    db_paths = {e['path'] for e in db_entries}
    # 新增文件 → 插入索引
    for new_file in actual_files - db_paths:
        db_manager.add_file_entry(get_file_info(new_file))
    # 删除文件 → 移除索引
    for deleted_file in db_paths - actual_files:
        db_manager.delete_file_entry(deleted_file)
```

### 4.8 PyInstaller 打包配置

```spec
# filefinder.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    datas=[
        ('icons', 'icons'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'charset_normalizer',
    ],
)

exe = EXE(
    pyz,
    a.scripts,
    name='FileFinder',
    console=False,
    icon='icons/app_icon.ico',
)
```

---

## 5. 已知问题与技术债务

### 5.1 Bug 修复

| 问题 | 位置 | 严重程度 | 说明 |
|------|------|----------|------|
| `history_dao.py` 调用不存在的方法 | `database/history_dao.py` | 高 | 调用 `DatabaseManager().get_connection()` 但该方法不存在，需改用 `DatabaseManager()` 的其他方法 |
| `settings_dao.py` 同上 | `database/settings_dao.py` | 高 | 同上 |
| `is_binary_file()` 逻辑反转 | `utils/path_helper.py` | 高 | 非文本字符判断条件反了，可能导致二进制文件被误判为文本 |

### 5.2 架构优化

| 问题 | 说明 | 优先级 |
|------|------|--------|
| `main_window.py` 过于臃肿（2718 行） | 包含 WelcomePage/ScanProgressDialog/SearchScopePanel 等多个应独立的组件 | 中 |
| `_styled_msg_box` 重复实现 | 在 main_window.py、filter_bar.py、settings_dialog.py 中各有一份 | 中 |
| `FILE_ICON_MAP` 重复定义 | 在 result_list.py 和 preview_panel.py 中各有一份 | 低 |
| Debouncer 未在 SearchBar 中集成 | 防抖器已实现但搜索仅在回车/点击时触发 | 低 |

---

## 附录

### A. 依赖清单

```
PySide6>=6.5.0              # GUI 框架
PyMuPDF>=1.23.0             # PDF 文本提取（P1）
python-docx>=0.8.11         # Word 文本提取（P1）
openpyxl>=3.1.0             # Excel 文本提取（P1）
charset-normalizer>=3.0.0   # 编码检测
```

### B. 开发环境要求

- Python 3.10+
- Windows 10/11 (64-bit)
- 建议内存 8GB+

### C. AnyTXT Searcher 技术参考

| 技术点 | AnyTXT 实现 | FileFinder 借鉴方案 |
|--------|-------------|---------------------|
| 文件读取 | mmap 内存映射 | P2: 使用 `mmap.mmap()` 流式读取 |
| 搜索模式 | 无索引实时扫描 | P0: 已实现实时扫描 + 多线程 |
| 索引方式 | 倒排索引 + 布尔查询 | P2: 构建倒排索引表 |
| 编码处理 | UTF-8 原生解析 + 容错 | 已实现: BOM + charset_normalizer |
| 格式支持 | 50+ 原生解析器 | P0: TextParser; P1: PDF/Word/Excel |
| 增量更新 | 实时监控 + 差异更新 | 已实现: QFileSystemWatcher + _sync_directory |
| 索引加密 | AES-256 | 暂不实现 |
| OCR | Tesseract v5 | 暂不实现（超出项目范围） |
