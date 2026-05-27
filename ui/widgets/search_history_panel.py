"""
搜索历史面板组件
================
显示搜索历史记录，支持分类浏览、再次查询、多选删除和清空操作。
"""

import logging
from datetime import datetime
from typing import List, Optional

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QCheckBox,
                               QSizePolicy, QGraphicsDropShadowEffect)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, QRectF, Property
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics

from models.search_history import SearchHistory
from database.history_dao import get_histories, delete_histories, clear_histories
from ..style_constants import COLORS, FONT, RADIUS, BTN, SPACING
from ..style_manager import scrollbar_style, button_danger, button_secondary, label_caption_style

logger = logging.getLogger(__name__)


class _HistoryItemWidget(QWidget):
    """单条历史记录项组件"""

    search_requested = Signal(str, str, str)  # name_query, content_query, name_mode
    delete_requested = Signal(int)  # history_id

    def __init__(self, history: SearchHistory, show_checkbox: bool = False, parent=None):
        super().__init__(parent)
        self._history = history
        self._hovered = False
        self._checkbox_visible = show_checkbox
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("historyItem")
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.LG, SPACING.SM, SPACING.LG, SPACING.SM)
        layout.setSpacing(SPACING.MD)

        # 复选框
        self._checkbox = QCheckBox()
        self._checkbox.setVisible(self._checkbox_visible)
        self._checkbox.setFixedSize(18, 18)
        self._checkbox.setStyleSheet(f"""
            QCheckBox {{
                spacing: 0;
                outline: none;
                border: none;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: {RADIUS.SMALL}px;
                border: 2px solid {COLORS.BORDER_HOVER};
                background-color: transparent;
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLORS.BRAND};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS.BRAND};
                border-color: {COLORS.BRAND};
            }}
        """)
        layout.addWidget(self._checkbox)

        # 左侧内容区域
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        # 搜索内容
        query_text = self._history.name_query or self._history.content_query or ""
        self._query_label = QLabel(query_text)
        self._query_label.setStyleSheet(f"""
            color: {COLORS.TEXT_PRIMARY};
            font-size: {FONT.BODY_PT}px;
            font-weight: medium;
            border: none;
            background: transparent;
        """)
        self._query_label.setMaximumWidth(300)
        fm = QFontMetrics(QFont("Microsoft YaHei", FONT.BODY_PT))
        elided = fm.elidedText(query_text, Qt.TextElideMode.ElideRight, 300)
        self._query_label.setText(elided)
        if query_text != elided:
            self._query_label.setToolTip(query_text)
        content_layout.addWidget(self._query_label)

        # 模式和时间
        meta_layout = QHBoxLayout()
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(SPACING.SM)

        mode_label = QLabel(self._history.mode_display)
        mode_label.setStyleSheet(f"""
            background-color: {COLORS.BRAND_LIGHTER_BG};
            color: {COLORS.TEXT_BRAND};
            border-radius: 4px;
            padding: 1px 6px;
            font-size: {FONT.MICRO_PT}px;
            border: none;
        """)
        meta_layout.addWidget(mode_label)

        time_str = self._format_time(self._history.created_at)
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"""
            color: {COLORS.TEXT_PLACEHOLDER};
            font-size: {FONT.MICRO_PT}px;
            border: none;
            background: transparent;
        """)
        meta_layout.addWidget(time_label)
        meta_layout.addStretch()

        content_layout.addLayout(meta_layout)
        layout.addLayout(content_layout, 1)

        # 删除按钮
        self._delete_btn = QPushButton("×")
        self._delete_btn.setFixedSize(24, 24)
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.setVisible(False)
        self._delete_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-radius: {RADIUS.SMALL}px;
                background: transparent;
                color: {COLORS.TEXT_PLACEHOLDER};
                font-size: 14px;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS.ERROR_LIGHT_BG};
                color: {COLORS.ERROR};
            }}
        """)
        self._delete_btn.clicked.connect(lambda: self.delete_requested.emit(self._history.id))
        layout.addWidget(self._delete_btn)

    @staticmethod
    def _format_time(dt: datetime) -> str:
        """格式化时间为友好展示文本"""
        now = datetime.now()
        delta = now - dt
        if delta.days == 0:
            hours = delta.seconds // 3600
            if hours == 0:
                minutes = delta.seconds // 60
                if minutes <= 1:
                    return "刚刚"
                return f"{minutes}分钟前"
            return f"{hours}小时前"
        elif delta.days == 1:
            return "昨天"
        elif delta.days < 7:
            return f"{delta.days}天前"
        else:
            return dt.strftime("%m-%d %H:%M")

    def set_checkbox_visible(self, visible: bool):
        """设置复选框可见性"""
        self._checkbox_visible = visible
        self._checkbox.setVisible(visible)

    def is_checked(self) -> bool:
        """返回复选框是否选中"""
        return self._checkbox.isChecked()

    def get_history_id(self) -> int:
        """返回历史记录ID"""
        return self._history.id

    def enterEvent(self, event):
        self._hovered = True
        self._delete_btn.setVisible(True)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._delete_btn.setVisible(False)
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 如果点击在复选框区域，不触发搜索
            if self._checkbox_visible and self._checkbox.geometry().contains(event.position().toPoint()):
                self._checkbox.setChecked(not self._checkbox.isChecked())
                return
            # 如果点击在删除按钮区域，不触发搜索
            if self._delete_btn.geometry().contains(event.position().toPoint()):
                return
            # 触发搜索
            name_q = self._history.name_query or ""
            content_q = self._history.content_query or ""
            self.search_requested.emit(name_q, content_q, self._history.name_mode)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._hovered:
            painter.setBrush(QColor(COLORS.BG_HOVER))
        else:
            painter.setBrush(QColor(COLORS.BG_PRIMARY))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), RADIUS.DEFAULT, RADIUS.DEFAULT)
        # 底部分割线
        painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 1))
        painter.drawLine(SPACING.LG, self.height() - 1, self.width() - SPACING.LG, self.height() - 1)
        painter.end()
        super().paintEvent(event)


class SearchHistoryPanel(QWidget):
    """搜索历史面板，显示在搜索栏下方"""

    search_requested = Signal(str, str, str)  # name_query, content_query, name_mode

    # 搜索类型标签
    TAB_LABELS = ['文件名搜索', '文件内容搜索']
    TAB_TYPES = ['name', 'content']

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_tab = 0
        self._select_mode = False
        self._name_histories: List[SearchHistory] = []
        self._content_histories: List[SearchHistory] = []
        self._name_items: List[_HistoryItemWidget] = []
        self._content_items: List[_HistoryItemWidget] = []
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedWidth(460)
        self.setMaximumHeight(420)
        self.setObjectName("historyPanel")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 面板容器
        container = QWidget()
        container.setObjectName("historyContainer")
        container.setStyleSheet(f"""
            QWidget#historyContainer {{
                background-color: {COLORS.BG_PRIMARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {RADIUS.LARGE}px;
            }}
        """)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(0, 4)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 25))
        container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(SPACING.XL, SPACING.LG, SPACING.XL, SPACING.LG)
        container_layout.setSpacing(SPACING.SM)

        # 顶部：标题 + 操作按钮
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING.SM)

        title_label = QLabel("搜索历史")
        title_label.setStyleSheet(f"""
            color: {COLORS.TEXT_PRIMARY};
            font-size: {FONT.TITLE_PT}px;
            font-weight: bold;
            border: none;
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # 多选按钮
        self._select_btn = QPushButton("多选删除")
        self._select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._select_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                color: {COLORS.TEXT_TERTIARY};
                font-size: {FONT.MICRO_PT}px;
                outline: none;
                padding: 4px 8px;
                border-radius: {RADIUS.SMALL}px;
            }}
            QPushButton:hover {{
                color: {COLORS.BRAND};
                background-color: {COLORS.BRAND_LIGHT_BG};
            }}
        """)
        self._select_btn.clicked.connect(self._toggle_select_mode)
        header_layout.addWidget(self._select_btn)

        # 清空按钮
        self._clear_btn = QPushButton("清空")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                color: {COLORS.TEXT_TERTIARY};
                font-size: {FONT.MICRO_PT}px;
                outline: none;
                padding: 4px 8px;
                border-radius: {RADIUS.SMALL}px;
            }}
            QPushButton:hover {{
                color: {COLORS.ERROR};
                background-color: {COLORS.ERROR_LIGHT_BG};
            }}
        """)
        self._clear_btn.clicked.connect(self._on_clear_all)
        header_layout.addWidget(self._clear_btn)

        container_layout.addLayout(header_layout)

        # 标签页切换
        self._tab_bar = QWidget()
        self._tab_bar.setFixedHeight(32)
        self._tab_bar.setObjectName("historyTabBar")
        self._tab_bar.setStyleSheet(f"""
            QWidget#historyTabBar {{
                background-color: {COLORS.BG_SECONDARY};
                border-radius: {RADIUS.DEFAULT}px;
            }}
        """)
        tab_layout = QHBoxLayout(self._tab_bar)
        tab_layout.setContentsMargins(2, 2, 2, 2)
        tab_layout.setSpacing(2)

        self._tab_buttons = []
        for i, label in enumerate(self.TAB_LABELS):
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName(f"tabBtn_{i}")
            btn.setStyleSheet(self._tab_button_style(i == 0))
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            tab_layout.addWidget(btn)
            self._tab_buttons.append(btn)

        container_layout.addWidget(self._tab_bar)

        # 内容区域（滚动区域）
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS.BG_PRIMARY};
                border-radius: {RADIUS.DEFAULT}px;
            }}
        """ + scrollbar_style())

        self._content_widget = QWidget()
        self._content_widget.setStyleSheet(f"background-color: {COLORS.BG_PRIMARY};")
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_layout.addStretch()

        self._scroll_area.setWidget(self._content_widget)
        container_layout.addWidget(self._scroll_area, 1)

        # 多选模式底部操作栏
        self._select_bar = QWidget()
        self._select_bar.setVisible(False)
        self._select_bar.setObjectName("selectBar")
        self._select_bar.setStyleSheet(f"""
            QWidget#selectBar {{
                background-color: {COLORS.BG_SECONDARY};
                border-radius: {RADIUS.DEFAULT}px;
                border-top: 1px solid {COLORS.BORDER_DEFAULT};
            }}
        """)
        select_bar_layout = QHBoxLayout(self._select_bar)
        select_bar_layout.setContentsMargins(SPACING.LG, SPACING.SM, SPACING.LG, SPACING.SM)
        select_bar_layout.setSpacing(SPACING.SM)

        self._select_all_cb = QCheckBox("全选")
        self._select_all_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS.TEXT_SECONDARY};
                font-size: {FONT.CAPTION_PT}px;
                spacing: 6px;
                outline: none;
                border: none;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: {RADIUS.SMALL}px;
                border: 2px solid {COLORS.BORDER_HOVER};
                background-color: transparent;
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLORS.BRAND};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS.BRAND};
                border-color: {COLORS.BRAND};
            }}
        """)
        self._select_all_cb.stateChanged.connect(self._on_select_all)
        select_bar_layout.addWidget(self._select_all_cb)
        select_bar_layout.addStretch()

        self._delete_selected_btn = QPushButton("删除选中")
        self._delete_selected_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_selected_btn.setStyleSheet(button_danger(
            f"padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H}; "
            f"font-size: {BTN.SMALL_FONT_SIZE}; border-radius: {BTN.SMALL_BORDER_RADIUS}px; min-width: 60px;"
        ))
        self._delete_selected_btn.clicked.connect(self._on_delete_selected)
        select_bar_layout.addWidget(self._delete_selected_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(button_secondary(
            f"padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H}; "
            f"font-size: {BTN.SMALL_FONT_SIZE}; border-radius: {BTN.SMALL_BORDER_RADIUS}px; min-width: 60px;"
        ))
        cancel_btn.clicked.connect(self._toggle_select_mode)
        select_bar_layout.addWidget(cancel_btn)

        container_layout.addWidget(self._select_bar)

        # 空状态标签
        self._empty_label = QLabel("暂无搜索历史")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {COLORS.TEXT_PLACEHOLDER};
            font-size: {FONT.CAPTION_PT}px;
            padding: 40px 0;
            border: none;
            background: transparent;
        """)
        self._empty_label.setVisible(False)
        container_layout.addWidget(self._empty_label)

        main_layout.addWidget(container)

    def _tab_button_style(self, active: bool) -> str:
        """生成标签按钮样式"""
        if active:
            return f"""
                QPushButton {{
                    background-color: {COLORS.BRAND};
                    color: {COLORS.BG_PRIMARY};
                    border: none;
                    border-radius: {RADIUS.DEFAULT - 2}px;
                    padding: 4px 16px;
                    font-size: {FONT.MICRO_PT}px;
                    font-weight: bold;
                    outline: none;
                }}
                QPushButton:hover {{
                    background-color: {COLORS.BRAND_HOVER};
                }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS.TEXT_TERTIARY};
                border: none;
                border-radius: {RADIUS.DEFAULT - 2}px;
                padding: 4px 16px;
                font-size: {FONT.MICRO_PT}px;
                outline: none;
            }}
            QPushButton:hover {{
                color: {COLORS.TEXT_PRIMARY};
                background-color: {COLORS.BG_HOVER};
            }}
        """

    def _switch_tab(self, index: int):
        """切换标签页"""
        self._current_tab = index
        for i, btn in enumerate(self._tab_buttons):
            btn.setStyleSheet(self._tab_button_style(i == index))
        self._refresh_display()

    def _toggle_select_mode(self):
        """切换多选模式"""
        self._select_mode = not self._select_mode
        self._select_bar.setVisible(self._select_mode)
        self._select_all_cb.setChecked(False)
        items = self._current_items()
        for item in items:
            item.set_checkbox_visible(self._select_mode)
        if not self._select_mode:
            for item in items:
                item._checkbox.setChecked(False)

    def _on_select_all(self, state):
        """全选/取消全选"""
        checked = state == Qt.CheckState.Checked.value
        for item in self._current_items():
            item._checkbox.setChecked(checked)

    def _current_items(self) -> List[_HistoryItemWidget]:
        """返回当前标签页的项列表"""
        if self._current_tab == 0:
            return self._name_items
        return self._content_items

    def _on_delete_selected(self):
        """删除选中的历史记录"""
        ids = [item.get_history_id() for item in self._current_items() if item.is_checked()]
        if not ids:
            return
        from ..modern_dialog import styled_msg_box
        from PySide6.QtWidgets import QMessageBox, QApplication
        parent = QApplication.activeWindow()
        reply = styled_msg_box(
            parent, QMessageBox.Icon.Question,
            "确认删除",
            f"确定要删除选中的 {len(ids)} 条搜索历史吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_histories(ids)
            self.refresh()

    def _on_clear_all(self):
        """清空所有历史记录"""
        from ..modern_dialog import styled_msg_box
        from PySide6.QtWidgets import QMessageBox, QApplication
        parent = QApplication.activeWindow()
        reply = styled_msg_box(
            parent, QMessageBox.Icon.Question,
            "确认清空",
            "确定要清空所有搜索历史吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_histories()
            self.refresh()

    def refresh(self):
        """从数据库刷新历史记录"""
        histories = get_histories(limit=100)
        self._name_histories = []
        self._content_histories = []

        for h in histories:
            if h.search_type == 'name':
                self._name_histories.append(h)
            else:
                self._content_histories.append(h)

        self._refresh_display()

    def _refresh_display(self):
        """刷新当前标签页的显示"""
        # 清除现有内容
        while self._content_layout.count() > 0:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 获取当前标签页的数据
        if self._current_tab == 0:
            histories_data = self._name_histories
        else:
            histories_data = self._content_histories

        items = []

        for h in histories_data:
            item_widget = _HistoryItemWidget(h, show_checkbox=self._select_mode)
            item_widget.search_requested.connect(self._on_item_search)
            item_widget.delete_requested.connect(self._on_item_delete)
            self._content_layout.addWidget(item_widget)
            items.append(item_widget)

        # 更新内部项列表引用（用于多选操作）
        if self._current_tab == 0:
            self._name_items = items
        else:
            self._content_items = items

        self._content_layout.addStretch()

        # 空状态
        has_items = len(items) > 0
        self._empty_label.setVisible(not has_items)
        self._scroll_area.setVisible(has_items)
        self._tab_bar.setVisible(True)

        # 更新标签页计数
        name_count = len(self._name_histories)
        content_count = len(self._content_histories)
        self._tab_buttons[0].setText(f"文件名搜索 ({name_count})")
        self._tab_buttons[1].setText(f"文件内容搜索 ({content_count})")

    def _on_item_search(self, name_query: str, content_query: str, name_mode: str):
        """点击历史记录项触发搜索"""
        self.search_requested.emit(name_query, content_query, name_mode)
        self.hide()

    def _on_item_delete(self, history_id: int):
        """删除单条历史记录"""
        from database.history_dao import delete_history
        delete_history(history_id)
        self.refresh()

    def show_panel(self, pos=None):
        """显示面板"""
        self.refresh()
        if self._select_mode:
            self._toggle_select_mode()
        if pos:
            self.move(pos)
        self.show()

    def hideEvent(self, event):
        """隐藏时退出多选模式"""
        if self._select_mode:
            self._toggle_select_mode()
        super().hideEvent(event)
