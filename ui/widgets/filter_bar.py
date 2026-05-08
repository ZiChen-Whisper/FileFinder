import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QDialog, QListWidget, QLineEdit,
                             QFileDialog, QMessageBox, QProgressBar, QSizePolicy)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from constants import FILE_TYPE_CATEGORIES
from utils.path_helper import get_all_drives, get_user_directories, normalize_path
from database.db_manager import DatabaseManager

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
        padding: 6px 14px;
        border-radius: 8px;
        border: none;
        background-color: #7C3AED;
        color: #FFFFFF;
        font-size: 12px;
        font-weight: bold;
        min-height: 28px;
    }
    QPushButton:hover {
        background-color: #6D28D9;
    }
    QPushButton:disabled {
        background-color: #C4B5FD;
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
    source_size = size * 6
    pixmap = QIcon(icon_path).pixmap(QSize(source_size, source_size))
    if pixmap.isNull():
        return QIcon(icon_path)
    colored = QPixmap(pixmap.size())
    colored.fill(Qt.GlobalColor.transparent)
    painter = QPainter(colored)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored.rect(), QColor(color_hex))
    painter.end()
    scaled = colored.scaled(size * 2, size * 2, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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
        self.setWindowTitle("配置搜索范围")
        self.setMinimumSize(520, 380)
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("搜索范围配置")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937; border: none; background: transparent;")
        layout.addWidget(header)

        desc = QLabel("默认扫描所有本地驱动器。添加/移除特定目录后需要重新扫描。")
        desc.setStyleSheet("font-size: 13px; color: #6B7280; border: none; background: transparent; text-decoration: none;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("输入目录路径或点击选择...")
        self.path_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
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
        browse_btn.setStyleSheet(CONFIG_BTN_STYLE)
        browse_btn.clicked.connect(self._on_browse)

        add_btn = QPushButton("+ 添加")
        add_btn.setStyleSheet(SCAN_BTN_STYLE)
        add_btn.clicked.connect(self._on_add)

        add_row.addWidget(self.path_input, 1)
        add_row.addWidget(browse_btn)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        self.dir_list = QListWidget()
        self.dir_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #FAFAFA;
                padding: 4px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item { padding: 6px 10px; border-radius: 4px; border: none; }
            QListWidget::item:selected { background-color: #F5F3FF; color: #1F2937; border: none; }
        """)
        for d in self._dirs:
            self.dir_list.addItem(d)
        layout.addWidget(self.dir_list, 1)

        remove_row = QHBoxLayout()
        remove_btn = QPushButton("- 移除选中")
        remove_btn.setStyleSheet(CONFIG_BTN_STYLE)
        remove_btn.clicked.connect(self._on_remove)
        remove_row.addWidget(remove_btn)
        remove_row.addStretch()
        layout.addLayout(remove_row)

        quick_add_row = QHBoxLayout()
        quick_add_row.setSpacing(6)
        quick_label = QLabel("快速添加：")
        quick_label.setStyleSheet("font-size: 12px; color: #6B7280; border: none; background: transparent; text-decoration: none;")
        add_all_drives_btn = QPushButton("所有驱动器")
        add_user_dirs_btn = QPushButton("常用目录")
        add_all_drives_btn.setStyleSheet(CONFIG_BTN_STYLE)
        add_user_dirs_btn.setStyleSheet(CONFIG_BTN_STYLE)
        add_all_drives_btn.clicked.connect(self._on_add_all_drives)
        add_user_dirs_btn.clicked.connect(self._on_add_user_dirs)
        quick_add_row.addWidget(quick_label)
        quick_add_row.addWidget(add_all_drives_btn)
        quick_add_row.addWidget(add_user_dirs_btn)
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

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择搜索目录")
        if path:
            self.path_input.setText(path)

    def _on_add(self):
        path = self.path_input.text().strip()
        if path and path not in self._dirs:
            self._dirs.append(path)
            self.dir_list.addItem(path)
            self.path_input.clear()

    def _on_remove(self):
        selected = self.dir_list.selectedItems()
        for item in selected:
            self.dir_list.takeItem(self.dir_list.row(item))
            if item.text() in self._dirs:
                self._dirs.remove(item.text())

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

    def get_dirs(self):
        return self._dirs


class FilterBar(QWidget):
    filter_changed = Signal(str)
    scope_changed = Signal(list)
    scan_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_category = 'all'
        self._search_dirs = []
        self._indexed_count = 0
        self._is_scanning = False
        self._init_ui()
        self._reload_scope()

    def _reload_scope(self):
        from config import get_default_search_dirs
        self._search_dirs = get_default_search_dirs()
        self._update_scope_label()

    def _check_index(self):
        db = DatabaseManager()
        self._indexed_count = db.get_index_count()
        self._update_scope_label()
        self._update_status_dot()

    def _update_scope_label(self):
        parts = []
        dir_count = len(self._search_dirs)
        if dir_count == 1:
            parts.append(f"{self._search_dirs[0]}")
        else:
            parts.append(f"{dir_count} 个目录")

        if self._indexed_count > 0:
            parts.append(f" | 已索引 {self._indexed_count:,} 个文件")
        else:
            parts.append(" | 未扫描")

        self.scope_label.setText("  ".join(parts))

    def _update_status_dot(self):
        if self._indexed_count > 0:
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
        else:
            self.status_dot.setStyleSheet("""
                QLabel {
                    min-width: 8px; max-width: 8px;
                    min-height: 8px; max-height: 8px;
                    border-radius: 4px;
                    background-color: #F59E0B;
                    border: none;
                }
            """)
            self.status_dot.setToolTip("未扫描")

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

        purple_settings = _make_colored_icon("icons/settings.svg", "#7C3AED", 16)
        self.configure_btn = QPushButton()
        self.configure_btn.setIcon(purple_settings)
        self.configure_btn.setIconSize(QSize(18, 18))
        self.configure_btn.setFixedSize(32, 32)
        self.configure_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                outline: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
                border-radius: 6px;
            }
        """)
        self.configure_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.configure_btn.setToolTip("配置搜索范围")
        self.configure_btn.clicked.connect(self._on_configure_scope)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(180)
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setStyleSheet(PROGRESS_STYLE)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        white_refresh = _make_colored_icon("icons/refresh.svg", "#FFFFFF", 14)
        self.scan_btn = QPushButton()
        self.scan_btn.setIcon(white_refresh)
        self.scan_btn.setIconSize(QSize(16, 16))
        self.scan_btn.setText(" 重新扫描")
        self.scan_btn.setStyleSheet(SCAN_BTN_STYLE)
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.setFixedWidth(116)
        self.scan_btn.clicked.connect(self._on_scan_clicked)

        top_row.addWidget(self.status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addSpacing(4)
        top_row.addWidget(self.scope_label, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addSpacing(4)
        top_row.addWidget(self.configure_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addSpacing(6)
        top_row.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignVCenter)
        top_row.addSpacing(4)
        top_row.addWidget(self.scan_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        main_layout.addLayout(top_row)
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
                QMessageBox.warning(self, "配置错误", "搜索范围不能为空")
                return
            self._search_dirs = new_dirs
            self._update_scope_label()
            self.scope_changed.emit(list(self._search_dirs))

            from config import load_config, save_config
            config = load_config()
            config["search"]["default_dirs"] = list(self._search_dirs)
            save_config(config)

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
        white_refresh = _make_colored_icon("icons/refresh.svg", "#FFFFFF", 14)
        self.scan_btn.setIcon(white_refresh)
        self.scan_btn.setIconSize(QSize(16, 16))
        self.scan_btn.setStyleSheet(SCAN_BTN_STYLE)
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.setText(" 重新扫描")
        self.progress_bar.setVisible(False)
        self._indexed_count = file_count
        self._update_scope_label()
        self._update_status_dot()

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
