from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QMessageBox, QGroupBox, QFrame)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QPixmap, QPolygonF

SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        background: transparent;
        width: 6px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: #D1D5DB;
        min-height: 40px;
        border-radius: 3px;
    }
    QScrollBar::handle:vertical:hover {
        background: #9CA3AF;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px; background: none;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 6px;
        margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: #D1D5DB;
        min-width: 40px;
        border-radius: 3px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #9CA3AF;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px; background: none;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
"""

MSG_BOX_STYLE = """
    QMessageBox {
        background-color: #FFFFFF;
    }
    QMessageBox QLabel {
        color: #374151;
        font-size: 14px;
        border: none;
        background: transparent;
    }
    QPushButton {
        padding: 8px 24px;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        color: #4B5563;
        font-size: 13px;
        outline: none;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #F3F4F6;
        border-color: #D1D5DB;
    }
"""


class _ModernMessageBox(QDialog):
    def __init__(self, parent=None, icon_type='info', title='', text='', buttons=None):
        super().__init__(parent)
        self._result = None
        self._buttons = buttons or {}
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(420)
        self._icon_type = icon_type
        self._title_text = title
        self._text = text
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        shadow_frame = QFrame()
        shadow_frame.setObjectName("shadowFrame")
        shadow_frame.setStyleSheet("""
            QFrame#shadowFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #F3F4F6;
            }
        """)
        layout = QVBoxLayout(shadow_frame)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 28, 28, 24)
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(self._create_icon_pixmap())
        title_label = QLabel(self._title_text)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1F2937; border: none; background: transparent;")
        text_label = QLabel(self._text)
        text_label.setStyleSheet("color: #4B5563; font-size: 14px; line-height: 1.6; border: none; background: transparent;")
        text_label.setWordWrap(True)
        content_row = QHBoxLayout()
        content_row.setSpacing(16)
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
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px 28px; border-radius: 10px; border: none;
                        background-color: #7C3AED; color: #FFFFFF;
                        font-size: 13px; font-weight: bold; outline: none; min-width: 80px;
                    }
                    QPushButton:hover { background-color: #6D28D9; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px 28px; border-radius: 10px;
                        border: 1px solid #E5E7EB; background-color: #FFFFFF;
                        color: #4B5563; font-size: 13px; outline: none; min-width: 80px;
                    }
                    QPushButton:hover { background-color: #F3F4F6; border-color: #D1D5DB; }
                """)
            btn.clicked.connect(lambda checked, k=key: self._on_button(k))
            btn_row.addWidget(btn)
            btn_row.addSpacing(8)
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


DIALOG_STYLE = """
    QDialog {
        background-color: #FFFFFF;
    }
    QLabel {
        color: #1F2937;
        border: none;
        background: transparent;
    }
"""

BTN_STYLE = """
    QPushButton {
        padding: 8px 24px;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        color: #4B5563;
        font-size: 13px;
        outline: none;
    }
    QPushButton:hover {
        background-color: #F3F4F6;
        border-color: #D1D5DB;
    }
"""

PRIMARY_BTN_STYLE = """
    QPushButton {
        padding: 8px 24px;
        border-radius: 8px;
        border: none;
        background-color: #7C3AED;
        color: #FFFFFF;
        font-size: 13px;
        font-weight: bold;
        outline: none;
    }
    QPushButton:hover {
        background-color: #6D28D9;
    }
"""

DANGER_BTN_STYLE = """
    QPushButton {
        padding: 8px 24px;
        border-radius: 8px;
        border: none;
        background-color: #EF4444;
        color: #FFFFFF;
        font-size: 13px;
        font-weight: bold;
        outline: none;
    }
    QPushButton:hover {
        background-color: #DC2626;
    }
"""


class SettingsDialog(QDialog):
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(520, 480)
        self.setStyleSheet(DIALOG_STYLE + SCROLLBAR_STYLE)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 20)

        header = QLabel("设置")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        general_group = QGroupBox("通用设置")
        general_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #374151;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 20px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        general_layout = QVBoxLayout()
        general_layout.setSpacing(8)

        from config import load_config
        config = load_config()

        theme_label = QLabel(f"主题：{config.get('general', {}).get('theme', 'system')}")
        theme_label.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        lang_label = QLabel(f"语言：{config.get('general', {}).get('language', 'zh_CN')}")
        lang_label.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        shortcut_label = QLabel(f"全局快捷键：{config.get('general', {}).get('global_shortcut', 'Ctrl+Alt+F')}")
        shortcut_label.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        general_layout.addWidget(theme_label)
        general_layout.addWidget(lang_label)
        general_layout.addWidget(shortcut_label)
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        search_group = QGroupBox("搜索设置")
        search_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #374151;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 20px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        search_layout = QVBoxLayout()
        search_layout.setSpacing(8)

        search_config = config.get("search", {})
        max_results_label = QLabel(f"最大结果数：{search_config.get('max_results', 1000)}")
        max_results_label.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        content_max_label = QLabel(f"内容搜索文件大小上限：{search_config.get('content_max_size_mb', 10)} MB")
        content_max_label.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        case_label = QLabel(f"区分大小写：{'是' if search_config.get('case_sensitive', False) else '否'}")
        case_label.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        scanned_dirs = search_config.get("scanned_dirs", [])
        scanned_label = QLabel(f"已扫描目录：{len(scanned_dirs)} 个")
        scanned_label.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        search_layout.addWidget(max_results_label)
        search_layout.addWidget(content_max_label)
        search_layout.addWidget(case_label)
        search_layout.addWidget(scanned_label)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        layout.addStretch()

        danger_zone = QGroupBox("危险操作")
        danger_zone.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #EF4444;
                border: 1px solid #FCA5A5;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 20px;
                background-color: #FEF2F2;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        danger_layout = QVBoxLayout()
        danger_layout.setSpacing(8)

        reset_desc = QLabel("恢复默认设置将清除所有用户自定义配置，包括已扫描目录、\n搜索历史和文件索引。此操作不可恢复。")
        reset_desc.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        reset_btn = QPushButton("恢复默认设置")
        reset_btn.setStyleSheet(DANGER_BTN_STYLE)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._on_reset_clicked)

        danger_layout.addWidget(reset_desc)
        danger_layout.addWidget(reset_btn, 0, Qt.AlignmentFlag.AlignRight)
        danger_zone.setLayout(danger_layout)
        layout.addWidget(danger_zone)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(BTN_STYLE)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _on_reset_clicked(self):
        reply = _styled_msg_box(
            self, QMessageBox.Icon.Warning,
            "恢复默认设置",
            "此操作将删除所有用户自定义设置，包括：\n\n"
            "  \u2022 所有已扫描目录的记录\n"
            "  \u2022 所有用户偏好设置\n"
            "  \u2022 搜索历史记录\n"
            "  \u2022 文件索引数据库\n"
            "  \u2022 自定义搜索范围\n\n"
            "此操作不可恢复！确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.reset_requested.emit()
            self.accept()
