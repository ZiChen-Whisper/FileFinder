# 文件内容搜索功能实现计划

## 概述

实现纯文本/代码文件和 PDF 文件的内容搜索功能，并在预览面板中实现搜索关键词高亮显示和匹配结果跳转（上一个/下一个）。**不修改文件名搜索相关逻辑。**

## 当前状态分析

### 已有的基础设施
- `core/file_parser.py`：注册表模式（ParserRegistry），当前仅有 TextParser
- `core/content_searcher.py`：多线程内容搜索，关键词匹配，信号通知
- `core/search_engine.py`：搜索调度，支持联合搜索（文件名 ∩ 内容）
- `models/search_result.py`：ContentMatch 数据类（line_number, match_start, match_end 等）
- `ui/widgets/preview_panel.py`：文本/PDF/Word 等多种格式预览
- `requirements.txt`：PyMuPDF (fitz) 已在依赖中

### 需要修复的阻断问题
1. **`ui/main_window.py` 第 604-612 行**：纯内容搜索被拦截，显示"即将上线"提示
2. **`core/content_searcher.py` 第 44-47 行**：`_collect_files` 仅收集 TextParser 支持的扩展名，PDF 文件不会被收集
3. **预览面板无搜索高亮**：当前只有语法高亮，无搜索关键词高亮
4. **无匹配导航**：无上一个/下一个跳转功能

## 实现步骤

### 步骤 1：在 file_parser.py 中添加 PDFParser

**文件**：`core/file_parser.py`

- 新增 `PDFParser(FileParser)` 类
  - `can_parse()`: 判断扩展名是否为 `.pdf`
  - `parse()`: 使用 PyMuPDF (fitz) 提取 PDF 全文文本
  - 处理异常（文件损坏、加密等），返回 None
- 在 `ParserRegistry.__init__` 中注册 PDFParser
- 给 `FileParser` 基类添加 `supported_extensions` 属性方法，返回该解析器支持的扩展名集合
- `TextParser.supported_extensions` 返回 `self._text_exts`
- `PDFParser.supported_extensions` 返回 `{'.pdf'}`
- `ParserRegistry` 添加 `get_all_supported_extensions()` 方法，汇总所有解析器的扩展名

### 步骤 2：修改 content_searcher.py 的文件收集逻辑

**文件**：`core/content_searcher.py`

- 修改 `_collect_files` 方法（第 43-47 行）：使用 `ParserRegistry.get_all_supported_extensions()` 替代直接访问 `_text_exts`
- 同时修改 `_search_file` 中 PDF 的匹配逻辑：PDF 文本提取后行号概念不同，需要为 PDF 的 ContentMatch 记录页码信息

### 步骤 3：扩展 ContentMatch 数据模型

**文件**：`models/search_result.py`

- 给 `ContentMatch` 添加可选字段 `page_number: int = 0`
  - 纯文本文件：page_number 为 0（不适用）
  - PDF 文件：page_number 为匹配所在页码（从 1 开始）
- 给 `ContentMatch` 添加可选字段 `page_rect: tuple = ()`
  - 用于 PDF 高亮时定位匹配区域在页面上的矩形坐标 (x0, y0, x1, y1)

### 步骤 4：修改 PDF 内容搜索的匹配逻辑

**文件**：`core/content_searcher.py`

- 在 `_search_file` 方法中，对 PDF 文件使用逐页搜索：
  - 用 fitz 打开 PDF，逐页提取文本
  - 在每页文本中搜索关键词
  - 记录匹配的页码和位置信息（使用 `page.search_for(pattern)` 获取矩形坐标）
  - ContentMatch 的 line_number 记录页内行号，page_number 记录页码

### 步骤 5：解除 main_window.py 中的内容搜索拦截

**文件**：`ui/main_window.py`

- 删除第 604-612 行的"即将上线"拦截代码
- 让纯内容搜索正常走 SearchWorker → SearchEngine → ContentSearcher 流程
- 需要处理：纯内容搜索不需要索引检查（当前索引检查仅对文件名搜索有意义），但内容搜索也需要知道搜索目录

### 步骤 6：预览面板 - 搜索关键词高亮（文本/代码文件）

**文件**：`ui/widgets/preview_panel.py`

- 添加实例变量追踪搜索状态：
  - `_search_keyword: str` - 当前搜索关键词
  - `_search_case_sensitive: bool` - 是否区分大小写
  - `_match_positions: list` - 所有匹配位置列表
  - `_current_match_index: int` - 当前高亮的匹配索引
- 在 `set_result()` 中，从 `_current_result.content_matches` 提取搜索关键词
- 在 `_show_text_content()` 完成后，调用高亮方法
- 实现文本高亮方法 `_apply_search_highlight()`：
  - 使用 QTextEdit 的 `ExtraSelection` 机制高亮所有匹配
  - 当前匹配用不同颜色（如橙色背景）区分
  - 记录所有匹配的 QTextCursor 位置用于导航

### 步骤 7：预览面板 - 搜索关键词高亮（PDF 文件）

**文件**：`ui/widgets/preview_panel.py`

- 在 `_show_pdf_content()` 中，如果有搜索关键词，使用 fitz 的 `page.search_for()` 获取匹配矩形
- 在 PDF 页面渲染时，在匹配矩形位置绘制半透明高亮覆盖层
- 当前匹配用不同颜色区分
- 需要在 `_on_pdf_page_rendered` 或 `_display_pdf_page` 中加入高亮绘制逻辑

### 步骤 8：预览面板 - 匹配导航 UI（上一个/下一个）

**文件**：`ui/widgets/preview_panel.py`

- 在预览面板头部添加匹配导航控件：
  - 匹配计数显示：如 "3/12 处匹配"
  - 上一个/下一个按钮（使用现有图标或简单箭头）
- 导航逻辑：
  - 文本文件：移动 QTextCursor 到对应匹配位置，滚动到可见区域
  - PDF 文件：切换到对应页面，高亮当前匹配
- 控件样式：使用 style_constants 令牌，通过 style_manager 生成 QSS

### 步骤 9：连接搜索关键词到预览面板

**文件**：`ui/main_window.py`

- 在 `_on_result_selected` 中，将当前搜索的 content_query 和大小写设置传递给 preview_panel
- PreviewPanel 新增方法 `set_search_keyword(keyword, case_sensitive)` 供外部调用

## 涉及文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `core/file_parser.py` | 修改 | 添加 PDFParser，扩展注册表 |
| `core/content_searcher.py` | 修改 | 修复扩展名收集，添加 PDF 搜索逻辑 |
| `models/search_result.py` | 修改 | ContentMatch 添加 page_number, page_rect 字段 |
| `ui/main_window.py` | 修改 | 解除内容搜索拦截，传递搜索关键词到预览面板 |
| `ui/widgets/preview_panel.py` | 修改 | 添加搜索高亮、匹配导航功能 |
| `ui/style_constants.py` | 可能修改 | 添加搜索高亮相关颜色令牌 |
| `ui/style_manager.py` | 可能修改 | 添加导航按钮样式 |

## 不修改的部分

- `core/name_searcher.py` - 文件名搜索逻辑
- `core/search_engine.py` - 搜索调度逻辑（已支持内容搜索）
- `database/` - 数据库层
- `ui/widgets/search_bar.py` - 搜索栏
- `ui/widgets/filter_bar.py` - 筛选栏
- `ui/widgets/result_list.py` - 结果列表

## 假设与决策

1. **PDF 高亮方式**：在渲染的 PDF 页面图片上绘制半透明矩形覆盖层，而非切换到文本模式。这样用户体验更直观。
2. **搜索关键词来源**：从 `SearchResult.content_matches` 中推断，同时由 main_window 显式传递 content_query。
3. **PDF 行号处理**：PDF 的 ContentMatch.line_number 记录页内文本的行号，page_number 记录页码。
4. **导航控件位置**：放在预览面板头部右侧（文件信息旁边），与现有 UI 风格一致。
5. **匹配数量上限**：沿用现有 content_searcher 的每文件最多 10 个匹配限制。

## 验证步骤

1. 纯文本内容搜索：在搜索栏输入内容关键词，验证能搜索到 .py/.txt/.md 等文件
2. PDF 内容搜索：搜索 PDF 中的文字，验证能找到匹配的 PDF 文件
3. 预览高亮 - 文本：选中搜索结果，验证预览面板中关键词被高亮
4. 预览高亮 - PDF：选中 PDF 搜索结果，验证页面上匹配区域被高亮
5. 匹配导航：点击上一个/下一个按钮，验证能跳转到对应匹配位置
6. 联合搜索：同时输入文件名和内容关键词，验证结果正确
7. 大小写敏感：切换大小写选项，验证搜索和高亮行为正确
8. 无匹配：搜索不存在的内容，验证显示"未找到"
