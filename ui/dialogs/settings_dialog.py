from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QGroupBox, QComboBox, QFrame, QMessageBox)
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QPolygonF
from PySide6.QtCore import Qt, QRectF, QPointF
from ..style_constants import COLORS, FONT, RADIUS, BTN, DIALOG
from ..style_manager import (
    scrollbar_style, msg_box_style, button_primary, button_secondary,
    button_danger, dialog_frame_style, dialog_title_style, dialog_body_style,
    dialog_style, group_box_style, danger_zone_style, label_caption_style,
)


class _ModernMessageBox(QDialog):
    def __init__(self, parent=None, icon_type='info', title='', text='', buttons=None):
        super().__init__(parent)
        self._result = None
        self._buttons = buttons or {}
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(DIALOG.MIN_WIDTH)
        self._icon_type = icon_type
        self._title_text = title
        self._text = text
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(DIALOG.OUTER_MARGIN, DIALOG.OUTER_MARGIN, DIALOG.OUTER_MARGIN, DIALOG.OUTER_MARGIN)
        shadow_frame = QFrame()
        shadow_frame.setObjectName("shadowFrame")
        shadow_frame.setStyleSheet(dialog_frame_style())
        layout = QVBoxLayout(shadow_frame)
        layout.setSpacing(DIALOG.CONTENT_SPACING)
        layout.setContentsMargins(DIALOG.PADDING, DIALOG.PADDING, DIALOG.PADDING, 24)
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(self._create_icon_pixmap())
        title_label = QLabel(self._title_text)
        title_font = QFont()
        title_font.setPointSize(FONT.TITLE_PT)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(dialog_title_style())
        text_label = QLabel(self._text)
        text_label.setStyleSheet(dialog_body_style())
        text_label.setWordWrap(True)
        content_row = QHBoxLayout()
        content_row.setSpacing(DIALOG.CONTENT_SPACING)
        content_row.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(6)
        col.addWidget(title_label)
        col.addWidget(text_label)
        col.addStretch()
        content_row.addLayout(col, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        for key, (label, style_type) in self._buttons.items():
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if style_type == 'primary':
                btn.setStyleSheet(button_primary("padding: 8px 28px; border-radius: 10px; min-width: 80px;"))
            else:
                btn.setStyleSheet(button_secondary("padding: 8px 28px; border-radius: 10px; min-width: 80px;"))
            btn.clicked.connect(lambda checked, k=key: self._on_button(k))
            btn_row.addWidget(btn)
            btn_row.addSpacing(DIALOG.BUTTON_SPACING)
        layout.addLayout(content_row)
        layout.addSpacing(8)
        layout.addLayout(btn_row)
        outer.addWidget(shadow_frame)

    def _create_icon_pixmap(self) -> QPixmap:
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._icon_type == 'warning':
            painter.setBrush(QColor(245, 158, 11))
            painter.setPen(Qt.PenStyle.NoPen)
            tri = QPolygonF()
            tri.append(QPointF(24, 6))
            tri.append(QPointF(44, 42))
            tri.append(QPointF(4, 42))
            painter.drawPolygon(tri)
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(24, 18, 24, 30)
            painter.drawPoint(24, 35)
        elif self._icon_type == 'error':
            painter.setBrush(QColor(239, 68, 68))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(4, 4, 40, 40, 10, 10)
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(16, 16, 32, 32)
            painter.drawLine(32, 16, 16, 32)
        elif self._icon_type == 'question':
            painter.setBrush(QColor(59, 130, 246))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(4, 4, 40, 40, 10, 10)
            painter.setPen(QColor(255, 255, 255))
            font = QFont()
            font.setPointSize(24)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRectF(4, 4, 40, 40), Qt.AlignmentFlag.AlignCenter, "?")
        else:
            painter.setBrush(QColor(16, 185, 129))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(4, 4, 40, 40, 10, 10)
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(14, 24, 21, 32)
            painter.drawLine(21, 32, 34, 16)
        painter.end()
        return pixmap

    def _on_button(self, key):
        self._result = key
        self.accept()

    def exec(self):
        super().exec()
        return self._result


def _styled_msg_box(parent, icon, title, text, buttons=None):
    if buttons is None:
        buttons = QMessageBox.StandardButton.Ok
    icon_map = {
        QMessageBox.Icon.Information: 'info',
        QMessageBox.Icon.Warning: 'warning',
        QMessageBox.Icon.Critical: 'error',
        QMessageBox.Icon.Question: 'question',
        QMessageBox.Icon.NoIcon: 'info',
    }
    icon_type = icon_map.get(icon, 'info')
    btn_defs = {}
    if buttons == QMessageBox.StandardButton.Ok:
        btn_defs['ok'] = ('确定', 'primary')
    elif buttons == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
        btn_defs['no'] = ('否', 'secondary')
        btn_defs['yes'] = ('是', 'primary')
    else:
        btn_defs['ok'] = ('确定', 'primary')
    dlg = _ModernMessageBox(parent, icon_type, title, text, btn_defs)
    result = dlg.exec()
    if result == 'yes':
        return QMessageBox.StandardButton.Yes
    elif result == 'no':
        return QMessageBox.StandardButton.No
    return QMessageBox.StandardButton.Ok


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(520, 480)
        self.setStyleSheet(dialog_style() + scrollbar_style())
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 20)

        general_group = QGroupBox("通用设置")
        general_group.setStyleSheet(group_box_style())
        general_layout = QVBoxLayout()
        general_layout.setSpacing(12)
        general_layout.setContentsMargins(16, 8, 16, 16)

        theme_label = QLabel("界面主题")
        theme_label.setStyleSheet(label_caption_style())
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["跟随系统", "浅色", "深色"])
        self.theme_combo.setFixedHeight(36)
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 0px 12px;
                border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
                border-radius: {BTN.BORDER_RADIUS}px;
                background-color: {COLORS.BG_PRIMARY};
                font-size: {BTN.FONT_SIZE};
                color: {COLORS.TEXT_PRIMARY};
                outline: none;
            }}
            QComboBox:hover {{
                border-color: {COLORS.BORDER_HOVER};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)

        lang_label = QLabel("语言")
        lang_label.setStyleSheet(label_caption_style())
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["简体中文"])
        self.lang_combo.setFixedHeight(36)
        self.lang_combo.setStyleSheet(self.theme_combo.styleSheet())

        shortcut_label = QLabel("全局快捷键")
        shortcut_label.setStyleSheet(label_caption_style())
        self.shortcut_combo = QComboBox()
        self.shortcut_combo.addItems(["Ctrl+Shift+F", "Alt+F", "自定义"])
        self.shortcut_combo.setFixedHeight(36)
        self.shortcut_combo.setStyleSheet(self.theme_combo.styleSheet())

        general_layout.addWidget(theme_label)
        general_layout.addWidget(self.theme_combo)
        general_layout.addWidget(lang_label)
        general_layout.addWidget(self.lang_combo)
        general_layout.addWidget(shortcut_label)
        general_layout.addWidget(self.shortcut_combo)
        general_group.setLayout(general_layout)

        search_group = QGroupBox("搜索设置")
        search_group.setStyleSheet(group_box_style())
        search_layout = QVBoxLayout()
        search_layout.setSpacing(12)
        search_layout.setContentsMargins(16, 8, 16, 16)

        max_results_label = QLabel("最大结果数")
        max_results_label.setStyleSheet(label_caption_style())
        self.max_results_combo = QComboBox()
        self.max_results_combo.addItems(["100", "500", "1000", "2000", "5000"])
        self.max_results_combo.setCurrentIndex(2)
        self.max_results_combo.setFixedHeight(36)
        self.max_results_combo.setStyleSheet(self.theme_combo.styleSheet())

        max_file_size_label = QLabel("内容搜索最大文件大小 (MB)")
        max_file_size_label.setStyleSheet(label_caption_style())
        self.max_file_size_combo = QComboBox()
        self.max_file_size_combo.addItems(["1", "5", "10", "20", "50"])
        self.max_file_size_combo.setCurrentIndex(2)
        self.max_file_size_combo.setFixedHeight(36)
        self.max_file_size_combo.setStyleSheet(self.theme_combo.styleSheet())

        search_layout.addWidget(max_results_label)
        search_layout.addWidget(self.max_results_combo)
        search_layout.addWidget(max_file_size_label)
        search_layout.addWidget(self.max_file_size_combo)
        search_group.setLayout(search_layout)

        danger_zone = QGroupBox("危险区域")
        danger_zone.setStyleSheet(danger_zone_style())
        danger_layout = QVBoxLayout()
        danger_layout.setSpacing(12)
        danger_layout.setContentsMargins(16, 8, 16, 16)

        reset_desc = QLabel("重置所有设置到默认值，此操作不可撤销。")
        reset_desc.setStyleSheet(label_caption_style())

        self.reset_btn = QPushButton("重置设置")
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet(button_danger())
        self.reset_btn.clicked.connect(self._on_reset)

        danger_layout.addWidget(reset_desc)
        danger_layout.addWidget(self.reset_btn)
        danger_zone.setLayout(danger_layout)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.close_btn = QPushButton("关闭")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet(button_secondary())
        self.close_btn.clicked.connect(self.accept)

        btn_row.addWidget(self.close_btn)

        layout.addWidget(general_group)
        layout.addWidget(search_group)
        layout.addWidget(danger_zone)
        layout.addStretch()
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _on_reset(self):
        result = _styled_msg_box(
            self,
            QMessageBox.Icon.Question,
            "确认重置",
            "确定要重置所有设置到默认值吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if result == QMessageBox.StandardButton.Yes:
            self.theme_combo.setCurrentIndex(0)
            self.lang_combo.setCurrentIndex(0)
            self.shortcut_combo.setCurrentIndex(0)
            self.max_results_combo.setCurrentIndex(2)
            self.max_file_size_combo.setCurrentIndex(2)
            _styled_msg_box(
                self,
                QMessageBox.Icon.Information,
                "重置完成",
                "所有设置已恢复为默认值。"
            )
