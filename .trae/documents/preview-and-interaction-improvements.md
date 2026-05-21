# FileFinder 预览与交互优化计划

## 概述

本次修改包含 5 项改进，涉及预览面板的音视频详情、PDF 渲染、空状态显示，以及结果列表的空页面和取消选中功能。

***

## 1. 音视频预览详细信息增强

### 现状分析

当前音视频预览通过 `_show_media_properties()` 方法展示属性信息表格，已有字段包括：文件名、文件大小、时长、分辨率、帧宽度、帧高度、帧速率、视频编码、像素格式、视频比特率、音频编码、总比特率、采样率、声道、比特率、位深度。

**问题**：`_get_media_info()` 方法依赖 `ffprobe` 提取信息，但很多字段只在 ffprobe 返回对应数据时才显示。实际显示时信息可能不全，且缺少一些用户期望的详细信息（如容器格式、创建时间等）。

### 修改方案

**文件**: `ui/widgets/preview_panel.py`

1. **扩展** **`_get_media_info()`** **方法**（第 3105 行），增加提取以下字段：

   * 容器格式（format\_name，从 `format.format_name` 获取，如 "mov,mp4,m4a,3gp,3g2,mj2"）

   * 文件创建时间（`format.tags.creation_time`）

   * 视频色彩空间（`stream.color_space`）

   * 视频色彩范围（`stream.color_range`）

   * 视频宽高比（`stream.display_aspect_ratio`）

   * 音频语言（`stream.tags.language`）

   * 专辑/艺术家/标题等标签信息（`format.tags` 中的 title, artist, album 等）

2. **扩展** **`_show_media_properties()`** **方法**（第 2506 行），在属性列表中添加新字段的显示：

   * 在基本信息区域增加：容器格式、文件修改时间

   * 在视频区域增加：色彩空间、色彩范围、显示宽高比

   * 在音频区域增加：音频语言

   * 新增"媒体标签"区域：标题、艺术家、专辑（仅在有数据时显示）

3. **优化属性表格列宽**：将键名列宽从 70px 增加到 80px，以容纳更长的键名（如"色彩空间"）

***

## 2. PDF 预览渲染方式替换

### 现状分析

当前 PDF 预览使用 PyMuPDF (fitz) 渲染为 PNG 图片 → base64 编码 → 嵌入 HTML → 通过 `QTextBrowser` 显示。

**问题**：

* `QTextBrowser` 渲染图片会缩放，导致模糊

* 默认放大，右侧内容看不全

* 图片宽度硬编码为 `min(img_w, 800)` px，不适配面板宽度

### 修改方案

**文件**: `ui/widgets/preview_panel.py`

**方案：使用 QScrollArea + QLabel 逐页渲染显示**

替换 `QTextBrowser` 为 `QScrollArea` 内嵌垂直布局的多个 `QLabel`，每个 QLabel 显示一页的 QPixmap。这种方式：

* 直接使用 QPixmap 显示，无需 base64 编码/解码，无 HTML 渲染损失

* 图片按面板实际宽度自适应缩放

* 支持滚动浏览多页

具体修改：

1. **修改** **`_PdfRenderWorker`**（第 654 行）：

   * 信号改为 `page_rendered(int, QPixmap)` — 直接传递 QPixmap 而非 base64 字符串

   * 渲染后直接生成 QPixmap 而非 base64 编码

   * 注意：QPixmap 不能跨线程传递，改为传递 PNG 字节数据（QByteArray），在主线程中构建 QPixmap

   实际方案：保持传递 base64 或改为传递临时文件路径。更优方案是传递 `QImage`（可以跨线程）：

   * 信号改为 `page_rendered(int, QImage, int, int)`

   * 在 worker 中用 `QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)` 转换

   * 在主线程中用 `QPixmap.fromImage(image)` 转换

   **最终方案**：保持 base64 传递方式（避免 QImage 跨线程问题），但改用 QScrollArea + QLabel 显示。

2. **替换 PDF 预览 UI 组件**（约第 1370 行的 `_pdf_preview` 创建区域）：

   * 移除 `_pdf_browser: QTextBrowser`

   * 新建 `_pdf_scroll_area: QScrollArea`，内部使用 `_pdf_pages_layout: QVBoxLayout`

   * 每个 PDF 页面用一个 `QLabel` 显示 QPixmap

   * `_pdf_page_labels: list[QLabel]` 管理所有页面标签

3. **修改** **`_on_pdf_page_rendered()`**（第 2191 行）：

   * 接收 base64 数据后，解码为 QPixmap

   * 按面板宽度等比缩放

   * 创建/更新对应位置的 QLabel，设置缩放后的 QPixmap

4. **修改** **`_on_pdf_render_finished()`**（第 2209 行）：

   * 不再拼接 HTML，直接显示 `_pdf_scroll_area`

5. **修改** **`_show_pdf_content()`**（第 2141 行）：

   * 切换到 `_pdf_preview` 时显示 `_pdf_scroll_area`

6. **页面宽度自适应**：

   * 渲染 DPI 根据面板实际宽度动态计算

   * 显示时图片宽度 = 面板内容区宽度 - 边距

   * 使用 `scaled(width, height, KeepAspectRatio, SmoothTransformation)` 缩放

***

## 3. 结果列表空页面（未搜索/无结果）

### 现状分析

* 搜索无结果时，`result_list.show_empty_state()` 已实现，显示"未找到匹配文件"

* **但**：在用户尚未开始搜索时（刚进入主页面），结果列表直接显示所有文件，没有引导性的空页面

* 用户期望：在未搜索时显示一个引导空页面（如"输入关键词开始搜索"）

### 修改方案

**文件**: `ui/widgets/result_list.py`

1. **扩展** **`_setup_empty_state()`** **方法**（第 366 行）：

   * 添加一个 `_idle_widget`（空闲引导页面），在未搜索时显示

   * 包含：搜索图标 + "开始搜索" 标题 + "输入关键词查找文件" 提示

   * 与 `_empty_widget`（搜索无结果页面）分开管理

2. **新增方法**：

   * `show_idle_state()` — 显示空闲引导页面，隐藏空结果页面

   * `hide_idle_state()` — 隐藏空闲引导页面

3. **修改** **`set_results()`** **方法**：

   * 当 results 为空且是初始状态时，显示 idle 状态而非 empty 状态

**文件**: `ui/main_window.py`

1. **在** **`_switch_to_main()`** **方法中**（第 2779 行）：

   * 加载完索引后，如果用户尚未搜索，调用 `result_list.show_idle_state()` 显示引导页面

2. **在搜索开始时**：

   * 调用 `result_list.hide_idle_state()` 隐藏引导页面

***

## 4. 预览面板空界面显示修复

### 现状分析

预览面板的空状态由 `empty_placeholder` 组件实现（第 1169 行），布局结构：

```
empty_placeholder (QWidget, margins: 12,0,12,12)
  └── empty_inner (QWidget, margins: 24,32,24,32)
        ├── _empty_icon (56x56)
        ├── _empty_title
        └── _empty_hint
```

**问题**：用户反馈"下面会出现一个圆角矩形的框，导致上面的内容被挤压，icon 被截断"。

根因分析：`empty_inner` 是一个 QWidget，在 Qt 默认样式中可能有背景色，形成可见的矩形区域。同时 `empty_placeholder` 和 `_content_stack` 同时在布局中（stretch=1），当 `_content_stack` 隐藏后，`empty_placeholder` 占满空间，但 `empty_inner` 的居中对齐可能因空间分配问题导致内容被挤压。

### 修改方案

**文件**: `ui/widgets/preview_panel.py`

1. **移除** **`empty_inner`** **包装层**，将图标、标题、提示直接放在 `empty_placeholder` 的布局中，减少嵌套层级

2. **为** **`empty_placeholder`** **设置透明背景和明确样式**：

   ```python
   self.empty_placeholder.setStyleSheet("background: transparent; border: none;")
   ```

3. **调整布局边距和间距**：

   * `empty_placeholder` 的 margins 改为 `(0, 0, 0, 0)`，让内容有更大空间

   * 图标和文字之间保持适当间距

   * 使用 `addStretch()` 在上下添加弹性空间，确保内容居中且不被挤压

4. **确保 icon 不被截断**：

   * 给 `_empty_icon` 设置 `setMinimumSize(56, 56)` 确保最小尺寸

   * 检查父布局是否有最小高度限制

***

## 5. 再次点击取消选中结果

### 现状分析

当前 `ResultListWidget` 使用 `ExtendedSelection` 模式，单击已选中项不会取消选中，只有 Ctrl+点击才能切换。`_on_item_clicked()` 方法（第 621 行）只处理了双击激活逻辑，没有实现再次点击取消选中。

### 修改方案

**文件**: `ui/widgets/result_list.py`

1. **修改** **`_on_item_clicked()`** **方法**（第 621 行），实现再次点击取消选中逻辑：

   ```python
   def _on_item_clicked(self, item):
       index = self.row(item)
       if index == self._anchor_index and len(self.selectedItems()) == 1:
           # 再次点击同一个已选中项 → 取消选中
           self.clearSelection()
           for w in self._item_widgets.values():
               w.set_selected(False)
           self._anchor_index = -1
       else:
           self._anchor_index = index
   ```

2. **修改** **`_on_selection_changed()`** **方法**（第 604 行）：

   * 当选中集为空时，发射一个信号通知预览面板清空预览

   * 新增或复用 `result_selected` 信号，传递 `None` 表示无选中

3. **修改** **`main_window.py`** **中的** **`_on_result_selected()`**（第 3068 行）：

   * 处理 `result is None` 的情况，调用 `preview_panel.set_result(None)` 清空预览

***

## 修改文件清单

| 文件                            | 修改内容                   |
| ----------------------------- | ---------------------- |
| `ui/widgets/preview_panel.py` | 音视频详情增强、PDF 渲染替换、空界面修复 |
| `ui/widgets/result_list.py`   | 空闲引导页面、再次点击取消选中        |
| `ui/main_window.py`           | 空闲页面状态管理、取消选中时清空预览     |

***

## 验证步骤

1. **音视频详情**：打开音视频文件，确认属性表格显示完整详细信息（容器格式、色彩空间、标签等）
2. **PDF 预览**：打开 PDF 文件，确认渲染清晰、宽度自适应面板、可滚动浏览多页
3. **空页面**：启动应用后未搜索时，确认结果列表显示引导页面；搜索无结果时显示"未找到匹配文件"
4. **预览空界面**：未选中文件时，确认预览面板空状态无多余圆角矩形框，图标完整显示
5. **取消选中**：点击选中一个结果后，再次点击同一结果，确认选中被取消且预览面板清空

