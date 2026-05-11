import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QDialog, QListWidget, QListWidgetItem,
                             QMessageBox, QProgressBar, QSizePolicy, QLineEdit,
                             QFileDialog, QFrame, QApplication, QRadioButton,
                             QButtonGroup, QComboBox)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, QSize, QPointF, QRectF, Property
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QFont, QFontMetrics, QPolygonF
from constants import FILE_TYPE_CATEGORIES
from utils.path_helper import get_all_drives, get_user_directories, normalize_path
from database.db_manager import DatabaseManager
from ..style_constants import COLORS, FONT, RADIUS, BTN, DIALOG, TRANSITION
from ..modern_dialog import ModernDialogBase
from ..style_manager import (
    msg_box_style, button_primary, button_secondary, button_filter,
    button_scan, button_scan_green, button_small_primary, button_small_secondary,
    button_cancel_danger, remove_button_style, radio_button_style,
    input_style, dialog_frame_style, dialog_title_style, dialog_body_style,
    dialog_style, list_style, progress_bar_style, label_caption_style,
    label_micro_style, label_header_style,
)


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


class _ModernMessageBox(ModernDialogBase):
    def __init__(self, parent=None, icon_type='info', title='', text='', buttons=None):
        super().__init__(parent, title=title, min_width=DIALOG.MIN_WIDTH, resizable=False)
        self._result = None
        self._buttons = buttons or {}
        self._icon_type = icon_type
        self._text = text
        self._init_ui()

    def _init_ui(self):
        def build_content(content_widget):
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(DIALOG.CONTENT_SPACING)
            layout.setContentsMargins(DIALOG.PADDING, 4, DIALOG.PADDING, DIALOG.PADDING)
            icon_label = QLabel()
            icon_label.setFixedSize(48, 48)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setPixmap(self._create_icon_pixmap())
            text_label = QLabel(self._text)
            text_label.setStyleSheet(dialog_body_style())
            text_label.setWordWrap(True)
            content_row = QHBoxLayout()
            content_row.setSpacing(DIALOG.CONTENT_SPACING)
            content_row.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
            col = QVBoxLayout()
            col.setSpacing(6)
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

        self._create_shadow_frame(build_content)

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
        self._hover_opacity = 0.0
        self._hover_anim = QPropertyAnimation(self, b"hover_opacity")
        self._hover_anim.setDuration(150)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._press_anim = QPropertyAnimation(self, b"minimumSize")
        self._press_anim.setDuration(80)
        self._press_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._release_anim = QPropertyAnimation(self, b"minimumSize")
        self._release_anim.setDuration(180)
        self._release_anim.setEasingCurve(QEasingCurve.Type.OutBack)

    def get_hover_opacity(self):
        return self._hover_opacity

    def set_hover_opacity(self, opacity):
        self._hover_opacity = opacity
        self.update()

    hover_opacity = Property(float, get_hover_opacity, set_hover_opacity)

    def enterEvent(self, event):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_opacity)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_opacity)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(event)

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


class SearchScopeDialog(ModernDialogBase):
    def __init__(self, current_dirs, parent=None):
        super().__init__(parent, title="管理扫描路径", min_width=520, min_height=420, resizable=True)
        self._dirs = list(current_dirs)
        self._init_ui()

    def _init_ui(self):
        def build_content(content_widget):
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(12)
            layout.setContentsMargins(20, 4, 20, 20)

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
            confirm_btn.clicked.connect(self._on_confirm)

            btn_row.addWidget(cancel_btn)
            btn_row.addSpacing(8)
            btn_row.addWidget(confirm_btn)

            layout.addLayout(btn_row)

        self._create_shadow_frame(build_content)

    def _on_confirm(self):
        if not self._dirs:
            _styled_msg_box(
                self, QMessageBox.Icon.Warning,
                "路径不能为空", "至少需要保留一个扫描路径，否则无法进行搜索。"
            )
            return
        self.accept()

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
    sort_order_changed = Signal(bool)

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
        self._sort_ascending = True
        self._init_ui()
        self._reload_scope()

    def _reload_scope(self):
        from config import get_default_search_dirs, get_scanned_dirs
        self._search_dirs = get_default_search_dirs()
        self._scanned_dirs = get_scanned_dirs()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 4, 16, 4)
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

        sort_card = QFrame()
        sort_card.setObjectName("sortCard")
        sort_card.setStyleSheet(f"""
            QFrame#sortCard {{
                background-color: {COLORS.BG_PRIMARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {BTN.BORDER_RADIUS}px;
                padding: 6px 10px;
            }}
        """)
        sort_card_layout = QHBoxLayout(sort_card)
        sort_card_layout.setContentsMargins(6, 4, 6, 4)
        sort_card_layout.setSpacing(8)

        sort_label = QLabel("排序方式:")
        sort_label.setStyleSheet(label_caption_style())
        sort_card_layout.addWidget(sort_label)

        self._sort_group = QButtonGroup(self)
        self._sort_radios = {}
        for mode, label in self.SORT_OPTIONS:
            radio = AnimatedRadioButton(label, font_pt=FONT.MICRO_PT)
            radio.setCursor(Qt.CursorShape.PointingHandCursor)
            if mode == self._sort_mode:
                radio.setChecked(True)
            radio.clicked.connect(lambda checked, m=mode: self._on_sort_clicked(m))
            self._sort_group.addButton(radio)
            self._sort_radios[mode] = radio
            sort_card_layout.addWidget(radio)

        sort_card_layout.addStretch()

        sort_order_sep = QFrame()
        sort_order_sep.setFrameShape(QFrame.Shape.VLine)
        sort_order_sep.setFixedHeight(16)
        sort_order_sep.setStyleSheet(f"color: {COLORS.BORDER_DEFAULT}; border: none; background: transparent;")
        sort_card_layout.addWidget(sort_order_sep)

        self._sort_order_btn = QPushButton("升序")
        self._sort_order_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sort_order_btn.setFixedHeight(22)
        self._sort_order_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-radius: {RADIUS.SMALL}px;
                background-color: transparent;
                color: {COLORS.TEXT_SECONDARY};
                font-size: {BTN.SMALL_FONT_SIZE};
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_HOVER};
                color: {COLORS.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.BG_TERTIARY};
            }}
        """)
        self._sort_order_btn.clicked.connect(self._toggle_sort_order)
        sort_card_layout.addWidget(self._sort_order_btn)

        main_layout.addWidget(flow_widget)
        main_layout.addWidget(sort_card)
        self.setLayout(main_layout)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_SECONDARY};
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

    def _toggle_sort_order(self):
        self._sort_ascending = not self._sort_ascending
        self._sort_order_btn.setText("升序" if self._sort_ascending else "降序")
        self.sort_order_changed.emit(self._sort_ascending)

    def is_sort_ascending(self):
        return self._sort_ascending

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
