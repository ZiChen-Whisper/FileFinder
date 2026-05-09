import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QDialog, QListWidget, QListWidgetItem,
                             QMessageBox, QProgressBar, QSizePolicy, QLineEdit,
                             QFileDialog, QFrame, QApplication)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, QSize, QPointF, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QFont, QPolygonF
from constants import FILE_TYPE_CATEGORIES
from utils.path_helper import get_all_drives, get_user_directories, normalize_path
from database.db_manager import DatabaseManager

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

BTN_BASE = """
    QPushButton {
        outline: none;
    }
"""

FILTER_BTN_STYLE = BTN_BASE + """
    QPushButton {
        padding: 6px 16px;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        color: #4B5563;
        font-size: 12px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #F3F4F6;
        border-color: #D1D5DB;
    }
    QPushButton:checked {
        background-color: #7C3AED;
        border-color: #7C3AED;
        color: #FFFFFF;
    }
    QPushButton:checked:hover {
        background-color: #6D28D9;
        border-color: #6D28D9;
    }
"""

CONFIG_BTN_STYLE = BTN_BASE + """
    QPushButton {
        padding: 4px 12px;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        color: #6B7280;
        font-size: 12px;
        text-decoration: none;
    }
    QPushButton:hover {
        background-color: #F3F4F6;
        border-color: #D1D5DB;
        color: #4B5563;
    }
"""

SCAN_BTN_STYLE = """
    QPushButton {
        padding: 4px 12px;
        border-radius: 8px;
        border: none;
        background-color: #7C3AED;
        color: #FFFFFF;
        font-size: 12px;
        font-weight: bold;
        min-height: 24px;
    }
    QPushButton:hover {
        background-color: #6D28D9;
    }
    QPushButton:disabled {
        background-color: #C4B5FD;
    }
"""

SCAN_BTN_GREEN_STYLE = """
    QPushButton {
        padding: 4px 12px;
        border-radius: 8px;
        border: none;
        background-color: #10B981;
        color: #FFFFFF;
        font-size: 12px;
        font-weight: bold;
        min-height: 24px;
    }
    QPushButton:hover {
        background-color: #059669;
    }
    QPushButton:disabled {
        background-color: #6EE7B7;
    }
"""

PROGRESS_STYLE = """
    QProgressBar {
        border: none;
        background-color: #E5E7EB;
        border-radius: 6px;
        height: 12px;
        text-align: center;
        font-size: 10px;
        color: #6B7280;
        outline: none;
    }
    QProgressBar::chunk {
        background-color: #7C3AED;
        border-radius: 6px;
    }
"""


def _make_colored_icon(icon_path: str, color_hex: str, size: int = 16) -> QIcon:
    screen = QApplication.primaryScreen()
    dpr = screen.devicePixelRatio() if screen else 1.0
    source_size = int(size * 8 * dpr)
    pixmap = QIcon(icon_path).pixmap(QSize(source_size, source_size))
    if pixmap.isNull():
        return QIcon(icon_path)
    colored = QPixmap(pixmap.size())
    colored.fill(Qt.GlobalColor.transparent)
    colored.setDevicePixelRatio(dpr)
    painter = QPainter(colored)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored.rect(), QColor(color_hex))
    painter.end()
    target_size = int(size * 4 * dpr)
    scaled = colored.scaled(target_size, target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    scaled.setDevicePixelRatio(dpr)
    return QIcon(scaled)


class AnimatedButton(QPushButton):
    def __init__(self, text="", icon_path=None, parent=None):
        super().__init__(text, parent)
        if icon_path:
            self.setIcon(QIcon(icon_path))
        self._orig_size = None
        self._press_anim = QPropertyAnimation(self, b"minimumSize")
        self._press_anim.setDuration(80)
        self._press_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._release_anim = QPropertyAnimation(self, b"minimumSize")
        self._release_anim.setDuration(180)
        self._release_anim.setEasingCurve(QEasingCurve.Type.OutBack)

    def showEvent(self, event):
        super().showEvent(event)
        self._orig_size = self.size()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._orig_size is None or self._orig_size.width() <= 0:
            self._orig_size = self.size()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._release_anim.stop()
            self._press_anim.stop()
            cur = self.size()
            target = QSize(int(cur.width() * 1.06), int(cur.height() * 1.06))
            self._press_anim.setStartValue(cur)
            self._press_anim.setEndValue(target)
            self._press_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_anim.stop()
            self._release_anim.stop()
            self._release_anim.setStartValue(self.size())
            sz = self._orig_size if (self._orig_size and self._orig_size.width() > 0) else self.size()
            self._release_anim.setEndValue(sz)
            self._release_anim.start()
        super().mouseReleaseEvent(event)


class ScanConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("开始扫描")
        self.setFixedWidth(400)
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 20)

        title = QLabel("开始扫描")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1F2937; border: none; background: transparent;")

        desc = QLabel("将扫描所选目录/驱动器，这可能需要几分钟时间。\n确定要开始扫描吗？")
        desc.setStyleSheet("font-size: 14px; color: #6B7280; border: none; background: transparent; text-decoration: none;")
        desc.setWordWrap(True)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
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
        """)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("开始扫描")
        confirm_btn.setStyleSheet("""
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
        """)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(8)
        btn_row.addWidget(confirm_btn)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()
        layout.addLayout(btn_row)

        self.setLayout(layout)


class SearchScopeDialog(QDialog):
    def __init__(self, current_dirs, parent=None):
        super().__init__(parent)
        self._dirs = list(current_dirs)
        self.setWindowTitle("管理扫描路径")
        self.setMinimumSize(520, 420)
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("管理扫描路径")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937; border: none; background: transparent;")
        layout.addWidget(header)

        desc = QLabel("管理要扫描的目录路径。添加/移除目录后需要重新扫描。")
        desc.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.dir_list = DirListWidget(self)
        self.dir_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #FAFAFA;
                padding: 4px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 32px 8px 10px;
                border-radius: 4px;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #F3F4F6;
            }
            QListWidget::item:selected {
                background-color: #F5F3FF;
                color: #1F2937;
                border: none;
            }
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
        """)
        for d in self._dirs:
            item = QListWidgetItem(d)
            self.dir_list.addItem(item)
        layout.addWidget(self.dir_list, 1)

        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("输入目录路径，如 D:\\Projects 或 C:\\Users")
        self.path_input.setFixedHeight(36)
        self.path_input.setStyleSheet("""
            QLineEdit {
                padding: 0px 12px;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                font-size: 13px;
                background-color: #FAFAFA;
                outline: none;
                text-decoration: none;
            }
            QLineEdit:focus { border-color: #7C3AED; background-color: #FFFFFF; }
        """)

        DIALOG_SECONDARY_BTN = """
            QPushButton {
                padding: 0px 16px;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
                background-color: #FFFFFF;
                color: #6B7280;
                font-size: 12px;
                outline: none;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
                border-color: #D1D5DB;
                color: #4B5563;
            }
        """

        DIALOG_ACTION_BTN = """
            QPushButton {
                padding: 0px 16px;
                border-radius: 8px;
                border: none;
                background-color: #7C3AED;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
                outline: none;
            }
            QPushButton:hover {
                background-color: #6D28D9;
            }
        """

        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedHeight(36)
        browse_btn.setStyleSheet(DIALOG_SECONDARY_BTN)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse)

        add_btn = QPushButton("+ 添加")
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(DIALOG_ACTION_BTN)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add)

        add_row.addWidget(self.path_input, 1)
        add_row.addWidget(browse_btn)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        quick_add_row = QHBoxLayout()
        quick_add_row.setSpacing(6)
        quick_label = QLabel("快速添加：")
        quick_label.setStyleSheet("font-size: 12px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        QUICK_ADD_BTN = """
            QPushButton {
                padding: 4px 12px;
                border-radius: 6px;
                border: 1px solid #E5E7EB;
                background-color: #FFFFFF;
                color: #6B7280;
                font-size: 11px;
                outline: none;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
                border-color: #D1D5DB;
                color: #4B5563;
            }
        """

        add_all_drives_btn = QPushButton("所有驱动器")
        add_all_drives_btn.setStyleSheet(QUICK_ADD_BTN)
        add_all_drives_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_all_drives_btn.clicked.connect(self._on_add_all_drives)

        add_user_dirs_btn = QPushButton("常用目录")
        add_user_dirs_btn.setStyleSheet(QUICK_ADD_BTN)
        add_user_dirs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_user_dirs_btn.clicked.connect(self._on_add_user_dirs)

        self._quick_drive_btns = []
        for drive in get_all_drives():
            drive_letter = drive[:2]
            btn = QPushButton(drive_letter)
            btn.setStyleSheet(QUICK_ADD_BTN)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, d=drive: self._on_add_drive(d))
            self._quick_drive_btns.append(btn)

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        desktop_btn = QPushButton("桌面")
        desktop_btn.setStyleSheet(QUICK_ADD_BTN)
        desktop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        desktop_btn.clicked.connect(lambda: self._on_add_drive(desktop_path))

        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        downloads_btn = QPushButton("下载")
        downloads_btn.setStyleSheet(QUICK_ADD_BTN)
        downloads_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        downloads_btn.clicked.connect(lambda: self._on_add_drive(downloads_path))

        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        documents_btn = QPushButton("文档")
        documents_btn.setStyleSheet(QUICK_ADD_BTN)
        documents_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        documents_btn.clicked.connect(lambda: self._on_add_drive(documents_path))

        quick_add_row.addWidget(quick_label)
        quick_add_row.addWidget(add_all_drives_btn)
        quick_add_row.addWidget(add_user_dirs_btn)
        for btn in self._quick_drive_btns:
            quick_add_row.addWidget(btn)
        quick_add_row.addWidget(desktop_btn)
        quick_add_row.addWidget(downloads_btn)
        quick_add_row.addWidget(documents_btn)
        quick_add_row.addStretch()
        layout.addLayout(quick_add_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
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
        """)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("确定")
        confirm_btn.setStyleSheet("""
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
        """)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(8)
        btn_row.addWidget(confirm_btn)

        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _remove_dir_item(self, item):
        path = item.text()
        self.dir_list.takeItem(self.dir_list.row(item))
        if path in self._dirs:
            self._dirs.remove(path)

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择扫描目录")
        if path:
            self.path_input.setText(path)

    def _on_add(self):
        path = self.path_input.text().strip()
        if path and path not in self._dirs:
            if os.path.isdir(path):
                self._dirs.append(path)
                self.dir_list.addItem(path)
                self.path_input.clear()
            else:
                _styled_msg_box(
                    self, QMessageBox.Icon.Warning,
                    "路径无效", f"目录不存在或无法访问：\n{path}"
                ).exec()
        elif path and path in self._dirs:
            _styled_msg_box(
                self, QMessageBox.Icon.Information,
                "提示", "该目录已在列表中"
            ).exec()

    def _on_add_all_drives(self):
        for drive in get_all_drives():
            if drive not in self._dirs:
                self._dirs.append(drive)
                self.dir_list.addItem(drive)

    def _on_add_user_dirs(self):
        for d in get_user_directories():
            if d not in self._dirs:
                self._dirs.append(d)
                self.dir_list.addItem(d)

    def _on_add_drive(self, path: str):
        if path not in self._dirs:
            self._dirs.append(path)
            self.dir_list.addItem(path)

    def get_dirs(self):
        return self._dirs


class DirListWidget(QListWidget):
    def __init__(self, dialog, parent=None):
        super().__init__(parent)
        self._dialog = dialog
        self._remove_btn = None
        self._hovered_item = None
        self.setMouseTracking(True)
        self.entered.connect(self._on_entered)

    def _on_entered(self, index):
        self._update_remove_button(index)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        index = self.indexAt(event.pos())
        self._update_remove_button(index)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hide_remove_btn()

    def _update_remove_button(self, index):
        if not index.isValid():
            self._hide_remove_btn()
            return

        item = self.item(index.row())
        if item == self._hovered_item and self._remove_btn and self._remove_btn.isVisible():
            return

        self._hide_remove_btn()

        self._hovered_item = item
        rect = self.visualItemRect(item)

        self._remove_btn = QPushButton("移除", self)
        self._remove_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                outline: none;
                padding: 2px 8px;
                color: #9CA3AF;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                color: #EF4444;
            }
        """)
        self._remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._remove_btn.setFixedHeight(22)

        btn_width = self._remove_btn.sizeHint().width()
        x = rect.right() - btn_width - 6
        y = rect.top() + (rect.height() - 22) // 2
        self._remove_btn.move(x, y)
        self._remove_btn.clicked.connect(lambda: self._dialog._remove_dir_item(item))
        self._remove_btn.show()
        self._remove_btn.raise_()

    def _hide_remove_btn(self):
        if self._remove_btn:
            self._remove_btn.deleteLater()
            self._remove_btn = None
        self._hovered_item = None


class FilterBar(QWidget):
    filter_changed = Signal(str)
    scope_changed = Signal(list)
    scan_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_category = 'all'
        self._search_dirs = []
        self._scanned_dirs = []
        self._indexed_count = 0
        self._is_scanning = False
        self._init_ui()
        self._reload_scope()

    def _reload_scope(self):
        from config import get_default_search_dirs, get_scanned_dirs
        self._search_dirs = get_default_search_dirs()
        self._scanned_dirs = get_scanned_dirs()
        self._update_scope_label()

    def _check_index(self):
        db = DatabaseManager()
        self._indexed_count = db.get_index_count()
        if self._indexed_count > 0 and not self._scanned_dirs:
            self._scanned_dirs = list(self._search_dirs)
        self._update_scope_label()
        self._update_status_dot()
        self._update_scan_btn_state()

    def _update_scope_label(self):
        parts = []
        dir_count = len(self._search_dirs)
        parts.append(f"{dir_count} 个目录")

        if self._indexed_count > 0:
            parts.append(f" | 已索引 {self._indexed_count:,} 个文件")
        else:
            parts.append(" | 未扫描")

        self.scope_label.setText("  ".join(parts))

    def _update_status_dot(self):
        if self._indexed_count == 0:
            self.status_dot.setStyleSheet("""
                QLabel {
                    min-width: 8px; max-width: 8px;
                    min-height: 8px; max-height: 8px;
                    border-radius: 4px;
                    background-color: #EF4444;
                    border: none;
                }
            """)
            self.status_dot.setToolTip("未扫描")
        elif self._has_unscanned_dirs():
            self.status_dot.setStyleSheet("""
                QLabel {
                    min-width: 8px; max-width: 8px;
                    min-height: 8px; max-height: 8px;
                    border-radius: 4px;
                    background-color: #F59E0B;
                    border: none;
                }
            """)
            self.status_dot.setToolTip("部分路径未扫描")
        else:
            self.status_dot.setStyleSheet("""
                QLabel {
                    min-width: 8px; max-width: 8px;
                    min-height: 8px; max-height: 8px;
                    border-radius: 4px;
                    background-color: #10B981;
                    border: none;
                }
            """)
            self.status_dot.setToolTip("已扫描")

    def _has_unscanned_dirs(self) -> bool:
        if not self._scanned_dirs:
            return bool(self._search_dirs)
        scanned_set = set(d.rstrip(os.sep).lower() for d in self._scanned_dirs)
        for d in self._search_dirs:
            if d.rstrip(os.sep).lower() not in scanned_set:
                return True
        return False

    def _update_scan_btn_state(self):
        if self._indexed_count == 0:
            self.scan_btn.setText("开始扫描")
            self.scan_btn.setStyleSheet(SCAN_BTN_GREEN_STYLE)
            self.scan_btn.setFixedWidth(86)
        elif self._has_unscanned_dirs():
            self.scan_btn.setText("扫描新增路径")
            self.scan_btn.setStyleSheet(SCAN_BTN_GREEN_STYLE)
            self.scan_btn.setFixedWidth(86)
        else:
            self.scan_btn.setText("重新扫描")
            self.scan_btn.setStyleSheet(SCAN_BTN_STYLE)
            self.scan_btn.setFixedWidth(86)

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 4, 20, 4)
        main_layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self.type_buttons = {}
        for key, label in FILE_TYPE_CATEGORIES.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(FILTER_BTN_STYLE)
            if key == 'all':
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, k=key: self._on_type_clicked(k))
            self.type_buttons[key] = btn
            top_row.addWidget(btn)

        top_row.addStretch()

        self.status_dot = QLabel()
        self._update_status_dot()

        self.scope_label = QLabel()
        self.scope_label.setStyleSheet("font-size: 12px; color: #6B7280; padding: 4px 0; border: none; background: transparent; text-decoration: none;")

        gray_settings = _make_colored_icon("icons/settings.svg", "#6B7280", 16)
        self.configure_btn = QPushButton()
        self.configure_btn.setIcon(gray_settings)
        self.configure_btn.setIconSize(QSize(16, 16))
        self.configure_btn.setFixedSize(28, 28)
        self.configure_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                outline: none;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
                border-radius: 6px;
            }
        """)
        self.configure_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.configure_btn.setToolTip("管理扫描路径")
        self.configure_btn.clicked.connect(self._on_configure_scope)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E5E7EB;
                border-radius: 3px;
                height: 6px;
                text-align: center;
                outline: none;
            }
            QProgressBar::chunk {
                background-color: #7C3AED;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        self.scan_btn = QPushButton()
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.setFixedWidth(86)
        self.scan_btn.clicked.connect(self._on_scan_clicked)
        self._update_scan_btn_state()

        top_row.addWidget(self.status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addSpacing(4)
        top_row.addWidget(self.scope_label, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addWidget(self.configure_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addSpacing(6)
        top_row.addWidget(self.scan_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        main_layout.addLayout(top_row)
        main_layout.addWidget(self.progress_bar)
        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FAFAFA;
                border-bottom: 1px solid #E5E7EB;
            }
        """)

    def _on_type_clicked(self, category):
        self._selected_category = category
        for key, btn in self.type_buttons.items():
            btn.setChecked(key == category)
        self.filter_changed.emit(category)

    def _on_configure_scope(self):
        dialog = SearchScopeDialog(self._search_dirs, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_dirs = dialog.get_dirs()
            if not new_dirs:
                _styled_msg_box(
                    self, QMessageBox.Icon.Warning,
                    "配置错误", "扫描路径不能为空"
                )
                return
            old_dirs = set(self._search_dirs)
            self._search_dirs = new_dirs
            self._update_scope_label()
            self._update_status_dot()
            self._update_scan_btn_state()
            self.scope_changed.emit(list(self._search_dirs))

            from config import load_config, save_config
            config = load_config()
            config["search"]["default_dirs"] = list(self._search_dirs)
            save_config(config)

            new_set = set(new_dirs)
            added = new_set - old_dirs
            removed = old_dirs - new_set
            if added or removed:
                msg_parts = []
                if added:
                    msg_parts.append(f"新增 {len(added)} 个目录")
                if removed:
                    msg_parts.append(f"移除 {len(removed)} 个目录")
                _styled_msg_box(
                    self, QMessageBox.Icon.Information,
                    "路径已更新",
                    f"扫描路径已更新（{'，'.join(msg_parts)}）。\n请点击「重新扫描」以更新文件索引。"
                )

    def _on_scan_clicked(self):
        if self._is_scanning:
            return

        dialog = ScanConfirmDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._is_scanning = True
        self.scan_btn.setEnabled(False)
        self.scan_btn.setIcon(QIcon())
        self.scan_btn.setText("扫描中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.scan_requested.emit()

    def reset_scan_state(self, file_count: int = 0):
        self._is_scanning = False
        self.scan_btn.setEnabled(True)
        self.scan_btn.setIcon(QIcon())
        self._scanned_dirs = list(self._search_dirs)
        self._indexed_count = file_count
        self.progress_bar.setVisible(False)
        self._update_scan_btn_state()
        self._update_scope_label()
        self._update_status_dot()

        from config import save_scanned_dirs
        save_scanned_dirs(self._scanned_dirs)

    def get_selected_category(self):
        return self._selected_category

    def get_search_dirs(self):
        return list(self._search_dirs)

    def get_indexed_count(self):
        return self._indexed_count

    def is_scanning(self):
        return self._is_scanning

    def show_search_progress(self):
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setVisible(True)

    def hide_search_progress(self):
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
