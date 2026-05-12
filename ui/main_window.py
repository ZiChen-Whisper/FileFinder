import os
import math
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QStatusBar,
                             QLabel, QHBoxLayout, QMessageBox, QSplitter, QFrame,
                             QStackedWidget, QSizePolicy, QDialog, QProgressBar,
                             QPushButton, QCheckBox, QTreeWidget, QTreeWidgetItem,
                             QLineEdit, QFileDialog, QApplication,
                             QListWidget, QListWidgetItem, QScrollArea, QAbstractItemView,
                             QTextEdit, QRadioButton, QButtonGroup, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QFileSystemWatcher, QPropertyAnimation, QEasingCurve, QRectF, QSize, QPointF, Property
from PySide6.QtGui import QIcon, QAction, QPainter, QColor, QPen, QFont, QFontMetrics, QPixmap, QPolygonF
from models.search_query import SearchQuery
from core.search_engine import SearchEngine
from .widgets import SearchBar, ResultListWidget, FilterBar, PreviewPanel, RoundedMenu
from .widgets.filter_bar import DirListWidget
from .dialogs import SettingsDialog
from .style_constants import COLORS, FONT, RADIUS, BTN, DIALOG, TRANSITION
from .modern_dialog import ModernDialogBase
from .style_manager import (
    scrollbar_style, msg_box_style, status_bar_style, status_divider_style,
    button_primary, button_secondary, button_small_primary, button_small_secondary,
    button_cancel_danger, button_tag, button_scan, button_scan_green,
    button_filter, config_button_style, icon_button_style,
    dialog_frame_style, dialog_title_style, dialog_body_style, dialog_style,
    input_style, search_input_style, radio_button_style,
    list_style, progress_bar_style, progress_bar_success_style,
    progress_bar_warning_style, progress_bar_error_style,
    scan_log_style, splitter_style, menubar_style, menu_style,
    tree_widget_style, scope_info_scroll_style,
    label_caption_style, label_micro_style, label_header_style, label_body_style,
    badge_style, badge_brand_style,
)
from config import get_exclude_dirs, get_max_results, is_first_launch, get_scanned_dirs, save_scanned_dirs, load_config, save_config, get_default_search_dirs, reset_all_settings, SCAN_STATUS_COMPLETE, SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED, SCAN_STATUS_SCANNING, set_scan_status, set_scan_status_batch, get_scan_status

logger = logging.getLogger(__name__)

from utils.flow_layout import FlowLayout


class ModernMessageBox(ModernDialogBase):
    def __init__(self, parent=None, icon_type='info', title='', text='',
                 buttons=None, default_button=None):
        super().__init__(parent, title=title, min_width=DIALOG.MIN_WIDTH, resizable=False)
        self._result = None
        self._buttons = buttons or {}
        self._icon_type = icon_type
        self._text = text
        self._default_button = default_button
        self._init_ui()

    def _init_ui(self):
        icon_pixmap = self._create_icon_pixmap()

        def build_content(content_widget):
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(DIALOG.CONTENT_SPACING)
            layout.setContentsMargins(DIALOG.PADDING, 4, DIALOG.PADDING, DIALOG.PADDING)

            text_label = QLabel(self._text)
            text_label.setStyleSheet(dialog_body_style())
            text_label.setWordWrap(True)

            layout.addWidget(text_label)

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

            layout.addSpacing(8)
            layout.addLayout(btn_row)

        self._create_shadow_frame(build_content, icon_pixmap=icon_pixmap)

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
            color = QColor(COLORS.BRAND)
            color.setAlpha(alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(int(x - self._dot_radius), int(y - self._dot_radius),
                              self._dot_radius * 2, self._dot_radius * 2)
        painter.end()



class ScanWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(int, float)
    error = Signal(str)
    dir_completed = Signal(str)
    dir_scanned = Signal(str)

    SKIP_DIR_NAMES = frozenset({
        'node_modules', '__pycache__', '.git', '.svn', '.hg',
        '.venv', 'venv', '.tox', '.eggs', 'build', 'dist',
        '.idea', '.vscode', '.vs', '$RECYCLE.BIN',
        'System Volume Information', 'Windows',
        'Program Files', 'Program Files (x86)', 'ProgramData'
    })

    def __init__(self, search_dirs, exclude_dirs, parent=None):
        super().__init__(parent)
        self._search_dirs = search_dirs
        self._exclude_dirs = set(
            os.path.normpath(d).lower() for d in (exclude_dirs or [])
        )
        self._cancelled = False
        self._last_progress_time = 0
        self._progress_interval = 0.3
        self._batch_size = 500
        self._total_dirs = 0

    def cancel(self):
        self._cancelled = True

    def _should_skip_dir(self, name, full_path):
        if name in self.SKIP_DIR_NAMES:
            return True
        if name.startswith('.') or name.startswith('$'):
            return True
        normalized = os.path.normpath(full_path).lower()
        for exc in self._exclude_dirs:
            if normalized == exc or normalized.startswith(exc + os.sep):
                return True
        return False

    def _pre_scan_count_dirs(self, normalized_dirs):
        total = 0
        for base_dir in normalized_dirs:
            if self._cancelled:
                return 0
            if not os.path.isdir(base_dir):
                continue
            for root, dirs, _ in os.walk(base_dir, onerror=lambda e: None):
                if self._cancelled:
                    return 0
                dirs[:] = [
                    d for d in dirs
                    if not self._should_skip_dir(d, os.path.join(root, d))
                ]
                total += len(dirs) + 1
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

            for d in normalized_dirs:
                set_scan_status(d, SCAN_STATUS_SCANNING)

            self.progress.emit(0, 0, "准备扫描...")

            self.progress.emit(0, 0, "正在统计目录数量...")
            self._total_dirs = self._pre_scan_count_dirs(normalized_dirs)
            if self._cancelled:
                for d in normalized_dirs:
                    set_scan_status(d, SCAN_STATUS_INCOMPLETE)
                db.clear_index()
                return

            total_files = 0
            visited_dirs = 0
            batch = []
            dir_sizes = {}
            dir_count = 0
            file_count = 0
            current_dir_display = ""

            for base_dir in normalized_dirs:
                if self._cancelled:
                    break
                if not os.path.isdir(base_dir):
                    logger.warning(f"扫描目录不存在，跳过: {base_dir}")
                    continue

                for root, dirs, files in os.walk(base_dir, onerror=lambda e: None):
                    if self._cancelled:
                        break
                    dirs[:] = [
                        d for d in dirs
                        if not self._should_skip_dir(d, os.path.join(root, d))
                    ]

                    visited_dirs += 1
                    current_dir_display = root

                    if self._total_dirs > 0:
                        pct = min(int(visited_dirs / self._total_dirs * 100), 99)
                    else:
                        pct = 0

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
                            dir_count += 1
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
                            file_count += 1

                            parent = root
                            dir_sizes.setdefault(parent, 0)
                            dir_sizes[parent] += stat.st_size

                            if len(batch) >= self._batch_size:
                                db.insert_file_batch(batch, skip_cache_invalidate=True)
                                batch.clear()
                                total_files = dir_count + file_count
                                now = time.time()
                                if now - self._last_progress_time >= self._progress_interval:
                                    self._last_progress_time = now
                                    self.progress.emit(total_files, pct, current_dir_display)
                                    self.dir_scanned.emit(current_dir_display)
                        except Exception:
                            continue

                if not self._cancelled:
                    self.dir_completed.emit(base_dir)

            if self._cancelled:
                for d in normalized_dirs:
                    set_scan_status(d, SCAN_STATUS_INCOMPLETE)
                db.clear_index()
                return

            if batch:
                db.insert_file_batch(batch, skip_cache_invalidate=True)

            all_dirs_sorted = sorted(dir_sizes.keys(), key=lambda p: -p.count(os.sep))
            for dir_path in all_dirs_sorted:
                parent = os.path.dirname(dir_path)
                if parent and parent != dir_path:
                    dir_sizes.setdefault(parent, 0)
                    dir_sizes[parent] += dir_sizes[dir_path]

            if dir_sizes:
                db.update_folder_sizes(dir_sizes, skip_cache_invalidate=True)

            db._search_cache.invalidate()

            total_files = dir_count + file_count
            for d in normalized_dirs:
                set_scan_status(d, SCAN_STATUS_COMPLETE)

            elapsed = time.time() - start_time
            self.progress.emit(total_files, 100, "扫描完成")
            self.finished.emit(total_files, elapsed)
        except Exception as e:
            logger.error(f"扫描异常: {e}", exc_info=True)
            if not self._cancelled:
                for d in self._search_dirs:
                    set_scan_status(d, SCAN_STATUS_FAILED)
                self.error.emit(str(e))


class SearchWorker(QThread):
    results_ready = Signal(object)

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self._query = query
        self._engine = SearchEngine()

    def run(self):
        try:
            results = self._engine.search(self._query)
            self.results_ready.emit(results)
        except Exception:
            self.results_ready.emit([])

    def cancel(self):
        self._engine.cancel()




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
        title_font.setPointSize(FONT.DISPLAY_PT)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(dialog_title_style())
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dir_input_row = QHBoxLayout()
        dir_input_row.setSpacing(8)

        self._dir_input = QLineEdit()
        self._dir_input.setPlaceholderText("输入目录路径，如 D:\\Projects 或 C:\\Users")
        self._dir_input.setFixedHeight(40)
        self._dir_input.setStyleSheet(input_style())

        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedSize(80, 40)
        browse_btn.setStyleSheet(button_secondary("padding: 0px 14px; border-radius: 10px;"))
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse)

        add_btn = QPushButton("+ 添加")
        add_btn.setFixedSize(80, 40)
        add_btn.setStyleSheet(button_primary("padding: 0px 14px; border-radius: 10px;"))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add_dir)

        dir_input_row.addWidget(self._dir_input, 1)
        dir_input_row.addWidget(browse_btn)
        dir_input_row.addWidget(add_btn)

        self._dir_list_widget = DirListWidget(self)
        self._dir_list_widget.setMinimumHeight(80)
        self._dir_list_widget.setMaximumHeight(200)
        self._dir_list_widget.setStyleSheet(list_style())
        self._dir_list_widget.setVisible(False)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)

        all_drives_btn = QPushButton("所有驱动器")
        all_drives_btn.setStyleSheet(button_small_secondary())
        all_drives_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_drives_btn.clicked.connect(self._on_add_all_drives)

        user_dirs_btn = QPushButton("常用目录")
        user_dirs_btn.setStyleSheet(button_small_secondary())
        user_dirs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        user_dirs_btn.clicked.connect(self._on_add_user_dirs)

        self._quick_drive_btns = []
        from utils.path_helper import get_all_drives
        for drive in get_all_drives():
            drive_letter = drive[:2]
            btn = QPushButton(drive_letter)
            btn.setStyleSheet(button_small_secondary())
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
        self._start_btn.setStyleSheet(button_primary("padding: 10px 20px; border-radius: 12px; font-size: 16px;"))
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
        self.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; }}")

    def _create_fallback_pixmap(self) -> QPixmap:
        pixmap = QPixmap(96, 96)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(COLORS.BRAND))
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

    def reset(self):
        self._selected_dirs = []
        self._dir_input.clear()
        self._update_dir_display()


class ScanProgressDialog(QWidget):
    scan_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_cancelling = False
        self._scan_start_time = 0.0
        self._last_logged_dir = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(60, 40, 60, 40)

        self._title = QLabel("正在扫描文件...")
        title_font = QFont()
        title_font.setPointSize(FONT.DISPLAY_PT)
        title_font.setBold(True)
        self._title.setFont(title_font)
        self._title.setStyleSheet(dialog_title_style())
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setWordWrap(True)

        self._percentage = QLabel("0%")
        pct_font = QFont()
        pct_font.setPointSize(48)
        pct_font.setBold(True)
        self._percentage.setFont(pct_font)
        self._percentage.setStyleSheet(f"color: {COLORS.BRAND}; border: none; background: transparent;")
        self._percentage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(16)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(progress_bar_style(16, 8))

        detail_row = QHBoxLayout()
        detail_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._detail = QLabel("已发现 0 个文件")
        self._detail.setStyleSheet(label_body_style())

        self._eta_label = QLabel("")
        self._eta_label.setStyleSheet(f"font-size: {DIALOG.BODY_FONT_SIZE}; color: {COLORS.TEXT_PLACEHOLDER}; border: none; background: transparent; text-decoration: none;")

        detail_row.addWidget(self._detail)
        detail_row.addSpacing(16)
        detail_row.addWidget(self._eta_label)

        self._scan_log = QTextEdit()
        self._scan_log.setReadOnly(True)
        self._scan_log.setStyleSheet(scan_log_style())
        self._scan_log.setMaximumHeight(200)

        self._cancel_btn = QPushButton("取消扫描")
        self._cancel_btn.setFixedSize(140, 40)
        self._cancel_btn.setStyleSheet(button_cancel_danger())
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._on_cancel)

        layout.addWidget(self._title)
        layout.addWidget(self._percentage)
        layout.addWidget(self._progress_bar)
        layout.addLayout(detail_row)
        layout.addSpacing(8)
        layout.addWidget(self._scan_log, 1)
        layout.addSpacing(20)
        layout.addWidget(self._cancel_btn, 0, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        self.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; }}")

    def start_scan(self):
        import time
        self._scan_start_time = time.time()
        self._last_logged_dir = ""
        self._scan_log.clear()

    def update_progress(self, count: int, percentage: int = None, current_dir: str = ""):
        self._detail.setText(f"已发现 {count:,} 个文件")

        if current_dir and current_dir not in ("准备扫描...", "正在统计目录数量...", "扫描完成"):
            self._title.setText(f"正在扫描 {current_dir}")

            if current_dir != self._last_logged_dir:
                self._last_logged_dir = current_dir
                self._scan_log.append(current_dir)
                sb = self._scan_log.verticalScrollBar()
                sb.setValue(sb.maximum())

        if percentage is not None and percentage >= 0:
            self._progress_bar.setMaximum(100)
            pct_val = min(percentage, 100)
            self._progress_bar.setValue(pct_val)
            self._percentage.setText(f"{pct_val}%")

            if 0 < percentage < 100 and self._scan_start_time > 0:
                import time
                elapsed = time.time() - self._scan_start_time
                if elapsed > 0:
                    eta_seconds = elapsed * (100 - percentage) / percentage
                    if eta_seconds > 60:
                        self._eta_label.setText(f"预计剩余: {int(eta_seconds // 60)}分{int(eta_seconds % 60)}秒")
                    else:
                        self._eta_label.setText(f"预计剩余: {int(eta_seconds)}秒")
            elif percentage >= 100:
                self._eta_label.setText("")
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
        self._percentage.setStyleSheet(f"color: {COLORS.SUCCESS}; border: none; background: transparent;")
        self._title.setText("扫描完成！")
        self._detail.setText("正在加载索引...")
        self._eta_label.setText("")
        self._cancel_btn.setVisible(False)
        self._cancel_btn.setEnabled(False)
        self._progress_bar.setStyleSheet(progress_bar_success_style(16, 8))

    def set_cancelling(self):
        self._is_cancelling = True
        self._title.setText("正在取消扫描...")
        self._title.setStyleSheet(f"color: {COLORS.WARNING}; border: none; background: transparent;")
        self._detail.setText("请稍候，正在安全终止扫描进程")
        self._eta_label.setText("")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setText("取消中...")
        self._progress_bar.setStyleSheet(progress_bar_warning_style(16, 8))

    def set_error(self, err_msg: str):
        self._title.setText("扫描失败")
        self._title.setStyleSheet(f"color: {COLORS.ERROR}; border: none; background: transparent;")
        self._percentage.setText("!")
        self._percentage.setStyleSheet(f"color: {COLORS.ERROR}; border: none; background: transparent;")
        self._detail.setText(f"错误: {err_msg[:80]}")
        self._eta_label.setText("")
        self._cancel_btn.setText("返回")
        self._cancel_btn.setEnabled(True)
        self._cancel_btn.setVisible(True)
        self._progress_bar.setStyleSheet(progress_bar_error_style(16, 8))

    def reset_state(self):
        self._is_cancelling = False
        self._title.setText("正在扫描文件...")
        self._title.setStyleSheet(dialog_title_style())
        self._percentage.setStyleSheet(f"color: {COLORS.BRAND}; border: none; background: transparent;")
        self._progress_bar.setStyleSheet(progress_bar_style(16, 8))
        self._cancel_btn.setText("取消扫描")
        self._cancel_btn.setEnabled(True)
        self._cancel_btn.setVisible(True)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._percentage.setText("0%")
        self._detail.setText("已发现 0 个文件")
        self._eta_label.setText("")
        self._scan_log.clear()
        self._last_logged_dir = ""
        self._scan_start_time = 0.0

    def _on_cancel(self):
        if not self._is_cancelling:
            self.set_cancelling()
            self.scan_cancelled.emit()


class ElidedPathLabel(QLabel):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self._full_path = path
        self._update_display()
        self.setToolTip(path)

    def _update_display(self):
        path = self._full_path.rstrip(os.sep)
        name = os.path.basename(path) or path
        parent_part = path[:len(path) - len(name)] if name != path else ""
        if parent_part and name != path:
            self.setText(f"{parent_part}<b>{name}</b>")
        else:
            self.setText(f"<b>{name}</b>")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self):
        fm = self.fontMetrics()
        available = self.width()
        path = self._full_path.rstrip(os.sep)
        name = os.path.basename(path) or path
        parent_part = path[:len(path) - len(name)] if name != path else ""
        full_text = f"{parent_part}{name}"
        elided = fm.elidedText(full_text, Qt.TextElideMode.ElideMiddle, available)
        if elided.endswith('…') or elided != full_text:
            super().setText(elided)
        else:
            if parent_part and name != path:
                super().setText(f"{parent_part}<b>{name}</b>")
            else:
                super().setText(f"<b>{name}</b>")

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self):
        return QSize(0, super().minimumSizeHint().height())


class AnimatedRadioButton(QRadioButton):
    _INDICATOR_MARGIN = 3

    def __init__(self, text="", parent=None, font_pt=None):
        super().__init__(text, parent)
        self._check_opacity = 0.0
        self._hovered = False
        self._font_pt = font_pt or FONT.CAPTION_PT
        self._anim = QPropertyAnimation(self, b"check_opacity")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._check_opacity)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def get_check_opacity(self):
        return self._check_opacity

    def set_check_opacity(self, opacity):
        self._check_opacity = opacity
        self.update()

    check_opacity = Property(float, get_check_opacity, set_check_opacity)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        m = self._INDICATOR_MARGIN
        indicator_size = 14
        indicator_y = (self.height() - indicator_size) / 2
        indicator_rect = QRectF(m, indicator_y, indicator_size, indicator_size)
        center = indicator_rect.center()
        outer_radius = indicator_size / 2

        if self.isEnabled():
            if self.isChecked():
                border_color = QColor(COLORS.BRAND)
                border_color.setAlphaF(max(0.3, self._check_opacity))
                if self._hovered:
                    border_color = QColor(COLORS.BRAND_HOVER)
                    border_color.setAlphaF(max(0.5, self._check_opacity))
                painter.setPen(QPen(border_color, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, outer_radius, outer_radius)

                inner_radius = outer_radius * 0.4
                dot_color = QColor(COLORS.BRAND_HOVER if self._hovered else COLORS.BRAND)
                dot_color.setAlphaF(self._check_opacity)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(dot_color)
                painter.drawEllipse(center, inner_radius, inner_radius)
            else:
                hover_border = QColor(COLORS.BRAND) if self._hovered else QColor(COLORS.BORDER_HOVER)
                painter.setPen(QPen(hover_border, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, outer_radius, outer_radius)
        else:
            if self.isChecked():
                painter.setPen(QPen(QColor(COLORS.BORDER_HOVER), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, outer_radius, outer_radius)

                inner_radius = outer_radius * 0.4
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(COLORS.BORDER_HOVER))
                painter.drawEllipse(center, inner_radius, inner_radius)
            else:
                painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, outer_radius, outer_radius)

        text_x = m + indicator_size + 6
        text_color = QColor(COLORS.TEXT_SECONDARY if self.isEnabled() else COLORS.TEXT_PLACEHOLDER)
        if self._hovered and self.isEnabled():
            text_color = QColor(COLORS.TEXT_PRIMARY)
        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(self._font_pt)
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_rect = QRectF(text_x, 0, fm.horizontalAdvance(self.text()) + 4, self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        painter.end()

    def minimumSizeHint(self):
        font = QFont()
        font.setPointSize(self._font_pt)
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self.text())
        return QSize(self._INDICATOR_MARGIN + 14 + 6 + text_width + 4, 26)

    def sizeHint(self):
        return self.minimumSizeHint()


class _RoundedPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._resize_edge_width = 6
        self._hovering_edge = False
        self._dragging = False
        self._drag_start_x = 0
        self._drag_start_sizes = []
        self.setMouseTracking(True)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(0, 0)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = RADIUS.LARGE
        rect = QRectF(self.rect())

        painter.setBrush(QColor(COLORS.BG_PRIMARY))
        painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 1))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), r, r)

        painter.end()

    def _get_splitter(self):
        splitter = self.parent()
        if isinstance(splitter, QSplitter):
            return splitter
        return None

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and event.position().x() < self._resize_edge_width):
            splitter = self._get_splitter()
            if splitter:
                self._dragging = True
                self._drag_start_x = event.globalPosition().x()
                self._drag_start_sizes = splitter.sizes()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            splitter = self._get_splitter()
            if splitter:
                delta = self._drag_start_x - event.globalPosition().x()
                my_index = splitter.indexOf(self)
                new_width = max(self.minimumWidth(),
                                self._drag_start_sizes[my_index] + delta)
                total = sum(self._drag_start_sizes)
                other_index = 1 - my_index
                other_width = max(splitter.widget(other_index).minimumWidth(),
                                  total - new_width)
                if new_width + other_width <= total:
                    splitter.setSizes([other_width, new_width]
                                      if my_index == 1 else [new_width, other_width])
            event.accept()
            return
        if event.position().x() < self._resize_edge_width:
            if not self._hovering_edge:
                self._hovering_edge = True
                self.setCursor(Qt.CursorShape.SplitHCursor)
        else:
            if self._hovering_edge:
                self._hovering_edge = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        if not self._dragging:
            if self._hovering_edge:
                self._hovering_edge = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)


class CollapsibleSection(QWidget):
    def __init__(self, title: str, default_expanded: bool = True, parent=None):
        super().__init__(parent)
        self._expanded = default_expanded
        self._title = title
        self._content_widget = None
        self._toggle_btn = None
        self._header_widget = None
        self._animation = None
        self._content_height = 0
        self._init_header()

    def _init_header(self):
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._header_widget = QWidget()
        self._header_widget.setObjectName("sectionHeader")
        self._header_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header_widget.setStyleSheet(f"""
            QWidget#sectionHeader {{
                background-color: {COLORS.BG_PRIMARY};
                border-radius: {RADIUS.LARGE}px;
                border: none;
            }}
            QWidget#sectionHeader:hover {{
                background-color: {COLORS.BG_HOVER};
            }}
        """)
        header_row = QHBoxLayout(self._header_widget)
        header_row.setContentsMargins(10, 6, 10, 6)
        header_row.setSpacing(6)

        self._toggle_btn = QPushButton()
        self._toggle_btn.setFixedSize(16, 16)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                outline: none;
                border-radius: {RADIUS.SMALL}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_HOVER};
            }}
        """)
        self._toggle_btn.clicked.connect(self._toggle)
        self._update_toggle_icon()

        title_label = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(FONT.BODY_PT)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; border: none; background: transparent;")

        header_row.addWidget(self._toggle_btn)
        header_row.addWidget(title_label)
        header_row.addStretch()

        self._header_widget.mousePressEvent = lambda e: self._toggle() if e.button() == Qt.MouseButton.LeftButton else None

        self._main_layout.addWidget(self._header_widget)
        self.setLayout(self._main_layout)

    def _update_toggle_icon(self):
        painter = QPainter()
        dpr = self.devicePixelRatio() if hasattr(self, 'devicePixelRatio') else 1.0
        pixmap = QPixmap(int(16 * dpr), int(16 * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(COLORS.BRAND), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        cx, cy = 8, 8
        if self._expanded:
            painter.drawLine(4, 6, 8, 10)
            painter.drawLine(8, 10, 12, 6)
        else:
            painter.drawLine(6, 4, 10, 8)
            painter.drawLine(10, 8, 6, 12)
        painter.end()
        self._toggle_btn.setIcon(QIcon(pixmap))

    def _toggle(self):
        self._expanded = not self._expanded
        self._update_toggle_icon()
        if self._content_widget:
            if self._animation:
                self._animation.stop()
                self._animation = None
            if self._expanded:
                self._content_widget.setVisible(True)
                content_height = self._content_widget.sizeHint().height()
                self._content_widget.setMaximumHeight(0)
                self._animation = QPropertyAnimation(self._content_widget, b"maximumHeight")
                self._animation.setDuration(200)
                self._animation.setStartValue(0)
                self._animation.setEndValue(content_height)
                self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                self._animation.finished.connect(self._on_expand_finished)
                self._animation.start()
            else:
                current_height = self._content_widget.height()
                self._animation = QPropertyAnimation(self._content_widget, b"maximumHeight")
                self._animation.setDuration(200)
                self._animation.setStartValue(current_height)
                self._animation.setEndValue(0)
                self._animation.setEasingCurve(QEasingCurve.Type.InCubic)
                self._animation.finished.connect(self._on_collapse_finished)
                self._animation.start()

    def _on_expand_finished(self):
        if self._content_widget:
            self._content_widget.setMaximumHeight(16777215)

    def _on_collapse_finished(self):
        if self._content_widget and not self._expanded:
            self._content_widget.setVisible(False)
            self._content_widget.setMaximumHeight(0)

    def set_content(self, widget: QWidget):
        self._content_widget = widget
        self._content_widget.setVisible(self._expanded)
        if not self._expanded:
            self._content_widget.setMaximumHeight(0)
        self._main_layout.addWidget(self._content_widget)


class HoverInfoIcon(QLabel):
    def __init__(self, tooltip_text: str, parent=None):
        super().__init__(parent)
        self._tooltip_text = tooltip_text
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setToolTip(tooltip_text)
        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        bg_color = QColor(COLORS.BRAND) if self._hovered else QColor(COLORS.BORDER_HOVER)
        painter.setBrush(bg_color)
        painter.drawEllipse(0, 0, 16, 16)
        painter.setPen(QColor(COLORS.BG_PRIMARY))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, 16, 16), Qt.AlignmentFlag.AlignCenter, "!")
        painter.end()


class InfoIconLabel(QLabel):
    def __init__(self, tooltip_text: str, parent=None):
        super().__init__(parent)
        self._tooltip_text = tooltip_text
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setToolTip(tooltip_text)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS.BORDER_HOVER))
        painter.drawEllipse(0, 0, 16, 16)
        painter.setPen(QColor(COLORS.BG_PRIMARY))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, 16, 16), Qt.AlignmentFlag.AlignCenter, "!")
        painter.end()


class SearchScopePanel(QWidget):
    scope_changed = Signal(list)
    scan_unscanned_requested = Signal(list)
    scan_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scanned_dirs = []
        self._selected_dirs = set()
        self._custom_dir_list = []
        self._scope_mode = 'all'
        self._indexed_count = 0
        self._is_scanning = False
        self._search_dirs = []
        self._init_ui()
        self._reload_scope()

    def _reload_scope(self):
        from config import get_default_search_dirs, get_scanned_dirs
        self._search_dirs = get_default_search_dirs()
        self._scanned_dirs = get_scanned_dirs()
        self._update_scope_info()
        self._update_status_dot()
        self._update_scan_btn_state()

    def _init_ui(self):
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(12, 8, 12, 8)
        self._main_layout.setSpacing(4)

        self._scope_collapsible = CollapsibleSection("指定搜索范围", default_expanded=True)
        scope_content = QWidget()
        scope_content.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; border-radius: {RADIUS.LARGE}px; }}")
        scope_content_layout = QVBoxLayout()
        scope_content_layout.setContentsMargins(10, 6, 10, 6)
        scope_content_layout.setSpacing(4)

        self._scope_detail = QLabel("")
        self._scope_detail.setStyleSheet(label_micro_style())
        scope_content_layout.addWidget(self._scope_detail)

        radio_row = QHBoxLayout()
        radio_row.setSpacing(12)

        self._scope_radio_group = QButtonGroup(self)
        self._all_radio = AnimatedRadioButton("全部已扫描目录", font_pt=FONT.MICRO_PT)
        self._all_radio.setChecked(True)
        self._all_radio.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scope_radio_group.addButton(self._all_radio)

        self._custom_radio = AnimatedRadioButton("自定义搜索范围", font_pt=FONT.MICRO_PT)
        self._custom_radio.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scope_radio_group.addButton(self._custom_radio)

        from .widgets.filter_bar import _make_colored_icon
        custom_settings_icon = _make_colored_icon("icons/settings.svg", COLORS.TEXT_SECONDARY, 16)
        self._custom_settings_btn = QPushButton()
        self._custom_settings_btn.setIcon(custom_settings_icon)
        self._custom_settings_btn.setIconSize(QSize(14, 14))
        self._custom_settings_btn.setFixedSize(28, 28)
        self._custom_settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._custom_settings_btn.setStyleSheet(f"""
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
        """)
        self._custom_settings_btn.clicked.connect(self._on_custom_settings_clicked)
        self._custom_settings_btn.setVisible(False)

        radio_row.addWidget(self._all_radio)
        radio_row.addWidget(self._custom_radio)
        radio_row.addWidget(self._custom_settings_btn)
        radio_row.addStretch()
        scope_content_layout.addLayout(radio_row)

        self._scope_radio_group.buttonClicked.connect(self._on_scope_radio_clicked)

        self._dir_flow_layout = FlowLayout(spacing=6)

        self._dir_scroll_content = QWidget()
        self._dir_scroll_content.setLayout(self._dir_flow_layout)
        self._dir_scroll_content.setStyleSheet("QWidget { background: transparent; }")

        self._scroll = QScrollArea()
        self._scroll.setWidget(self._dir_scroll_content)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setMinimumHeight(32)
        self._scroll.setMaximumHeight(80)
        self._scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {COLORS.BG_SECONDARY}; border-radius: {RADIUS.SMALL}px; }}" + scrollbar_style())
        self._scroll.setVisible(False)

        scope_content_layout.addWidget(self._scroll)
        scope_content.setLayout(scope_content_layout)
        self._scope_collapsible.set_content(scope_content)

        self._main_layout.addWidget(self._scope_collapsible)

        self._manage_collapsible = CollapsibleSection("管理扫描路径", default_expanded=True)
        manage_content = QWidget()
        manage_content.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; border-radius: {RADIUS.LARGE}px; }}")
        manage_content_layout = QVBoxLayout()
        manage_content_layout.setContentsMargins(10, 6, 10, 6)
        manage_content_layout.setSpacing(4)

        self._scope_status_widget = QWidget()
        self._scope_status_widget.setStyleSheet("QWidget { background: transparent; }")
        self._scope_status_layout = QHBoxLayout(self._scope_status_widget)
        self._scope_status_layout.setContentsMargins(0, 0, 0, 4)
        self._scope_status_layout.setSpacing(4)

        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(f"""
            QLabel {{
                border-radius: 4px;
                background-color: {COLORS.ERROR};
                border: none;
            }}
        """)
        self._scope_status_layout.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self._status_label = QLabel("0 个目录 · 未扫描")
        self._status_label.setStyleSheet(label_micro_style())
        self._scope_status_layout.addWidget(self._status_label, 1, Qt.AlignmentFlag.AlignVCenter)

        manage_content_layout.addWidget(self._scope_status_widget)

        self._scope_info_scroll = QScrollArea()
        self._scope_info_scroll.setWidgetResizable(True)
        self._scope_info_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scope_info_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scope_info_scroll.setMinimumHeight(40)
        self._scope_info_scroll.setMaximumHeight(120)
        self._scope_info_scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {COLORS.BG_SECONDARY}; border-radius: {RADIUS.SMALL}px; }}" + scrollbar_style())
        self._scope_info_container = QWidget()
        self._scope_info_layout = QVBoxLayout(self._scope_info_container)
        self._scope_info_layout.setContentsMargins(8, 4, 8, 4)
        self._scope_info_layout.setSpacing(2)
        self._scope_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scope_info_container.setStyleSheet("QWidget { background: transparent; }")
        self._scope_info_scroll.setWidget(self._scope_info_container)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        from .widgets.filter_bar import _make_colored_icon
        gray_settings = _make_colored_icon("icons/settings.svg", COLORS.TEXT_SECONDARY, 16)
        self.configure_btn = QPushButton("  管理扫描路径")
        self.configure_btn.setIcon(gray_settings)
        self.configure_btn.setIconSize(QSize(14, 14))
        self.configure_btn.setFixedHeight(28)
        self.configure_btn.setStyleSheet(config_button_style())
        self.configure_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.configure_btn.clicked.connect(self._on_configure_scope)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(progress_bar_style(6, 3))
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        self.scan_btn = QPushButton()
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.setFixedHeight(28)
        self.scan_btn.clicked.connect(self._on_scan_clicked)
        self._update_scan_btn_state()

        action_row.addStretch()
        action_row.addWidget(self.configure_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        action_row.addWidget(self.scan_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        manage_content_layout.addWidget(self._scope_info_scroll, 1)
        manage_content_layout.addLayout(action_row)
        manage_content.setLayout(manage_content_layout)
        self._manage_collapsible.set_content(manage_content)

        self._main_layout.addWidget(self._manage_collapsible)
        self._main_layout.addWidget(self.progress_bar)

        self.setLayout(self._main_layout)
        self.setStyleSheet(f"""
            SearchScopePanel {{
                background-color: transparent;
            }}
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
            self._status_dot.setStyleSheet(f"""
                QLabel {{
                    border-radius: 4px;
                    background-color: {COLORS.ERROR};
                    border: none;
                }}
            """)
            self._status_label.setText("0 个目录 · 未扫描")
            self._status_label.setStyleSheet(label_micro_style())
            return

        incomplete_count = 0
        for d in self._scanned_dirs:
            status = get_scan_status(d)
            if status is None or status in (SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED, SCAN_STATUS_SCANNING):
                incomplete_count += 1

        if self._indexed_count == 0:
            dot_color = COLORS.ERROR
            dot_tip = "未扫描"
        elif incomplete_count > 0:
            dot_color = COLORS.WARNING
            dot_tip = "部分目录未完成扫描"
        else:
            dot_color = COLORS.SUCCESS
            dot_tip = "已扫描"
        self._status_dot.setStyleSheet(f"""
            QLabel {{
                border-radius: 4px;
                background-color: {dot_color};
                border: none;
            }}
        """)
        self._status_dot.setToolTip(dot_tip)

        status_text = ""
        if incomplete_count > 0:
            status_text = f" · {incomplete_count} 个目录未完成扫描"

        header_text = f"{dir_count} 个目录" + (f" · 已索引 {self._indexed_count:,} 个文件" if self._indexed_count > 0 else " · 未扫描") + status_text
        self._status_label.setText(header_text)
        if incomplete_count > 0:
            self._status_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.WARNING}; border: none; background: transparent;")
        else:
            self._status_label.setStyleSheet(label_micro_style())

        for d in self._scanned_dirs:
            status = get_scan_status(d)
            dir_label = ElidedPathLabel(d)
            if status is None:
                dir_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.WARNING}; border: none; background: transparent; padding: 1px 2px; margin: 0px;")
                dir_label.setToolTip(f"{d} (未扫描)")
            elif status == SCAN_STATUS_INCOMPLETE:
                dir_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.WARNING}; border: none; background: transparent; padding: 1px 2px; margin: 0px;")
                dir_label.setToolTip(f"{d} (扫描未完成)")
            elif status == SCAN_STATUS_FAILED:
                dir_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.ERROR}; border: none; background: transparent; padding: 1px 2px; margin: 0px;")
                dir_label.setToolTip(f"{d} (扫描失败)")
            else:
                dir_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.TEXT_SECONDARY}; border: none; background: transparent; padding: 1px 2px; margin: 0px;")
                dir_label.setToolTip(d)
            self._scope_info_layout.addWidget(dir_label)

    def _update_scope_detail(self):
        if self._scope_mode == 'all':
            self._scope_detail.setText(f"搜索所有已扫描目录（共 {len(self._scanned_dirs)} 个）")
        else:
            count = len(self._selected_dirs)
            total = len(self._custom_dir_list)
            self._scope_detail.setText(f"已选择 {count}/{total} 个目录")

    def _rebuild_dir_buttons(self):
        while self._dir_flow_layout.count():
            item = self._dir_flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dirs_to_show = self._custom_dir_list if self._scope_mode == 'custom' else list(self._selected_dirs)
        tag_style = button_tag()
        for d in dirs_to_show:
            display_name = self._get_display_path(d)
            btn = QPushButton(display_name)
            btn.setCheckable(True)
            is_selected = d in self._selected_dirs
            btn.setChecked(is_selected)
            btn.setToolTip(d)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(tag_style)
            btn.clicked.connect(lambda checked, path=d: self._on_dir_toggled(path, checked))
            self._dir_flow_layout.addWidget(btn)

    def _on_scope_radio_clicked(self, btn):
        if btn == self._all_radio:
            self._on_all_clicked()
        elif btn == self._custom_radio:
            self._on_custom_radio_selected()

    def _on_all_clicked(self):
        self._scope_mode = 'all'
        self._all_radio.setChecked(True)
        self._custom_radio.setChecked(False)
        self._selected_dirs = set(self._scanned_dirs)
        self._custom_dir_list = []
        self._scroll.setVisible(False)
        self._custom_settings_btn.setVisible(False)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self.scope_changed.emit(list(self._selected_dirs))

    def _on_custom_radio_selected(self):
        self._scope_mode = 'custom'
        self._all_radio.setChecked(False)
        self._custom_radio.setChecked(True)
        if not self._custom_dir_list:
            self._custom_dir_list = list(self._scanned_dirs)
            self._selected_dirs = set(self._scanned_dirs)
        self._scroll.setVisible(True)
        self._custom_settings_btn.setVisible(True)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self.scope_changed.emit(list(self._selected_dirs))

    def _on_custom_settings_clicked(self):
        self._all_radio.setChecked(False)
        self._custom_radio.setChecked(True)

        dialog = _ScopeSelectionDialog(self._scanned_dirs, self._selected_dirs, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_dirs()
            unscanned = dialog.get_unscanned_dirs()

            def _is_under_scanned_dir(path: str) -> bool:
                norm_p = os.path.normcase(os.path.normpath(path))
                for sd in self._scanned_dirs:
                    norm_sd = os.path.normcase(os.path.normpath(sd))
                    if norm_p == norm_sd or norm_p.startswith(norm_sd + os.sep):
                        status = get_scan_status(sd)
                        if status == SCAN_STATUS_COMPLETE:
                            return True
                return False

            incomplete_selected = []
            for d in selected:
                if _is_under_scanned_dir(d):
                    continue
                status = get_scan_status(d)
                if status is None or status in (SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED):
                    incomplete_selected.append(d)

            if incomplete_selected:
                reply = _styled_msg_box(
                    self, QMessageBox.Icon.Warning,
                    "目录扫描未完成",
                    "以下目录扫描未完成或失败，搜索结果可能不完整：\n\n" +
                    "\n".join(f"  \u2022 {d}" for d in incomplete_selected) +
                    "\n\n建议重新扫描这些目录。是否仍要将其加入搜索范围？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    selected = [d for d in selected if d not in incomplete_selected]

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
            if not self._selected_dirs:
                _styled_msg_box(
                    self, QMessageBox.Icon.Warning,
                    "搜索范围为空",
                    "未选择任何目录作为搜索范围，搜索将不会返回结果。\n建议至少选择一个目录。"
                )
            self._custom_dir_list = list(selected)
            self._scroll.setVisible(True)
            self._custom_settings_btn.setVisible(True)
            self._rebuild_dir_buttons()
            self._update_scope_detail()
            self.scope_changed.emit(list(self._selected_dirs))
        else:
            if not self._selected_dirs:
                self._on_all_clicked()
            else:
                self._scope_mode = 'custom'
                self._all_radio.setChecked(False)
                self._custom_radio.setChecked(True)
                self._custom_settings_btn.setVisible(True)

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

    def _update_status_dot(self):
        self._update_scope_info()

    def _has_unscanned_dirs(self) -> bool:
        from config import get_scan_status, SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED, SCAN_STATUS_COMPLETE
        for d in self._scanned_dirs:
            status = get_scan_status(d)
            if status is None or status in (SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED):
                return True
        if not self._scanned_dirs and hasattr(self, '_search_dirs'):
            return bool(self._search_dirs)
        return False

    def _update_scan_btn_state(self):
        if self._indexed_count == 0:
            self.scan_btn.setText("开始扫描")
            self.scan_btn.setStyleSheet(button_scan_green())
            self.scan_btn.setFixedHeight(28)
        elif self._has_unscanned_dirs():
            self.scan_btn.setText("新增扫描")
            self.scan_btn.setStyleSheet(button_scan_green())
            self.scan_btn.setFixedHeight(28)
        else:
            self.scan_btn.setText("重新扫描")
            self.scan_btn.setStyleSheet(button_scan())
            self.scan_btn.setFixedHeight(28)

    def _on_configure_scope(self):
        from .widgets.filter_bar import SearchScopeDialog, _styled_msg_box
        dialog = SearchScopeDialog(self._scanned_dirs, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_dirs = dialog.get_dirs()
            if not new_dirs:
                _styled_msg_box(
                    self, QMessageBox.Icon.Warning,
                    "配置错误", "扫描路径不能为空"
                )
                return
            old_dirs = set(self._scanned_dirs)
            new_set = set(new_dirs)
            added = new_set - old_dirs
            removed = old_dirs - new_set

            self._scanned_dirs = new_dirs
            if self._scope_mode == 'all':
                self._selected_dirs = set(new_dirs)
            self._update_scope_info()
            self._update_status_dot()
            self._update_scan_btn_state()
            self._update_scope_info()
            self.scope_changed.emit(list(self._selected_dirs))

            from config import load_config, save_config
            config = load_config()
            config["search"]["default_dirs"] = list(new_dirs)
            save_config(config)

            if added or removed:
                msg_parts = []
                if added:
                    msg_parts.append(f"新增 {len(added)} 个目录")
                if removed:
                    msg_parts.append(f"移除 {len(removed)} 个目录")
                scan_btn_text = "新增扫描" if added else "重新扫描"
                _styled_msg_box(
                    self, QMessageBox.Icon.Information,
                    "路径已更新",
                    f"扫描路径已更新（{'，'.join(msg_parts)}）。\n请点击「{scan_btn_text}」以更新文件索引。"
                )

    def _on_scan_clicked(self):
        if self._is_scanning:
            return

        if self._indexed_count == 0:
            title = "开始扫描"
            text = "将扫描所选目录/驱动器以建立文件索引，这可能需要几分钟时间。\n确定要开始扫描吗？"
        elif self._has_unscanned_dirs():
            title = "新增扫描"
            text = "发现新增的未扫描目录，需要扫描以建立文件索引。\n确定要开始新增扫描吗？"
        else:
            title = "重新扫描"
            text = "将重新扫描所有目录/驱动器，更新文件索引。\n这可能需要几分钟时间，确定要继续吗？"

        reply = _styled_msg_box(
            self, QMessageBox.Icon.Question,
            title, text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._is_scanning = True
        self.scan_btn.setEnabled(False)
        self.scan_btn.setIcon(QIcon())
        self.scan_btn.setText("正在扫描")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.scan_requested.emit()

    def reset_scan_state(self, file_count: int = 0):
        self._is_scanning = False
        self.scan_btn.setEnabled(True)
        self.scan_btn.setIcon(QIcon())
        self._indexed_count = file_count
        self.progress_bar.setVisible(False)
        self._update_scan_btn_state()
        self._update_scope_info()
        self._update_status_dot()

        from config import save_scanned_dirs
        save_scanned_dirs(self._scanned_dirs)

    def set_search_dirs(self, dirs: list):
        self._search_dirs = dirs
        self._update_scope_info()
        self._update_status_dot()
        self._update_scan_btn_state()

    def get_search_dirs(self) -> list:
        return list(getattr(self, '_search_dirs', self._scanned_dirs))

    def get_indexed_count(self) -> int:
        return self._indexed_count

    def is_scanning(self) -> bool:
        return self._is_scanning

    def show_search_progress(self):
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setVisible(True)

    def hide_search_progress(self):
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)

    def reset(self):
        self._scope_mode = 'all'
        self._selected_dirs = set()
        self._custom_dir_list = []
        self._scanned_dirs = []
        self._indexed_count = 0
        self._all_radio.setChecked(True)
        self._custom_radio.setChecked(False)
        self._scroll.setVisible(False)
        self._custom_settings_btn.setVisible(False)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self._update_scope_info()
        self._update_status_dot()
        self._update_scan_btn_state()


class _ScopeSelectionDialog(ModernDialogBase):
    _PLACEHOLDER_KEY = "__placeholder__"

    def __init__(self, scanned_dirs: list, current_selected: set, parent=None):
        super().__init__(parent, title="自定义搜索范围", min_width=560, min_height=540, resizable=True)
        self._scanned_dirs = list(scanned_dirs)
        self._selected_dirs = set(current_selected)
        self._unscanned_dirs = []
        self._updating_tree = False
        self._loaded_items = set()
        self._init_ui()

    def _init_ui(self):
        def build_content(content_widget):
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(12)
            layout.setContentsMargins(DIALOG.PADDING, 4, DIALOG.PADDING, 20)

            desc = QLabel("FileFinder将在指定的搜索范围中进行搜索")
            desc.setStyleSheet(label_caption_style())
            desc.setWordWrap(True)

            select_row = QHBoxLayout()
            select_row.setSpacing(6)

            select_all_btn = QPushButton("全选")
            select_all_btn.setStyleSheet(button_small_secondary())
            select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            select_all_btn.clicked.connect(self._on_select_all)

            deselect_all_btn = QPushButton("全不选")
            deselect_all_btn.setStyleSheet(button_small_secondary())
            deselect_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            deselect_all_btn.clicked.connect(self._on_deselect_all)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setStyleSheet(f"color: {COLORS.BORDER_DEFAULT}; border: none; background: transparent;")

            expand_all_btn = QPushButton("全部展开")
            expand_all_btn.setStyleSheet(button_small_secondary())
            expand_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            expand_all_btn.clicked.connect(self._on_expand_all)

            collapse_all_btn = QPushButton("全部折叠")
            collapse_all_btn.setStyleSheet(button_small_secondary())
            collapse_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            collapse_all_btn.clicked.connect(self._on_collapse_all)

            self._count_label = QLabel("")
            self._count_label.setStyleSheet(label_micro_style())

            select_row.addWidget(select_all_btn)
            select_row.addWidget(deselect_all_btn)
            select_row.addWidget(sep)
            select_row.addWidget(expand_all_btn)
            select_row.addWidget(collapse_all_btn)
            select_row.addStretch()
            select_row.addWidget(self._count_label)

            self._tree = QTreeWidget()
            self._tree.setHeaderLabel("选择目录")
            self._tree.setAnimated(True)
            self._tree.setIndentation(16)
            self._tree.setExpandsOnDoubleClick(True)

            icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons')
            checkmark_path = os.path.join(icons_dir, 'checkmark.svg').replace('\\', '/')
            partial_path = os.path.join(icons_dir, 'partial-check.svg').replace('\\', '/')
            branch_closed_path = os.path.join(icons_dir, 'branch-closed.svg').replace('\\', '/')
            branch_open_path = os.path.join(icons_dir, 'branch-open.svg').replace('\\', '/')

            tree_style = tree_widget_style(checkmark_path, partial_path, branch_closed_path, branch_open_path)
            self._tree.setStyleSheet(tree_style)
            self._tree.header().setStretchLastSection(True)
            self._tree.itemChanged.connect(self._on_tree_item_changed)
            self._tree.itemExpanded.connect(self._on_item_expanded)
            self._populate_tree()

            browse_row = QHBoxLayout()
            browse_row.setSpacing(8)

            self._path_input = QLineEdit()
            self._path_input.setPlaceholderText("输入目标路径，如 D:\\Projects 或 C:\\Users")
            self._path_input.setFixedHeight(36)
            self._path_input.setStyleSheet(input_style())

            browse_btn = QPushButton("浏览...")
            browse_btn.setFixedHeight(36)
            browse_btn.setStyleSheet(button_small_secondary())
            browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            browse_btn.clicked.connect(self._on_browse)

            add_btn = QPushButton("+ 添加")
            add_btn.setFixedHeight(36)
            add_btn.setStyleSheet(button_small_primary())
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.clicked.connect(self._on_add)

            browse_row.addWidget(self._path_input, 1)
            browse_row.addWidget(browse_btn)
            browse_row.addWidget(add_btn)

            btn_row = QHBoxLayout()
            btn_row.addStretch()

            cancel_btn = QPushButton("取消")
            cancel_btn.setStyleSheet(button_secondary())
            cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cancel_btn.clicked.connect(self.reject)

            confirm_btn = QPushButton("确定")
            confirm_btn.setStyleSheet(button_primary())
            confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            confirm_btn.clicked.connect(self._on_confirm)

            btn_row.addWidget(cancel_btn)
            btn_row.addSpacing(8)
            btn_row.addWidget(confirm_btn)

            layout.addWidget(desc)
            layout.addLayout(select_row)
            layout.addWidget(self._tree, 1)
            layout.addLayout(browse_row)
            layout.addLayout(btn_row)

        self._create_shadow_frame(build_content)
        self._update_count_label()

    def _populate_tree(self):
        self._updating_tree = True
        self._tree.clear()
        self._loaded_items.clear()
        for d in self._scanned_dirs:
            name = os.path.basename(d.rstrip(os.sep)) or d
            scan_status = get_scan_status(d)
            if scan_status == SCAN_STATUS_INCOMPLETE:
                name = f"{name} (扫描未完成)"
            elif scan_status == SCAN_STATUS_FAILED:
                name = f"{name} (扫描失败)"
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
            if scan_status == SCAN_STATUS_INCOMPLETE:
                item.setForeground(0, QColor(245, 158, 11))
                item.setToolTip(0, f"{d}\n扫描未完成，搜索结果可能不完整")
            elif scan_status == SCAN_STATUS_FAILED:
                item.setForeground(0, QColor(239, 68, 68))
                item.setToolTip(0, f"{d}\n扫描失败，请重新扫描此目录")
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
    _fs_paths_ready = Signal(list)

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
        self._fs_paths_ready.connect(self._apply_fs_watcher_paths)
        self._init_ui()
        self._connect_signals()
        self._check_index_on_startup()

    def _init_ui(self):
        self.setWindowTitle("FileFinder - 本地文件搜索工具")
        self.setMinimumSize(900, 600)
        self.resize(1100, 720)

        icon = QIcon("icons/search-alt.svg")
        self.setWindowIcon(icon)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS.BG_PRIMARY};
            }}
            QWidget {{
                font-family: {FONT.FAMILY};
            }}
        """ + scrollbar_style())

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

        content_split = QSplitter(Qt.Orientation.Horizontal)
        content_split.setContentsMargins(0, 8, 8, 8)
        content_split.setChildrenCollapsible(False)

        left_panel = QWidget()
        left_panel.setMinimumWidth(540)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(8, 0, 8, 0)
        left_layout.setSpacing(4)

        settings_wrapper = QWidget()
        settings_wrapper_layout = QVBoxLayout(settings_wrapper)
        settings_wrapper_layout.setContentsMargins(16, 0, 16, 0)
        settings_wrapper_layout.setSpacing(0)
        settings_wrapper_layout.addWidget(self.search_bar.get_settings_widget())
        left_layout.addWidget(settings_wrapper)

        self.filter_bar = FilterBar()
        left_layout.addWidget(self.filter_bar)

        self.result_list = ResultListWidget()

        self._loading_overlay = QFrame(self.result_list)
        self._loading_overlay.setStyleSheet(f"QFrame {{ background-color: {COLORS.BG_PRIMARY}; }}")
        overlay_layout = QVBoxLayout(self._loading_overlay)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.setSpacing(12)

        self._loading_spinner = LoadingSpinner(self._loading_overlay)
        loading_label = QLabel("正在初始化...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet(f"color: {COLORS.TEXT_TERTIARY}; font-size: {DIALOG.BODY_FONT_SIZE}; border: none; background: transparent;")

        overlay_layout.addStretch()
        overlay_layout.addWidget(self._loading_spinner, 0, Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(loading_label, 0, Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addStretch()

        left_layout.addWidget(self.result_list, 1)
        left_panel.setLayout(left_layout)

        right_panel = _RoundedPanel()
        right_panel.setMinimumWidth(360)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(1, 1, 1, 1)
        right_layout.setSpacing(0)

        self._search_scope_panel = SearchScopePanel()
        right_layout.addWidget(self._search_scope_panel)

        self.preview_panel = PreviewPanel()
        self.preview_panel.setMinimumWidth(200)
        right_layout.addWidget(self.preview_panel, 1)

        right_panel.setLayout(right_layout)

        content_split.addWidget(left_panel)
        content_split.addWidget(right_panel)
        content_split.setStretchFactor(0, 3)
        content_split.setStretchFactor(1, 2)
        content_split.setSizes([660, 440])
        content_split.setHandleWidth(4)
        content_split.setStyleSheet(f"""
            QSplitter::handle {{
                background: transparent;
            }}
            QSplitter::handle:hover {{
                background: transparent;
            }}
        """)

        layout.addWidget(content_split, 1)

        page.setLayout(layout)
        return page

    def _init_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(status_bar_style())
        self.setStatusBar(self.status_bar)

        self.status_left = QLabel("就绪")
        self.status_left.setStyleSheet(f"color: {COLORS.TEXT_TERTIARY}; font-size: {BTN.SMALL_FONT_SIZE};")

        self.status_separator1 = QLabel("|")
        self.status_separator1.setStyleSheet(status_divider_style())

        self.status_size = QLabel("")
        self.status_separator2 = QLabel("|")
        self.status_separator2.setStyleSheet(status_divider_style())
        self.status_date = QLabel("")
        self.status_separator3 = QLabel("|")
        self.status_separator3.setStyleSheet(status_divider_style())
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
        menubar.setStyleSheet(menubar_style())

        file_menu = RoundedMenu(self)
        file_menu.setTitle("文件")
        file_menu.setStyleSheet(menu_style())
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        menubar.addMenu(file_menu)

        settings_menu = RoundedMenu(self)
        settings_menu.setTitle("设置")
        settings_menu.setStyleSheet(menu_style())
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
        help_menu.setStyleSheet(menu_style())
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

        self._all_results = []
        self._current_file_types = []
        self._exclude_known_types = False
        self._selected_dirs = set()
        self._is_first_launch = True

        self.result_list.clear_results()
        self.preview_panel.clear_preview()
        self.filter_bar._reload_scope()
        self._search_scope_panel.reset()
        self._search_scope_panel._reload_scope()
        self._welcome_page.reset()

        self.search_bar.search_input.clear()
        self.search_bar._set_mode('name')
        self.search_bar.case_sensitive_checkbox.setChecked(False)

        for key, btn in self.filter_bar.type_buttons.items():
            btn.setChecked(key == 'all')
        self.filter_bar._selected_category = 'all'
        self.filter_bar._selected_sub_extensions = set()
        self.filter_bar._sub_filter_widget.setVisible(False)

        self._switch_to_welcome()

        _styled_msg_box(
            self, QMessageBox.Icon.Information,
            "操作成功", "所有设置已恢复为默认值。\n应用将重置为首次启动状态。"
        )

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
        )

    def _connect_signals(self):
        self._welcome_page.scan_requested_with_dirs.connect(self._start_scan_with_dirs)
        self._scan_progress_page.scan_cancelled.connect(self._on_scan_cancelled)
        self._search_scope_panel.scope_changed.connect(self._on_scope_changed)
        self._search_scope_panel.scan_unscanned_requested.connect(self._on_scan_unscanned)
        self.search_bar.search_triggered.connect(self._on_search)
        self.result_list.result_selected.connect(self._on_result_selected)
        self.result_list.status_info_requested.connect(self._update_status_info)
        self.filter_bar.filter_changed.connect(self._on_filter_changed)
        self.filter_bar.sort_changed.connect(self._on_sort_changed)
        self.filter_bar.sort_order_changed.connect(self._on_sort_order_changed)
        self._search_scope_panel.scan_requested.connect(self._on_scan_requested)

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
        self._search_scope_panel.update_scope_info(self._search_scope_panel.get_indexed_count())
        if not self._all_results and self._search_scope_panel.get_indexed_count() > 0:
            self._load_all_files()

    def _switch_to_scan_progress(self):
        self._scan_progress_page.reset_state()
        self._scan_progress_page.start_scan()
        self._stacked.setCurrentWidget(self._scan_progress_page)

    def _deferred_index_check(self):
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        count = db.get_index_count()
        self._search_scope_panel._indexed_count = count
        if count > 0 and not self._search_scope_panel._scanned_dirs:
            self._search_scope_panel._scanned_dirs = list(self._search_scope_panel.get_search_dirs())
        self._search_scope_panel._update_scope_info()
        self._search_scope_panel._update_status_dot()
        self._search_scope_panel._update_scan_btn_state()
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

        self._search_scope_panel.set_search_dirs(get_default_search_dirs())

        self._switch_to_scan_progress()
        self._do_scan(dirs)

    def _on_scan_requested(self):
        self._switch_to_scan_progress()
        self.status_left.setText("正在扫描...")
        self.status_right.setText("")

        self._do_scan(self._search_scope_panel.get_search_dirs())

    def _do_scan(self, search_dirs: list, exclude_dirs: list = None):
        if exclude_dirs is None:
            exclude_dirs = get_exclude_dirs()

        self._scan_worker = ScanWorker(search_dirs, exclude_dirs)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

    def _on_scan_progress(self, count: int, percentage: int, current_dir: str):
        self._scan_progress_page.update_progress(count, percentage if percentage >= 0 else None, current_dir)
        self.status_left.setText(f"正在扫描... 已发现 {count:,} 个文件")

    def _on_scan_finished(self, total_files: int, elapsed: float):
        self._scan_progress_page.set_finishing()

        self._search_scope_panel.reset_scan_state(total_files)

        all_dirs = self._search_scope_panel.get_search_dirs()
        save_scanned_dirs(all_dirs)
        self._search_scope_panel.set_scanned_dirs(all_dirs)
        self._search_scope_panel.update_scope_info(total_files)

        config = load_config()
        existing_dirs = set(config.get("search", {}).get("default_dirs", []))
        for d in all_dirs:
            existing_dirs.add(d)
        config.setdefault("search", {})["default_dirs"] = list(existing_dirs)
        save_config(config)
        self._search_scope_panel.set_search_dirs(list(existing_dirs))

        self.status_left.setText(f"扫描完成 - 共 {total_files:,} 个文件，耗时 {elapsed:.1f} 秒")
        self.status_right.setText("")

        self._update_fs_watcher_async()

        self._is_first_launch = False

        self._hide_loading()
        QTimer.singleShot(800, self._switch_to_main)
        QTimer.singleShot(1200, self._load_all_files)

    def _on_scan_error(self, err_msg: str):
        self._scan_progress_page.set_error(err_msg)
        self._search_scope_panel.reset_scan_state()
        self.status_left.setText("扫描失败")
        logger.error(f"扫描失败: {err_msg}")

    def _on_scan_cancelled(self):
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
            self._scan_worker.wait(1000)
            if self._scan_worker.isRunning():
                logger.warning("扫描线程未在1秒内响应取消，强制终止")
                self._scan_worker.terminate()
                self._scan_worker.wait(2000)

        from database.db_manager import DatabaseManager
        DatabaseManager()._search_cache.invalidate()
        self._search_scope_panel.reset_scan_state()
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

    def _load_all_files(self):
        if self._search_worker and self._search_worker.isRunning():
            return
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        all_dirs = self._search_scope_panel.get_all_scanned_dirs()
        if not all_dirs:
            all_dirs = self._search_scope_panel.get_search_dirs()
        self._selected_dirs = set(self._search_scope_panel.get_selected_dirs())

        db_results = db.search_files(
            pattern="",
            case_sensitive=False,
            max_results=get_max_results()
        )

        from models.file_item import FileItem
        from models.search_result import SearchResult
        from datetime import datetime
        results = []
        for row in db_results:
            try:
                item = FileItem(
                    path=row["path"],
                    name=row["name"],
                    size=row["size"],
                    modified_time=datetime.fromtimestamp(row["modified_time"]),
                    extension=row["extension"] or "",
                    is_directory=bool(row.get("is_directory", 0)),
                    item_count=row.get("item_count", 0)
                )
                if all_dirs and not any(
                    os.path.normcase(os.path.normpath(item.path)).startswith(
                        os.path.normcase(os.path.normpath(d)) + os.sep
                    ) or os.path.normcase(os.path.normpath(item.path)) == os.path.normcase(os.path.normpath(d))
                    for d in all_dirs
                ):
                    continue
                results.append(SearchResult(file_item=item, match_reason='name', name_match_score=0))
            except Exception:
                continue

        self._all_results = results
        self._apply_current_filter()

    def _on_search(self, name_query, content_query):
        if not name_query.strip() and not content_query.strip():
            return

        if self._search_scope_panel.get_indexed_count() == 0:
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

        if not all_dirs and not self._search_scope_panel.get_search_dirs():
            _styled_msg_box(
                self, QMessageBox.Icon.Warning,
                "无可搜索目录",
                "当前没有可搜索的目录。请先添加扫描路径并完成扫描。"
            )
            return

        query = SearchQuery(
            name_query=name_query if name_query else None,
            name_mode=self.search_bar.get_name_mode(),
            content_query=content_query if content_query else None,
            content_mode='keyword',
            include_dirs=all_dirs if all_dirs else self._search_scope_panel.get_search_dirs(),
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
        self._search_worker.results_ready.connect(self._on_search_finished)
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

        filtered = self._sort_results(filtered)

        self.result_list.set_results(filtered)

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
        self.preview_panel.set_result(result)

    def _update_status_info(self, result):
        file_item = result.file_item

        self.status_size.setText(f"大小：{file_item.size_display}")
        self.status_date.setText(f"修改时间：{file_item.modified_date}")
        self.status_path.setText(f"路径：{file_item.path}")

        for w in [self.status_separator1, self.status_size,
                  self.status_separator2, self.status_date,
                  self.status_separator3, self.status_path]:
            w.setVisible(True)

    def _on_filter_changed(self, category, sub_extensions=None):
        from models.file_item import FILE_TYPE_MAP
        self._current_file_types = []
        self._exclude_known_types = False
        if category == 'other':
            self._exclude_known_types = True
        elif category == 'folder':
            pass
        elif category != 'all':
            if sub_extensions:
                self._current_file_types = list(sub_extensions)
            else:
                for ext, ftype in FILE_TYPE_MAP.items():
                    if ftype == category:
                        self._current_file_types.append(ext)

        if self._all_results and len(self._all_results) > 200:
            self.result_list.show_search_progress("正在筛选...")
            if hasattr(self, '_filter_timer'):
                self._filter_timer.stop()
            else:
                self._filter_timer = QTimer(self)
                self._filter_timer.setSingleShot(True)
                self._filter_timer.timeout.connect(self._apply_current_filter)
            self._filter_timer.start(50)
        elif self._all_results:
            self._apply_current_filter()

    def _on_scope_changed(self, dirs):
        self._selected_dirs = set(dirs)
        if self._all_results:
            self._apply_current_filter()

    def _on_sort_changed(self, mode):
        if self._all_results:
            self._apply_current_filter()

    def _on_sort_order_changed(self, ascending):
        if self._all_results:
            self._apply_current_filter()

    def _sort_results(self, results):
        sort_mode = self.filter_bar.get_sort_mode()
        ascending = self.filter_bar.is_sort_ascending()

        def _sort_key(result):
            item = result.file_item
            if sort_mode == 'name':
                return item.name.lower()
            elif sort_mode == 'modified':
                return item.modified_time.timestamp() if item.modified_time else 0
            elif sort_mode == 'size':
                return item.size
            else:
                return result.score

        return sorted(results, key=_sort_key, reverse=not ascending)

    def _is_path_in_selected_dirs(self, file_path: str) -> bool:
        if not self._selected_dirs:
            return True
        normalized = os.path.normcase(os.path.normpath(file_path))
        for d in self._selected_dirs:
            norm_d = os.path.normcase(os.path.normpath(d))
            if normalized.startswith(norm_d + os.sep) or normalized == norm_d:
                return True
        return False

    def _update_fs_watcher_async(self):
        from concurrent.futures import ThreadPoolExecutor
        search_dirs = self._search_scope_panel.get_search_dirs()

        def _collect_watch_paths():
            paths = []
            for d in search_dirs:
                if os.path.isdir(d):
                    paths.append(d)
                    try:
                        for root, dirs, _ in os.walk(d):
                            for sub in dirs:
                                full = os.path.join(root, sub)
                                paths.append(full)
                    except Exception:
                        continue
            return paths

        def _on_paths_collected(future):
            try:
                paths = future.result()
                self._fs_paths_ready.emit(paths)
            except Exception as e:
                logger.warning(f"设置文件监控失败: {e}")

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(_collect_watch_paths)
        future.add_done_callback(_on_paths_collected)

    def _apply_fs_watcher_paths(self, paths: list):
        try:
            self._fs_watcher.removePaths(self._fs_watcher.directories())
            for p in paths:
                try:
                    self._fs_watcher.addPath(p)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"应用文件监控路径失败: {e}")

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
            try:
                deleted = db.delete_entries_by_prefix(dir_path)
                if deleted > 0:
                    logger.debug(f"目录已删除，清理 {deleted} 条索引: {dir_path}")
            except Exception as e:
                logger.warning(f"清理已删除目录索引失败: {dir_path}, {e}")
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

            indexed_paths = db.get_paths_by_parent(dir_path)
            for ep in indexed_paths:
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
            self._scan_worker.wait(1000)
            if self._scan_worker.isRunning():
                self._scan_worker.terminate()
                self._scan_worker.wait(1000)

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.terminate()
            self._search_worker.wait(1000)

        from database.db_manager import DatabaseManager
        DatabaseManager().close()

        super().closeEvent(event)
