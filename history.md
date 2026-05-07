# FileFinder 开发历史记录

---

## [架构重构：Everything 风格全盘索引 + 10项改进] - 2026-05-07

### 架构变更：从 os.walk 实时遍历 → SQLite 持久化索引

| 旧架构 | 新架构 |
|--------|--------|
| 每次搜索用 `os.walk` 遍历目录 | 一次扫描写入 SQLite，搜索直接查表 |
| 搜索可能耗时数分钟 | 搜索毫秒级完成 |
| 用户输入即触发搜索（容易卡死） | 按回车/按钮触发，后台线程 |
| 每次启动重新遍历 | 一次扫描终生复用（Everything 方式） |

### 完成的 10 项改进

| # | 任务 | 实现 |
|---|------|------|
| 1 | 修复报错 | 移除 deadlock 来源：deboucer + QThread 复用问题 |
| 2 | 修复搜索卡住 | SQLite 索引替代 os.walk，搜索永不阻塞 UI |
| 3 | 文件类型 SVG 图标 | `FILE_ICON_MAP` 映射 70+ 扩展名到 `icons/doctype/*.svg` |
| 4 | 预扫描 + 进度条 | `ScanWorker(QThread)` + `QProgressBar`，实时显示扫描文件数 |
| 5 | 取消实时搜索 | 移除 `textChanged→debouncer`，仅保留 `returnPressed` + 按钮 `clicked` |
| 6 | 右键菜单 | `📂 打开` / `📁 打开文件所在目录` / `📋 复制完整路径和文件名` |
| 7 | 选中效果 + 状态栏 | 紫色边框高亮 `#F5F3FF` + `border: 2px solid #7C3AED`；状态栏显示大小/日期/路径 |
| 8 | 文件拖拽复制 | `QDrag` + `QMimeData(QUrl)` + `Qt.CopyAction`（复制非移动）|
| 9 | 滚动条美化 | 6px 细条、圆角 `#D1D5DB`、hover `#9CA3AF` |
| 10 | 持久化索引 | `file_index_cache` 表 + 批量写入(500条) + 启动自动加载 |

### 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| database/db_manager.py | 重写 | 新增 `file_index_cache` 表(带索引)、`insert_file_batch()`、`search_files()` |
| core/name_searcher.py | 重写 | 从 `db.search_files()` 查询而非 `os.walk`；`_row_to_file_item()` 转换 |
| core/search_engine.py | 重写 | 简化：移除路径展开，直接调用 `search_by_name(query)` |
| core/__init__.py | 修改 | 导出 `get_index_count` |
| ui/widgets/search_bar.py | 重写 | 移除 debouncer/实时搜索；添加紫色搜索按钮；仅回车/点击触发 |
| ui/widgets/result_list.py | 重写 | 自定义 `ResultItemWidget(QFrame)`；SVG图标；选中高亮；右键菜单；拖拽 |
| ui/widgets/filter_bar.py | 重写 | 添加 `🔄 扫描索引` 按钮；`QProgressBar`；`ScanWorker` 线程 |
| ui/main_window.py | 重写 | `ScanWorker` + `SearchWorker`(QThread)；状态栏文件详情；启动索引检查 |
| plan.md | 更新 | 新增 2.8、4.7-4.10、更新 9.4、11.1-11.4 |
| history.md | 更新 | 本文档 |

### 关键设计决策

**索引排除策略（参考 Everything 默认排除项）：**
```
排除目录：node_modules, __pycache__, .git, .svn, .hg, .venv, venv,
          .tox, .eggs, build, dist, .idea, .vscode, .vs,
          $RECYCLE.BIN, System Volume Information, Windows,
          Program Files, Program Files (x86), ProgramData
```

**SQLite 性能优化：**
- 表上创建 4 个索引：`name`、`extension`、`size`、`modified_time`
- 批量写入：每 500 条 commit 一次
- 搜索使用 `LIKE` + `LIMIT`，结果在 Python 层做精确/通配符二次过滤

**图标映射体系：**
- `code.svg` → .py .js .ts .java .c .cpp .go .rs .rb .php .html .css .sql .sh .bat .ps1
- `TXT.svg` → .txt .md .log .json .xml .csv .yaml .ini .cfg .conf .toml
- `PDF.svg` → .pdf
- `Doc.svg` → .doc .docx
- `Excel.svg` → .xls .xlsx
- `PPT.svg` → .ppt .pptx
- `Gif.svg` → .gif
- `Mp3.svg` → .mp3
- `Wav.svg` → .wav .flac .aac
- `Mov.svg` → .mov .mp4 .avi .mkv
- `Zip.svg` → .zip .rar .7z .tar .gz
- `图片.svg` → .jpg .jpeg .png .bmp .tiff .ico
- 其他专业格式：`Ai.svg`, `Ps.svg`, `Ae.svg`, `Pr.svg`, `Xd.svg`, `Rp.svg`, `Swf.svg`, `Svg.svg`, `图书.svg`, `思维导图.svg`

---

## [BUG修复：搜索不到文件问题 + 全盘搜索功能] - 2026-05-07

### 问题诊断

搜索调用链中发现 4 个导致"根本搜不到文件"的核心问题：

| 问题 | 位置 | 原因 |
|------|------|------|
| `'~'` 不展开 | search_engine.py:L22 | `query.include_dirs = ['~']` 传递给 `os.walk` 时不会自动展开为用户目录 |
| 路径不规范化 | name_searcher.py | `search_by_name` 未调用 `normalize_path`，未检查目录存在性 |
| 默认只搜用户目录 | config.py | `get_default_search_dirs()` 只返回 `~`，不像 Everything 扫描所有驱动器 |
| UI 无搜索范围 | main_window.py | 用户无法查看或配置搜索范围 |

### 修复内容

| 文件 | 操作 | 说明 |
|------|------|------|
| core/search_engine.py | 修改 | 修复 `'~'` 展开问题：使用 `normalize_path` + `get_all_drives()` 替代硬编码 `'~'` |
| core/name_searcher.py | 修改 | 添加 `normalize_path(directory)` 路径规范化；添加 `os.path.isdir` 检查 |
| utils/path_helper.py | 修改 | 新增 `get_all_drives()` 和 `get_user_directories()` 函数 |
| utils/__init__.py | 修改 | 导出 `get_all_drives`, `get_user_directories` |
| config.py | 修改 | `get_default_search_dirs()` 默认返回所有驱动器 |
| ui/widgets/filter_bar.py | 重构 | 新增搜索范围配置功能：`SearchScopeDialog` 对话框 + `⚙ 配置范围` 按钮 |
| ui/main_window.py | 修改 | `_on_search` 使用 `filter_bar.get_search_dirs()` 替代 `get_default_search_dirs()` |

### 技术实现要点

**全盘搜索（参考 Everything 实现方式）：**
- `get_all_drives()` 遍历 `A:\` 到 `Z:\`，用 `os.path.exists()` 检测可用驱动器
- 首次启动默认搜索所有驱动器（Everything 行为）
- 用户可通过"⚙ 配置范围"按钮自定义搜索范围
- 支持快速添加：所有驱动器 / 常用目录（桌面、文档、下载）
- 配置持久化到 `~/.filefinder/config.json`

**SearchScopeDialog 功能：**
- 列表展示当前搜索目录
- 支持手动输入路径或浏览选择
- 一键添加所有驱动器
- 一键添加常用目录
- 移除不需要的目录
- 点击确定后自动保存到配置文件

---

## [阶段 2：文件名搜索（P0核心）] - 2026-05-07

### 完成的任务

| 序号 | 任务 | 说明 |
|------|------|------|
| 2.1 | 实现模糊匹配算法 | `fuzzy_match()`，支持大小写不敏感的子串匹配 |
| 2.2 | 实现通配符匹配 | `wildcard_match()`，基于 `fnmatch`，支持 `*` 和 `?` |
| 2.3 | 实现精确匹配 | 在 `search_by_name()` 中支持 `exact` 模式，完整名称匹配 |
| 2.4 | 目录遍历与排除 | `os.walk` 遍历 + `is_excluded_directory` 排除 node_modules/.git 等 |
| 2.5 | 搜索结果排序 | 实现 `_calculate_name_relevance()` 相关性评分，按精确>前缀>边界>包含四级排序 |

### 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| core/name_searcher.py | 修改 | 新增 `_calculate_name_relevance()` 评分函数；`search_by_name()` 返回带评分的元组并降序排序 |
| models/search_result.py | 修改 | 新增 `name_match_score` 字段；`score` 属性支持文件名相关性加权 |
| core/search_engine.py | 修改 | `search()` 适配 `search_by_name` 新返回值，传递 `name_match_score` 到 `SearchResult` |

### 技术实现要点

**相关性评分四级体系：**
- 精确匹配（name == pattern）：100 + 模式长度
- 前缀匹配（name.startswith）：80 + 模式长度
- 单词边界匹配（_ - . 或驼峰切换后）：60 + 模式长度
- 包含匹配（任意位置）：40 + 模式长度
- 模式长度加成确保更具体的关键词获得更高分

**排序集成：**
- `search_by_name` 内部按评分降序排列，返回 `List[Tuple[int, FileItem]]`
- `SearchEngine.search()` 创建 `SearchResult` 时传入 `name_match_score`
- `SearchResult.score` 将 `name_match_score * 10` 作为评分因子
- 最终结果按综合评分降序排列

---

## [阶段 1：基础架构搭建] - 2026-05-07

### 完成的任务

| 序号 | 任务 | 说明 |
|------|------|------|
| 1.1 | 创建项目目录结构 | 建立 models/、core/、ui/、utils/、database/ 目录 |
| 1.2 | 配置开发环境 | 创建 requirements.txt，包含 PySide6、PyMuPDF、python-docx、openpyxl、charset-normalizer 等依赖 |
| 1.3 | 创建配置管理 | 实现 config.py，包含默认配置、配置加载/保存、深度合并等功能 |
| 1.4 | 创建数据模型 | 实现 FileItem、SearchQuery、SearchResult 三个核心数据类 |

### 新增文件

```
filefinder/
├── config.py                    # 配置管理模块
├── constants.py                 # 常量定义
├── requirements.txt             # 依赖清单
│
├── models/                      # 数据模型层
│   ├── __init__.py
│   ├── file_item.py             # FileItem 数据类
│   ├── search_query.py          # SearchQuery 数据类
│   ├── search_result.py         # SearchResult 数据类
│   └── search_history.py        # SearchHistory 数据类
│
├── core/                        # 核心业务逻辑层
│   ├── __init__.py
│   ├── name_searcher.py         # 文件名搜索器
│   ├── content_searcher.py      # 内容搜索器
│   ├── file_parser.py           # 文件解析器
│   └── search_engine.py         # 搜索引擎调度
│
├── ui/                          # 用户界面层
│   ├── __init__.py
│   ├── main_window.py           # 主窗口
│   └── widgets/                 # UI 组件
│       ├── __init__.py
│       ├── search_bar.py        # 搜索栏
│       ├── result_list.py       # 结果列表
│       ├── preview_panel.py     # 预览面板
│       └── filter_bar.py        # 过滤栏
│
├── utils/                       # 工具函数层
│   ├── __init__.py
│   ├── encoding.py              # 编码检测
│   ├── path_helper.py           # 路径工具
│   └── thread_helper.py         # 线程工具
│
└── database/                    # 数据访问层
    ├── __init__.py
    ├── db_manager.py            # 数据库管理器
    ├── settings_dao.py          # 设置数据访问
    └── history_dao.py           # 历史记录数据访问
```
