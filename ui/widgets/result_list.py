import os
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QWidget, QVBoxLayout,
                             QLabel, QHBoxLayout, QFrame, QApplication,
                             QAbstractItemView, QProgressBar, QStackedWidget, QSizePolicy,
                             QPushButton)
from PySide6.QtGui import QFont, QIcon, QFontMetrics, QDrag, QPixmap, QPainter, QColor, QPen, QKeySequence, QPainterPath
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QUrl, QPoint, QRectF, QTimer
from models import SearchResult
from ..style_constants import COLORS, FONT, RADIUS, BTN
from ..style_manager import (
    scrollbar_style, menu_style, badge_style, badge_brand_style,
    progress_bar_style, label_caption_style, label_micro_style,
)
from ..style_constants import FILE_ICON_MAP
from .rounded_menu import RoundedMenu


class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full_text = text
        self._elide_mode = Qt.TextElideMode.ElideRight

    def set_elide_mode(self, mode):
        self._elide_mode = mode

    def setText(self, text):
        self._full_text = text
        super().setText(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self):
        fm = self.fontMetrics()
        available = self.width()
        elided = fm.elidedText(self._full_text, self._elide_mode, available)
        super().setText(elided)

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self):
        return QSize(0, super().minimumSizeHint().height())


LIST_STYLE = f"""
    QListWidget {{
        background-color: {COLORS.BG_PRIMARY};
        border: none;
        outline: none;
        padding: 8px 6px;
    }}
    QListWidget::item {{
        border-radius: {RADIUS.LARGE}px;
        margin: 2px 4px;
        padding: 0px;
        background: transparent;
        border: none;
        outline: none;
    }}
    QListWidget::item:selected {{
        background: transparent;
        border: none;
        outline: none;
    }}
    {scrollbar_style()}
"""

CENTER_PROGRESS_STYLE = progress_bar_style(8, 4)

UNIFIED_MENU_STYLE = menu_style(rounded=True)


class ResultItemWidget(QFrame):
    _icon_cache: dict = {}

    def __init__(self, result: SearchResult, selected: bool = False, parent=None):
        super().__init__(parent)
        self._result = result
        self._selected = selected
        self._init_ui()
        if selected:
            self._apply_selected_style()

    @classmethod
    def _get_cached_pixmap(cls, icon_name: str, size: QSize) -> QPixmap:
        key = (icon_name, size.width(), size.height())
        if key not in cls._icon_cache:
            cls._icon_cache[key] = QIcon(f"icons/{icon_name}").pixmap(size)
        return cls._icon_cache[key]

    def _get_icon_name(self) -> str:
        if self._result.file_item.is_directory:
            return 'doctype/Folder.svg'
        ext = self._result.file_item.extension.lower()
        return FILE_ICON_MAP.get(ext, 'doctype/File.svg')

    def _get_type_label(self) -> str:
        if self._result.file_item.is_directory:
            return '文件夹'
        file_type = self._result.file_item.file_type
        labels = {
            'document': '文档', 'code': '代码', 'image': '图片',
            'video': '视频', 'audio': '音频', 'archive': '压缩包', 'other': '其他'
        }
        return labels.get(file_type, '其他')

    def _get_match_badge(self) -> str:
        count = len(self._result.content_matches)
        if not count:
            return ""
        return f"  匹配 {count} 处"

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 8, 14, 8)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_name = self._get_icon_name()
        icon_label.setPixmap(self._get_cached_pixmap(icon_name, QSize(28, 28)))
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("border: none; background: transparent;")

        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        name_label = ElidedLabel(self._result.file_item.name)
        name_font = QFont()
        name_font.setPointSize(FONT.BODY_PT)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent; border: none;")
        name_label.setTextFormat(Qt.TextFormat.PlainText)
        name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        match_badge = self._get_match_badge()
        match_label = QLabel(match_badge)
        match_label.setStyleSheet(f"color: {COLORS.BRAND}; font-size: {BTN.SMALL_FONT_SIZE}; font-weight: bold; background: transparent; border: none;")

        name_row.addWidget(name_label, 1)
        if match_badge:
            name_row.addWidget(match_label)

        dir_path = os.path.dirname(self._result.file_item.path)
        path_label = ElidedLabel(dir_path)
        path_font = QFont()
        path_font.setPointSize(FONT.MICRO_PT)
        path_label.setFont(path_font)
        path_label.setStyleSheet(f"color: {COLORS.TEXT_TERTIARY}; background: transparent; border: none;")
        path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        path_label.set_elide_mode(Qt.TextElideMode.ElideLeft)

        info_row = QHBoxLayout()
        info_row.setSpacing(10)

        type_label = QLabel(self._get_type_label())
        type_label.setStyleSheet(badge_style())

        size_label = QLabel(self._result.file_item.size_display)
        size_label.setStyleSheet(badge_style())

        date_label = QLabel(self._result.file_item.modified_date)
        date_label.setStyleSheet(badge_style())

        info_row.addWidget(type_label)
        if size_label.text():
            info_row.addWidget(size_label)
        if date_label.text():
            info_row.addWidget(date_label)

        if self._result.file_item.is_directory and self._result.file_item.item_count > 0:
            item_count_label = QLabel(self._result.file_item.item_count_display)
            item_count_label.setStyleSheet(badge_brand_style())
            info_row.addWidget(item_count_label)

        info_row.addStretch()

        content_layout.addLayout(name_row)
        content_layout.addWidget(path_label)
        content_layout.addLayout(info_row)

        layout.addWidget(icon_label)
        layout.addLayout(content_layout)

        self.setLayout(layout)
        self.setObjectName("resultItemWidget")
        self.setMinimumHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_default_style()

    def _apply_default_style(self):
        self.setStyleSheet(f"""
            QFrame#resultItemWidget {{
                background-color: {COLORS.BG_PRIMARY};
                border-radius: {RADIUS.LARGE}px;
                border: 1px solid transparent;
            }}
            QFrame#resultItemWidget:hover {{
                background-color: {COLORS.BG_TERTIARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
            }}
        """)

    def _apply_selected_style(self):
        self.setStyleSheet(f"""
            QFrame#resultItemWidget {{
                background-color: {COLORS.BRAND_LIGHT_BG};
                border-radius: {RADIUS.LARGE}px;
                border: 2px solid {COLORS.BRAND};
            }}
        """)

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self._apply_selected_style()
        else:
            self._apply_default_style()

    def get_result(self) -> SearchResult:
        return self._result


class ResultListWidget(QListWidget):
    result_activated = Signal(object)
    result_selected = Signal(object)
    status_info_requested = Signal(object)

    INITIAL_DISPLAY_LIMIT = 200
    LOAD_MORE_BATCH = 100

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []
        self._all_results = []
        self._item_widgets = {}
        self._anchor_index = -1
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setStyleSheet(LIST_STYLE)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.setDragEnabled(True)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_double_click)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.itemSelectionChanged.connect(self._on_selection_changed)

        self._progress_overlay = None
        self._progress_bar = None
        self._progress_label = None
        self._empty_widget = None
        self._empty_text_label = None
        self._idle_widget = None
        self._load_more_widget = None
        self._setup_progress_overlay()
        self._setup_empty_state()
        self._setup_idle_state()
        self._setup_load_more()

    def _setup_progress_overlay(self):
        self._progress_overlay = QFrame(self.viewport())
        self._progress_overlay.setMinimumWidth(280)
        self._progress_overlay.setMaximumWidth(360)
        self._progress_overlay.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.OVERLAY_LIGHT};
                border-radius: {RADIUS.XLARGE}px;
            }}
        """)
        overlay_layout = QVBoxLayout(self._progress_overlay)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.setSpacing(6)
        overlay_layout.setContentsMargins(32, 24, 32, 24)

        self._progress_label = QLabel("正在搜索...")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setStyleSheet(f"""
            font-size: 15px;
            font-weight: bold;
            color: {COLORS.TEXT_SECONDARY};
            background: transparent;
            border: none;
        """)
        overlay_layout.addWidget(self._progress_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(8)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(CENTER_PROGRESS_STYLE)
        overlay_layout.addWidget(self._progress_bar)

        # 文件进度标签：显示 "已搜索 123/456 个文件"
        self._progress_file_label = QLabel("")
        self._progress_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_file_label.setStyleSheet(f"""
            font-size: {FONT.CAPTION_PT}px;
            color: {COLORS.TEXT_TERTIARY};
            background: transparent;
            border: none;
        """)
        self._progress_file_label.setVisible(False)
        overlay_layout.addWidget(self._progress_file_label)

        # 当前搜索文件标签：显示正在搜索的文件名
        self._progress_current_file_label = QLabel("")
        self._progress_current_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_current_file_label.setStyleSheet(f"""
            font-size: {FONT.MICRO_PT}px;
            color: {COLORS.TEXT_TERTIARY};
            background: transparent;
            border: none;
        """)
        self._progress_current_file_label.setWordWrap(True)
        self._progress_current_file_label.setVisible(False)
        overlay_layout.addWidget(self._progress_current_file_label)

        # 耐心等待提示标签
        self._progress_patience_label = QLabel("")
        self._progress_patience_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_patience_label.setStyleSheet(f"""
            font-size: {FONT.MICRO_PT}px;
            color: {COLORS.TEXT_BRAND};
            background: transparent;
            border: none;
        """)
        self._progress_patience_label.setVisible(False)
        overlay_layout.addWidget(self._progress_patience_label)

        self._progress_overlay.setVisible(False)

    def _setup_empty_state(self):
        self._empty_widget = QFrame(self.viewport())
        self._empty_widget.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        layout = QVBoxLayout(self._empty_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        empty_icon = QLabel()
        empty_icon.setPixmap(QIcon("icons/search-alt.svg").pixmap(QSize(64, 64)))
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet("background: transparent; border: none;")

        self._empty_text_label = QLabel("未找到匹配文件")
        self._empty_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_text_label.setStyleSheet(f"""
            font-size: {FONT.TITLE_PT}px;
            font-weight: bold;
            color: {COLORS.TEXT_PLACEHOLDER};
            background: transparent;
            border: none;
        """)

        hint_label = QLabel("尝试修改搜索条件或扩大搜索范围")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet(f"""
            font-size: {FONT.CAPTION_PT}px;
            color: {COLORS.TEXT_TERTIARY};
            background: transparent;
            border: none;
        """)

        layout.addStretch()
        layout.addWidget(empty_icon, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty_text_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        self._empty_widget.setVisible(False)

    def _setup_idle_state(self):
        """创建空闲引导页面（未搜索时显示）"""
        self._idle_widget = QFrame(self.viewport())
        self._idle_widget.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        layout = QVBoxLayout(self._idle_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        idle_icon = QLabel()
        idle_icon.setPixmap(QIcon("icons/search-alt.svg").pixmap(QSize(72, 72)))
        idle_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_icon.setStyleSheet("background: transparent; border: none;")

        idle_title = QLabel("开始搜索")
        idle_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_title.setStyleSheet(f"""
            font-size: {FONT.TITLE_PT + 2}px;
            font-weight: bold;
            color: {COLORS.TEXT_PLACEHOLDER};
            background: transparent;
            border: none;
        """)

        idle_hint = QLabel("输入关键词查找文件")
        idle_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_hint.setStyleSheet(f"""
            font-size: {FONT.CAPTION_PT}px;
            color: {COLORS.TEXT_TERTIARY};
            background: transparent;
            border: none;
        """)

        layout.addStretch()
        layout.addWidget(idle_icon, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(idle_title, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(idle_hint, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        self._idle_widget.setVisible(False)

    def _setup_load_more(self):
        """创建「加载更多」按钮组件"""
        self._load_more_widget = QFrame(self)
        self._load_more_widget.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
            }}
        """)
        layout = QVBoxLayout(self._load_more_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 8, 0, 8)

        self._load_more_btn = QPushButton("加载更多结果")
        self._load_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._load_more_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_SECONDARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {RADIUS.MEDIUM}px;
                padding: 8px 24px;
                font-size: {BTN.SMALL_FONT_SIZE};
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_TERTIARY};
                border-color: {COLORS.BORDER_HOVER};
            }}
        """)
        self._load_more_btn.clicked.connect(self._on_load_more)
        layout.addWidget(self._load_more_btn, 0, Qt.AlignmentFlag.AlignCenter)
        self._load_more_widget.setVisible(False)

    def _position_load_more(self):
        if not self._load_more_widget or not self._load_more_widget.isVisible():
            return
        y = self.viewport().height() - self._load_more_widget.height()
        self._load_more_widget.setGeometry(0, y, self.viewport().width(), self._load_more_widget.height())

    def _on_load_more(self):
        """加载更多搜索结果"""
        current_count = len(self._results)
        remaining = self._all_results[current_count:]
        if not remaining:
            self._load_more_widget.setVisible(False)
            return
        batch = remaining[:self.LOAD_MORE_BATCH]
        self.setUpdatesEnabled(False)
        for result in batch:
            idx = len(self._results)
            self._results.append(result)
            item = QListWidgetItem(self)
            widget = ResultItemWidget(result)
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)
            self._item_widgets[idx] = widget
        self.setUpdatesEnabled(True)
        self.viewport().update()
        new_count = len(self._results)
        if new_count < len(self._all_results):
            self._load_more_btn.setText(f"加载更多结果（还有 {len(self._all_results) - new_count} 项）")
        else:
            self._load_more_widget.setVisible(False)

    def _position_empty_widget(self):
        if not self._empty_widget:
            return
        vp = self.viewport()
        self._empty_widget.setGeometry(0, 0, vp.width(), vp.height())

    def show_empty_state(self, text: str = "未找到匹配文件"):
        self.hide_idle_state()
        if self._empty_text_label:
            self._empty_text_label.setText(text)
        if self._empty_widget:
            self._empty_widget.setVisible(True)
            self._empty_widget.raise_()
            self._position_empty_widget()

    def hide_empty_state(self):
        if self._empty_widget:
            self._empty_widget.setVisible(False)

    def show_coming_soon(self, text: str = "功能即将上线"):
        """显示功能未实现的提示页面"""
        self.hide_idle_state()
        self.show_empty_state(text)

    def show_idle_state(self):
        """显示空闲引导页面（未搜索时）"""
        self.hide_empty_state()
        if self._idle_widget:
            self._idle_widget.setVisible(True)
            self._idle_widget.raise_()
            self._position_idle_widget()

    def hide_idle_state(self):
        """隐藏空闲引导页面"""
        if self._idle_widget:
            self._idle_widget.setVisible(False)

    def _position_idle_widget(self):
        if not self._idle_widget:
            return
        vp = self.viewport()
        self._idle_widget.setGeometry(0, 0, vp.width(), vp.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._progress_overlay and self._progress_overlay.isVisible():
            self._position_progress_overlay()
        if self._empty_widget and self._empty_widget.isVisible():
            self._position_empty_widget()
        if self._idle_widget and self._idle_widget.isVisible():
            self._position_idle_widget()
        if self._load_more_widget and self._load_more_widget.isVisible():
            self._position_load_more()

    def _position_progress_overlay(self):
        if not self._progress_overlay:
            return
        overlay_w = min(self.width() - 40, 360)
        # 让 overlay 根据内容自动计算高度
        self._progress_overlay.adjustSize()
        overlay_h = self._progress_overlay.sizeHint().height()
        # 限制最大高度不超过视口高度的 80%
        max_h = int(self.height() * 0.8)
        overlay_h = min(overlay_h, max_h)
        x = (self.width() - overlay_w) // 2
        y = (self.height() - overlay_h) // 2
        self._progress_overlay.setGeometry(x, y, overlay_w, overlay_h)

    def show_search_progress(self, text: str = "正在搜索..."):
        self.hide_empty_state()
        if self._progress_label:
            self._progress_label.setText(text)
        if self._progress_overlay:
            self._progress_overlay.setVisible(True)
            self._progress_overlay.raise_()
            self._position_progress_overlay()

    def update_search_progress(self, processed: int, total: int):
        """更新搜索进度详情

        Args:
            processed: 已处理的文件数
            total: 总文件数
        """
        if not self._progress_overlay or not self._progress_overlay.isVisible():
            return

        # 更新进度条为确定模式
        if total > 0:
            self._progress_bar.setMaximum(total)
            self._progress_bar.setValue(processed)

        # 更新文件进度标签
        if self._progress_file_label:
            self._progress_file_label.setText(f"已搜索 {processed}/{total} 个文件")
            self._progress_file_label.setVisible(True)

        # 文件数量较多时显示耐心等待提示
        if self._progress_patience_label:
            if total > 500:
                self._progress_patience_label.setText("文件较多，请耐心等待...")
                self._progress_patience_label.setVisible(True)
            elif total > 100:
                self._progress_patience_label.setText("搜索中，请稍候...")
                self._progress_patience_label.setVisible(True)
            else:
                self._progress_patience_label.setVisible(False)

        self._position_progress_overlay()

    def update_searching_file(self, file_path: str):
        """更新当前正在搜索的文件路径显示

        Args:
            file_path: 当前正在搜索的文件路径
        """
        if not self._progress_overlay or not self._progress_overlay.isVisible():
            return

        if self._progress_current_file_label:
            # 只显示文件名，避免路径过长
            filename = os.path.basename(file_path)
            self._progress_current_file_label.setText(f"正在搜索: {filename}")
            self._progress_current_file_label.setVisible(True)

    def hide_search_progress(self):
        if self._progress_overlay:
            self._progress_overlay.setVisible(False)
        # 重置进度条为不确定模式
        if self._progress_bar:
            self._progress_bar.setMaximum(0)
            self._progress_bar.setValue(0)
        # 隐藏详情标签
        if hasattr(self, '_progress_file_label'):
            self._progress_file_label.setVisible(False)
        if hasattr(self, '_progress_current_file_label'):
            self._progress_current_file_label.setVisible(False)
        if hasattr(self, '_progress_patience_label'):
            self._progress_patience_label.setVisible(False)

    def add_result(self, result: SearchResult):
        idx = len(self._results)
        self._results.append(result)
        item = QListWidgetItem(self)
        widget = ResultItemWidget(result)
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)
        self._item_widgets[idx] = widget

    def clear_results(self):
        self._results.clear()
        self._all_results.clear()
        self._item_widgets.clear()
        self._anchor_index = -1
        self._prev_selected_rows = set()
        self._load_more_widget.setVisible(False)
        self.clear()

    def set_results(self, results):
        self._all_results = list(results)
        self._pending_results = self._all_results[:self.INITIAL_DISPLAY_LIMIT]
        self._pending_index = 0
        self._results.clear()
        self._item_widgets.clear()
        self._anchor_index = -1
        self._prev_selected_rows = set()
        self.clear()
        self._load_more_widget.setVisible(False)
        self._batch_add()

    def _batch_add(self):
        if not hasattr(self, '_pending_results') or self._pending_index >= len(self._pending_results):
            # 所有批次添加完成，检查是否需要显示「加载更多」
            if len(self._results) < len(self._all_results):
                remaining = len(self._all_results) - len(self._results)
                self._load_more_btn.setText(f"加载更多结果（还有 {remaining} 项）")
                self._load_more_widget.setVisible(True)
                self._position_load_more()
            return

        batch_size = 50
        end = min(self._pending_index + batch_size, len(self._pending_results))
        self.setUpdatesEnabled(False)
        for i in range(self._pending_index, end):
            result = self._pending_results[i]
            idx = len(self._results)
            self._results.append(result)
            item = QListWidgetItem(self)
            widget = ResultItemWidget(result)
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)
            self._item_widgets[idx] = widget
        self.setUpdatesEnabled(True)
        self.viewport().update()
        self._pending_index = end

        if self._pending_index < len(self._pending_results):
            QTimer.singleShot(10, self._batch_add)
        else:
            # 所有批次添加完成，检查是否需要显示「加载更多」
            if len(self._results) < len(self._all_results):
                remaining = len(self._all_results) - len(self._results)
                self._load_more_btn.setText(f"加载更多结果（还有 {remaining} 项）")
                self._load_more_widget.setVisible(True)
                self._position_load_more()

    def get_selected_result(self):
        items = self.selectedItems()
        if items:
            index = self.row(items[0])
            if 0 <= index < len(self._results):
                return self._results[index]
        return None

    def get_selected_results(self):
        results = []
        for item in self.selectedItems():
            index = self.row(item)
            if 0 <= index < len(self._results):
                results.append(self._results[index])
        return results

    def _on_selection_changed(self):
        selected_rows = {self.row(item) for item in self.selectedItems()}
        if not hasattr(self, '_prev_selected_rows'):
            self._prev_selected_rows = set()

        changed = selected_rows.symmetric_difference(self._prev_selected_rows)
        for idx in changed:
            if idx in self._item_widgets:
                self._item_widgets[idx].set_selected(idx in selected_rows)
        self._prev_selected_rows = selected_rows

        if selected_rows:
            last_idx = max(selected_rows)
            if 0 <= last_idx < len(self._results):
                self.result_selected.emit(self._results[last_idx])
                self.status_info_requested.emit(self._results[last_idx])
        else:
            # 选中集为空时，发射 None 通知预览面板清空
            self.result_selected.emit(None)
            self.status_info_requested.emit(None)

    def _on_item_clicked(self, item):
        index = self.row(item)
        self._anchor_index = index

    def _on_double_click(self, item):
        index = self.row(item)
        if 0 <= index < len(self._results):
            result = self._results[index]
            if result.file_item.is_directory:
                os.startfile(result.file_item.path)
            else:
                os.startfile(result.file_item.path)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item is None:
            self.clearSelection()
            for w in self._item_widgets.values():
                w.set_selected(False)
        super().mousePressEvent(event)

    def _on_context_menu(self, pos: QPoint):
        item = self.itemAt(pos)
        if item is not None:
            if not item.isSelected():
                self.clearSelection()
                item.setSelected(True)

        result = self.get_selected_result()
        if not result:
            return

        menu = RoundedMenu(self)
        menu.setStyleSheet(UNIFIED_MENU_STYLE)

        open_action = menu.addAction("打开")
        open_action.setShortcut(QKeySequence("Enter"))
        copy_action = menu.addAction("复制")
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_path_action = menu.addAction("复制文件地址")
        copy_path_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        menu.addSeparator()
        props_action = menu.addAction("属性")
        props_action.setShortcut(QKeySequence("Alt+Enter"))

        action = menu.exec(self.mapToGlobal(pos))

        if action == open_action:
            self._open_file(result)
        elif action == copy_action:
            self._copy_file(result)
        elif action == copy_path_action:
            self._copy_path(result)
        elif action == props_action:
            self._show_properties(result)

    def _open_file(self, result: SearchResult):
        try:
            file_path = result.file_item.path
            if os.path.exists(file_path):
                os.startfile(file_path)
        except Exception:
            pass

    def _open_file_path(self, result: SearchResult):
        try:
            directory = os.path.dirname(result.file_item.path)
            if directory and os.path.exists(directory):
                os.system(f'explorer /select,"{result.file_item.path}"')
        except Exception:
            pass

    def _copy_path(self, result: SearchResult):
        clipboard = QApplication.clipboard()
        clipboard.setText(result.file_item.path)

    def _copy_file(self, result: SearchResult):
        """复制文件到剪贴板（可粘贴到资源管理器）"""
        try:
            path = result.file_item.path
            if not os.path.exists(path):
                return
            clipboard = QApplication.clipboard()
            data = QMimeData()
            data.setUrls([QUrl.fromLocalFile(path)])
            clipboard.setMimeData(data)
        except Exception:
            clipboard = QApplication.clipboard()
            clipboard.setText(result.file_item.path)

    def _show_properties(self, result: SearchResult):
        """弹出 Windows 自带的文件属性对话框"""
        try:
            import ctypes
            from ctypes import wintypes
            file_path = result.file_item.path
            if not os.path.exists(file_path):
                return
            SEE_MASK_INVOKEIDLIST = 0x0000000C
            class SHELLEXECUTEINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("fMask", wintypes.ULONG),
                    ("hwnd", wintypes.HWND),
                    ("lpVerb", wintypes.LPCWSTR),
                    ("lpFile", wintypes.LPCWSTR),
                    ("lpParameters", wintypes.LPCWSTR),
                    ("lpDirectory", wintypes.LPCWSTR),
                    ("nShow", ctypes.c_int),
                    ("hInstApp", wintypes.HINSTANCE),
                    ("lpIDList", ctypes.c_void_p),
                    ("lpClass", wintypes.LPCWSTR),
                    ("hKeyClass", wintypes.HKEY),
                    ("dwHotKey", wintypes.DWORD),
                    ("hIconOrMonitor", wintypes.HANDLE),
                    ("hProcess", wintypes.HANDLE),
                ]
            sei = SHELLEXECUTEINFO()
            sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
            sei.fMask = SEE_MASK_INVOKEIDLIST
            sei.lpVerb = "properties"
            sei.lpFile = file_path
            sei.nShow = 1
            ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
        except Exception:
            pass

    def keyPressEvent(self, event):
        # Alt+Enter: 属性
        if event.key() == Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.AltModifier:
            result = self.get_selected_result()
            if result:
                self._show_properties(result)
            return

        # Ctrl+Shift+C: 复制文件地址
        if event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            result = self.get_selected_result()
            if result:
                self._copy_path(result)
            return

        # Ctrl+C: 复制文件
        if event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            result = self.get_selected_result()
            if result:
                self._copy_file(result)
            return

        # Enter: 打开
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            result = self.get_selected_result()
            if result:
                self._open_file(result)
            return

        if event.key() == Qt.Key.Key_Down:
            if not self.selectedItems() and self.count() > 0:
                self.item(0).setSelected(True)
                self.setCurrentRow(0)
                self._scroll_to_index(0)
                return
            current = self.currentRow()
            if current < self.count() - 1:
                new_idx = current + 1
                if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.clearSelection()
                self.item(new_idx).setSelected(True)
                self.setCurrentRow(new_idx)
                self._scroll_to_index(new_idx)
            return

        if event.key() == Qt.Key.Key_Up:
            current = self.currentRow()
            if current > 0:
                new_idx = current - 1
                if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.clearSelection()
                self.item(new_idx).setSelected(True)
                self.setCurrentRow(new_idx)
                self._scroll_to_index(new_idx)
            return

        super().keyPressEvent(event)

    def _scroll_to_index(self, index):
        self.scrollToItem(self.item(index), QAbstractItemView.ScrollHint.EnsureVisible)

    def mimeData(self, items):
        results = self.get_selected_results()
        if not results:
            return None
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(r.file_item.path) for r in results]
        mime_data.setUrls(urls)
        return mime_data

    def startDrag(self, supportedActions):
        results = self.get_selected_results()
        if not results:
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(r.file_item.path) for r in results]
        mime_data.setUrls(urls)
        drag.setMimeData(mime_data)

        if len(results) == 1:
            result = results[0]
            icon_name = self._get_icon_for_result(result)
            icon = QIcon(f"icons/{icon_name}")
            name = result.file_item.name

            pm_w, pm_h = 220, 52
            pixmap = QPixmap(pm_w, pm_h)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 20))
            painter.drawRoundedRect(2, 3, pm_w - 2, pm_h - 3, 10, 10)

            painter.setBrush(QColor(COLORS.BG_PRIMARY))
            painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 1))
            painter.drawRoundedRect(0, 0, pm_w - 2, pm_h - 3, 10, 10)

            icon_pixmap = icon.pixmap(QSize(28, 28))
            painter.drawPixmap(10, (pm_h - 3 - 28) // 2, icon_pixmap)

            painter.setPen(QColor(COLORS.TEXT_PRIMARY))
            font = QFont()
            font.setPointSize(FONT.BODY_PT)
            font.setBold(True)
            painter.setFont(font)
            fm = QFontMetrics(font)
            max_text_w = pm_w - 56
            elided = fm.elidedText(name, Qt.TextElideMode.ElideRight, max_text_w)
            painter.drawText(QRectF(44, 0, max_text_w, pm_h - 3), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided)

            painter.end()
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(20, 26))
        else:
            count = len(results)
            pm_w, pm_h = 140, 44
            pixmap = QPixmap(pm_w, pm_h)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 20))
            painter.drawRoundedRect(2, 3, pm_w - 2, pm_h - 3, 10, 10)

            painter.setBrush(QColor(COLORS.BRAND))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, 0, pm_w - 2, pm_h - 3, 10, 10)

            painter.setPen(QColor(COLORS.BG_PRIMARY))
            font = QFont()
            font.setPointSize(FONT.BODY_PT)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRectF(0, 0, pm_w - 2, pm_h - 3), Qt.AlignmentFlag.AlignCenter, f"{count} 个文件")
            painter.end()
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(70, 22))

        drag.exec(Qt.DropAction.CopyAction)

    @staticmethod
    def _get_icon_for_result(result: SearchResult) -> str:
        if result.file_item.is_directory:
            return 'doctype/Folder.svg'
        ext = result.file_item.extension.lower()
        return FILE_ICON_MAP.get(ext, 'doctype/File.svg')
