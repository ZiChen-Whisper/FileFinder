# FileFinder AI 开发指令

> 本文档是 FileFinder 项目开发的行为准则和操作指南，供 AI 助手在开发过程中遵循。
> 版本：v2.0 | 更新日期：2026-05-22

---

## 1. 项目概述

### 1.1 项目简介

FileFinder 是一款轻量级的本地文件搜索桌面工具，帮助用户通过**文件名**或**文件内容**快速定位电脑中的文件。

### 1.2 核心特性

| 特性 | 说明 | 状态 |
|------|------|------|
| **文件名搜索** | 模糊/精确/通配符/正则匹配 + SQLite 索引 + 内存缓存 + 评分排序 | ✅ 已实现 |
| **文件内容搜索** | 纯文本/代码文件搜索，多线程并发 | ✅ 已实现 |
| **联合搜索** | 文件名 + 内容 AND 组合搜索 | ✅ 已实现 |
| **磁盘扫描索引** | SQLite 持久化索引，一次扫描终生复用 | ✅ 已实现 |
| **文件系统监控** | QFileSystemWatcher 自动同步索引 | ✅ 已实现 |
| **内容预览 + 高亮** | 文本/代码/图片/PDF/Excel/Markdown/HTML 预览 + 搜索关键词高亮 | ✅ 已实现 |
| **结果排序** | 按相关度/名称/修改时间/大小排序 + 升降序 | ✅ 已实现 |
| **文档格式内容搜索** | PDF/Word/Excel 内容搜索（需在 file_parser.py 注册解析器） | ❌ 未实现 |
| **搜索历史 UI** | DAO 层已完成，搜索栏历史下拉未集成 | ❌ 未实现 |
| **内容正则搜索** | 文件名正则已实现，内容搜索仅支持关键词 | ❌ 未实现 |
| **高级过滤** | 文件大小/修改日期范围筛选（SearchQuery 有字段，UI 无控件） | ❌ 未实现 |
| **系统托盘** | 全局快捷键唤起，后台常驻 | ❌ P2 |

### 1.3 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| GUI 框架 | **PySide6** | 桌面应用界面（注意：非 PyQt6） |
| 编程语言 | Python 3.10+ | 后端业务逻辑 |
| 数据库 | SQLite 3 | 本地数据存储 + 内存缓存 |
| 文档预览 | PyMuPDF / openpyxl / markdown | PDF/Excel/Markdown 预览渲染 |
| 文档解析 | python-docx / python-pptx | Word/PPT 内容提取（待集成到搜索） |
| 编码检测 | charset-normalizer | 自动检测文件编码 |
| 样式系统 | style_constants.py + style_manager.py | 集中化样式令牌 + QSS 生成 |
| 打包工具 | PyInstaller | 打包为 exe |

### 1.4 相关文档

| 文档 | 用途 |
|------|------|
| RESEARCH.md | 市场调研和技术可行性分析 |
| PRD.md | 产品需求规格说明书（初期版本，部分内容已过时） |
| TECH_DESIGN.md | 技术架构和实现方案 |
| **AGENTS.md** | **开发行为准则（本文档，以本文件为准）** |
| PLAN.md | 开发步骤和里程碑（初期版本，部分内容已过时） |

---

## 2. 开发规范

### 2.1 项目结构规范

```
filefinder/
├── main.py                    # 程序入口，只做做初始化
├── config.py                  # 配置管理（JSON 文件读写 + 扫描状态管理）
├── constants.py               # 常量定义（扩展名分类、窗口尺寸、性能参数等）
├── requirements.txt           # 依赖清单
│
├── models/                    # 数据模型层
│   ├── file_item.py           # FileItem 数据类 + FILE_TYPE_MAP
│   ├── search_query.py        # SearchQuery 数据类（含大小/日期过滤字段）
│   ├── search_result.py       # SearchResult / ContentMatch 数据类
│   └── search_history.py      # SearchHistory 数据类
│
├── core/                      # 核心业务逻辑层
│   ├── name_searcher.py       # 文件名搜索（模糊/精确/通配符/正则 + 评分 + 预过滤优化）
│   ├── content_searcher.py    # 内容搜索（多线程 + 信号通知 + 取消支持）
│   ├── file_parser.py         # 文件解析（注册表模式，当前仅 TextParser）
│   └── search_engine.py       # 搜索调度引擎（联合搜索 + 排序）
│
├── ui/                        # 用户界面层
│   ├── main_window.py         # 主窗口（⚠️ 约3300行，含多个应独立的内联组件）
│   ├── style_constants.py     # 样式令牌（颜色/字号/圆角/间距/FILE_ICON_MAP）
│   ├── style_manager.py       # QSS 样式生成函数（30+ 个组件样式）
│   ├── modern_dialog.py       # 现代化对话框基类（阴影/动画/拖拽）
│   ├── widgets/
│   │   ├── search_bar.py      # 搜索栏（防抖已集成，4种匹配模式切换）
│   │   ├── result_list.py     # 结果列表（分批渲染 + 加载更多 + 拖拽）
│   │   ├── filter_bar.py      # 筛选栏（9大分类 + 子分类 + 排序）
│   │   ├── preview_panel.py   # 预览面板（⚠️ 约3300行，功能丰富）
│   │   └── rounded_menu.py    # 圆角右键菜单
│   └── dialogs/
│       └── settings_dialog.py # 设置对话框
│
├── utils/                     # 工具函数
│   ├── encoding.py            # 编码检测 + 文本文件读取
│   ├── path_helper.py         # 路径工具（规范化/二进制检测/排除判断）
│   ├── thread_helper.py       # 防抖器（Debouncer，已集成到 SearchBar）
│   └── flow_layout.py         # 流式布局（用于筛选栏标签排列）
│
├── database/                  # 数据访问层
│   ├── db_manager.py          # 数据库管理器（单例 + 内存缓存 SearchCache）
│   ├── history_dao.py         # 搜索历史 DAO（已修复连接问题）
│   └── settings_dao.py        # 设置 DAO（已修复连接问题）
│
├── data/                      # 运行时数据
│   └── filefinder.db          # SQLite 数据库
│
└── icons/                     # 图标资源
    ├── doctype/               # 文件类型图标（SVG，60+ 种）
    └── *.svg                  # UI 图标
```

### 2.2 模块职责规范

| 模块 | 职责 | 禁止事项 |
|------|------|---------|
| **models/** | 定义数据结构，不包含业务逻辑 | 不做 IO 操作 |
| **core/** | 实现搜索算法和解析逻辑 | 不直接操作 UI |
| **ui/** | 只做界面展示和用户交互 | 不直接读写数据库 |
| **ui/style_constants.py** | 集中定义所有样式令牌和图标映射 | 禁止在组件中重复定义样式常量 |
| **ui/style_manager.py** | 根据 style_constants 生成 QSS | 不硬编码颜色/字号 |
| **utils/** | 纯函数，无状态 | 不依赖业务逻辑 |
| **database/** | 数据读写，SQL 操作 | 不处理业务规则 |

### 2.3 功能实现状态

#### ✅ 已完成功能

**文件名搜索（core/name_searcher.py）：**
- [x] 模糊匹配（子串包含）
- [x] 精确匹配（完全相等）
- [x] 通配符匹配（fnmatch）
- [x] 正则匹配（re.search）
- [x] 相关度评分（精确100 > 前缀80 > 词边界60 > 子串40）
- [x] 预过滤优化（从通配符/正则中提取字面量用于 SQL 预过滤）
- [x] SQLite 索引 + 内存缓存（SearchCache）
- [x] 文件大小过滤（SearchCache 已支持 size_min/size_max）

**文件内容搜索（core/content_searcher.py）：**
- [x] 关键词搜索（大小写敏感/不敏感）
- [x] 多线程并发搜索（ThreadPoolExecutor, max_workers=4）
- [x] 搜索取消（_canceled 标志 + cancel_futures）
- [x] 上下文行提取（匹配行前后各3行）
- [x] 进度信号通知（progress_updated / result_found / search_completed）

**搜索调度（core/search_engine.py）：**
- [x] 统一搜索入口
- [x] 联合搜索（文件名 ∩ 内容 取交集）
- [x] 结果排序（按 score 降序）
- [x] 搜索取消

**磁盘扫描与索引（database/db_manager.py）：**
- [x] SQLite 持久化索引（file_index_cache 表）
- [x] 内存缓存（SearchCache，线程安全，启动时全表加载）
- [x] WAL 模式 + PRAGMA 优化（16MB 缓存 + 64MB 内存映射）
- [x] 批量写入（500条/批 commit）
- [x] 增量同步（add_file_entry / delete_file_entry / update_file_entry）
- [x] name_stem 字段迁移
- [x] 文件系统监控（QFileSystemWatcher + 增量同步）

**UI 组件：**
- [x] 主窗口布局（QStackedWidget 管理欢迎页/扫描页/搜索页）
- [x] 搜索栏（双输入框 + 4种匹配模式切换 + 大小写复选框 + 防抖器）
- [x] 结果列表（自定义 ResultItemWidget + SVG 图标 + 分批渲染 + 加载更多）
- [x] 筛选栏（9大分类 + 子分类滑块 + 排序方式 + 升降序）
- [x] 预览面板（文本/代码/图片/PDF/Excel/Markdown/HTML/视频/音频/压缩包/文件夹）
- [x] 搜索关键词高亮（preview_panel.py 中 _highlight_matches）
- [x] 代码语法高亮（Python/JS/Markdown/JSON/通用代码）
- [x] 圆角右键菜单（打开/复制/复制路径/属性）
- [x] 拖拽文件（自定义拖拽 pixmap）
- [x] 欢迎页 + 扫描进度
- [x] 搜索范围选择（树形目录选择器）
- [x] 加载动画（旋转点动画）
- [x] 集中化样式系统（style_constants.py 令牌 + style_manager.py QSS 生成）
- [x] 现代化对话框基类（modern_dialog.py，阴影/动画/拖拽）
- [x] FILE_ICON_MAP 集中定义（style_constants.py，不再重复）

**数据层：**
- [x] 搜索历史 DAO（add / get / delete / clear）
- [x] 设置 DAO（save / load / dict 批量操作）
- [x] 配置管理（config.py，JSON 文件读写 + 扫描状态管理）

**工具函数：**
- [x] 编码检测（BOM + charset_normalizer）
- [x] 文本文件读取（大小限制 + 编码检测 + errors='replace'）
- [x] 二进制文件检测（空字节 + 非文本字符判断，已修复）
- [x] 防抖器（Debouncer，QTimer 实现，已集成到 SearchBar）
- [x] 流式布局（FlowLayout，用于筛选栏标签排列）

#### ❌ 未完成功能

**P1 增强功能（当前阶段）：**

| 功能 | 说明 | 涉及文件 | 备注 |
|------|------|---------|------|
| PDF 内容搜索 | 在 file_parser.py 中实现 PDFParser，注册到 ParserRegistry | `core/file_parser.py` | 预览已支持 PDF，但搜索内容时无法解析 |
| Word 内容搜索 | 在 file_parser.py 中实现 DocxParser | `core/file_parser.py` | python-docx 已在依赖中 |
| Excel 内容搜索 | 在 file_parser.py 中实现 XlsxParser | `core/file_parser.py` | 预览已支持 Excel，但搜索内容时无法解析 |
| Word 文档预览 | 在 preview_panel.py 中添加 Word 预览方法 | `ui/widgets/preview_panel.py` | python-docx 已在依赖中 |
| 搜索历史 UI | 搜索栏历史下拉列表 + 自动保存 + 删除/清空 | `ui/widgets/search_bar.py`, `ui/main_window.py` | DAO 层已完成 |
| 内容正则搜索 | content_searcher.py 支持 content_mode='regex' | `core/content_searcher.py` | 文件名正则已实现 |
| 文件大小过滤 UI | 在筛选栏添加大小范围控件 | `ui/widgets/filter_bar.py` | SearchQuery 已有 size_min/size_max 字段 |
| 修改日期过滤 | SearchCache.search() 处理 date_from/date_to + UI 控件 | `database/db_manager.py`, `ui/widgets/filter_bar.py` | SearchQuery 已有字段但未使用 |

**P1 代码重构（高优先级）：**

| 任务 | 说明 | 涉及文件 |
|------|------|---------|
| 拆分 main_window.py | 约3300行含15个类，需提取 ScanWorker/SearchWorker/WelcomePage/ScanProgressDialog/SearchScopePanel 等为独立模块 | `ui/main_window.py` |
| 提取重复的 _ModernMessageBox | main_window.py / filter_bar.py / settings_dialog.py 各有一份几乎相同的实现 | 多个文件 |
| 提取重复的 AnimatedRadioButton | main_window.py / search_bar.py / filter_bar.py 各有一份 | 多个文件 |
| 设置对话框持久化 | SettingsDialog 的控件值变化后未保存到数据库或配置文件 | `ui/dialogs/settings_dialog.py` |

**P2 完善功能：**

- [ ] 系统托盘 + 全局快捷键
- [ ] 主题切换（浅色/深色/跟随系统）
- [ ] 窗口位置记忆
- [ ] 全文索引（倒排索引，借鉴 AnyTXT）
- [ ] mmap 流式搜索（借鉴 AnyTXT）
- [ ] 搜索性能优化
- [ ] PPT 内容搜索 + 预览
- [ ] 打包发布（PyInstaller）

**P1 阶段禁止添加的功能：**
- 系统托盘（P2）
- 全局快捷键（P2）
- 倒排索引（P2）
- mmap 流式搜索（P2）

### 2.4 配置管理规范

**所有可配置项必须写入 `config.py`、`constants.py` 或 `style_constants.py`，禁止硬编码：**

```python
# ✅ 正确：在 config.py 中定义
DEFAULT_EXCLUDE_DIRS = ['node_modules', '__pycache__', '.git', '.venv']
MAX_SEARCH_RESULTS = 1000
CONTENT_MAX_FILE_SIZE_MB = 10

# ✅ 正确：在 constants.py 中定义
TEXT_EXTENSIONS = {'.txt', '.md', '.log', ...}
CODE_EXTENSIONS = {'.py', '.js', '.ts', ...}
SEARCH_DEBOUNCE_MS = 300
MAX_WORKERS = 4
BATCH_SIZE = 500

# ✅ 正确：在 style_constants.py 中定义
FILE_ICON_MAP = {'.py': 'python', '.js': 'javascript', ...}

# ❌ 错误：在业务代码中硬编码
if directory not in ['node_modules', '__pycache__']:  # 硬编码
```

**样式管理规范：**
- 所有颜色、字号、圆角、间距等视觉参数必须定义在 `style_constants.py` 的令牌类中
- 所有 QSS 样式字符串必须通过 `style_manager.py` 的函数生成，引用令牌而非硬编码
- 修改视觉样式时只改 `style_constants.py`，组件自动更新

---

## 3. 代码风格

### 3.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `FileItem`, `SearchResult` |
| 函数名 | snake_case | `search_by_name()`, `parse_file()` |
| 变量名 | snake_case | `file_path`, `result_list` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RESULTS`, `DEFAULT_DIRS` |
| 私有属性 | `_前缀 + snake_case` | `_search_engine`, `_config` |
| 文件名 | snake_case.py | `file_parser.py`, `name_searcher.py` |
| Qt Signal | snake_case | `result_found`, `search_completed` |
| 样式令牌类 | PascalCase + Tokens 后缀 | `ColorTokens`, `FontTokens` |

### 3.2 函数设计规范

**每个函数必须：**
1. 有清晰的函数名（动宾结构，如 `search_files`, `parse_content`）
2. 有类型注解（参数和返回值）
3. 有文档字符串（说明功能和参数）

```python
# ✅ 正确：有类型注解和文档字符串
def search_by_name(directory: str, pattern: str) -> List[FileItem]:
    """
    在指定目录中按文件名搜索。

    Args:
        directory: 要搜索的目录路径
        pattern: 搜索模式（支持通配符）

    Returns:
        匹配的文件列表
    """
    pass

# ❌ 错误：无类型注解、无文档、命名模糊
def search(d, p):
    pass
```

### 3.3 数据类规范

**使用 `@dataclass` 定义数据模型：**

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class FileItem:
    """单个文件的信息模型"""
    path: str
    name: str
    size: int
    modified_time: datetime
    extension: str = ""                          # 有默认值放最后
    content_matches: List[str] = field(default_factory=list)  # 可变默认用 field

    @property
    def size_display(self) -> str:
        """返回人类可读的文件大小"""
        if self.size < 1024:
            return f"{self.size}B"
        # ...
```

### 3.4 异常处理规范

**异常处理遵循最小暴露原则：**

```python
# ✅ 正确：记录异常，不泄露敏感信息
import logging

logger = logging.getLogger(__name__)

def parse_file(file_path: str) -> Optional[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"文件不存在: {file_path}")
        return None
    except PermissionError:
        logger.warning(f"无权限读取: {file_path}")
        return None
    except Exception as e:
        logger.error(f"解析文件失败: {file_path}, {type(e).__name__}")
        return None

# ❌ 错误：向上抛出未处理异常
def parse_file(file_path: str):
    with open(file_path, 'r') as f:  # 可能抛出各种异常
        return f.read()  # 让异常传播
```

### 3.5 日志规范

**使用 Python 标准库 logging：**

```python
import logging

# 在模块顶部定义 logger
logger = logging.getLogger(__name__)

# 日志级别使用规范
logger.debug("调试信息：正在遍历目录")
logger.info("搜索完成，找到 %d 个结果", count)
logger.warning("文件过大，跳过: %s", path)
logger.error("解析失败: %s", path, exc_info=True)  # 记录堆栈
```

### 3.6 PySide6 特有规范

**注意：本项目使用 PySide6，而非 PyQt6，API 差异需注意：**

| 差异点 | PyQt6 | PySide6 |
|--------|-------|---------|
| 信号定义 | `pyqtSignal` | `Signal` |
| 槽装饰器 | `@pyqtSlot` | `@Slot` |
| 导入路径 | `from PyQt6.QtCore import ...` | `from PySide6.QtCore import ...` |
| 枚举访问 | `Qt.AlignmentFlag.AlignLeft` | `Qt.AlignmentFlag.AlignLeft` |

---

## 4. 测试要求

### 4.1 测试策略

| 阶段 | 测试方式 | 覆盖要求 |
|------|---------|---------|
| 开发中 | 手动测试 | 每个函数写完后测试核心逻辑 |
| 完成后 | 集成测试 | 完整搜索流程端到端 |
| 发布前 | 回归测试 | 确保新功能不破坏已有功能 |

**当前状态：项目没有任何自动化测试文件，全部依赖手动测试。**

### 4.2 手动测试清单

#### 文件名搜索测试

| 用例 | 操作步骤 | 预期结果 |
|------|---------|---------|
| 模糊匹配 | 搜索 `readme` | 返回所有包含 `readme` 的文件 |
| 精确匹配 | 切换到精确模式，搜索 `main.py` | 只返回 `main.py` |
| 通配符匹配 | 切换到通配符模式，搜索 `*.py` | 返回所有 .py 文件 |
| 正则匹配 | 切换到正则模式，搜索 `test_\d+` | 返回匹配正则的文件 |
| 无结果 | 搜索不存在的文件名 | 显示「未找到匹配文件」 |

#### 内容搜索测试

| 用例 | 操作步骤 | 预期结果 |
|------|---------|---------|
| 纯文本搜索 | 搜索 `def main` | 返回包含该文本的所有 .py 文件 |
| 大小写不敏感 | 搜索 `HELLO` | 匹配 `hello`, `Hello`, `HELLO` |
| 大小写敏感 | 勾选「区分大小写」，搜索 `HELLO` | 只匹配 `HELLO` |
| 二进制跳过 | 搜索包含在 .dll 中的文本 | 自动跳过，不报错 |

#### 预览面板测试

| 用例 | 操作步骤 | 预期结果 |
|------|---------|---------|
| 文本预览 | 选中 .txt/.py 文件 | 显示文件内容 + 语法高亮 |
| 搜索高亮 | 内容搜索后选中结果 | 预览中高亮匹配关键词 |
| PDF 预览 | 选中 .pdf 文件 | 渲染 PDF 页面，支持缩放 |
| Excel 预览 | 选中 .xlsx 文件 | 显示表格内容，支持 Sheet 切换 |
| 图片预览 | 选中 .png/.jpg 文件 | 显示图片，支持缩放和拖拽 |
| Markdown 预览 | 选中 .md 文件 | 渲染 Markdown，支持预览/源码切换 |

#### 编码测试

| 用例 | 操作步骤 | 预期结果 |
|------|---------|---------|
| UTF-8 文件 | 搜索 UTF-8 编码的中文文件 | 正常匹配 |
| GBK 文件 | 搜索 GBK 编码的中文文件 | 正常匹配 |
| 混合编码目录 | 在混合编码的目录下搜索 | 都能正确解析 |

#### 性能测试

| 用例 | 操作步骤 | 预期结果 |
|------|---------|---------|
| 响应速度 | 在 10 万文件目录下搜索 | 响应时间 ≤ 3 秒 |
| UI 响应 | 搜索过程中点击界面 | 界面不卡顿，可取消搜索 |
| 内存占用 | 搜索完成后 | 内存占用 ≤ 200MB |
| 分批渲染 | 搜索返回大量结果 | 初始显示200条，底部"加载更多" |

### 4.3 边界情况测试

**必须测试以下边界情况：**

1. 空目录搜索
2. 权限不足的目录
3. 文件名含特殊字符（如 `test[1].txt`）
4. 超长路径（>260 字符，Windows 限制）
5. 符号链接/快捷方式
6. 网络路径（UNC 路径 `\\server\share`）
7. 大文件（接近内存限制，50MB+）
8. 正在被其他程序写入的文件
9. 搜索过程中目录结构变化
10. 搜索被中断（强制关闭文件句柄）

### 4.4 测试数据准备

**在开发目录下准备测试文件：**

```
test_data/
├── text/
│   ├── ascii.txt
│   ├── gbk.txt
│   ├── utf8-bom.txt
│   └── chinese.md
├── code/
│   ├── main.py
│   ├── utils.py
│   └── test.js
├── documents/
│   ├── sample.pdf
│   ├── sample.docx
│   └── sample.xlsx
├── special/
│   ├── file[1].txt     # 含特殊字符
│   └── 文件名中文.txt   # 中文文件名
└── large/
    └── largefile.txt  # 50MB+ 大文件
```

---

## 5. 注意事项

### 5.1 开发原则

| 原则 | 说明 | 优先级 |
|------|------|--------|
| **先跑通，再优化** | MVP 优先，确保功能可用后再考虑性能 | ⭐⭐⭐⭐⭐ |
| **保持简单** | 避免过度设计和过度抽象 | ⭐⭐⭐⭐⭐ |
| **增量开发** | 每个功能独立开发、独立测试 | ⭐⭐⭐⭐ |
| **最小依赖** | 优先使用标准库，减少外部依赖 | ⭐⭐⭐⭐ |
| **本地优先** | 所有数据存储在本地，不上传网络 | ⭐⭐⭐⭐⭐ |
| **样式集中管理** | 所有视觉参数通过 style_constants.py 令牌管理，禁止组件内硬编码 | ⭐⭐⭐⭐ |

### 5.2 性能注意事项

**必须遵守的性能约束：**

| 指标 | 限制 | 超出处理 |
|------|------|---------|
| 单文件大小 | 10MB | 跳过内容搜索 |
| 结果数量 | 1000 条 | 截断返回 |
| 搜索防抖 | 300ms | 延迟执行 |
| 线程数 | 4 个 | 限制并发 |
| 内存占用 | 200MB | 释放缓存 |
| 批量写入 | 500 条/批 | 数据库批量 commit |
| 分批渲染 | 50 条/批 | UI 分批添加结果项 |
| 初始显示 | 200 条 | 结果列表初始显示条数 |

**禁止在主线程执行耗时操作：**

```python
# ❌ 错误：在主线程（UI 线程）执行文件遍历
def search():
    for root, dirs, files in os.walk(directory):  # 可能阻塞很久
        process_files(files)

# ✅ 正确：使用 QThread 或 ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor
def search_async():
    with ThreadPoolExecutor() as executor:
        executor.submit(self._do_search)
```

**内容搜索性能优化方向（借鉴 AnyTXT Searcher）：**

| 优化方向 | 说明 | 阶段 |
|---------|------|------|
| mmap 流式搜索 | 使用 `mmap.mmap()` 替代 `open().read()`，大文件边读边搜 | P2 |
| 倒排索引 | 构建词项→文件映射，搜索复杂度从 O(N) 降为 O(1) | P2 |
| 增量索引 | 文件变化时只更新差异部分，避免全量重建 | 已部分实现 |
| 分块读取 | 大文件分块读取，避免一次性加载到内存 | P2 |
| 结果分批渲染 | 搜索结果分批加载到 UI，避免一次性渲染大量数据 | ✅ 已实现 |

### 5.3 安全注意事项

| 注意事项 | 说明 |
|---------|------|
| **禁止网络请求** | 程序不发起任何 HTTP/TCP 请求 |
| **禁止数据外传** | 不上传任何用户数据到外部 |
| **路径安全** | 使用 `pathlib` 处理路径，防止路径遍历攻击 |
| **命令注入** | 不使用 `os.system` 或 `subprocess` 执行用户输入 |
| **文件访问限制** | 尊重系统权限，权限不足时跳过而非报错 |

```python
# ✅ 安全：使用 pathlib
from pathlib import Path
def safe_resolve(path: str) -> Path:
    base = Path(directory).resolve()
    target = (base / path).resolve()
    if not target.is_relative_to(base):
        raise ValueError("路径越界")  # 防止 ../ 攻击
    return target
```

### 5.4 用户体验注意事项

| 注意事项 | 说明 | 状态 |
|---------|------|------|
| **即时反馈** | 搜索开始时显示加载状态 | ✅ |
| **可中断** | 用户可随时取消正在进行的搜索 | ✅ |
| **错误友好** | 出错时显示友好提示，不显示技术堆栈 | ✅ |
| **状态可见** | 状态栏显示索引状态、搜索耗时 | ✅ |
| **分批渲染** | 大量结果分批加载，避免界面卡顿 | ✅ |
| **窗口记忆** | 记住窗口大小和位置，下次启动恢复 | ❌ P2 |

### 5.5 兼容性注意事项

| 平台 | 注意事项 |
|------|---------|
| **Windows 10** | 路径分隔符用 `\` 或 `pathlib` 自动处理 |
| **Windows 11** | 注意长路径支持（需管理员权限启用） |
| **高 DPI** | 使用 Qt 的高 DPI 支持，不硬编码像素值 |
| **深色模式** | 支持系统主题切换，UI 样式自适应（P2） |

### 5.6 常见错误避免

| 错误 | 错误原因 | 正确做法 |
|------|---------|---------|
| 编码错误 | 用 UTF-8 硬编码打开 GBK 文件 | 用 `charset_normalizer` 检测 |
| 内存爆炸 | 一次性加载大文件到内存 | 分块读取，设置大小限制 |
| 线程冲突 | 多线程同时写 UI | 用信号槽跨线程更新 |
| 路径错误 | 硬编码分隔符 | 用 `pathlib` 或 `os.path.join` |
| 资源泄漏 | 打开文件未关闭 | 使用 `with` 语句 |
| 竞态条件 | 搜索过程中目录变化 | 使用文件锁或快照 |
| GUI 框架混淆 | 使用 PyQt6 的 API | 本项目使用 **PySide6**，注意 Signal/Slot 差异 |
| 样式硬编码 | 在组件中直接写颜色/字号 | 使用 `style_constants.py` 令牌 + `style_manager.py` 生成 |
| 组件重复定义 | 多个文件中复制粘贴相同组件 | 提取为公共模块，统一导入 |

### 5.7 已知 Bug 与技术债务

**开发时必须注意的已知问题：**

| 问题 | 位置 | 说明 | 优先级 |
|------|------|------|--------|
| `main_window.py` 过于臃肿 | `ui/main_window.py`（~3300行，15个类） | 包含 ScanWorker/SearchWorker/WelcomePage/ScanProgressDialog/SearchScopePanel 等应独立的组件 | 🔴 高 |
| `_ModernMessageBox` 重复3次 | main_window.py / filter_bar.py / settings_dialog.py | 几乎相同的实现，应提取为公共组件 | 🟡 中 |
| `AnimatedRadioButton` 重复3次 | main_window.py / search_bar.py / filter_bar.py | 几乎相同的实现，应提取为公共组件 | 🟡 中 |
| 设置对话框未持久化 | `ui/dialogs/settings_dialog.py` | 控件值变化后未保存到数据库或配置文件 | 🟡 中 |
| PDF/Word/Excel 内容搜索未实现 | `core/file_parser.py` | ParserRegistry 中只有 TextParser，搜索时无法解析文档格式 | 🔴 高 |
| Word 文档预览未实现 | `ui/widgets/preview_panel.py` | python-docx 已在依赖中但无预览方法 | 🟠 高 |
| 内容搜索不支持正则 | `core/content_searcher.py` | 使用 `re.escape(pattern)` 强制转义，content_mode 字段未使用 | 🟡 中 |
| 日期范围过滤未实现 | `database/db_manager.py` SearchCache | SearchQuery 有 date_from/to 字段但 SearchCache.search() 未处理 | 🟡 中 |
| 文件大小过滤 UI 未实现 | `ui/widgets/filter_bar.py` | SearchQuery 有 size_min/size_max 字段但 UI 无控件 | 🟡 中 |
| 搜索历史 UI 未集成 | `ui/widgets/search_bar.py` | DAO 层功能完整但搜索栏无历史下拉框 | 🟡 中 |
| history_dao / settings_dao 访问私有方法 | `database/history_dao.py`, `database/settings_dao.py` | 使用 `db._get_conn()` 访问私有方法获取连接，功能可用但不规范 | 🟢 低 |

**已修复的旧 Bug（无需再处理）：**

| 问题 | 位置 | 修复说明 |
|------|------|---------|
| ~~`history_dao.py` 调用不存在的方法~~ | `database/history_dao.py` | 已改为 `db._get_conn()` |
| ~~`settings_dao.py` 同上~~ | `database/settings_dao.py` | 已改为 `db._get_conn()` |
| ~~`is_binary_file()` 逻辑反转~~ | `utils/path_helper.py` | 已修复，当前逻辑正确 |
| ~~`FILE_ICON_MAP` 重复定义~~ | result_list.py + preview_panel.py | 已集中定义在 `style_constants.py` |
| ~~Debouncer 未集成~~ | `ui/widgets/search_bar.py` | 已集成到 SearchBar |

---

## 附录

### A. 快速开发检查清单

每次提交代码前检查：

- [ ] 代码符合命名规范（类名、函数名、常量）
- [ ] 所有函数有类型注解
- [ ] 异常已捕获，有友好提示
- [ ] 没有硬编码的可配置项
- [ ] 没有硬编码的样式值（颜色/字号/圆角等必须用 style_constants 令牌）
- [ ] 搜索功能在 UI 线程外执行
- [ ] 手动测试核心用例通过
- [ ] 日志级别使用正确
- [ ] 无网络请求代码
- [ ] 使用 PySide6 而非 PyQt6 的 API
- [ ] 没有重复定义的组件（如 _ModernMessageBox、AnimatedRadioButton）

### B. 调试技巧

| 问题 | 调试方法 |
|------|---------|
| 搜索结果不对 | 在 `search_by_name()` 中添加 `logger.debug` 打印匹配逻辑 |
| 文件打不开 | 检查文件路径是否正确，权限是否足够 |
| UI 卡顿 | 使用 `QThread` 或 `ThreadPoolExecutor` 移出主线程 |
| 编码乱码 | 使用 `encoding.py` 中的 `detect_file_encoding()` 检测 |
| 内存占用高 | 检查是否有大文件被一次性加载，添加大小限制 |
| 数据库操作失败 | 检查 `DatabaseManager` 单例是否正确初始化 |
| 样式不生效 | 检查是否使用了 style_constants 令牌而非硬编码值 |
| 预览面板异常 | 检查对应文件解析器是否正确注册 |

### C. 参考资源

| 资源 | 链接 |
|------|------|
| PySide6 文档 | https://doc.qt.io/qtforpython-6/ |
| Python 编码指南 | PEP 8 - https://pep8.org/ |
| PyInstaller 文档 | https://pyinstaller.org/en/stable/ |
| charset-normalizer | https://charset-normalizer.readthedocs.io/ |
| PyMuPDF (fitz) | https://pymupdf.readthedocs.io/ |
| python-docx | https://python-docx.readthedocs.io/ |
| openpyxl | https://openpyxl.readthedocs.io/ |
| AnyTXT Searcher | https://anytxt.net/ （全文索引设计参考） |
