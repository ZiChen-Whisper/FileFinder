import os
import math
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QStatusBar,
                             QLabel, QHBoxLayout, QMessageBox, QSplitter, QFrame,
                             QStackedWidget, QSizePolicy, QDialog, QProgressBar,
                             QPushButton, QCheckBox, QTreeWidget, QTreeWidgetItem,
                             QLineEdit, QFileDialog, QApplication,
                             QListWidget, QListWidgetItem, QScrollArea, QAbstractItemView)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QFileSystemWatcher, QPropertyAnimation, QEasingCurve, QRectF, QSize, QPointF
from PySide6.QtGui import QIcon, QAction, QPainter, QColor, QPen, QFont, QPixmap, QPolygonF
from models.search_query import SearchQuery
from core.search_engine import SearchEngine
from .widgets import SearchBar, ResultListWidget, FilterBar, PreviewPanel, RoundedMenu
from .widgets.filter_bar import DirListWidget
from .dialogs import SettingsDialog
from config import get_exclude_dirs, get_max_results, is_first_launch, get_scanned_dirs, save_scanned_dirs, load_config, save_config, get_default_search_dirs, reset_all_settings

logger = logging.getLogger(__name__)


STATUS_BAR_STYLE = """
    QStatusBar {
        background-color: #FAFAFA;
        border-top: 1px solid #E5E7EB;
        padding: 4px 12px;
        min-height: 36px;
    }
    QStatusBar QLabel {
        color: #4B5563;
        font-size: 12px;
        padding: 0 6px;
        border: none;
        background: transparent;
    }
"""

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


class ModernMessageBox(QDialog):
    def __init__(self, parent=None, icon_type='info', title='', text='',
                 buttons=None, default_button=None):
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
        self._default_button = default_button
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
        pixmap = self._create_icon_pixmap()
        icon_label.setPixmap(pixmap)

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
        content_row.addLayout(self._build_text_column(title_label, text_label), 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_map = {
            'ok': ('确定', 'primary'),
            'yes': ('是', 'primary'),
            'no': ('否', 'secondary'),
            'cancel': ('取消', 'secondary'),
        }

        for key, (label, style_type) in self._buttons.items():
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if style_type == 'primary':
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px 28px;
                        border-radius: 10px;
                        border: none;
                        background-color: #7C3AED;
                        color: #FFFFFF;
                        font-size: 13px;
                        font-weight: bold;
                        outline: none;
                        min-width: 80px;
                    }
                    QPushButton:hover { background-color: #6D28D9; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px 28px;
                        border-radius: 10px;
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
                """)
            btn.clicked.connect(lambda checked, k=key: self._on_button(k))
            btn_row.addWidget(btn)
            btn_row.addSpacing(8)

        layout.addLayout(content_row)
        layout.addSpacing(8)
        layout.addLayout(btn_row)

        outer.addWidget(shadow_frame)

    def _build_text_column(self, title_label, text_label):
        col = QVBoxLayout()
        col.setSpacing(6)
        col.addWidget(title_label)
        col.addWidget(text_label)
        col.addStretch()
        return col

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
    elif buttons == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                     QMessageBox.StandardButton.Cancel):
        btn_defs['cancel'] = ('取消', 'secondary')
        btn_defs['no'] = ('否', 'secondary')
        btn_defs['yes'] = ('是', 'primary')
    else:
        btn_defs['ok'] = ('确定', 'primary')

    dlg = ModernMessageBox(parent, icon_type, title, text, btn_defs)
    result = dlg.exec()

    if result == 'yes':
        return QMessageBox.StandardButton.Yes
    elif result == 'no':
        return QMessageBox.StandardButton.No
    elif result == 'cancel':
        return QMessageBox.StandardButton.Cancel
    return QMessageBox.StandardButton.Ok


class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._rotate)
        self._dot_count = 8
        self._dot_radius = 3
        self._radius = 14
        self.setFixedSize(48, 48)
        self.setVisible(False)

    def start(self):
        self._angle = 0
        self.setVisible(True)
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.setVisible(False)

    def _rotate(self):
        self._angle = (self._angle + 45) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center_x = self.width() / 2
        center_y = self.height() / 2

        for i in range(self._dot_count):
            angle = (self._angle + i * (360 / self._dot_count)) % 360
            alpha = int(255 * (1 - i / self._dot_count))
            rad = angle * 3.14159265 / 180
            x = center_x + self._radius * math.cos(rad)
            y = center_y + self._radius * math.sin(rad)
            color = QColor(124, 58, 237, alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(int(x - self._dot_radius), int(y - self._dot_radius),
                              self._dot_radius * 2, self._dot_radius * 2)
        painter.end()

STATUS_DIVIDER = """
    QLabel {
        color: #D1D5DB;
        padding: 0 2px;
        font-size: 12px;
        border: none;
        background: transparent;
    }
"""


class ScanWorker(QThread):
    progress = Signal(int, int)
    finished = Signal(int, float)
    error = Signal(str)

    def __init__(self, search_dirs, exclude_dirs, parent=None):
        super().__init__(parent)
        self._search_dirs = search_dirs
        self._exclude_dirs = set(exclude_dirs) if exclude_dirs else set()
        self._cancelled = False
        self._last_progress_time = 0
        self._progress_interval = 0.3

    def cancel(self):
        self._cancelled = True

    def _should_skip_dir(self, name):
        return (name in self._exclude_dirs
                or name.startswith('.')
                or name.startswith('$')
                or name == 'node_modules'
                or name == '__pycache__'
                or name == '.git'
                or name == '.venv'
                or name == 'venv'
                or name == 'Windows'
                or name == '$RECYCLE.BIN'
                or name == 'System Volume Information')

    def _count_files(self, normalized_dirs):
        total = 0
        for base_dir in normalized_dirs:
            if self._cancelled:
                return 0
            if not os.path.isdir(base_dir):
                continue
            try:
                for root, dirs, files in os.walk(base_dir, onerror=lambda e: None):
                    if self._cancelled:
                        return 0
                    dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]
                    total += len(files) + len(dirs)
                    if total % 5000 == 0:
                        self.progress.emit(total, -1)
            except Exception:
                continue
        return total

    def run(self):
        import time
        start_time = time.time()
        try:
            from database.db_manager import DatabaseManager
            from utils.path_helper import normalize_path

            db = DatabaseManager()
            db.clear_index()

            normalized_dirs = [normalize_path(d) for d in self._search_dirs]

            self.progress.emit(0, 0)
            estimated_total = self._count_files(normalized_dirs)
            if self._cancelled:
                db.clear_index()
                return

            total_files = 0
            batch = []
            batch_size = 500
            dir_sizes = {}
            last_batch_count = 0

            for base_dir in normalized_dirs:
                if self._cancelled:
                    break
                if not os.path.isdir(base_dir):
                    continue

                for root, dirs, files in os.walk(base_dir, onerror=lambda e: None):
                    if self._cancelled:
                        break
                    dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

                    for d in dirs:
                        if self._cancelled:
                            break
                        try:
                            dir_path = os.path.join(root, d)
                            try:
                                dir_items = os.listdir(dir_path)
                                item_count = len(dir_items)
                            except (PermissionError, OSError):
                                item_count = 0
                            try:
                                dir_stat = os.stat(dir_path)
                                dir_mtime = dir_stat.st_mtime
                            except (PermissionError, OSError):
                                dir_mtime = 0
                            batch.append((dir_path, d, None, 0, dir_mtime, 1, item_count))
                            total_files += 1
                            dir_sizes.setdefault(dir_path, 0)
                        except Exception:
                            continue

                    for filename in files:
                        if self._cancelled:
                            break
                        try:
                            file_path = os.path.join(root, filename)
                            stat = os.stat(file_path)
                            _, ext = os.path.splitext(filename)

                            batch.append((
                                file_path,
                                filename,
                                ext.lower() if ext else None,
                                stat.st_size,
                                stat.st_mtime,
                                0,
                                0
                            ))
                            total_files += 1

                            parent = root
                            dir_sizes.setdefault(parent, 0)
                            dir_sizes[parent] += stat.st_size

                            if len(batch) >= batch_size:
                                db.insert_file_batch(batch)
                                batch.clear()
                                now = time.time()
                                if now - self._last_progress_time >= self._progress_interval:
                                    self._last_progress_time = now
                                    if estimated_total > 0:
                                        pct = min(int(total_files / estimated_total * 95), 95)
                                    else:
                                        pct = -1
                                    self.progress.emit(total_files, pct)
                        except Exception:
                            continue

            if self._cancelled:
                db.clear_index()
                return

            if batch:
                db.insert_file_batch(batch)

            all_dirs_sorted = sorted(dir_sizes.keys(), key=lambda p: -p.count(os.sep))
            for dir_path in all_dirs_sorted:
                parent = os.path.dirname(dir_path)
                if parent and parent != dir_path:
                    dir_sizes.setdefault(parent, 0)
                    dir_sizes[parent] += dir_sizes[dir_path]

            if dir_sizes:
                db.update_folder_sizes(dir_sizes)

            elapsed = time.time() - start_time
            self.progress.emit(total_files, 100)
            self.finished.emit(total_files, elapsed)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))


class SearchWorker(QThread):
    finished = Signal(object)

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self._query = query
        self._engine = SearchEngine()

    def run(self):
        try:
            results = self._engine.search(self._query)
            self.finished.emit(results)
        except Exception:
            self.finished.emit([])

    def cancel(self):
        self._engine.cancel()


DIR_LIST_STYLE = """
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
""" + SCROLLBAR_STYLE


class WelcomePage(QWidget):
    scan_requested_with_dirs = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_dirs = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(60, 30, 60, 30)

        icon_label = QLabel()
        app_icon = QIcon("icons/search-alt.svg")
        pixmap = app_icon.pixmap(QSize(96, 96))
        if pixmap.isNull():
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                      "icons", "doctype", "modified-logo.png")
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path).scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio,
                                                     Qt.TransformationMode.SmoothTransformation)
            else:
                pixmap = self._create_fallback_pixmap()
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("FileFinder 初始化配置")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1F2937; border: none; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dir_input_row = QHBoxLayout()
        dir_input_row.setSpacing(8)

        self._dir_input = QLineEdit()
        self._dir_input.setPlaceholderText("输入目录路径，如 D:\\Projects 或 C:\\Users")
        self._dir_input.setFixedHeight(40)
        self._dir_input.setStyleSheet("""
            QLineEdit {
                padding: 0px 14px;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                font-size: 13px;
                background-color: #FFFFFF;
                outline: none;
                text-decoration: none;
            }
            QLineEdit:focus { border-color: #7C3AED; }
        """)

        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedSize(80, 40)
        browse_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                background-color: #FFFFFF;
                color: #6B7280;
                font-size: 13px;
                outline: none;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
                border-color: #D1D5DB;
                color: #4B5563;
            }
        """)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse)

        add_btn = QPushButton("+ 添加")
        add_btn.setFixedSize(80, 40)
        add_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 10px;
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
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add_dir)

        dir_input_row.addWidget(self._dir_input, 1)
        dir_input_row.addWidget(browse_btn)
        dir_input_row.addWidget(add_btn)

        self._dir_list_widget = DirListWidget(self)
        self._dir_list_widget.setMinimumHeight(80)
        self._dir_list_widget.setMaximumHeight(200)
        self._dir_list_widget.setStyleSheet(DIR_LIST_STYLE)
        self._dir_list_widget.setVisible(False)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)

        QUICK_BTN = """
            QPushButton {
                padding: 5px 14px;
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

        all_drives_btn = QPushButton("所有驱动器")
        all_drives_btn.setStyleSheet(QUICK_BTN)
        all_drives_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_drives_btn.clicked.connect(self._on_add_all_drives)

        user_dirs_btn = QPushButton("常用目录")
        user_dirs_btn.setStyleSheet(QUICK_BTN)
        user_dirs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        user_dirs_btn.clicked.connect(self._on_add_user_dirs)

        self._quick_drive_btns = []
        from utils.path_helper import get_all_drives
        for drive in get_all_drives():
            drive_letter = drive[:2]
            btn = QPushButton(drive_letter)
            btn.setStyleSheet(QUICK_BTN)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, d=drive: self._on_add_drive(d))
            self._quick_drive_btns.append(btn)

        quick_row.addWidget(all_drives_btn)
        quick_row.addWidget(user_dirs_btn)
        for btn in self._quick_drive_btns:
            quick_row.addWidget(btn)
        quick_row.addStretch()

        self._start_btn = QPushButton("开始扫描")
        self._start_btn.setFixedSize(220, 48)
        self._start_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 12px;
                background-color: #7C3AED;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
                outline: none;
            }
            QPushButton:hover {
                background-color: #6D28D9;
            }
            QPushButton:disabled {
                background-color: #C4B5FD;
            }
        """)
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._on_start_scan)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addSpacing(4)
        layout.addLayout(dir_input_row)
        layout.addWidget(self._dir_list_widget)
        layout.addLayout(quick_row)
        layout.addSpacing(8)
        layout.addWidget(self._start_btn, 0, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        self.setStyleSheet("QWidget { background-color: #FFFFFF; }")

    def _create_fallback_pixmap(self) -> QPixmap:
        pixmap = QPixmap(96, 96)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(124, 58, 237))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, 88, 88, 18, 18)
        painter.setBrush(QColor(255, 255, 255))
        pen = QPen(QColor(255, 255, 255), 4)
        painter.setPen(pen)
        cx, cy = 48, 42
        painter.drawEllipse(cx - 14, cy - 14, 28, 28)
        painter.drawLine(cx + 10, cy + 10, cx + 24, cy + 24)
        painter.end()
        return pixmap

    def _remove_dir_item(self, item):
        path = item.text()
        self._dir_list_widget.takeItem(self._dir_list_widget.row(item))
        if path in self._selected_dirs:
            self._selected_dirs.remove(path)
        self._start_btn.setEnabled(len(self._selected_dirs) > 0)

    def _update_dir_display(self):
        self._dir_list_widget.clear()
        for d in self._selected_dirs:
            item = QListWidgetItem(d)
            item.setToolTip(d)
            self._dir_list_widget.addItem(item)

        has_dirs = len(self._selected_dirs) > 0
        self._dir_list_widget.setVisible(has_dirs)
        self._start_btn.setEnabled(has_dirs)

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择扫描目录")
        if path:
            self._dir_input.setText(path)

    def _on_add_dir(self):
        path = self._dir_input.text().strip()
        if path and path not in self._selected_dirs:
            self._selected_dirs.append(path)
            self._dir_input.clear()
            self._update_dir_display()

    def _on_add_all_drives(self):
        from utils.path_helper import get_all_drives
        for drive in get_all_drives():
            if drive not in self._selected_dirs:
                self._selected_dirs.append(drive)
        self._update_dir_display()

    def _on_add_user_dirs(self):
        from utils.path_helper import get_user_directories
        for d in get_user_directories():
            if d not in self._selected_dirs:
                self._selected_dirs.append(d)
        self._update_dir_display()

    def _on_add_drive(self, path: str):
        if path not in self._selected_dirs:
            self._selected_dirs.append(path)
            self._update_dir_display()

    def _on_start_scan(self):
        if self._selected_dirs:
            self.scan_requested_with_dirs.emit(list(self._selected_dirs))


class ScanProgressDialog(QWidget):
    scan_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(60, 40, 60, 40)

        self._title = QLabel("正在扫描文件...")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        self._title.setFont(title_font)
        self._title.setStyleSheet("color: #1F2937; border: none; background: transparent;")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._percentage = QLabel("0%")
        pct_font = QFont()
        pct_font.setPointSize(48)
        pct_font.setBold(True)
        self._percentage.setFont(pct_font)
        self._percentage.setStyleSheet("color: #7C3AED; border: none; background: transparent;")
        self._percentage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(16)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E5E7EB;
                border-radius: 8px;
                outline: none;
            }
            QProgressBar::chunk {
                background-color: #7C3AED;
                border-radius: 8px;
            }
        """)

        self._detail = QLabel("已发现 0 个文件")
        self._detail.setStyleSheet("font-size: 14px; color: #6B7280; border: none; background: transparent; text-decoration: none;")
        self._detail.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._cancel_btn = QPushButton("取消扫描")
        self._cancel_btn.setFixedSize(140, 40)
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                background-color: #FFFFFF;
                color: #6B7280;
                font-size: 13px;
                outline: none;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                border-color: #FCA5A5;
                color: #EF4444;
            }
        """)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._on_cancel)

        layout.addWidget(self._title)
        layout.addWidget(self._percentage)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._detail)
        layout.addSpacing(20)
        layout.addWidget(self._cancel_btn, 0, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        self.setStyleSheet("QWidget { background-color: #FFFFFF; }")

    def update_progress(self, count: int, percentage: int = None):
        self._detail.setText(f"已发现 {count:,} 个文件")
        if percentage is not None:
            self._progress_bar.setMaximum(100)
            self._progress_bar.setValue(min(percentage, 100))
            self._percentage.setText(f"{min(percentage, 100)}%")
        else:
            if self._progress_bar.maximum() == 0:
                self._progress_bar.setMaximum(100)
            if count < 1000:
                pct = min(int(count / 1000 * 30), 30)
            elif count < 5000:
                pct = 30 + min(int((count - 1000) / 4000 * 30), 30)
            elif count < 20000:
                pct = 60 + min(int((count - 5000) / 15000 * 20), 20)
            elif count < 100000:
                pct = 80 + min(int((count - 20000) / 80000 * 15), 15)
            else:
                pct = 95
            self._progress_bar.setValue(pct)
            self._percentage.setText(f"{pct}%")

    def set_finishing(self):
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(100)
        self._percentage.setText("100%")
        self._title.setText("扫描完成！")
        self._detail.setText("正在加载索引...")
        self._cancel_btn.setVisible(False)
        self._cancel_btn.setEnabled(False)

    def _on_cancel(self):
        self.scan_cancelled.emit()


class SearchScopePanel(QWidget):
    scope_changed = Signal(list)
    scan_unscanned_requested = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scanned_dirs = []
        self._selected_dirs = set()
        self._custom_dir_list = []
        self._scope_mode = 'all'
        self._indexed_count = 0
        self._init_ui()

    def _init_ui(self):
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(20, 6, 20, 6)
        self._main_layout.setSpacing(4)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        header = QLabel("搜索范围：")
        header.setStyleSheet("font-size: 12px; font-weight: bold; color: #374151; border: none; background: transparent;")

        self._all_btn = QPushButton("全部已扫描目录")
        self._all_btn.setCheckable(True)
        self._all_btn.setChecked(True)
        self._all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._all_btn.setStyleSheet("""
            QPushButton {
                padding: 3px 14px;
                border-radius: 6px;
                border: 1px solid #E5E7EB;
                background-color: #FFFFFF;
                color: #4B5563;
                font-size: 11px;
                outline: none;
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
            }
        """)
        self._all_btn.clicked.connect(self._on_all_clicked)

        self._custom_btn = QPushButton("自定义范围")
        self._custom_btn.setCheckable(True)
        self._custom_btn.setChecked(False)
        self._custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._custom_btn.setStyleSheet(self._all_btn.styleSheet())
        self._custom_btn.clicked.connect(self._on_custom_clicked)

        self._scope_info_scroll = QScrollArea()
        self._scope_info_scroll.setWidgetResizable(True)
        self._scope_info_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scope_info_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scope_info_scroll.setFixedHeight(56)
        self._scope_info_scroll.setMinimumWidth(120)
        self._scope_info_scroll.setMaximumWidth(220)
        self._scope_info_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                background-color: #FAFAFA;
            }
        """ + SCROLLBAR_STYLE)
        self._scope_info_container = QWidget()
        self._scope_info_layout = QVBoxLayout(self._scope_info_container)
        self._scope_info_layout.setContentsMargins(6, 4, 6, 4)
        self._scope_info_layout.setSpacing(2)
        self._scope_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scope_info_container.setStyleSheet("QWidget { background: transparent; }")
        self._scope_info_scroll.setWidget(self._scope_info_container)

        header_row.addWidget(header)
        header_row.addWidget(self._all_btn)
        header_row.addWidget(self._custom_btn)
        header_row.addStretch()
        header_row.addWidget(self._scope_info_scroll)

        self._scope_detail = QLabel("")
        self._scope_detail.setStyleSheet("font-size: 12px; color: #6B7280; border: none; background: transparent; text-decoration: none;")

        self._dir_layout = QHBoxLayout()
        self._dir_layout.setSpacing(6)
        self._dir_layout.setContentsMargins(0, 0, 0, 0)

        self._dir_scroll_content = QWidget()
        self._dir_scroll_content.setLayout(self._dir_layout)
        self._dir_scroll_content.setStyleSheet("QWidget { background: transparent; }")

        self._scroll = QScrollArea()
        self._scroll.setWidget(self._dir_scroll_content)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFixedHeight(36)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }" + SCROLLBAR_STYLE)
        self._scroll.setVisible(False)

        self._main_layout.addLayout(header_row)
        self._main_layout.addWidget(self._scope_detail)
        self._main_layout.addWidget(self._scroll)

        self.setLayout(self._main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #F9FAFB;
                border-bottom: 1px solid #E5E7EB;
            }
        """)

    def _get_display_path(self, path: str) -> str:
        path_clean = path.rstrip(os.sep)
        for scan_dir in self._scanned_dirs:
            scan_clean = scan_dir.rstrip(os.sep)
            if os.path.normcase(os.path.normpath(path_clean)) == os.path.normcase(os.path.normpath(scan_clean)):
                return os.path.basename(scan_clean) or scan_dir
            try:
                rel = os.path.relpath(path_clean, scan_clean)
                if not rel.startswith('..'):
                    return rel
            except ValueError:
                pass
        return os.path.basename(path_clean) or path

    def set_scanned_dirs(self, dirs: list):
        self._scanned_dirs = list(dirs)
        if self._scope_mode == 'all':
            self._selected_dirs = set(dirs)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self._update_scope_info()
        self.scope_changed.emit(list(self._selected_dirs))

    def update_scope_info(self, file_count: int = 0):
        self._indexed_count = file_count
        self._update_scope_info()

    def _update_scope_info(self):
        while self._scope_info_layout.count():
            item = self._scope_info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dir_count = len(self._scanned_dirs)
        if dir_count == 0:
            return

        header_label = QLabel(f"{dir_count} 个目录" + (f" · 已索引 {self._indexed_count:,} 个文件" if self._indexed_count > 0 else " · 未扫描"))
        header_label.setStyleSheet("font-size: 10px; color: #9CA3AF; border: none; background: transparent; padding: 0px; margin: 0px;")
        self._scope_info_layout.addWidget(header_label)

        for d in self._scanned_dirs:
            name = os.path.basename(d.rstrip(os.sep)) or d
            dir_label = QLabel(name)
            dir_label.setToolTip(d)
            dir_label.setStyleSheet("font-size: 11px; color: #4B5563; border: none; background: transparent; padding: 1px 2px; margin: 0px;")
            self._scope_info_layout.addWidget(dir_label)

    def _update_scope_detail(self):
        if self._scope_mode == 'all':
            self._scope_detail.setText(f"搜索所有已扫描目录（共 {len(self._scanned_dirs)} 个）")
        else:
            count = len(self._selected_dirs)
            total = len(self._custom_dir_list)
            self._scope_detail.setText(f"已选择 {count}/{total} 个目录")

    def _rebuild_dir_buttons(self):
        while self._dir_layout.count():
            item = self._dir_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dirs_to_show = self._custom_dir_list if self._scope_mode == 'custom' else list(self._selected_dirs)
        DIR_TAG_STYLE = """
            QPushButton {
                padding: 4px 10px;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
                background-color: #FFFFFF;
                color: #6B7280;
                font-size: 11px;
                outline: none;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
                border-color: #D1D5DB;
                color: #374151;
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
            QPushButton:!checked {
                border: 1px solid #E5E7EB;
                background-color: #FFFFFF;
                color: #6B7280;
            }
            QPushButton:!checked:hover {
                background-color: #F3F4F6;
                border-color: #D1D5DB;
                color: #374151;
            }
        """
        for d in dirs_to_show:
            display_name = self._get_display_path(d)
            btn = QPushButton(display_name)
            btn.setCheckable(True)
            is_selected = d in self._selected_dirs
            btn.setChecked(is_selected)
            btn.setToolTip(d)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(DIR_TAG_STYLE)
            btn.clicked.connect(lambda checked, path=d: self._on_dir_toggled(path, checked))
            self._dir_layout.addWidget(btn)

        self._dir_layout.addStretch()

    def _on_all_clicked(self):
        self._scope_mode = 'all'
        self._all_btn.setChecked(True)
        self._custom_btn.setChecked(False)
        self._selected_dirs = set(self._scanned_dirs)
        self._custom_dir_list = []
        self._scroll.setVisible(False)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self.scope_changed.emit(list(self._selected_dirs))

    def _on_custom_clicked(self):
        self._all_btn.setChecked(False)
        self._custom_btn.setChecked(True)

        dialog = _ScopeSelectionDialog(self._scanned_dirs, self._selected_dirs, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_dirs()
            unscanned = dialog.get_unscanned_dirs()
            if unscanned:
                reply = _styled_msg_box(
                    self, QMessageBox.Icon.Question,
                    "发现未扫描目录",
                    "以下目录尚未扫描：\n\n" +
                    "\n".join(f"  \u2022 {d}" for d in unscanned) +
                    "\n\n是否立即扫描这些目录？\n（选择\"取消\"则不会将这些目录加入搜索范围）",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._scope_mode = 'custom'
                    self.scan_unscanned_requested.emit(unscanned)
                    return

            self._scope_mode = 'custom'
            self._selected_dirs = set(selected)
            self._custom_dir_list = list(selected)
            self._scroll.setVisible(True)
            self._rebuild_dir_buttons()
            self._update_scope_detail()
            self.scope_changed.emit(list(self._selected_dirs))
        else:
            if not self._selected_dirs:
                self._on_all_clicked()
            else:
                self._scope_mode = 'custom'
                self._all_btn.setChecked(False)
                self._custom_btn.setChecked(True)

    def _on_dir_toggled(self, path: str, checked: bool):
        if checked:
            self._selected_dirs.add(path)
        else:
            self._selected_dirs.discard(path)
        self._update_scope_detail()
        self.scope_changed.emit(list(self._selected_dirs))

    def get_selected_dirs(self) -> list:
        if self._scope_mode == 'all':
            return list(self._scanned_dirs)
        return list(self._selected_dirs)

    def get_all_scanned_dirs(self) -> list:
        return list(self._scanned_dirs)

    def add_scanned_dir(self, dirs: list):
        for d in dirs:
            if d not in self._scanned_dirs:
                self._scanned_dirs.append(d)
            self._selected_dirs.add(d)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self._update_scope_info()
        self.scope_changed.emit(list(self._selected_dirs))

    def reset(self):
        self._scope_mode = 'all'
        self._selected_dirs = set()
        self._custom_dir_list = []
        self._scanned_dirs = []
        self._indexed_count = 0
        self._all_btn.setChecked(True)
        self._custom_btn.setChecked(False)
        self._scroll.setVisible(False)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self._update_scope_info()


class _ScopeSelectionDialog(QDialog):
    _PLACEHOLDER_KEY = "__placeholder__"

    def __init__(self, scanned_dirs: list, current_selected: set, parent=None):
        super().__init__(parent)
        self._scanned_dirs = list(scanned_dirs)
        self._selected_dirs = set(current_selected)
        self._unscanned_dirs = []
        self._updating_tree = False
        self._loaded_items = set()
        self.setWindowTitle("指定搜索范围")
        self.setMinimumSize(560, 540)
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 20)

        header = QLabel("指定搜索范围")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937; border: none; background: transparent;")

        desc = QLabel("勾选要搜索的目录。勾选父目录将自动包含所有子目录，部分勾选子目录时父目录显示为半选状态。")
        desc.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")
        desc.setWordWrap(True)

        select_row = QHBoxLayout()
        select_row.setSpacing(6)

        CHECK_BTN_STYLE = """
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

        select_all_btn = QPushButton("全选")
        select_all_btn.setStyleSheet(CHECK_BTN_STYLE)
        select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        select_all_btn.clicked.connect(self._on_select_all)

        deselect_all_btn = QPushButton("全不选")
        deselect_all_btn.setStyleSheet(CHECK_BTN_STYLE)
        deselect_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        deselect_all_btn.clicked.connect(self._on_deselect_all)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #E5E7EB; border: none; background: transparent;")

        expand_all_btn = QPushButton("全部展开")
        expand_all_btn.setStyleSheet(CHECK_BTN_STYLE)
        expand_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        expand_all_btn.clicked.connect(self._on_expand_all)

        collapse_all_btn = QPushButton("全部折叠")
        collapse_all_btn.setStyleSheet(CHECK_BTN_STYLE)
        collapse_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        collapse_all_btn.clicked.connect(self._on_collapse_all)

        self._count_label = QLabel("")
        self._count_label.setStyleSheet("font-size: 12px; color: #9CA3AF; border: none; background: transparent;")

        select_row.addWidget(select_all_btn)
        select_row.addWidget(deselect_all_btn)
        select_row.addWidget(sep)
        select_row.addWidget(expand_all_btn)
        select_row.addWidget(collapse_all_btn)
        select_row.addStretch()
        select_row.addWidget(self._count_label)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("目录")
        self._tree.setAnimated(True)
        self._tree.setIndentation(16)
        self._tree.setExpandsOnDoubleClick(True)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons')
        checkmark_path = os.path.join(icons_dir, 'checkmark.svg').replace('\\', '/')
        partial_path = os.path.join(icons_dir, 'partial-check.svg').replace('\\', '/')
        branch_closed_path = os.path.join(icons_dir, 'branch-closed.svg').replace('\\', '/')
        branch_open_path = os.path.join(icons_dir, 'branch-open.svg').replace('\\', '/')

        tree_style = f"""
            QTreeWidget {{
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #FAFAFA;
                font-size: 13px;
                outline: none;
                padding: 4px;
            }}
            QTreeWidget::item {{
                padding: 4px 2px;
                border-radius: 4px;
                border: none;
            }}
            QTreeWidget::item:hover {{
                background-color: #F3F4F6;
            }}
            QTreeWidget::item:selected {{
                background-color: #F5F3FF;
                color: #1F2937;
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
                border-radius: 4px;
                border: 2px solid #D1D5DB;
                background-color: #FFFFFF;
            }}
            QTreeWidget::indicator:hover {{
                border-color: #7C3AED;
                background-color: #F5F3FF;
            }}
            QTreeWidget::indicator:unchecked {{
                image: none;
            }}
            QTreeWidget::indicator:checked {{
                background-color: #7C3AED;
                border-color: #7C3AED;
                image: url({checkmark_path});
            }}
            QTreeWidget::indicator:checked:hover {{
                background-color: #6D28D9;
                border-color: #6D28D9;
                image: url({checkmark_path});
            }}
            QTreeWidget::indicator:indeterminate {{
                background-color: #7C3AED;
                border-color: #7C3AED;
                image: url({partial_path});
            }}
            QTreeWidget::indicator:indeterminate:hover {{
                background-color: #6D28D9;
                border-color: #6D28D9;
                image: url({partial_path});
            }}
        """ + SCROLLBAR_STYLE
        self._tree.setStyleSheet(tree_style)
        self._tree.header().setStretchLastSection(True)
        self._tree.itemChanged.connect(self._on_tree_item_changed)
        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._populate_tree()

        browse_row = QHBoxLayout()
        browse_row.setSpacing(8)

        self._path_input = QLineEdit()
        self._path_input.setPlaceholderText("输入目录路径或点击浏览...")
        self._path_input.setFixedHeight(36)
        self._path_input.setStyleSheet("""
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

        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedHeight(36)
        browse_btn.setStyleSheet("""
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
        """)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse)

        add_btn = QPushButton("+ 添加")
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet("""
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
        """)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add)

        browse_row.addWidget(self._path_input, 1)
        browse_row.addWidget(browse_btn)
        browse_row.addWidget(add_btn)

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
        confirm_btn.clicked.connect(self._on_confirm)

        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(8)
        btn_row.addWidget(confirm_btn)

        layout.addWidget(header)
        layout.addWidget(desc)
        layout.addLayout(select_row)
        layout.addWidget(self._tree, 1)
        layout.addLayout(browse_row)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self._update_count_label()

    def _populate_tree(self):
        self._updating_tree = True
        self._tree.clear()
        self._loaded_items.clear()
        for d in self._scanned_dirs:
            name = os.path.basename(d.rstrip(os.sep)) or d
            item = QTreeWidgetItem(self._tree, [name])
            d_norm = os.path.normcase(os.path.normpath(d.rstrip(os.sep)))
            if d in self._selected_dirs:
                item.setCheckState(0, Qt.CheckState.Checked)
            elif any(
                os.path.normcase(os.path.normpath(s.rstrip(os.sep))).startswith(d_norm + os.sep)
                for s in self._selected_dirs
            ):
                item.setCheckState(0, Qt.CheckState.PartiallyChecked)
            else:
                item.setCheckState(0, Qt.CheckState.Unchecked)
            item.setData(0, Qt.ItemDataRole.UserRole, d)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, 'scanned')
            item.setToolTip(0, d)
            if self._has_subdirectories(d):
                self._add_placeholder(item)
            else:
                item.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
        self._updating_tree = False
        self._update_count_label()

    def _has_subdirectories(self, dir_path: str) -> bool:
        try:
            for name in os.listdir(dir_path):
                full = os.path.join(dir_path, name)
                try:
                    if os.path.isdir(full) and not os.path.islink(full):
                        return True
                except Exception:
                    continue
        except (PermissionError, OSError, TypeError):
            return False
        return False

    def _add_placeholder(self, item: QTreeWidgetItem):
        placeholder = QTreeWidgetItem(item, ["加载中..."])
        placeholder.setData(0, Qt.ItemDataRole.UserRole, self._PLACEHOLDER_KEY)
        placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
        placeholder.setForeground(0, QColor(156, 163, 175))

    def _has_placeholder(self, item: QTreeWidgetItem) -> bool:
        if item.childCount() == 0:
            return False
        first = item.child(0)
        return first.data(0, Qt.ItemDataRole.UserRole) == self._PLACEHOLDER_KEY

    def _on_item_expanded(self, item: QTreeWidgetItem):
        if not self._has_placeholder(item):
            return
        self._updating_tree = True
        try:
            item.takeChild(0)
            dir_path = item.data(0, Qt.ItemDataRole.UserRole)
            if not dir_path or not os.path.isdir(dir_path):
                item.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
                self._updating_tree = False
                return
            parent_state = item.checkState(0)
            self._load_children(item, dir_path)
            if parent_state == Qt.CheckState.Checked:
                for i in range(item.childCount()):
                    self._cascade_check(item.child(i), True)
            elif parent_state == Qt.CheckState.PartiallyChecked:
                self._apply_partial_inherit(item)
            self._loaded_items.add(id(item))
        except Exception:
            logger.debug("Error loading tree children", exc_info=True)
        self._updating_tree = False
        self._update_count_label()

    def _load_children(self, parent_item: QTreeWidgetItem, dir_path: str):
        try:
            entries = sorted(os.listdir(dir_path))
        except (PermissionError, OSError, TypeError):
            parent_item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
            return
        has_dirs = False
        for name in entries:
            full = os.path.join(dir_path, name)
            try:
                if not os.path.isdir(full) or os.path.islink(full):
                    continue
            except Exception:
                continue
            has_dirs = True
            child = QTreeWidgetItem(parent_item, [name])
            child.setCheckState(0, Qt.CheckState.Unchecked)
            child.setData(0, Qt.ItemDataRole.UserRole, full)
            child.setData(0, Qt.ItemDataRole.UserRole + 1, 'scanned')
            child.setToolTip(0, full)
            if self._has_subdirectories(full):
                self._add_placeholder(child)
            else:
                child.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
        if not has_dirs:
            parent_item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)

    def _cascade_check(self, item: QTreeWidgetItem, checked: bool):
        item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        if not self._has_placeholder(item):
            for i in range(item.childCount()):
                self._cascade_check(item.child(i), checked)

    def _apply_partial_inherit(self, item: QTreeWidgetItem):
        for i in range(item.childCount()):
            child = item.child(i)
            child_path = child.data(0, Qt.ItemDataRole.UserRole) or ''
            if child_path in self._selected_dirs:
                child.setCheckState(0, Qt.CheckState.Checked)
            else:
                child.setCheckState(0, Qt.CheckState.Unchecked)

    def _on_expand_all(self):
        self._expand_queue = []
        self._expand_depth = 0
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._expand_queue.append((root.child(i), 0))
        if self._expand_queue:
            self._count_label.setText("正在展开...")
            self._expand_index = 0
            self._expand_timer = QTimer(self)
            self._expand_timer.timeout.connect(self._expand_next_batch)
            self._expand_timer.start(0)

    def _expand_next_batch(self):
        batch_size = 15
        new_queue = []
        for _ in range(batch_size):
            if self._expand_index >= len(self._expand_queue):
                self._expand_queue = new_queue
                self._expand_index = 0
                if not self._expand_queue:
                    self._expand_timer.stop()
                    self._update_count_label()
                    return
                return
            item, depth = self._expand_queue[self._expand_index]
            self._expand_index += 1
            if depth >= 3:
                continue
            self._tree.expandItem(item)
            if not self._has_placeholder(item):
                for i in range(item.childCount()):
                    new_queue.append((item.child(i), depth + 1))
        if self._expand_index >= len(self._expand_queue):
            self._expand_queue = new_queue
            self._expand_index = 0
            if not self._expand_queue:
                self._expand_timer.stop()
                self._update_count_label()
        QApplication.processEvents()

    def _on_collapse_all(self):
        self._collapse_all_items(self._tree.invisibleRootItem())

    def _collapse_all_items(self, parent: QTreeWidgetItem):
        for i in range(parent.childCount()):
            child = parent.child(i)
            self._collapse_all_items(child)
            self._tree.collapseItem(child)

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int):
        if self._updating_tree:
            return
        self._updating_tree = True
        state = item.checkState(0)
        if state == Qt.CheckState.Checked:
            self._cascade_check(item, True)
        elif state == Qt.CheckState.Unchecked:
            self._cascade_check(item, False)
        self._update_parent_check_state(item)
        self._updating_tree = False
        self._update_count_label()

    def _update_parent_check_state(self, item: QTreeWidgetItem):
        parent = item.parent()
        if parent is None:
            return
        checked_count = 0
        partial_count = 0
        total = parent.childCount()
        for i in range(total):
            cs = parent.child(i).checkState(0)
            if cs == Qt.CheckState.Checked:
                checked_count += 1
            elif cs == Qt.CheckState.PartiallyChecked:
                partial_count += 1
        if checked_count == 0 and partial_count == 0:
            parent.setCheckState(0, Qt.CheckState.Unchecked)
        elif checked_count == total:
            parent.setCheckState(0, Qt.CheckState.Checked)
        else:
            parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
        self._update_parent_check_state(parent)

    def _on_select_all(self):
        self._updating_tree = True
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._cascade_check(root.child(i), True)
        self._updating_tree = False
        self._update_count_label()

    def _on_deselect_all(self):
        self._updating_tree = True
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._cascade_check(root.child(i), False)
        self._updating_tree = False
        self._update_count_label()

    def _update_count_label(self):
        checked = 0
        total = 0
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            c = root.child(i)
            total += 1
            if c.checkState(0) == Qt.CheckState.Checked:
                checked += 1
        self._count_label.setText(f"已选 {checked}/{total} 个根目录")

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择目录")
        if not path:
            return
        self._path_input.setText(path)
        self._add_path_to_tree(path)

    def _on_add(self):
        path = self._path_input.text().strip()
        if not path:
            return
        if not os.path.isdir(path):
            _styled_msg_box(
                self, QMessageBox.Icon.Warning,
                "路径无效", f"目录不存在或无法访问：\n{path}"
            )
            return
        self._add_path_to_tree(path)
        self._path_input.clear()

    def _add_path_to_tree(self, path: str):
        existing = self._find_tree_item_by_path(path)
        if existing is not None:
            self._updating_tree = True
            self._cascade_check(existing, True)
            self._update_parent_check_state(existing)
            self._updating_tree = False
            self._update_count_label()
            self._tree.scrollToItem(existing)
            self._path_input.clear()
            return

        visible = self._ensure_path_visible(path)
        if visible is not None:
            self._updating_tree = True
            self._cascade_check(visible, True)
            self._update_parent_check_state(visible)
            self._updating_tree = False
            self._update_count_label()
            self._tree.scrollToItem(visible)
            self._path_input.clear()
            return

        is_scanned = any(
            os.path.normcase(os.path.normpath(path)).startswith(
                os.path.normcase(os.path.normpath(d)) + os.sep)
            or os.path.normcase(os.path.normpath(path)) == os.path.normcase(os.path.normpath(d))
            for d in self._scanned_dirs
        )

        tag = 'scanned'
        if not is_scanned:
            reply = _styled_msg_box(
                self, QMessageBox.Icon.Question,
                "目录未扫描",
                f"目录不在已扫描范围内：\n{path}\n\n"
                "是否添加到扫描路径并扫描？\n"
                "（选择\"否\"则仅添加到选择列表，不会索引其中的文件）",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._unscanned_dirs.append(path)
                self._scanned_dirs.append(path)
                tag = 'unscanned'

        self._updating_tree = True
        name = os.path.basename(path.rstrip(os.sep)) or path
        item = QTreeWidgetItem(self._tree, [name])
        item.setCheckState(0, Qt.CheckState.Checked)
        item.setData(0, Qt.ItemDataRole.UserRole, path)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, tag)
        item.setToolTip(0, path)
        if not is_scanned:
            item.setForeground(0, QColor(239, 68, 68))
        if self._has_subdirectories(path):
            self._add_placeholder(item)
        else:
            item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
        self._tree.scrollToItem(item)
        self._updating_tree = False
        self._update_count_label()
        self._path_input.clear()

    def _ensure_path_visible(self, target_path: str):
        norm_target = os.path.normcase(os.path.normpath(target_path))
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            root_item = root.child(i)
            root_path = os.path.normcase(os.path.normpath(
                root_item.data(0, Qt.ItemDataRole.UserRole) or ''))
            if norm_target == root_path:
                return root_item
            if norm_target.startswith(root_path + os.sep):
                return self._expand_to_path(root_item, root_path, norm_target)
        return None

    def _expand_to_path(self, parent_item: QTreeWidgetItem, parent_path: str, target_path: str):
        rel = target_path[len(parent_path):].lstrip(os.sep)
        if not rel:
            return parent_item
        parts = rel.split(os.sep)
        current_item = parent_item
        current_path = parent_path
        for part in parts:
            if self._has_placeholder(current_item):
                self._updating_tree = True
                current_item.takeChild(0)
                dir_path = current_item.data(0, Qt.ItemDataRole.UserRole)
                parent_state = current_item.checkState(0)
                self._load_children(current_item, dir_path)
                if parent_state == Qt.CheckState.Checked:
                    for j in range(current_item.childCount()):
                        self._cascade_check(current_item.child(j), True)
                self._loaded_items.add(id(current_item))
                self._updating_tree = False
                current_item.setExpanded(True)
            found = None
            norm_part = os.path.normcase(part)
            for j in range(current_item.childCount()):
                child = current_item.child(j)
                if os.path.normcase(child.text(0)) == norm_part:
                    found = child
                    break
            if found is None:
                return None
            current_item = found
            current_path = os.path.join(current_path, part)
        return current_item

    def _find_tree_item_by_path(self, path: str):
        norm = os.path.normcase(os.path.normpath(path))
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            result = self._search_item(root.child(i), norm)
            if result is not None:
                return result
        return None

    def _search_item(self, item: QTreeWidgetItem, norm_path: str):
        item_path = os.path.normcase(os.path.normpath(
            item.data(0, Qt.ItemDataRole.UserRole) or ''))
        if item_path == norm_path:
            return item
        if not self._has_placeholder(item):
            for i in range(item.childCount()):
                result = self._search_item(item.child(i), norm_path)
                if result is not None:
                    return result
        return None

    def _on_confirm(self):
        self._selected_dirs = set()
        self._unscanned_dirs = []
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._collect_checked(root.child(i))
        self.accept()

    def _collect_checked(self, item: QTreeWidgetItem):
        if item.checkState(0) == Qt.CheckState.Checked:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            tag = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if path:
                self._selected_dirs.add(path)
                if tag == 'unscanned' and path not in self._unscanned_dirs:
                    self._unscanned_dirs.append(path)
        elif item.checkState(0) == Qt.CheckState.PartiallyChecked:
            for i in range(item.childCount()):
                self._collect_checked(item.child(i))
        else:
            for i in range(item.childCount()):
                self._collect_checked(item.child(i))

    def get_selected_dirs(self) -> list:
        return list(self._selected_dirs)

    def get_unscanned_dirs(self) -> list:
        return list(self._unscanned_dirs)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._scan_worker = None
        self._search_worker = None
        self._current_file_types = []
        self._exclude_known_types = False
        self._all_results = []
        self._selected_dirs = set()
        self._fs_watcher = QFileSystemWatcher(self)
        self._fs_watcher.directoryChanged.connect(self._on_fs_directory_changed)
        self._fs_refresh_timer = QTimer(self)
        self._fs_refresh_timer.setSingleShot(True)
        self._fs_refresh_timer.setInterval(500)
        self._fs_refresh_timer.timeout.connect(self._on_fs_refresh_timeout)
        self._pending_fs_changes = set()
        self._is_first_launch = is_first_launch()
        self._init_ui()
        self._connect_signals()
        self._check_index_on_startup()

    def _init_ui(self):
        self.setWindowTitle("FileFinder - 本地文件搜索工具")
        self.setMinimumSize(900, 600)
        self.resize(1100, 720)

        icon = QIcon("icons/search-alt.svg")
        self.setWindowIcon(icon)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QWidget {
                font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
            }
        """ + SCROLLBAR_STYLE)

        self._init_menu_bar()

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._stacked = QStackedWidget()
        main_layout.addWidget(self._stacked)

        self._welcome_page = WelcomePage()
        self._scan_progress_page = ScanProgressDialog()
        self._main_page = self._create_main_page()

        self._stacked.addWidget(self._welcome_page)
        self._stacked.addWidget(self._scan_progress_page)
        self._stacked.addWidget(self._main_page)

        self._init_status_bar()

        central.setLayout(main_layout)

    def _create_main_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_bar = SearchBar()
        layout.addWidget(self.search_bar)

        self._search_scope_panel = SearchScopePanel()
        layout.addWidget(self._search_scope_panel)

        self.filter_bar = FilterBar()
        layout.addWidget(self.filter_bar)

        content_split = QSplitter(Qt.Orientation.Horizontal)
        content_split.setContentsMargins(0, 0, 0, 0)

        self.result_list = ResultListWidget()

        self._loading_overlay = QFrame(self.result_list)
        self._loading_overlay.setStyleSheet("QFrame { background-color: #FFFFFF; }")
        overlay_layout = QVBoxLayout(self._loading_overlay)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.setSpacing(12)

        self._loading_spinner = LoadingSpinner(self._loading_overlay)
        loading_label = QLabel("正在初始化...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("color: #6B7280; font-size: 14px; border: none; background: transparent;")

        overlay_layout.addStretch()
        overlay_layout.addWidget(self._loading_spinner, 0, Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(loading_label, 0, Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addStretch()

        self.preview_panel = PreviewPanel()
        self.preview_panel.setMinimumWidth(200)

        content_split.addWidget(self.result_list)
        content_split.addWidget(self.preview_panel)
        content_split.setStretchFactor(0, 3)
        content_split.setStretchFactor(1, 2)
        content_split.setSizes([700, 400])
        content_split.setHandleWidth(2)
        content_split.setStyleSheet("""
            QSplitter::handle {
                background-color: #E5E7EB;
            }
            QSplitter::handle:hover {
                background-color: #7C3AED;
            }
        """)

        layout.addWidget(content_split, 1)

        page.setLayout(layout)
        return page

    def _init_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(STATUS_BAR_STYLE)
        self.setStatusBar(self.status_bar)

        self.status_left = QLabel("就绪")
        self.status_left.setStyleSheet("color: #6B7280; font-size: 12px;")

        self.status_separator1 = QLabel("|")
        self.status_separator1.setStyleSheet(STATUS_DIVIDER)

        self.status_size = QLabel("")
        self.status_separator2 = QLabel("|")
        self.status_separator2.setStyleSheet(STATUS_DIVIDER)
        self.status_date = QLabel("")
        self.status_separator3 = QLabel("|")
        self.status_separator3.setStyleSheet(STATUS_DIVIDER)
        self.status_path = QLabel("")

        hide_detail_widgets = [
            self.status_separator1, self.status_separator2, self.status_separator3,
            self.status_size, self.status_date, self.status_path
        ]
        for w in hide_detail_widgets:
            w.setVisible(False)

        self.status_right = QLabel("")

        self.status_bar.addWidget(self.status_left, 1)
        self.status_bar.addWidget(self.status_separator1)
        self.status_bar.addWidget(self.status_size)
        self.status_bar.addWidget(self.status_separator2)
        self.status_bar.addWidget(self.status_date)
        self.status_bar.addWidget(self.status_separator3)
        self.status_bar.addWidget(self.status_path)
        self.status_bar.addWidget(self.status_right)

    def _show_loading(self):
        if self._loading_overlay:
            self._loading_overlay.setGeometry(self.result_list.rect())
            self._loading_overlay.raise_()
            self._loading_overlay.show()
            self._loading_spinner.start()

    def _hide_loading(self):
        if self._loading_spinner:
            self._loading_spinner.stop()
        if self._loading_overlay:
            self._loading_overlay.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_loading_overlay') and self._loading_overlay.isVisible():
            self._loading_overlay.setGeometry(self.result_list.rect())

    def _init_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #FAFAFA;
                border-bottom: 1px solid #E5E7EB;
                padding: 2px 8px;
                font-size: 13px;
            }
            QMenuBar::item {
                padding: 4px 12px;
                border-radius: 4px;
                color: #4B5563;
            }
            QMenuBar::item:selected {
                background-color: #F3F4F6;
                color: #1F2937;
            }
        """)

        TOP_MENU_STYLE = """
            QMenu {
                background-color: #FFFFFF;
                border: none;
                padding: 6px 4px;
            }
            QMenu::item {
                padding: 8px 28px 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                color: #1F2937;
                background: transparent;
                margin: 1px 4px;
            }
            QMenu::item:selected {
                background-color: #F5F3FF;
                color: #7C3AED;
            }
            QMenu::separator {
                height: 1px;
                background: #F3F4F6;
                margin: 4px 12px;
            }
        """

        file_menu = RoundedMenu(self)
        file_menu.setTitle("文件")
        file_menu.setStyleSheet(TOP_MENU_STYLE)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        menubar.addMenu(file_menu)

        settings_menu = RoundedMenu(self)
        settings_menu.setTitle("设置")
        settings_menu.setStyleSheet(TOP_MENU_STYLE)
        preferences_action = QAction("偏好设置", self)
        preferences_action.triggered.connect(self._on_open_settings)
        settings_menu.addAction(preferences_action)
        settings_menu.addSeparator()
        reset_action = QAction("恢复默认设置", self)
        reset_action.triggered.connect(self._on_reset_settings)
        settings_menu.addAction(reset_action)
        menubar.addMenu(settings_menu)

        help_menu = RoundedMenu(self)
        help_menu.setTitle("帮助")
        help_menu.setStyleSheet(TOP_MENU_STYLE)
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        menubar.addMenu(help_menu)

    def _on_reset_settings(self):
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
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
            self._scan_worker.wait(3000)
            if self._scan_worker.isRunning():
                self._scan_worker.terminate()
                self._scan_worker.wait()

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.terminate()
            self._search_worker.wait()

        reset_all_settings()

        _styled_msg_box(
            self, QMessageBox.Icon.Information,
            "操作成功", "所有设置已恢复为默认值。\n应用将重置为首次启动状态。"
        )

        self._all_results = []
        self._current_file_types = []
        self._exclude_known_types = False
        self._selected_dirs = set()
        self._is_first_launch = True

        self.result_list.clear_results()
        self.preview_panel.clear()
        self.filter_bar._reload_scope()
        self.filter_bar._check_index()
        self._search_scope_panel.reset()

        self.search_bar.search_input.clear()
        self.search_bar._set_mode('name')
        self.search_bar.case_sensitive_checkbox.setChecked(False)

        for key, btn in self.filter_bar.type_buttons.items():
            btn.setChecked(key == 'all')
        self.filter_bar._selected_category = 'all'

        self._switch_to_welcome()

    def _on_open_settings(self):
        dialog = SettingsDialog(self)
        dialog.reset_requested.connect(self._on_reset_settings)
        dialog.exec()

    def _on_about(self):
        _styled_msg_box(
            self, QMessageBox.Icon.Information,
            "关于 FileFinder",
            "FileFinder v1.0\n\n一款轻量级的本地文件搜索桌面工具\n"
            "帮助您通过文件名或文件内容快速定位电脑中的文件。"
        ).exec()

    def _connect_signals(self):
        self._welcome_page.scan_requested_with_dirs.connect(self._start_scan_with_dirs)
        self._scan_progress_page.scan_cancelled.connect(self._on_scan_cancelled)
        self._search_scope_panel.scope_changed.connect(self._on_scope_changed)
        self._search_scope_panel.scan_unscanned_requested.connect(self._on_scan_unscanned)
        self.search_bar.search_triggered.connect(self._on_search)
        self.result_list.result_selected.connect(self._on_result_selected)
        self.result_list.status_info_requested.connect(self._update_status_info)
        self.filter_bar.filter_changed.connect(self._on_filter_changed)
        self.filter_bar.scan_requested.connect(self._on_scan_requested)

    def _check_index_on_startup(self):
        if self._is_first_launch:
            self._switch_to_welcome()
            return

        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        count = db.get_index_count()

        if count == 0:
            scanned = get_scanned_dirs()
            if not scanned:
                self._switch_to_welcome()
                return

        self._switch_to_main()
        self._show_loading()
        QTimer.singleShot(100, self._deferred_index_check)

    def _switch_to_welcome(self):
        self._stacked.setCurrentWidget(self._welcome_page)
        self.status_left.setText("请选择要扫描的目录")
        self.status_right.setText("")

    def _switch_to_main(self):
        self._stacked.setCurrentWidget(self._main_page)
        self._hide_loading()
        scanned = get_scanned_dirs()
        if scanned:
            self._search_scope_panel.set_scanned_dirs(scanned)
        self._search_scope_panel.update_scope_info(self.filter_bar.get_indexed_count())

    def _switch_to_scan_progress(self):
        self._stacked.setCurrentWidget(self._scan_progress_page)
        self._scan_progress_page._title.setText("正在扫描文件...")
        self._scan_progress_page._cancel_btn.setVisible(True)
        self._scan_progress_page._cancel_btn.setEnabled(True)
        self._scan_progress_page._progress_bar.setMaximum(100)
        self._scan_progress_page._progress_bar.setValue(0)
        self._scan_progress_page._percentage.setText("0%")
        self._scan_progress_page._detail.setText("已发现 0 个文件")

    def _deferred_index_check(self):
        self.filter_bar._check_index()
        count = self.filter_bar.get_indexed_count()
        self._search_scope_panel.update_scope_info(count)
        if count == 0:
            self.status_left.setText("就绪 - 请点击[重新扫描]开始")
        else:
            self.status_left.setText(f"就绪 - 已索引 {count:,} 个文件")
        self._hide_loading()
        self.search_bar.set_focus()

    def _start_scan_with_dirs(self, dirs: list):
        config = load_config()
        current_dirs = config.get("search", {}).get("default_dirs", [])
        for d in dirs:
            if d not in current_dirs:
                current_dirs.append(d)
        config["search"]["default_dirs"] = current_dirs
        save_config(config)

        self.filter_bar._search_dirs = get_default_search_dirs()
        self.filter_bar._update_scope_label()

        self._switch_to_scan_progress()
        self._do_scan(dirs)

    def _on_scan_requested(self):
        self._switch_to_scan_progress()
        self.status_left.setText("正在扫描...")
        self.status_right.setText("")

        self._do_scan(self.filter_bar.get_search_dirs())

    def _do_scan(self, search_dirs: list, exclude_dirs: list = None):
        if exclude_dirs is None:
            exclude_dirs = [
                'node_modules', '__pycache__', '.git', '.svn', '.hg',
                '.venv', 'venv', '.tox', '.eggs', 'build', 'dist',
                '.idea', '.vscode', '.vs', '$RECYCLE.BIN',
                'System Volume Information', 'Windows', 'Program Files',
                'Program Files (x86)', 'ProgramData'
            ]

        self._scan_worker = ScanWorker(search_dirs, exclude_dirs)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

    def _on_scan_progress(self, count: int, percentage: int):
        self._scan_progress_page.update_progress(count, percentage if percentage >= 0 else None)
        self.status_left.setText(f"正在扫描... 已发现 {count:,} 个文件")

    def _on_scan_finished(self, total_files: int, elapsed: float):
        self._scan_progress_page.set_finishing()

        self.filter_bar.reset_scan_state(total_files)

        all_dirs = self.filter_bar.get_search_dirs()
        save_scanned_dirs(all_dirs)
        self._search_scope_panel.set_scanned_dirs(all_dirs)
        self._search_scope_panel.update_scope_info(total_files)

        from config import load_config, save_config
        config = load_config()
        existing_dirs = set(config.get("search", {}).get("default_dirs", []))
        for d in all_dirs:
            existing_dirs.add(d)
        config.setdefault("search", {})["default_dirs"] = list(existing_dirs)
        save_config(config)
        self.filter_bar._search_dirs = list(existing_dirs)
        self.filter_bar._update_scope_label()

        self.status_left.setText(f"扫描完成 - 共 {total_files:,} 个文件，耗时 {elapsed:.1f} 秒")
        self.status_right.setText("")

        self._update_fs_watcher()

        self._is_first_launch = False

        self._hide_loading()
        QTimer.singleShot(800, self._switch_to_main)

    def _on_scan_error(self, err_msg: str):
        self.filter_bar.reset_scan_state()
        self.status_left.setText("扫描失败")
        self._switch_to_main()
        _styled_msg_box(
            self, QMessageBox.Icon.Critical,
            "扫描错误", f"扫描过程中发生错误：\n{err_msg}"
        )

    def _on_scan_cancelled(self):
        self._scan_progress_page._detail.setText("正在取消扫描...")
        self._scan_progress_page._cancel_btn.setEnabled(False)
        QApplication.processEvents()

        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
            self._scan_worker.wait(3000)
            if self._scan_worker.isRunning():
                self._scan_worker.terminate()
                self._scan_worker.wait(2000)
        from database.db_manager import DatabaseManager
        DatabaseManager()._search_cache.invalidate()
        self.filter_bar.reset_scan_state()
        self.status_left.setText("扫描已取消")
        if self._is_first_launch:
            self._switch_to_welcome()
        else:
            self._switch_to_main()

    def _on_scan_unscanned(self, unscanned_dirs: list):
        reply = _styled_msg_box(
            self, QMessageBox.Icon.Question,
            "扫描未扫描目录",
            "以下目录尚未扫描：\n\n" +
            "\n".join(f"  \u2022 {d}" for d in unscanned_dirs) +
            "\n\n是否立即扫描这些目录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._start_scan_with_dirs(unscanned_dirs)

    def _on_search(self, name_query, content_query):
        if not name_query.strip() and not content_query.strip():
            return

        if self.filter_bar.get_indexed_count() == 0:
            reply = _styled_msg_box(
                self, QMessageBox.Icon.Question,
                "尚未扫描",
                "尚未建立文件索引。是否立即扫描磁盘？\n\n"
                "扫描后搜索速度将大幅提升，只需扫描一次即可。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_scan_requested()
            return

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.terminate()
            self._search_worker.wait()

        case_sensitive = self.search_bar.is_case_sensitive()
        all_dirs = self._search_scope_panel.get_all_scanned_dirs()
        selected_dirs = self._search_scope_panel.get_selected_dirs()
        self._selected_dirs = set(selected_dirs)

        query = SearchQuery(
            name_query=name_query if name_query else None,
            content_query=content_query if content_query else None,
            content_mode='keyword',
            include_dirs=all_dirs if all_dirs else self.filter_bar.get_search_dirs(),
            exclude_dirs=get_exclude_dirs(),
            max_results=get_max_results(),
            name_case_sensitive=case_sensitive,
            content_case_sensitive=case_sensitive,
            file_types=[],
            exclude_file_types=[]
        )

        self.status_left.setText("正在搜索...")
        self.status_right.setText("")
        self._hide_loading()
        self.result_list.clear_results()
        self.result_list.show_search_progress("正在搜索...")

        self._search_worker = SearchWorker(query)
        self._search_worker.finished.connect(self._on_search_finished)
        self._search_worker.start()

    def _on_search_finished(self, results):
        self._all_results = results
        self._apply_current_filter()

    def _apply_current_filter(self):
        self.result_list.hide_search_progress()

        filtered = self._all_results

        if self._selected_dirs:
            filtered = [r for r in filtered
                       if self._is_path_in_selected_dirs(r.file_item.path)]

        if self._exclude_known_types:
            from models.file_item import FILE_TYPE_MAP
            known_exts = set(FILE_TYPE_MAP.keys())
            filtered = [r for r in filtered
                       if r.file_item.extension.lower() not in known_exts
                       and not r.file_item.is_directory]
        elif self._current_file_types:
            filtered = [r for r in filtered
                       if r.file_item.extension.lower() in self._current_file_types
                       and not r.file_item.is_directory]
        elif self.filter_bar.get_selected_category() == 'folder':
            filtered = [r for r in filtered if r.file_item.is_directory]

        self.result_list.clear_results()
        for result in filtered:
            self.result_list.add_result(result)

        count = len(filtered)
        if count == 0:
            self.status_left.setText("未找到匹配的文件")
            self.status_right.setText("")
            if self._all_results is not None and len(self._all_results) > 0:
                self.result_list.show_empty_state("当前筛选下无匹配文件")
            else:
                self.result_list.show_empty_state("未找到匹配文件")
        else:
            self.result_list.hide_empty_state()
            self.status_left.setText(f"找到 {count} 个结果")
            self.status_right.setText(f"共 {count} 项")
            self.result_list.setFocus()

    def _on_result_selected(self, result):
        self.preview_panel.show_result(result)

    def _update_status_info(self, result):
        file_item = result.file_item

        self.status_size.setText(f"大小：{file_item.size_display}")
        self.status_date.setText(f"修改时间：{file_item.modified_date}")
        self.status_path.setText(f"路径：{file_item.path}")

        for w in [self.status_separator1, self.status_size,
                  self.status_separator2, self.status_date,
                  self.status_separator3, self.status_path]:
            w.setVisible(True)

    def _on_filter_changed(self, category):
        from models.file_item import FILE_TYPE_MAP
        self._current_file_types = []
        self._exclude_known_types = False
        if category == 'other':
            self._exclude_known_types = True
        elif category == 'folder':
            pass
        elif category != 'all':
            for ext, ftype in FILE_TYPE_MAP.items():
                if ftype == category:
                    self._current_file_types.append(ext)

        if self._all_results:
            self._apply_current_filter()

    def _on_scope_changed(self, dirs):
        self._selected_dirs = set(dirs)
        if self._all_results:
            self._apply_current_filter()

    def _is_path_in_selected_dirs(self, file_path: str) -> bool:
        if not self._selected_dirs:
            return True
        normalized = os.path.normcase(os.path.normpath(file_path))
        for d in self._selected_dirs:
            norm_d = os.path.normcase(os.path.normpath(d))
            if normalized.startswith(norm_d + os.sep) or normalized == norm_d:
                return True
        return False

    def _update_fs_watcher(self):
        self._fs_watcher.removePaths(self._fs_watcher.directories())
        search_dirs = self.filter_bar.get_search_dirs()
        for d in search_dirs:
            if os.path.isdir(d):
                self._fs_watcher.addPath(d)
                for root, dirs, _ in os.walk(d):
                    for sub in dirs:
                        full = os.path.join(root, sub)
                        try:
                            self._fs_watcher.addPath(full)
                        except Exception:
                            pass

    def _on_fs_directory_changed(self, path: str):
        self._pending_fs_changes.add(path)
        self._fs_refresh_timer.start()

    def _on_fs_refresh_timeout(self):
        if not self._pending_fs_changes:
            return

        from database.db_manager import DatabaseManager
        db = DatabaseManager()

        for dir_path in self._pending_fs_changes:
            try:
                self._sync_directory(db, dir_path)
            except Exception as e:
                logger.debug(f"同步目录变更失败: {dir_path}, {e}")

        self._pending_fs_changes.clear()

        if self._all_results:
            self._refresh_current_search()

    def _sync_directory(self, db, dir_path: str):
        if not os.path.isdir(dir_path):
            entries = db.search_files(pattern="", max_results=10000)
            for entry in entries:
                ep = entry["path"] if isinstance(entry, dict) else entry[0]
                if ep and ep.startswith(dir_path):
                    if not os.path.exists(ep):
                        db.delete_file_entry(ep)
            return

        try:
            current_files = set()
            for item in os.listdir(dir_path):
                full_path = os.path.join(dir_path, item)
                current_files.add(full_path)
                try:
                    stat = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)
                    _, ext = os.path.splitext(item)
                    existing = db.get_file_entry(full_path)
                    if existing is None:
                        db.add_file_entry(
                            path=full_path, name=item, ext=ext.lower() if ext else "",
                            size=stat.st_size if not is_dir else 0,
                            mtime=stat.st_mtime, is_dir=1 if is_dir else 0
                        )
                    else:
                        db.update_file_entry(
                            old_path=full_path, new_name=item,
                            new_ext=ext.lower() if ext else "",
                            new_size=stat.st_size if not is_dir else 0,
                            new_mtime=stat.st_mtime
                        )
                except (PermissionError, OSError):
                    continue

            entries = db.search_files(pattern="", max_results=10000)
            for entry in entries:
                ep = entry["path"] if isinstance(entry, dict) else entry[0]
                if ep:
                    parent = os.path.dirname(ep)
                    if parent == dir_path and ep not in current_files:
                        if not os.path.exists(ep):
                            db.delete_file_entry(ep)
        except (PermissionError, OSError):
            pass

    def _refresh_current_search(self):
        name_query = self.search_bar.get_name_query()
        content_query = self.search_bar.get_content_query()
        if name_query.strip() or content_query.strip():
            self._on_search(name_query, content_query)

    def closeEvent(self, event):
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
            self._scan_worker.wait(3000)
            if self._scan_worker.isRunning():
                self._scan_worker.terminate()
                self._scan_worker.wait()

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.terminate()
            self._search_worker.wait()

        from database.db_manager import DatabaseManager
        DatabaseManager().close()

        super().closeEvent(event)
