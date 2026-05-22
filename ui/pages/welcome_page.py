import os

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QLineEdit, QListWidgetItem, QFileDialog)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen

from ..style_constants import COLORS, FONT
from ..style_manager import (button_primary, button_secondary, button_small_secondary,
                             input_style, list_style, dialog_title_style)
from ..widgets.filter_bar import DirListWidget


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
