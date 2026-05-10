from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, QSize
from ..style_constants import COLORS, FONT, FILE_ICON_MAP


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setStyleSheet("border: none; background: transparent;")

        self.title_label = QLabel("预览")
        title_font = QFont()
        title_font.setPointSize(FONT.BODY_PT)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")

        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_SECONDARY};
                border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
            }}
        """)

        self.content_label = QLabel("选择文件以预览内容")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet(f"""
            background-color: {COLORS.BG_PRIMARY};
            color: {COLORS.TEXT_PLACEHOLDER};
            font-size: {FONT.DISPLAY_PT}px;
            border: none;
        """)

        self.empty_placeholder = QLabel("选择文件以预览内容")
        self.empty_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_placeholder.setStyleSheet(f"""
            background-color: {COLORS.BG_PRIMARY};
            color: {COLORS.TEXT_PLACEHOLDER};
            font-size: {FONT.DISPLAY_PT}px;
            border: none;
        """)

        layout.addWidget(self.header_widget)
        layout.addWidget(self.empty_placeholder, 1)

        self.setLayout(layout)
        self.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; }}")

    def set_result(self, result):
        self._current_result = result
        if result is None:
            self.empty_placeholder.setVisible(True)
            self.content_label.setVisible(False)
            self.title_label.setText("预览")
            self.icon_label.clear()
            return

        self.empty_placeholder.setVisible(False)
        self.content_label.setVisible(True)

        file_item = result.file_item
        self.title_label.setText(file_item.name)

        ext = file_item.extension.lower()
        icon_name = FILE_ICON_MAP.get(ext, 'file(solid).svg')
        self.icon_label.setPixmap(QIcon(f"icons/{icon_name}").pixmap(QSize(20, 20)))

    def clear_preview(self):
        self._current_result = None
        self.title_label.setText("预览")
        self.icon_label.clear()
        self.empty_placeholder.setVisible(True)
        self.content_label.setVisible(False)
