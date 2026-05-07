# 本地文件搜索工具 - 技术设计文档 (TECH_DESIGN)

> 版本：v1.0
> 关联文档：PRD.md、RESEARCH.md
> 更新日期：2026-05-07

---

## 1. 技术栈选择

### 1.1 技术选型总览

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (GUI)                             │
│                    PyQt6 / PySide6                           │
│              跨平台桌面应用框架 + Qt 控件库                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ Qt 信号槽 / API 调用
┌─────────────────────────▼───────────────────────────────────┐
│                      后端 (业务逻辑)                          │
│                         Python 3.10+                         │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐ │
│  │ 文件名搜索器  │ 内容搜索引擎  │  文件解析器  │ 索引管理  │ │
│  │ name_searcher│content_searcher│ file_parser │ indexer  │ │
│  └──────────────┴──────────────┴──────────────┴──────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      数据层 (SQLite)                         │
│              索引缓存 + 搜索历史 + 用户设置                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 前端：PyQt6

| 项目 | 选择 | 说明 |
|------|------|------|
| **框架** | PyQt6 | Qt 官方 Python 绑定，功能完整，文档丰富 |
| **备选** | PySide6 | 与 PyQt6 API 几乎相同，LGPL 许可证更宽松 |
| **版本** | ≥ 6.5.0 | 支持 Qt6 的现代特性 |

**选择理由：**
- Qt 控件库成熟度高，支持复杂 UI 组件
- 信号槽机制便于解耦 UI 和业务逻辑
- 内置样式系统支持主题切换
- 系统托盘、多窗口等桌面特性完善

### 1.3 后端：Python 3.10+

| 组件 | 选择 | 说明 |
|------|------|------|
| **核心语言** | Python 3.10+ | 用户熟悉，开发效率高 |
| **正则引擎** | re / regex | 标准库/第三方高性能正则 |
| **文件遍历** | os.scandir + pathlib | 标准库，Python 3.10+ 优化 |
| **多线程** | concurrent.futures | 标准库，ThreadPoolExecutor 实现并发 |
| **编码检测** | charset-normalizer | 自动检测文件编码 |

### 1.4 数据库：SQLite

| 项目 | 选择 | 说明 |
|------|------|------|
| **数据库** | SQLite 3 | Python 内置（sqlite3 模块），无需安装 |
| **ORM** | 原生 SQL | 避免额外依赖，轻量级 |
| **备选** | SQLAlchemy | 如需复杂查询可升级 |

**数据库用途：**
- 搜索历史记录存储
- 用户设置持久化
- 目录扫描缓存（可选）

### 1.5 文档解析库

| 格式 | 库 | 说明 |
|------|------|------|
| **PDF** | PyMuPDF (fitz) | 提取 PDF 文本内容，速度快 |
| **Word (.docx)** | python-docx | 读取 .docx 文档文本 |
| **Excel (.xlsx)** | openpyxl | 读取 .xlsx 单元格文本 |
| **PowerPoint** | python-pptx | 读取 .pptx 文本 |

### 1.6 打包工具

| 工具 | 选择 | 说明 |
|------|------|------|
| **打包** | PyInstaller | 成熟稳定，兼容性好 |
| **备选** | Nuitka | 编译为 C，性能更好，但配置复杂 |
| **图标** | PyQt6 内置 | 使用 Qt 的 QIcon |

---

## 2. 项目结构

### 2.1 目录结构

```
filefinder/
│
├── main.py                      # 🚀 程序入口
│                                  # - 初始化 QApplication
│                                  # - 创建主窗口
│                                  # - 启动事件循环
│
├── requirements.txt             # 📦 依赖清单
│
├── config.py                    # ⚙️ 配置管理
│                                  # - 读取/保存配置文件 (~/.filefinder/config.json)
│                                  # - 默认配置项定义
│                                  # - 配置验证
│
├── constants.py                 # 📝 常量定义
│                                  # - 窗口尺寸常量
│                                  # - 搜索参数常量
│                                  # - UI 文本常量
│
├── models/                     # 📊 数据模型层
│   ├── __init__.py
│   ├── file_item.py             # 文件条目模型
│   │                            # - FileItem: 文件名、路径、大小、时间、类型
│   ├── search_result.py         # 搜索结果模型
│   │                            # - SearchResult: 匹配文件 + 匹配上下文
│   ├── search_query.py          # 搜索查询模型
│   │                            # - SearchQuery: 搜索条件封装
│   └── search_history.py        # 搜索历史模型
│
├── core/                       # ⚡ 核心业务逻辑层
│   ├── __init__.py
│   ├── name_searcher.py         # 📁 文件名搜索引擎
│   │                            # - fuzzy_match(): 模糊匹配
│   │                            # - wildcard_match(): 通配符匹配
│   │                            # - search_by_name(): 主搜索方法
│   │
│   ├── content_searcher.py      # 📄 文件内容搜索引擎
│   │                            # - regex_search(): 正则搜索
│   │                            # - keyword_search(): 关键词搜索
│   │                            # - multi_thread_search(): 并发搜索
│   │
│   ├── file_parser.py          # 🔧 文件解析器（多格式）
│   │                            # - parse_text(): 纯文本解析
│   │                            # - parse_pdf(): PDF 文本提取
│   │                            # - parse_docx(): Word 文档解析
│   │                            # - parse_xlsx(): Excel 解析
│   │                            # - detect_encoding(): 编码检测
│   │
│   ├── indexer.py              # 🗂️ 文件索引管理
│   │                            # - build_index(): 建立索引
│   │                            # - update_index(): 增量更新
│   │                            # - clear_index(): 清除索引
│   │
│   ├── filter_engine.py         # 🔍 过滤引擎
│   │                            # - apply_filters(): 应用过滤条件
│   │                            # - filter_by_type(): 文件类型过滤
│   │                            # - filter_by_size(): 文件大小过滤
│   │                            # - filter_by_date(): 日期范围过滤
│   │
│   └── search_engine.py        # 🎯 搜索调度器
│                                # - 协调文件名搜索 + 内容搜索
│                                # - 处理联合搜索逻辑
│                                # - 合并和去重结果
│
├── ui/                         # 🖼️ 用户界面层
│   ├── __init__.py
│   ├── main_window.py          # 主窗口
│   │                            # - MainWindow: 窗口布局、信号连接
│   │
│   ├── widgets/                # UI 组件
│   │   ├── __init__.py
│   │   ├── search_bar.py       # 搜索栏组件
│   │   │                        # - SearchBar: 搜索输入框
│   │   ├── result_list.py      # 结果列表组件
│   │   │                        # - ResultListWidget: QListWidget 封装
│   │   ├── result_item.py      # 结果条目组件
│   │   │                        # - ResultItemWidget: 自定义 QWidget
│   │   ├── preview_panel.py     # 预览面板
│   │   │                        # - PreviewPanel: 文件内容预览
│   │   ├── filter_bar.py        # 过滤栏组件
│   │   │                        # - FilterBar: 类型按钮、日期选择等
│   │   └── status_bar.py       # 状态栏
│   │
│   ├── dialogs/                # 对话框
│   │   ├── __init__.py
│   │   ├── settings_dialog.py  # 设置对话框
│   │   └── about_dialog.py      # 关于对话框
│   │
│   └── styles/                 # 样式主题
│       ├── __init__.py
│       ├── light_theme.py      # 浅色主题
│       └── dark_theme.py       # 深色主题
│
├── utils/                      # 🔧 工具函数
│   ├── __init__.py
│   ├── encoding.py             # 编码检测工具
│   │                            # - detect_file_encoding(): 检测文件编码
│   │                            # - read_text_file(): 智能读取文本
│   │
│   ├── path_helper.py          # 路径处理工具
│   │                            # - normalize_path(): 路径规范化
│   │                            # - get_file_info(): 获取文件信息
│   │
│   ├── date_helper.py          # 日期处理工具
│   │                            # - parse_date(): 日期解析
│   │                            # - format_date(): 日期格式化
│   │
│   └── thread_helper.py        # 线程工具
│                                # - run_in_thread(): 线程装饰器
│                                # - ThreadTask: 线程任务封装
│
├── database/                  # 💾 数据层
│   ├── __init__.py
│   ├── db_manager.py           # 数据库管理器
│   │                            # - init_db(): 初始化数据库
│   │                            # - get_connection(): 获取连接
│   │
│   ├── history_dao.py          # 搜索历史 DAO
│   │                            # - add_history(): 添加历史
│   │                            # - get_histories(): 查询历史
│   │                            # - clear_histories(): 清除历史
│   │
│   └── settings_dao.py         # 设置 DAO
│                                # - save_settings(): 保存设置
│                                # - load_settings(): 加载设置
│
└── resources/                  # 📁 资源文件
    ├── icons/                  # 图标资源
    │   ├── app_icon.ico        # 应用图标
    │   ├── search.svg         # 搜索图标
    │   ├── file.svg           # 文件图标
    │   ├── folder.svg         # 文件夹图标
    │   └── ...
    │
    └── qss/                   # Qt 样式表
        └── main.qss           # 全局样式表
```

### 2.2 模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                            │                                 │
│              ┌─────────────┴─────────────┐                   │
│              ▼                           ▼                   │
│        MainWindow                  TrayIcon                  │
│              │                           │                   │
│    ┌────────┼────────┐                  │                   │
│    ▼        ▼        ▼                  │                   │
│ SearchBar  ResultList  PreviewPanel      │                   │
│    │        │                            │                   │
│    └────────┼────────────────────────────┘                   │
│             ▼                                                │
│      SearchEngine                                             │
│             │                                                │
│    ┌────────┼────────┬────────┐                              │
│    ▼        ▼        ▼        ▼                              │
│ NameSearcher ContentSearcher FilterEngine Indexer            │
│    │        │        │                                        │
│    │        ▼        │                                        │
│    │    FileParser   │                                        │
│    │        │        │                                        │
│    ▼        ▼        ▼                                        │
│  (utils)  (utils)  (utils)                                   │
│             │                                                │
│             ▼                                                │
│       DatabaseManager                                         │
│             │                                                │
│    ┌────────┼────────┐                                        │
│    ▼        ▼        ▼                                        │
│ HistoryDAO SettingsDAO                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型

### 3.1 核心数据模型

#### FileItem - 文件条目

```python
@dataclass
class FileItem:
    """单个文件的信息模型"""
    path: str                    # 完整文件路径
    name: str                    # 文件名（不含路径）
    extension: str                # 文件扩展名（如 '.txt'）
    size: int                    # 文件大小（字节）
    modified_time: datetime      # 修改时间
    created_time: datetime       # 创建时间
    is_directory: bool           # 是否为目录

    # 计算属性
    @property
    def size_display(self) -> str:
        """返回人类可读的文件大小"""
        # 1KB, 1MB, 1GB 等

    @property
    def modified_date(self) -> str:
        """返回格式化的修改日期"""
        # YYYY-MM-DD HH:MM

    @property
    def file_type(self) -> str:
        """返回文件类型分类"""
        # 'document', 'code', 'image', 'video', 'audio', 'archive', 'other'
```

#### SearchQuery - 搜索查询

```python
@dataclass
class SearchQuery:
    """搜索条件模型"""
    # 文件名搜索
    name_query: Optional[str]    # 文件名关键词
    name_mode: str               # 'fuzzy' | 'exact' | 'wildcard' | 'regex'
    name_case_sensitive: bool    # 是否区分大小写

    # 文件内容搜索
    content_query: Optional[str] # 内容关键词
    content_mode: str            # 'keyword' | 'regex'
    content_case_sensitive: bool # 是否区分大小写

    # 过滤条件
    file_types: List[str]        # 文件类型列表（如 ['.txt', '.md']）
    size_min: Optional[int]     # 最小文件大小（字节）
    size_max: Optional[int]     # 最大文件大小（字节）
    date_from: Optional[datetime]  # 修改日期范围起
    date_to: Optional[datetime]     # 修改日期范围止
    include_dirs: List[str]      # 搜索目录列表
    exclude_dirs: List[str]      # 排除目录列表
```

#### SearchResult - 搜索结果

```python
@dataclass
class SearchResult:
    """搜索结果模型"""
    file_item: FileItem          # 对应的文件条目
    match_reason: str            # 'name' | 'content' | 'both' 匹配原因

    # 内容匹配信息（仅内容搜索时有值）
    content_matches: List['ContentMatch'] = field(default_factory=list)

@dataclass
class ContentMatch:
    """内容匹配片段"""
    line_number: int             # 行号
    line_content: str            # 该行内容
    match_start: int             # 匹配起始位置
    match_end: int               # 匹配结束位置
    context_before: List[str]    # 前文（最多3行）
    context_after: List[str]     # 后文（最多3行）
```

#### SearchHistory - 搜索历史

```python
@dataclass
class SearchHistory:
    """搜索历史记录"""
    id: int                      # 主键
    query_text: str              # 搜索关键词（合并显示）
    name_query: Optional[str]    # 文件名搜索词
    content_query: Optional[str] # 内容搜索词
    created_at: datetime         # 搜索时间
    result_count: int            # 结果数量
```

### 3.2 数据库表设计

#### 表：search_history（搜索历史）

```sql
CREATE TABLE search_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name_query      TEXT,
    content_query   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result_count     INTEGER DEFAULT 0
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

-- 预置配置项：
-- theme: "light" | "dark" | "system"
-- search_dirs: JSON数组 ["C:\\Users\\xxx\\Documents", ...]
-- exclude_dirs: JSON数组 ["C:\\Windows", ...]
-- case_sensitive: "0" | "1"
-- max_results: "1000"
-- auto_start: "0" | "1"
-- minimize_to_tray: "0" | "1"
-- global_shortcut: "Ctrl+Alt+F"
```

#### 表：file_index_cache（文件索引缓存，可选）

```sql
CREATE TABLE file_index_cache (
    path            TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    extension       TEXT,
    size            INTEGER,
    modified_time   TIMESTAMP,
    indexed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_index_name ON file_index_cache(name);
CREATE INDEX idx_index_ext ON file_index_cache(extension);
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
        "default_dirs": ["C:\\Users\\username"],
        "exclude_dirs": [
            "C:\\Windows",
            "C:\\Program Files",
            "node_modules",
            "__pycache__",
            ".git"
        ],
        "exclude_extensions": [".dll", ".exe", ".sys"],
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

### 4.1 高性能文件内容搜索

#### 挑战

在大量文件（10 万+）中搜索内容，实时返回结果，同时不阻塞 UI。

#### 解决方案

```
┌─────────────────────────────────────────────────────────────┐
│                      搜索调度流程                             │
│                                                             │
│  1. 文件遍历                                                │
│     os.scandir() 遍历指定目录                               │
│     │                                                      │
│     ▼                                                      │
│  2. 过滤预处理                                              │
│     ├─ 跳过排除目录 (node_modules, .git)                   │
│     ├─ 跳过排除扩展名 (.dll, .exe)                          │
│     ├─ 按类型过滤（如只搜索 .txt）                          │
│     └─ 按大小过滤（跳过过大文件）                           │
│     │                                                      │
│     ▼                                                      │
│  3. 并发搜索                                                │
│     ThreadPoolExecutor(max_workers=4)                       │
│     │                                                      │
│     ├─ Worker 1: 搜索文件 1-250                             │
│     ├─ Worker 2: 搜索文件 251-500                          │
│     ├─ Worker 3: 搜索文件 501-750                           │
│     └─ Worker 4: 搜索文件 751-1000                         │
│     │                                                      │
│     ▼                                                      │
│  4. 结果收集                                                │
│     concurrent.futures.as_completed()                      │
│     │                                                      │
│     ▼                                                      │
│  5. UI 更新                                                │
│     信号槽跨线程更新                                        │
│     QMetaObject.invokeMethod() 安全调用                    │
│     分批渲染（每 50 条刷新一次）                            │
└─────────────────────────────────────────────────────────────┘
```

**关键代码片段：**

```python
# content_searcher.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QObject, pyqtSignal

class ContentSearcher(QObject):
    # 搜索进度信号
    progress_updated = pyqtSignal(int, int)  # current, total
    result_found = pyqtSignal(object)          # SearchResult
    search_completed = pyqtSignal(int)         # total results

    def search(self, query: SearchQuery, directory: str):
        """异步搜索入口"""
        # 1. 收集所有待搜索文件
        files = self._collect_files(directory, query)

        # 2. 多线程并发搜索
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(0, len(files), 100):
                batch = files[i:i+100]
                future = executor.submit(self._search_batch, batch, query)
                futures.append(future)

            # 3. 收集结果
            for future in as_completed(futures):
                results = future.result()
                for result in results:
                    self.result_found.emit(result)  # 实时推送结果

    def _search_batch(self, files: List[str], query: SearchQuery):
        """批量搜索（在线程中执行）"""
        results = []
        for file_path in files:
            if matches := self._search_file(file_path, query):
                results.append(matches)
        return results
```

### 4.2 文件编码自动检测

#### 挑战

Windows 系统文件编码多样（UTF-8、GBK、UTF-16），直接以 UTF-8 打开会乱码或报错。

#### 解决方案

```python
# encoding.py
import charset_normalizer
from typing import Optional

def detect_file_encoding(file_path: str) -> str:
    """
    自动检测文件编码
    优先级：UTF-8 > GBK > 其他
    """
    # 快速检查 BOM
    with open(file_path, 'rb') as f:
        raw = f.read(4)
        if raw.startswith(b'\xff\xfe'):
            return 'utf-16-le'
        if raw.startswith(b'\xfe\xff'):
            return 'utf-16-be'
        if raw.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'  # UTF-8 with BOM

    # 使用 charset_normalizer 检测
    try:
        result = charset_normalizer.from_path(file_path)
        best_match = result.best()
        if best_match:
            return best_match.encoding
    except Exception:
        pass

    # 默认回退
    return 'utf-8'


def read_text_file(file_path: str, max_size_mb: int = 10) -> Optional[str]:
    """安全读取文本文件"""
    import os
    if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
        return None  # 文件过大

    encoding = detect_file_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception:
        return None
```

### 4.3 多格式文档解析

#### 挑战

支持 PDF、Word、Excel 等二进制文档格式，需要专门的解析库。

#### 解决方案

```python
# file_parser.py
from abc import ABC, abstractmethod
from typing import Optional, List

class FileParser(ABC):
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """判断是否能够解析此文件"""
        pass

    @abstractmethod
    def parse(self, file_path: str) -> Optional[str]:
        """解析文件并返回文本内容"""
        pass

class TextParser(FileParser):
    """纯文本解析器"""
    def can_parse(self, file_path: str) -> bool:
        text_exts = {'.txt', '.md', '.log', '.csv', '.json', '.xml',
                     '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml',
                     '.py', '.js', '.ts', '.html', '.css', '.java',
                     '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php',
                     '.sh', '.bat', '.ps1', '.sql'}
        return Path(file_path).suffix.lower() in text_exts

    def parse(self, file_path: str) -> Optional[str]:
        return read_text_file(file_path)

class PDFParser(FileParser):
    """PDF 解析器（使用 PyMuPDF）"""
    def can_parse(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')

    def parse(self, file_path: str) -> Optional[str]:
        import fitz  # PyMuPDF
        try:
            doc = fitz.open(file_path)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return '\n'.join(text_parts)
        except Exception:
            return None

class DocxParser(FileParser):
    """Word 文档解析器"""
    def can_parse(self, file_path: str) -> bool:
        return file_path.lower().endswith('.docx')

    def parse(self, file_path: str) -> Optional[str]:
        from docx import Document
        try:
            doc = Document(file_path)
            return '\n'.join(para.text for para in doc.paragraphs)
        except Exception:
            return None

# 解析器注册表
class ParserRegistry:
    def __init__(self):
        self._parsers: List[FileParser] = [
            TextParser(),
            PDFParser(),
            DocxParser(),
            # 可扩展更多解析器
        ]

    def parse(self, file_path: str) -> Optional[str]:
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser.parse(file_path)
        return None
```

### 4.4 防抖搜索（Debounce）

#### 挑战

用户输入时实时搜索，但如果每次按键都触发搜索会导致性能浪费和 UI 卡顿。

#### 解决方案

```python
# utils/debouncer.py
from PyQt6.QtCore import QTimer, QObject

class Debouncer(QObject):
    """防抖器：延迟执行，等待用户停止输入"""

    def __init__(self, delay_ms: int = 300, parent=None):
        super().__init__(parent)
        self._delay_ms = delay_ms
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute)

    def trigger(self, callback, *args, **kwargs):
        """触发防抖"""
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        self._timer.stop()
        self._timer.start(self._delay_ms)

    def _execute(self):
        self._callback(*self._args, **self._kwargs)


# 使用示例
class SearchBar:
    def __init__(self):
        self._debouncer = Debouncer(delay_ms=300)

    def on_text_changed(self, text: str):
        # 用户输入时触发防抖
        self._debouncer.trigger(self._do_search, text)

    def _do_search(self, text: str):
        # 实际搜索逻辑（在用户停止输入 300ms 后执行）
        self.search_engine.search(text)
```

### 4.5 内容高亮显示

#### 挑战

在预览面板中显示文件内容时，需要将匹配关键词高亮显示。

#### 解决方案

```python
# utils/text_highlighter.py
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
from PyQt6.QtWidgets import QTextEdit
import re

class TextHighlighter:
    """文本内容高亮器"""

    def __init__(self, text_widget: QTextEdit):
        self._widget = text_widget
        self._keyword_format = QTextCharFormat()
        self._keyword_format.setBackground(QColor("#FFEB3B"))  # 黄色高亮

    def highlight(self, text: str, keywords: List[str]):
        """高亮显示关键词"""
        self._widget.clear()

        if not keywords:
            self._widget.setPlainText(text)
            return

        # 转义正则特殊字符
        escaped = [re.escape(k) for k in keywords]
        pattern = '|'.join(escaped)

        cursor = self._widget.textCursor()
        cursor.beginEditBlock()

        last_end = 0
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # 添加匹配前的文本
            cursor.insertText(text[last_end:match.start()])

            # 添加高亮的匹配文本
            cursor.insertText(match.group(), self._keyword_format)
            last_end = match.end()

        # 添加剩余文本
        cursor.insertText(text[last_end:])
        cursor.endEditBlock()

    def highlight_line(self, line: str, keyword: str,
                       context_before: List[str],
                       context_after: List[str]):
        """高亮显示单行及其上下文"""
        lines = []
        lines.extend(context_before)
        lines.append(line)
        lines.extend(context_after)

        result = []
        for i, l in enumerate(lines):
            prefix = "→ " if i == len(context_before) else "  "
            result.append(f"{prefix}{l}")

        self._widget.setPlainText('\n'.join(result))
```

### 4.6 系统托盘与全局快捷键

#### 挑战

实现后台常驻和全局快捷键唤起，需要系统级集成。

#### 解决方案

```python
# ui/tray_icon.py
from PyQt6.QtSystemTrayIcon import QSystemTrayIcon
from PyQt6.QtGui import QIcon, QAction, QShortcut, QKeySequence
from PyQt6.QtWidgets import QApplication, QMenu

class TrayIcon:
    def __init__(self, main_window):
        self._window = main_window

        # 创建托盘图标
        self._tray = QSystemTrayIcon()
        self._tray.setIcon(QIcon("resources/icons/app_icon.png"))
        self._tray.setToolTip("FileFinder - 文件搜索")

        # 创建右键菜单
        menu = QMenu()
        menu.addAction("打开主窗口", self._show_window)
        menu.addAction("快速搜索", self._show_and_focus)
        menu.addSeparator()
        menu.addAction("设置", self._open_settings)
        menu.addAction("退出", self._quit)
        self._tray.setContextMenu(menu)

        # 点击托盘图标显示窗口
        self._tray.activated.connect(self._on_activated)

        # 创建全局快捷键
        self._shortcut = QShortcut(
            QKeySequence("Ctrl+Alt+F"),
            QApplication.instance()
        )
        self._shortcut.activated.connect(self._show_and_focus)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()

    def _show_window(self):
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _show_and_focus(self):
        self._show_window()
        self._window.search_bar.setFocus()

    def _quit(self):
        QApplication.instance().quit()
```

### 4.7 PyInstaller 打包配置

#### 挑战

打包为单个 exe 文件时，需要包含 PyMuPDF 等有本地依赖的库。

#### 解决方案

```spec
# filefinder.spec
# PyInstaller 打包配置文件

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # 包含 PyMuPDF 的本地库
        ('C:\\Python310\\Lib\\site-packages\\fitz\\*.pyd', 'fitz'),
    ],
    datas=[
        # 包含资源文件
        ('resources/icons', 'resources/icons'),
        ('resources/qss', 'resources/qss'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'fitz',                    # PyMuPDF
        'docx',                    # python-docx
        'openpyxl',               # openpyxl
        'charset_normalizer',
    ],
    ...
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FileFinder',
    debug=False,
    bootloader_ignore_signals=False,
    console=False,               # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='resources/icons/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FileFinder',
)

# 合并为单文件
# 使用 --onefile 参数时需要：
# pyinstaller --onefile --add-data "resources;resources" main.py
```

---

## 附录

### A. 依赖清单

```
# requirements.txt
PyQt6>=6.5.0
PyMuPDF>=1.23.0
python-docx>=0.8.11
openpyxl>=3.1.0
charset-normalizer>=3.0.0
```

### B. 开发环境要求

- Python 3.10+
- Windows 10/11 (64-bit)
- 建议内存 8GB+（处理大文件时）

### C. 测试计划要点

| 测试类型 | 覆盖场景 |
|---------|---------|
| 单元测试 | 各模块函数逻辑测试 |
| 集成测试 | 搜索流程端到端测试 |
| 性能测试 | 10 万文件搜索耗时 |
| 编码测试 | GBK/UTF-8/UTF-16 文件解析 |
| 文档测试 | PDF/Word/Excel 解析准确性 |
