# FileFinder 预览与性能优化计划

## 摘要

针对用户提出的 9 个问题，涵盖搜索结果卡顿、预览显示异常、多媒体预览缺失、性能优化、扫描信息显示、未扫描目录提示、Excel/Markdown 模式切换、Markdown 图片、滚动条边距等方面进行修复和优化。

***

## 当前状态分析

### 问题 1：搜索结果出来后卡顿

* **根因**：`result_list.py` 使用 `QListWidget.setItemWidget()` 为每个结果创建 6-8 个子 widget，1000 条结果 = 6000+ widget，渲染开销巨大

* **次要原因**：`_batch_add()` 使用 `QTimer.singleShot(0)` 几乎不释放 UI 响应时间；SVG 图标每次从磁盘加载无缓存

### 问题 2：PDF/图片首次预览过大

* **根因**：`_fit_image_to_label()` 在首次调用时，`_image_label` 尚未完成布局，`size()` 返回的是初始/默认尺寸而非实际可用尺寸，导致缩放计算错误。第二次预览时 widget 已有正确尺寸

* **PDF 同理**：`_on_pdf_page_rendered()` 中 `self._pdf_scroll.viewport().width()` 在首次渲染时可能尚未正确计算

### 问题 3：视频/音频无法预览

* **根因**：`HAS_MULTIMEDIA` 为 `False`，说明 `PySide6.QtMultimediaWidgets` 导入失败。PySide6 默认安装可能不包含多媒体模块，需要单独安装 `PySide6-QtMultimedia` 或确认 PySide6 版本兼容性（如果要装多的依赖，需要在requirement.txt中补充）

* **修复方向**：添加更详细的检测和安装提示，尝试多种导入方式

### 问题 4：多次预览文件流畅性

* **根因**：预览切换时资源清理可能不彻底；大量结果列表 widget 常驻内存；无预览缓存机制

### 问题 5：加载详情只显示几行

* **根因**：`ScanProgressDialog._scan_log`（QTextEdit）设置了 `setMaximumHeight(200)`，限制了可见行数

* **次要原因**：ScanWorker 的 progress 信号有 0.3 秒节流，且仅在目录变化时追加日志行

### 问题 6：新增扫描目录后无提示

* **根因**：通过 `_on_configure_scope()` 添加新目录后，虽然弹窗提示"请点击新增扫描"，但 `SearchScopePanel` 的状态点/扫描按钮更新逻辑在 `_on_configure_scope` 中调用了 `_update_scan_btn_state()` 和 `_update_scope_info()`，但新目录的 scan\_status 为 None（未扫描），需要确认这些方法是否正确识别了未扫描状态

* **关键**：`add_scanned_dir()` 方法在添加目录时没有设置 scan\_status，导致 `get_scan_status()` 返回 None，但 `_has_unscanned_dirs()` 已处理了 None 的情况。需要检查 `_update_scan_btn_state` 是否在添加目录后被正确调用

### 问题 7：Excel/Markdown 模式切换滑块

* **现状**：Excel 使用 `QPushButton("渲染预览")` 切换，Markdown 使用 `QPushButton("源码模式")` 切换

* **目标**：改为类似 `SegmentedControl`（search\_bar.py 中的分段滑块）的二段式滑块

### 问题 8：Markdown 无法正确读取图片

* **根因**：`_render_markdown()` 中使用 `markdown.markdown()` 将 MD 转 HTML，但图片路径是相对路径，`QTextBrowser.setHtml()` 无法解析相对路径的图片。需要将相对路径转为 `file://` 绝对路径

### 问题 9：滚动条未贴合边框

* **根因**：`QTextEdit` 的 CSS `padding: 12px 16px` 导致内容区域与边框之间有间距，滚动条紧贴内容区域而非边框，造成视觉上滚动条没有贴合边框

* **修复方向**：将 padding 改为 QTextEdit 的 `setViewportMargins()`，这样 padding 作用于 viewport 内部，滚动条仍贴合边框

***

## 修改方案

### 修改 1：搜索结果渲染优化（问题 1 + 4）

**文件**：`ui/widgets/result_list.py`

**改动**：

1. **SVG 图标缓存**：添加类级别 `_icon_cache` 字典，避免同类文件重复从磁盘加载 SVG
2. **增大批次间隔**：`QTimer.singleShot(0)` 改为 `QTimer.singleShot(10)`，给 UI 更多响应时间
3. **虚拟化优化**：对视口外的 widget 释放不必要的资源（如缩小 pixmap）

**文件**：`ui/widgets/preview_panel.py`

**改动**：

1. **预览资源清理增强**：在 `set_result()` 中确保所有旧预览资源被彻底释放
2. **预览缓存**：添加简单的 LRU 缓存（最近 5 个文件的预览结果），避免来回切换时重复加载

### 修改 2：PDF/图片首次预览尺寸修复（问题 2）

**文件**：`ui/widgets/preview_panel.py`

**改动**：

1. **图片预览**：在 `_show_image_content()` 中，不立即调用 `_fit_image_to_label()`，而是使用 `QTimer.singleShot(0)` 延迟一帧执行，确保 widget 已完成布局
2. **PDF 预览**：在 `_on_pdf_page_rendered()` 中，对首次渲染的页面也使用延迟缩放，或在 `_on_pdf_render_finished()` 中统一重新缩放所有已渲染页面
3. **GIF 预览**：同样处理

### 修改 3：视频/音频预览修复（问题 3）

**文件**：`ui/widgets/preview_panel.py`

**改动**：

1. **改进多媒体检测**：尝试多种导入方式，提供更详细的安装指引
2. **添加安装检测**：检测 `PySide6-QtMultimedia` 是否安装，给出精确的 pip 安装命令
3. **降级方案**：如果多媒体组件不可用，使用系统默认播放器播放（通过 `os.startfile` 或 `subprocess`）

### 修改 4：预览性能优化（问题 4）

**文件**：`ui/widgets/preview_panel.py`

**改动**：

1. **预览延迟增加**：将 `_preview_timer` 间隔从 100ms 调整为 150ms，减少快速切换时的无效预览
2. **资源释放**：在 `_cancel_workers()` 中增加更彻底的清理
3. **结果列表优化**：配合修改 1 的图标缓存和批次间隔优化

### 修改 5：扫描详情显示完整（问题 5）

**文件**：`ui/main_window.py`（`ScanProgressDialog` 类）

**改动**：

1. **移除最大高度限制**：将 `_scan_log.setMaximumHeight(200)` 改为不限制或增大到合理值（如 400px），让日志区域随布局自动扩展
2. **增加日志信息**：在 `update_progress()` 中不仅记录目录路径，还记录文件计数变化，让用户看到更详细的扫描进度

### 修改 6：新增扫描目录提示（问题 6）

**文件**：`ui/main_window.py`（`SearchScopePanel` 类）

**改动**：

1. **添加目录后立即更新状态**：在 `add_scanned_dir()` 中确保调用 `_update_scan_btn_state()` 和 `_update_status_dot()`
2. **视觉提示增强**：当存在未扫描目录时，扫描按钮添加脉冲动画或更醒目的样式
3. **状态标签更新**：确保 `_update_scope_info()` 正确显示"存在未扫描目录"的提示文字

### 修改 7：Excel/Markdown 模式切换滑块（问题 7）

**文件**：`ui/widgets/preview_panel.py`

**改动**：

1. **提取通用分段滑块组件**：参考 `search_bar.py` 中的 `SegmentedControl`，创建一个轻量级的二段式滑块 `_PreviewModeSlider`
2. **替换 Excel 切换按钮**：将 `_excel_toggle_btn`（QPushButton）替换为 `_PreviewModeSlider`（"文本预览"/"渲染预览"）
3. **替换 Markdown 切换按钮**：将 `_md_toggle_btn`（QPushButton）替换为 `_PreviewModeSlider`（"源码"/"预览"）
4. **调整布局**：将滑块放在预览区域的标题栏或内容区顶部

### 修改 8：Markdown 图片路径修复（问题 8）

**文件**：`ui/widgets/preview_panel.py`

**改动**：

1. **图片路径转换**：在 `_render_markdown()` 中，解析 HTML 中的 `<img>` 标签，将相对路径转为基于当前文件目录的绝对 `file://` URL
2. **使用正则替换**：匹配 `<img src="...">` 中的相对路径，拼接文件所在目录的绝对路径

### 修改 9：滚动条贴合边框修复（问题 9）

**文件**：`ui/widgets/preview_panel.py`

**改动**：

1. **QTextEdit padding 改为 viewport margins**：将 `_text_edit`、`_md_browser`、`_excel_text_edit` 的 CSS `padding` 移除，改用 `setViewportMargins()` 设置内边距
2. **验证所有文本预览组件**：确保代码文件、纯文本、Markdown 源码模式、Excel 文本模式等所有使用 QTextEdit 的预览都正确处理

***

## 假设与决策

| 决策      | 选择               | 理由                                                |
| ------- | ---------------- | ------------------------------------------------- |
| 图标缓存策略  | 类级别字典缓存          | 简单有效，避免引入 LRU 库                                   |
| 预览缓存策略  | 不做文件内容缓存         | 预览内容类型多样（文本/图片/PDF），缓存管理复杂，优先保证资源释放               |
| 多媒体降级方案 | 系统默认播放器          | 用户明确要求"修复"，不能只显示提示                                |
| 分段滑块实现  | 内嵌轻量级组件          | 复用项目中已有的 `SegmentedControl` 模式，不引入新依赖             |
| 滚动条修复方式 | viewport margins | 这是 Qt 推荐的做法，padding 影响滚动条位置而 viewport margins 不影响 |

***

## 验证步骤

1. **搜索结果卡顿**：搜索返回 500+ 结果，观察结果列表渲染是否流畅，切换预览是否无卡顿
2. **PDF/图片首次预览**：首次预览 PDF 和图片，确认尺寸正确适配面板宽度
3. **视频/音频预览**：预览 .mp4 和 .mp3 文件，确认能播放或能通过降级方案打开
4. **多次预览流畅性**：在 500+ 结果中快速连续点击不同文件预览，确认无卡顿
5. **扫描详情**：执行扫描，确认日志区域显示足够多的目录信息
6. **未扫描目录提示**：添加新扫描目录后，确认状态点和扫描按钮正确变化
7. **Excel/Markdown 滑块**：预览 Excel 和 Markdown 文件，确认分段滑块切换正常
8. **Markdown 图片**：预览包含本地图片的 Markdown 文件，确认图片正确显示
9. **滚动条边距**：预览代码文件和纯文本文件，确认滚动条贴合边框

