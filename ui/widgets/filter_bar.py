import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QDialog, QListWidget, QListWidgetItem,
                             QMessageBox, QProgressBar, QSizePolicy, QLineEdit,
                             QFileDialog, QFrame, QApplication, QRadioButton,
                             QButtonGroup, QComboBox)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, QSize, QPointF, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QFont, QPolygonF
from constants import FILE_TYPE_CATEGORIES
from utils.path_helper import get_all_drives, get_user_directories, normalize_path
from database.db_manager import DatabaseManager
from ..style_constants import COLORS, FONT, RADIUS, BTN, DIALOG
from ..style_manager import (
    msg_box_style, button_primary, button_secondary, button_filter,
    button_scan, button_scan_green, button_small_primary, button_small_secondary,
    button_cancel_danger, remove_button_style, radio_button_style,
    input_style, dialog_frame_style, dialog_title_style, dialog_body_style,
    dialog_style, list_style, progress_bar_style, label_caption_style,
    label_micro_style, label_header_style,
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
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS.BG_PRIMARY}; }}")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 20)

        title = QLabel("开始扫描")
        title_font = QFont()
        title_font.setPointSize(FONT.DISPLAY_PT)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(dialog_title_style())

        desc = QLabel("将扫描所选目录/驱动器，这可能需要几分钟时间。\n确定要开始扫描吗？")
        desc.setStyleSheet(dialog_body_style())
        desc.setWordWrap(True)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(button_secondary())
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("开始扫描")
        confirm_btn.setStyleSheet(button_primary())
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
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS.BG_PRIMARY}; }}")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("管理扫描路径")
        header.setStyleSheet(f"font-size: {FONT.DISPLAY_PT}px; font-weight: bold; color: {COLORS.TEXT_PRIMARY}; border: none; background: transparent;")
        layout.addWidget(header)

        desc = QLabel("管理要扫描的目录路径。添加/移除目录后需要重新扫描。")
        desc.setStyleSheet(label_caption_style())
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.dir_list = DirListWidget(self)
        self.dir_list.setStyleSheet(list_style())
        for d in self._dirs:
            item = QListWidgetItem(d)
            self.dir_list.addItem(item)
        layout.addWidget(self.dir_list, 1)

        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("输入目录路径，如 D:\\Projects 或 C:\\Users")
        self.path_input.setFixedHeight(36)
        self.path_input.setStyleSheet(input_style())

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

        add_row.addWidget(self.path_input, 1)
        add_row.addWidget(browse_btn)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        quick_add_row = QHBoxLayout()
        quick_add_row.setSpacing(6)
        quick_label = QLabel("快速添加：")
        quick_label.setStyleSheet(label_caption_style())

        all_drives_btn = QPushButton("所有驱动器")
        all_drives_btn.setStyleSheet(button_small_secondary())
        all_drives_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_drives_btn.clicked.connect(self._on_add_all_drives)

        user_dirs_btn = QPushButton("常用目录")
        user_dirs_btn.setStyleSheet(button_small_secondary())
        user_dirs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        user_dirs_btn.clicked.connect(self._on_add_user_dirs)

        self._quick_drive_btns = []
        for drive in get_all_drives():
            drive_letter = drive[:2]
            btn = QPushButton(drive_letter)
            btn.setStyleSheet(button_small_secondary())
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, d=drive: self._on_add_drive(d))
            self._quick_drive_btns.append(btn)

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        desktop_btn = QPushButton("桌面")
        desktop_btn.setStyleSheet(button_small_secondary())
        desktop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        desktop_btn.clicked.connect(lambda: self._on_add_drive(desktop_path))

        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        downloads_btn = QPushButton("下载")
        downloads_btn.setStyleSheet(button_small_secondary())
        downloads_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        downloads_btn.clicked.connect(lambda: self._on_add_drive(downloads_path))

        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        documents_btn = QPushButton("文档")
        documents_btn.setStyleSheet(button_small_secondary())
        documents_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        documents_btn.clicked.connect(lambda: self._on_add_drive(documents_path))

        quick_add_row.addWidget(quick_label)
        quick_add_row.addWidget(all_drives_btn)
        quick_add_row.addWidget(user_dirs_btn)
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
        cancel_btn.setStyleSheet(button_secondary())
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("确定")
        confirm_btn.setStyleSheet(button_primary())
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
        self._remove_btn.setStyleSheet(remove_button_style())
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
    sort_changed = Signal(str)

    SORT_OPTIONS = [
        ('name', '名称'),
        ('relevance', '相关度'),
        ('modified', '修改时间'),
        ('size', '大小'),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_category = 'all'
        self._search_dirs = []
        self._scanned_dirs = []
        self._indexed_count = 0
        self._is_scanning = False
        self._sort_mode = 'name'
        self._init_ui()
        self._reload_scope()

    def _reload_scope(self):
        from config import get_default_search_dirs, get_scanned_dirs
        self._search_dirs = get_default_search_dirs()
        self._scanned_dirs = get_scanned_dirs()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 4, 20, 4)
        main_layout.setSpacing(4)

        from utils.flow_layout import FlowLayout
        flow = FlowLayout(spacing=6)

        self.type_buttons = {}
        for key, label in FILE_TYPE_CATEGORIES.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(button_filter())
            if key == 'all':
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, k=key: self._on_type_clicked(k))
            self.type_buttons[key] = btn
            flow.addWidget(btn)

        flow_widget = QWidget()
        flow_widget.setLayout(flow)
        flow_widget.setStyleSheet("QWidget { background: transparent; }")

        sort_row = QHBoxLayout()
        sort_row.setSpacing(8)

        sort_label = QLabel("排序方式:")
        sort_label.setStyleSheet(label_caption_style())
        sort_row.addWidget(sort_label)

        self._sort_group = QButtonGroup(self)
        self._sort_radios = {}
        for mode, label in self.SORT_OPTIONS:
            radio = QRadioButton(label)
            radio.setCursor(Qt.CursorShape.PointingHandCursor)
            radio.setStyleSheet(radio_button_style())
            if mode == self._sort_mode:
                radio.setChecked(True)
            radio.clicked.connect(lambda checked, m=mode: self._on_sort_clicked(m))
            self._sort_group.addButton(radio)
            self._sort_radios[mode] = radio
            sort_row.addWidget(radio)

        sort_row.addStretch()

        main_layout.addWidget(flow_widget)
        main_layout.addLayout(sort_row)
        self.setLayout(main_layout)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_SECONDARY};
                border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
            }}
        """)

    def _on_type_clicked(self, category):
        self._selected_category = category
        for key, btn in self.type_buttons.items():
            btn.setChecked(key == category)
        self.filter_changed.emit(category)

    def _on_sort_clicked(self, mode):
        self._sort_mode = mode
        self.sort_changed.emit(mode)

    def get_selected_category(self):
        return self._selected_category

    def get_sort_mode(self):
        return self._sort_mode

    def get_search_dirs(self):
        return list(self._search_dirs)

    def get_indexed_count(self):
        return self._indexed_count

    def is_scanning(self):
        return self._is_scanning
