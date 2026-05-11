from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QFont, QFontMetrics, QIcon
from PySide6.QtCore import Qt, QSize, QRectF
from ..style_constants import COLORS, FONT, RADIUS, FILE_ICON_MAP


class ElidedFileNameLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full_text = text

    def setText(self, text):
        self._full_text = text
        super().setText(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self):
        fm = self.fontMetrics()
        available = self.width()
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideMiddle, available)
        super().setText(elided)

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self):
        return QSize(0, super().minimumSizeHint().height())


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

        self.title_label = ElidedFileNameLabel("预览")
        title_font = QFont()
        title_font.setPointSize(FONT.BODY_PT)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; border: none; background: transparent;")

        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label, 1)
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

        self.empty_placeholder = QLabel("")
        self.empty_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_placeholder.setStyleSheet(f"""
            background-color: {COLORS.BG_PRIMARY};
            color: transparent;
            font-size: {FONT.DISPLAY_PT}px;
            border: none;
        """)

        self._preview_placeholder = QWidget()
        preview_layout = QVBoxLayout(self._preview_placeholder)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        preview_layout.setSpacing(8)

        preview_box = QWidget()
        preview_box.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_SECONDARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {RADIUS.DEFAULT}px;
            }}
        """)
        preview_box_layout = QVBoxLayout(preview_box)
        preview_box_layout.setContentsMargins(16, 16, 16, 16)
        preview_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        preview_hint = QLabel("文件预览区域")
        preview_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_hint.setStyleSheet(f"""
            color: {COLORS.TEXT_PLACEHOLDER};
            font-size: {FONT.BODY_PT}px;
            border: none;
            background: transparent;
        """)
        preview_box_layout.addWidget(preview_hint)

        preview_layout.addStretch()
        preview_layout.addWidget(preview_box, 1)
        preview_layout.addStretch()
        self._preview_placeholder.setVisible(False)

        layout.addWidget(self.header_widget)
        layout.addWidget(self.empty_placeholder, 1)
        layout.addWidget(self._preview_placeholder, 1)

        self.setLayout(layout)
        self.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; }}")

    def set_result(self, result):
        self._current_result = result
        if result is None:
            self.empty_placeholder.setVisible(True)
            self._preview_placeholder.setVisible(False)
            self.content_label.setVisible(False)
            self.title_label.setText("预览")
            self.icon_label.clear()
            return

        file_item = result.file_item
        if file_item.is_directory:
            self.clear_preview()
            self._current_result = result
            return

        self.empty_placeholder.setVisible(False)
        self.content_label.setVisible(True)
        self._preview_placeholder.setVisible(True)

        self.title_label.setText(file_item.name)

        ext = file_item.extension.lower()
        icon_name = FILE_ICON_MAP.get(ext, 'doctype/File.svg')
        self.icon_label.setPixmap(QIcon(f"icons/{icon_name}").pixmap(QSize(20, 20)))

    def clear_preview(self):
        self._current_result = None
        self.title_label.setText("预览")
        self.icon_label.clear()
        self.empty_placeholder.setVisible(True)
        self._preview_placeholder.setVisible(False)
        self.content_label.setVisible(False)
