"""
样式管理器
==========
本文件提供所有组件的 QSS 样式生成函数。每个函数返回一段 QSS 字符串，
所有颜色、字号、圆角等值均引用 style_constants.py 中的令牌，而非硬编码。

修改指南：
  - 修改某个组件的样式：找到对应的函数，修改其中的 QSS 属性
  - 修改颜色/字号等基础值：去 style_constants.py 修改令牌值，本文件自动生效
  - 添加新组件样式：新增一个函数，引用 COLORS/FONT/RADIUS/BTN/DIALOG 中的令牌

函数分类：
  1. 基础组件：scrollbar, input, radio_button, checkbox, progress_bar
  2. 按钮系列：button_primary, button_secondary, button_danger, button_small_*, button_tag 等
  3. 弹窗系列：dialog_frame_style, dialog_title_style, dialog_body_style, dialog_style, msg_box_style
  4. 容器组件：list_style, menu_style, group_box_style, tree_widget_style
  5. 标签系列：label_caption_style, label_micro_style, label_body_style, label_header_style, badge_style
  6. 布局组件：status_bar_style, splitter_style, menubar_style, scan_log_style
"""

from .style_constants import COLORS, FONT, RADIUS, SPACING, BTN, DIALOG, TRANSITION


# ============================================================================
# 1. 基础组件样式
# ============================================================================


def scrollbar_style() -> str:
    """
    全局滚动条样式。
    特点：细条式（6px宽）、圆角手柄、隐藏上下箭头按钮。
    应用于：所有 QListWidget、QTreeWidget、QScrollArea、QMainWindow 全局。
    """
    return f"""
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS.BORDER_HOVER};
        min-height: 40px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS.TEXT_PLACEHOLDER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px; background: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLORS.BORDER_HOVER};
        min-width: 40px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS.TEXT_PLACEHOLDER};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px; background: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
"""


def input_style() -> str:
    """
    通用输入框样式。
    特点：浅灰背景、焦点时变白+品牌色边框、圆角 8px。
    应用于：对话框中的路径输入框、设置页面的下拉框。
    """
    return f"""
    QLineEdit {{
        padding: 0px 12px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        font-size: {BTN.FONT_SIZE};
        background-color: {COLORS.BG_SECONDARY};
        outline: none;
    }}
    QLineEdit:focus {{
        border-color: {COLORS.BORDER_FOCUS};
        background-color: {COLORS.BG_PRIMARY};
    }}
    QLineEdit:hover {{
        border-color: {COLORS.BORDER_HOVER};
    }}
"""


def combo_box_style() -> str:
    return f"""
    QComboBox {{
        padding: 3px 28px 3px 10px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.MEDIUM}px;
        background-color: {COLORS.BG_PRIMARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        color: {COLORS.TEXT_SECONDARY};
        outline: none;
        min-height: 24px;
    }}
    QComboBox:hover {{
        border-color: {COLORS.BRAND};
        background-color: {COLORS.BG_PRIMARY};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
        subcontrol-origin: padding;
        subcontrol-position: center right;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {COLORS.TEXT_TERTIARY};
        margin-right: 8px;
    }}
    QComboBox::down-arrow:hover {{
        border-top-color: {COLORS.BRAND};
    }}
    QComboBox QAbstractItemView {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.DEFAULT}px;
        background-color: {COLORS.BG_PRIMARY};
        selection-background-color: {COLORS.BRAND_LIGHT_BG};
        selection-color: {COLORS.BRAND};
        outline: none;
        padding: 6px 4px;
        font-size: {BTN.SMALL_FONT_SIZE};
    }}
    QComboBox QAbstractItemView::item {{
        padding: 6px 12px;
        min-height: 28px;
        border-radius: {RADIUS.SMALL}px;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background-color: {COLORS.BG_HOVER};
    }}
"""


def search_input_style() -> str:
    """
    搜索栏输入框样式（比通用输入框更大更圆）。
    特点：白色背景、大圆角 12px、更大的内边距、品牌色焦点边框。
    应用于：SearchBar 中的主搜索输入框。
    """
    return f"""
    QLineEdit {{
        padding: 10px 14px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.XLARGE}px;
        font-size: {DIALOG.BODY_FONT_SIZE};
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_PRIMARY};
        outline: none;
    }}
    QLineEdit:hover {{
        border-color: {COLORS.BORDER_HOVER};
    }}
    QLineEdit:focus {{
        border-color: {COLORS.BORDER_FOCUS};
        background-color: {COLORS.BG_PRIMARY};
    }}
"""


def radio_button_style() -> str:
    return f"""
    QRadioButton {{
        font-size: {BTN.SMALL_FONT_SIZE};
        color: {COLORS.TEXT_SECONDARY};
        spacing: 4px;
        outline: none;
        border: none;
        background: transparent;
        text-decoration: none;
    }}
    QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 7px;
        border: 2px solid {COLORS.BORDER_HOVER};
        background-color: transparent;
    }}
    QRadioButton::indicator:hover {{
        border-color: {COLORS.BRAND};
    }}
    QRadioButton::indicator:checked {{
        border-color: {COLORS.BRAND};
        background-color: transparent;
        border-width: 2px;
        image: none;
    }}
    QRadioButton::indicator:checked:hover {{
        border-color: {COLORS.BRAND_HOVER};
    }}
    QRadioButton::indicator:unchecked:disabled {{
        border-color: {COLORS.BORDER_DEFAULT};
        background-color: transparent;
    }}
    QRadioButton::indicator:checked:disabled {{
        border-color: {COLORS.BORDER_HOVER};
        background-color: transparent;
    }}
    QRadioButton:disabled {{
        color: {COLORS.TEXT_PLACEHOLDER};
    }}
"""


def checkbox_style() -> str:
    """
    复选框样式（QSS 部分，实际绘制在 AnimatedCheckBox.paintEvent 中）。
    特点：透明背景、辅助文字色、无焦点框。
    应用于：SearchBar 的"区分大小写"复选框。
    """
    return f"""
    QCheckBox {{
        spacing: 6px;
        font-size: {BTN.SMALL_FONT_SIZE};
        color: {COLORS.TEXT_SECONDARY};
        outline: none;
        text-decoration: none;
        border: none;
        background: transparent;
    }}
    QCheckBox:focus {{
        outline: none;
        border: none;
    }}
"""


def progress_bar_style(height: int = 8, radius: int = 4) -> str:
    """
    进度条样式（品牌色/紫色）。
    参数：
      height: 进度条高度（px），默认 8
      radius: 进度条圆角（px），默认 4
    应用于：SearchScopePanel 小进度条、搜索进度条。
    """
    return f"""
    QProgressBar {{
        border: none;
        background-color: {COLORS.BORDER_DEFAULT};
        border-radius: {radius}px;
        height: {height}px;
        text-align: center;
        font-size: 10px;
        color: {COLORS.TEXT_TERTIARY};
        outline: none;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS.BRAND};
        border-radius: {radius}px;
    }}
"""


def progress_bar_success_style(height: int = 8, radius: int = 4) -> str:
    """
    进度条样式（成功/绿色）。
    应用于：ScanProgressDialog 扫描完成时的进度条。
    """
    return f"""
    QProgressBar {{
        border: none;
        background-color: {COLORS.BORDER_DEFAULT};
        border-radius: {radius}px;
        height: {height}px;
        text-align: center;
        outline: none;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS.SUCCESS};
        border-radius: {radius}px;
    }}
"""


def progress_bar_warning_style(height: int = 8, radius: int = 4) -> str:
    """
    进度条样式（警告/橙色）。
    应用于：ScanProgressDialog 取消扫描时的进度条。
    """
    return f"""
    QProgressBar {{
        border: none;
        background-color: {COLORS.BORDER_DEFAULT};
        border-radius: {radius}px;
        height: {height}px;
        text-align: center;
        outline: none;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS.WARNING};
        border-radius: {radius}px;
    }}
"""


def progress_bar_error_style(height: int = 8, radius: int = 4) -> str:
    """
    进度条样式（错误/红色）。
    应用于：ScanProgressDialog 扫描失败时的进度条。
    """
    return f"""
    QProgressBar {{
        border: none;
        background-color: {COLORS.BORDER_DEFAULT};
        border-radius: {radius}px;
        height: {height}px;
        text-align: center;
        outline: none;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS.ERROR};
        border-radius: {radius}px;
    }}
"""


# ============================================================================
# 2. 按钮系列
# ============================================================================
# 所有按钮函数返回 QSS 字符串，支持 4 种状态：默认 / 悬停 / 按下 / 禁用
# 带有 extra 参数的函数允许在基础样式上追加自定义 QSS 属性
# ============================================================================


def button_primary(extra: str = "") -> str:
    """
    主要按钮（紫色实心）。
    特点：品牌色背景、白色文字、无描边、粗体。
    状态：默认 → 悬停(深紫) → 按下(更深紫) → 禁用(浅紫)
    应用于：对话框"确定"/"开始扫描"按钮、WelcomePage"添加"按钮。
    参数 extra: 追加到默认样式末尾的额外 QSS 属性
    """
    base = f"""
    QPushButton {{
        padding: {BTN.PADDING_V} {BTN.PADDING_H_WIDE};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        outline: none;
        min-width: {BTN.MIN_WIDTH};
    }}
    QPushButton:hover {{
        background-color: {COLORS.BRAND_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {COLORS.BRAND_PRESSED};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BRAND_DISABLED};
    }}
    """
    if extra:
        base = base.rstrip() + "\n    " + extra + "\n"
    return base


def button_secondary(extra: str = "") -> str:
    base = f"""
    QPushButton {{
        padding: {BTN.PADDING_V} {BTN.PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: transparent;
        color: {COLORS.TEXT_SECONDARY};
        font-size: {BTN.FONT_SIZE};
        outline: none;
        min-width: {BTN.MIN_WIDTH};
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {COLORS.BORDER_DEFAULT};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BG_HOVER};
        color: {COLORS.TEXT_PLACEHOLDER};
        border-color: {COLORS.BORDER_DEFAULT};
    }}
    """
    if extra:
        base = base.rstrip() + "\n    " + extra + "\n"
    return base


def button_danger(extra: str = "") -> str:
    """
    危险按钮（红色实心）。
    特点：错误色背景、白色文字、无描边、粗体。
    状态：默认 → 悬停(深红) → 禁用(浅红边框色)
    应用于：SettingsDialog"重置设置"按钮。
    参数 extra: 追加到默认样式末尾的额外 QSS 属性
    """
    base = f"""
    QPushButton {{
        padding: {BTN.PADDING_V} {BTN.PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.ERROR};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.ERROR_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.ERROR_BORDER};
    }}
    """
    if extra:
        base = base.rstrip() + "\n    " + extra + "\n"
    return base


def button_small_primary() -> str:
    """
    小主要按钮（紫色实心，尺寸更小）。
    特点：更小的内边距和字号、圆角 6px。
    应用于：对话框中的"+ 添加"按钮、SearchScopeDialog 快速添加按钮。
    """
    return f"""
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.SMALL_BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BRAND_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BRAND_DISABLED};
    }}
"""


def button_small_secondary() -> str:
    return f"""
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.SMALL_BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: transparent;
        color: {COLORS.TEXT_TERTIARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
        color: {COLORS.TEXT_SECONDARY};
    }}
"""


def button_tag() -> str:
    return f"""
    QPushButton {{
        padding: {BTN.TAG_PADDING_V} {BTN.TAG_PADDING_H};
        border-radius: {BTN.TAG_BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: transparent;
        color: {COLORS.TEXT_TERTIARY};
        font-size: {BTN.TAG_FONT_SIZE};
        outline: none;
        text-align: left;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
        color: {COLORS.TEXT_PRIMARY};
    }}
    QPushButton:checked {{
        background-color: {COLORS.BRAND};
        border-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
    }}
    QPushButton:checked:hover {{
        background-color: {COLORS.BRAND_HOVER};
        border-color: {COLORS.BRAND_HOVER};
    }}
"""


def button_cancel_danger() -> str:
    return f"""
    QPushButton {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.LARGE}px;
        background-color: transparent;
        color: {COLORS.TEXT_TERTIARY};
        font-size: {BTN.FONT_SIZE};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.ERROR_LIGHT_BG};
        border-color: {COLORS.ERROR_BORDER};
        color: {COLORS.ERROR};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BG_HOVER};
        color: {COLORS.TEXT_PLACEHOLDER};
        border-color: {COLORS.BORDER_DEFAULT};
    }}
"""


def button_filter() -> str:
    return f"""
    QPushButton {{
        outline: none;
    }}
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} 16px;
        border-radius: {BTN.BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: transparent;
        color: {COLORS.TEXT_SECONDARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        font-weight: {FONT.WEIGHT_MEDIUM};
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
    }}
    QPushButton:checked {{
        background-color: {COLORS.BRAND};
        border-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
    }}
    QPushButton:checked:hover {{
        background-color: {COLORS.BRAND_HOVER};
        border-color: {COLORS.BRAND_HOVER};
    }}
"""


def button_scan() -> str:
    """
    扫描按钮（紫色实心，小尺寸）。
    特点：品牌色背景、固定最小高度 24px。
    应用于：FilterBar 中"重新扫描"按钮。
    """
    return f"""
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        min-height: 24px;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BRAND_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BRAND_DISABLED};
    }}
"""


def button_scan_green() -> str:
    """
    绿色扫描按钮（成功色实心，小尺寸）。
    特点：成功色背景、固定最小高度 24px。
    应用于：FilterBar 中"开始扫描"/"新增扫描"按钮。
    """
    return f"""
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.SUCCESS};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        min-height: 24px;
    }}
    QPushButton:hover {{
        background-color: {COLORS.SUCCESS_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.SUCCESS_DISABLED};
    }}
"""


def search_button_style() -> str:
    """
    搜索按钮样式（紫色实心，大圆角）。
    特点：品牌色背景、超大圆角 12px（与搜索输入框匹配）、按下态更深。
    应用于：SearchBar 中的"搜索"按钮。
    """
    return f"""
    QPushButton {{
        background-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
        border: none;
        border-radius: {RADIUS.XLARGE}px;
        padding: 10px 20px;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BRAND_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {COLORS.BRAND_PRESSED};
    }}
"""


def remove_button_style() -> str:
    """
    移除按钮（默认透明，悬停变红色）。
    特点：无边框、透明背景、悬停时红色背景+红色文字。
    应用于：SearchScopeDialog 中目录列表项的"移除"按钮。
    """
    return f"""
    QPushButton {{
        border: none;
        background: transparent;
        outline: none;
        padding: 2px 8px;
        color: {COLORS.TEXT_PLACEHOLDER};
        font-size: {BTN.SMALL_FONT_SIZE};
        border-radius: {RADIUS.SMALL}px;
    }}
    QPushButton:hover {{
        background-color: {COLORS.ERROR_LIGHT_BG};
        color: {COLORS.ERROR};
    }}
"""


def icon_button_style() -> str:
    return f"""
    QPushButton {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.MEDIUM}px;
        background-color: transparent;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
    }}
"""


def config_button_style() -> str:
    return f"""
    QPushButton {{
        outline: none;
    }}
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: transparent;
        color: {COLORS.TEXT_SECONDARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        text-decoration: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
        color: {COLORS.TEXT_PRIMARY};
    }}
"""


# ============================================================================
# 3. 弹窗系列
# ============================================================================


def dialog_frame_style() -> str:
    """
    弹窗外框样式（白色圆角卡片）。
    特点：白色背景、16px 大圆角、极浅灰描边。
    应用于：所有 ModernMessageBox / _ModernMessageBox 的 shadowFrame。
    注意：QSS 选择器为 QFrame#shadowFrame，使用时需设置 objectName。
    """
    return f"""
    QFrame#shadowFrame {{
        background-color: {COLORS.BG_PRIMARY};
        border-radius: {DIALOG.BORDER_RADIUS}px;
        border: {DIALOG.BORDER_WIDTH} {DIALOG.BORDER_STYLE} {DIALOG.BORDER_COLOR};
    }}
"""


def dialog_title_style() -> str:
    """
    弹窗标题文字样式。
    特点：深色文字、透明背景、无边框。
    应用于：所有弹窗/对话框的标题 QLabel。
    """
    return f"color: {DIALOG.TITLE_COLOR}; border: none; background: transparent;"


def dialog_body_style() -> str:
    """
    弹窗正文文字样式。
    特点：灰色文字、14px 字号、1.6 行高、透明背景。
    应用于：所有弹窗/对话框的正文 QLabel。
    """
    return f"color: {DIALOG.BODY_COLOR}; font-size: {DIALOG.BODY_FONT_SIZE}; line-height: {DIALOG.BODY_LINE_HEIGHT}; border: none; background: transparent;"


def dialog_style() -> str:
    """
    对话框整体样式（白色背景 + 标签文字色）。
    特点：白色背景、标签深色文字、透明背景。
    应用于：SettingsDialog、SearchScopeDialog 等完整对话框。
    """
    return f"""
    QDialog {{
        background-color: {COLORS.BG_PRIMARY};
    }}
    QLabel {{
        color: {COLORS.TEXT_PRIMARY};
        border: none;
        background: transparent;
    }}
"""


def msg_box_style() -> str:
    """
    QMessageBox 样式（覆盖系统默认外观）。
    特点：白色背景、标签深色文字、次要按钮风格的按钮。
    应用于：通过 _styled_msg_box() 创建的弹窗内部 QMessageBox。
    """
    return f"""
    QMessageBox {{
        background-color: {COLORS.BG_PRIMARY};
    }}
    QMessageBox QLabel {{
        color: {COLORS.TEXT_PRIMARY};
        font-size: {DIALOG.BODY_FONT_SIZE};
        border: none;
        background: transparent;
    }}
    QPushButton {{
        padding: {BTN.PADDING_V} {BTN.PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_SECONDARY};
        font-size: {BTN.FONT_SIZE};
        outline: none;
        min-width: {BTN.MIN_WIDTH};
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
    }}
"""


# ============================================================================
# 4. 容器组件样式
# ============================================================================


def list_style() -> str:
    """
    列表控件样式（QListWidget）。
    特点：浅灰背景、品牌色浅背景选中态、自带滚动条样式。
    应用于：SearchScopeDialog 中的目录列表。
    """
    return f"""
    QListWidget {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        background-color: {COLORS.BG_SECONDARY};
        padding: 4px;
        font-size: {BTN.FONT_SIZE};
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px 32px 8px 10px;
        border-radius: {RADIUS.SMALL}px;
        border: none;
    }}
    QListWidget::item:hover {{
        background-color: {COLORS.BG_HOVER};
    }}
    QListWidget::item:selected {{
        background-color: {COLORS.BRAND_LIGHT_BG};
        color: {COLORS.TEXT_PRIMARY};
        border: none;
    }}
    """ + scrollbar_style()


def menu_style() -> str:
    return f"""
    QMenu {{
        background-color: {COLORS.BG_PRIMARY};
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.DEFAULT}px;
        padding: 6px 4px;
    }}
    QMenu::item {{
        padding: 8px 28px 8px 20px;
        border-radius: {RADIUS.MEDIUM}px;
        font-size: {BTN.FONT_SIZE};
        color: {COLORS.TEXT_PRIMARY};
        background: transparent;
        margin: 1px 4px;
    }}
    QMenu::item:selected {{
        background-color: {COLORS.BRAND_LIGHT_BG};
        color: {COLORS.BRAND};
    }}
    QMenu::icon {{
        padding-left: 8px;
    }}
    QMenu::separator {{
        height: 1px;
        background: {COLORS.BG_HOVER};
        margin: 4px 12px;
    }}
    QMenu::right-arrow {{
        width: 12px;
        height: 12px;
    }}
"""


def group_box_style() -> str:
    """
    分组框样式（QGroupBox，普通版）。
    特点：浅灰背景、灰色描边、标题在左上角。
    应用于：SettingsDialog 中的"通用设置"、"搜索设置"分组。
    """
    return f"""
    QGroupBox {{
        font-size: {DIALOG.TITLE_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        color: {COLORS.TEXT_PRIMARY};
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        margin-top: 12px;
        padding-top: 20px;
        background-color: {COLORS.BG_SECONDARY};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
    }}
"""


def danger_zone_style() -> str:
    """
    危险区域分组框样式（QGroupBox，红色警告版）。
    特点：红色标题、红色描边、浅红背景。
    应用于：SettingsDialog 中的"危险区域"分组。
    """
    return f"""
    QGroupBox {{
        font-size: {DIALOG.TITLE_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        color: {COLORS.ERROR};
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.ERROR_BORDER};
        border-radius: {BTN.BORDER_RADIUS}px;
        margin-top: 12px;
        padding-top: 20px;
        background-color: {COLORS.ERROR_SURFACE};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
    }}
"""


def scope_info_scroll_style() -> str:
    return f"""
    QScrollArea {{
        border: none;
        border-radius: {RADIUS.MEDIUM}px;
        background-color: {COLORS.BG_SECONDARY};
    }}
    """ + scrollbar_style()


def tree_widget_style(checkmark_path: str, partial_path: str,
                      branch_closed_path: str, branch_open_path: str) -> str:
    """
    树形控件样式（QTreeWidget）。
    参数：
      checkmark_path: 勾选图标 SVG 的绝对路径
      partial_path: 半选图标 SVG 的绝对路径
      branch_closed_path: 折叠分支图标 SVG 的绝对路径
      branch_open_path: 展开分支图标 SVG 的绝对路径
    特点：浅灰背景、品牌色选中态、自定义复选框指示器、自带滚动条。
    应用于：_ScopeSelectionDialog 中的目录树。
    """
    return f"""
    QTreeWidget {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        background-color: {COLORS.BG_SECONDARY};
        font-size: {BTN.FONT_SIZE};
        outline: none;
        padding: 4px;
    }}
    QTreeWidget::item {{
        padding: 4px 2px;
        border-radius: {RADIUS.SMALL}px;
        border: none;
    }}
    QTreeWidget::item:hover {{
        background-color: {COLORS.BG_HOVER};
    }}
    QTreeWidget::item:selected {{
        background-color: {COLORS.BRAND_LIGHT_BG};
        color: {COLORS.TEXT_PRIMARY};
    }}
    QTreeWidget::branch {{
        background: transparent;
    }}
    QTreeWidget::branch:has-children:!closed {{
        image: url({branch_open_path});
        background: transparent;
    }}
    QTreeWidget::branch:closed:has-children {{
        image: url({branch_closed_path});
        background: transparent;
    }}
    QTreeWidget::indicator {{
        width: 16px;
        height: 16px;
        border-radius: {RADIUS.SMALL}px;
        border: 2px solid {COLORS.BORDER_HOVER};
        background-color: {COLORS.BG_PRIMARY};
    }}
    QTreeWidget::indicator:hover {{
        border-color: {COLORS.BRAND};
        background-color: {COLORS.BRAND_LIGHT_BG};
    }}
    QTreeWidget::indicator:unchecked {{
        image: none;
    }}
    QTreeWidget::indicator:checked {{
        background-color: {COLORS.BRAND};
        border-color: {COLORS.BRAND};
        image: url({checkmark_path});
    }}
    QTreeWidget::indicator:checked:hover {{
        background-color: {COLORS.BRAND_HOVER};
        border-color: {COLORS.BRAND_HOVER};
        image: url({checkmark_path});
    }}
    QTreeWidget::indicator:indeterminate {{
        background-color: {COLORS.BRAND};
        border-color: {COLORS.BRAND};
        image: url({partial_path});
    }}
    QTreeWidget::indicator:indeterminate:hover {{
        background-color: {COLORS.BRAND_HOVER};
        border-color: {COLORS.BRAND_HOVER};
        image: url({partial_path});
    }}
    """ + scrollbar_style()


# ============================================================================
# 5. 标签系列
# ============================================================================


def label_caption_style() -> str:
    """
    辅助说明标签样式。
    特点：12px 字号、三级文字色（灰色）、透明背景。
    应用于：对话框描述文字、设置页标签、筛选栏排序标签。
    """
    return f"font-size: {BTN.SMALL_FONT_SIZE}; color: {COLORS.TEXT_TERTIARY}; border: none; background: transparent; text-decoration: none;"


def label_micro_style() -> str:
    """
    微型标签样式。
    特点：11px 字号、三级文字色（灰色）、透明背景。
    应用于：目录路径标签、范围详情标签、弹窗计数标签。
    """
    return f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.TEXT_TERTIARY}; border: none; background: transparent; text-decoration: none;"


def label_body_style() -> str:
    """
    正文标签样式。
    特点：13px 字号、三级文字色（灰色）、透明背景。
    应用于：ScanProgressDialog 中的"已发现 N 个文件"标签。
    """
    return f"font-size: {BTN.FONT_SIZE}; color: {COLORS.TEXT_TERTIARY}; border: none; background: transparent; text-decoration: none;"


def label_header_style() -> str:
    """
    小标题标签样式。
    特点：12px 字号、粗体、一级文字色（深色）、透明背景。
    应用于：SearchScopePanel 中的"指定搜索范围"/"管理扫描路径"标题。
    """
    return f"font-size: {BTN.SMALL_FONT_SIZE}; font-weight: bold; color: {COLORS.TEXT_PRIMARY}; border: none; background: transparent; text-decoration: none;"


def badge_style(bg_color: str = COLORS.BG_HOVER, text_color: str = COLORS.TEXT_SECONDARY) -> str:
    """
    通用徽章/标签样式。
    参数：
      bg_color: 背景色，默认浅灰
      text_color: 文字色，默认二级灰
    特点：5px 圆角、小内边距、11px 字号、无边框。
    应用于：ResultListWidget 中的文件类型/大小/日期标签。
    """
    return f"""
        background-color: {bg_color};
        color: {text_color};
        border-radius: 5px;
        padding: 2px 8px;
        font-size: {BTN.TAG_FONT_SIZE};
        border: none;
    """


def badge_brand_style() -> str:
    """
    品牌色徽章样式（浅紫背景 + 紫色文字 + 粗体）。
    应用于：ResultListWidget 中的"匹配 N 处"数量标签。
    """
    return badge_style(COLORS.BRAND_LIGHTER_BG, COLORS.BRAND) + f"font-weight: {BTN.FONT_WEIGHT};"


# ============================================================================
# 6. 布局组件样式
# ============================================================================


def status_bar_style() -> str:
    """
    状态栏样式。
    特点：极浅灰背景、顶部灰色分割线、标签灰色小字。
    应用于：MainWindow 底部状态栏。
    """
    return f"""
    QStatusBar {{
        background-color: {COLORS.BG_SECONDARY};
        border-top: 1px solid {COLORS.BORDER_DEFAULT};
        padding: 4px 12px;
        min-height: 36px;
    }}
    QStatusBar QLabel {{
        color: {COLORS.TEXT_SECONDARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        padding: 0 6px;
        border: none;
        background: transparent;
    }}
"""


def status_divider_style() -> str:
    """
    状态栏分隔符样式（竖线 "|"）。
    特点：边框色文字、12px 字号、透明背景。
    应用于：MainWindow 状态栏中的 "|" 分隔符标签。
    """
    return f"""
    QLabel {{
        color: {COLORS.BORDER_HOVER};
        padding: 0 2px;
        font-size: {BTN.SMALL_FONT_SIZE};
        border: none;
        background: transparent;
    }}
"""


def splitter_style() -> str:
    return f"""
    QSplitter::handle {{
        background-color: {COLORS.BORDER_DEFAULT};
        margin: 2px 1px;
    }}
    QSplitter::handle:hover {{
        background-color: {COLORS.BRAND};
        margin: 1px 0px;
    }}
"""


def menubar_style() -> str:
    """
    菜单栏样式（QMenuBar）。
    特点：极浅灰背景、底部灰色分割线、小圆角菜单项。
    应用于：MainWindow 顶部菜单栏。
    """
    return f"""
    QMenuBar {{
        background-color: {COLORS.BG_SECONDARY};
        border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
        padding: 2px 8px;
        font-size: {BTN.FONT_SIZE};
    }}
    QMenuBar::item {{
        padding: 4px 12px;
        border-radius: {RADIUS.SMALL}px;
        color: {COLORS.TEXT_SECONDARY};
    }}
    QMenuBar::item:selected {{
        background-color: {COLORS.BG_HOVER};
        color: {COLORS.TEXT_PRIMARY};
    }}
"""


def scan_log_style() -> str:
    """
    扫描日志文本框样式（QTextEdit，只读）。
    特点：浅灰背景、灰色描边、小字号、辅助文字色。
    应用于：ScanProgressDialog 中的扫描日志区域。
    """
    return f"""
    QTextEdit {{
        background-color: {COLORS.BG_TERTIARY};
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        padding: 8px;
        font-size: {BTN.TAG_FONT_SIZE};
        color: {COLORS.TEXT_TERTIARY};
    }}
"""
