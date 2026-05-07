from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtGui import QFont, QIcon, QFontMetrics
from PySide6.QtCore import Qt, Signal, QSize, QRect
from models import SearchResult

FILE_ICON_MAP = {
    '.py': 'square-code(solid).svg',
    '.js': 'square-code(solid).svg',
    '.ts': 'square-code(solid).svg',
    '.java': 'square-code(solid).svg',
    '.c': 'square-code(solid).svg',
    '.cpp': 'square-code(solid).svg',
    '.h': 'square-code(solid).svg',
    '.go': 'square-code(solid).svg',
    '.rs': 'square-code(solid).svg',
    '.rb': 'square-code(solid).svg',
    '.php': 'square-code(solid).svg',
    '.html': 'square-code(solid).svg',
    '.css': 'square-code(solid).svg',
    '.sql': 'square-code(solid).svg',
    '.sh': 'square-code(solid).svg',
    '.bat': 'square-code(solid).svg',
    '.ps1': 'square-code(solid).svg',
    '.txt': 'text(solid).svg',
    '.md': 'text(solid).svg',
    '.log': 'text(solid).svg',
    '.json': 'text(solid).svg',
    '.xml': 'text(solid).svg',
    '.csv': 'text(solid).svg',
    '.yaml': 'text(solid).svg',
    '.yml': 'text(solid).svg',
    '.ini': 'text(solid).svg',
    '.cfg': 'text(solid).svg',
    '.toml': 'text(solid).svg',
    '.pdf': 'document(solid).svg',
    '.docx': 'document(solid).svg',
    '.xlsx': 'document(solid).svg',
    '.pptx': 'document(solid).svg',
}

LIST_STYLE = """
    QListWidget {
        background-color: #FFFFFF;
        border: none;
        outline: none;
        padding: 8px 6px;
    }
    QListWidget::item {
        border-radius: 10px;
        margin: 2px 4px;
        padding: 0px;
        background: transparent;
        border: none;
    }
    QListWidget::item:selected {
        background: transparent;
        border: none;
    }
"""

class ResultListWidget(QListWidget):
    result_double_clicked = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []
        self._current_selected_index = -1
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.itemDoubleClicked.connect(self._on_double_click)
        self.setStyleSheet(LIST_STYLE)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)

    def add_result(self, result: SearchResult):
        self._results.append(result)
        item = QListWidgetItem(self)
        widget = ResultItemWidget(result)
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)

    def clear_results(self):
        self._results.clear()
        self._current_selected_index = -1
        self.clear()

    def get_selected_result(self):
        selected_items = self.selectedItems()
        if selected_items:
            index = self.row(selected_items[0])
            if 0 <= index < len(self._results):
                return self._results[index]
        return None

    def _on_double_click(self, item):
        result = self.get_selected_result()
        if result:
            self.result_double_clicked.emit(result)

class ResultItemWidget(QFrame):
    def __init__(self, result: SearchResult, parent=None):
        super().__init__(parent)
        self._result = result
        self._selected = False
        self._init_ui()

    def _get_icon_name(self) -> str:
        ext = self._result.file_item.extension.lower()
        return FILE_ICON_MAP.get(ext, 'file(solid).svg')

    def _get_type_label(self) -> str:
        file_type = self._result.file_item.file_type
        labels = {
            'document': '文档',
            'code': '代码',
            'image': '图片',
            'video': '视频',
            'audio': '音频',
            'archive': '压缩包',
            'other': '其他'
        }
        return labels.get(file_type, '其他')

    def _get_match_badge(self) -> str:
        count = len(self._result.content_matches)
        if not count:
            return ""
        return f"  匹配 {count} 处"

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 8, 14, 8)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_name = self._get_icon_name()
        icon_label.setPixmap(QIcon(f"icons/{icon_name}").pixmap(QSize(28, 28)))
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        name_label = QLabel(self._result.file_item.name)
        name_font = QFont()
        name_font.setPointSize(13)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #111827; background: transparent; border: none;")
        name_label.setTextFormat(Qt.TextFormat.PlainText)

        match_badge = self._get_match_badge()
        match_label = QLabel(match_badge)
        match_label.setStyleSheet("color: #7C3AED; font-size: 12px; font-weight: bold; background: transparent; border: none;")

        name_row.addWidget(name_label)
        if match_badge:
            name_row.addWidget(match_label)
        name_row.addStretch()

        path_label = QLabel(self._result.file_item.path)
        path_font = QFont()
        path_font.setPointSize(11)
        path_label.setFont(path_font)
        path_label.setStyleSheet("color: #6B7280; background: transparent; border: none;")
        fm = QFontMetrics(path_font)
        elided = fm.elidedText(self._result.file_item.path, Qt.TextElideMode.ElideLeft, 500)
        path_label.setText(elided)

        info_row = QHBoxLayout()
        info_row.setSpacing(10)

        type_label = QLabel(self._get_type_label())
        type_label.setStyleSheet("""
            background-color: #F3F4F6;
            color: #4B5563;
            border-radius: 5px;
            padding: 2px 8px;
            font-size: 11px;
            border: none;
        """)

        size_label = QLabel(self._result.file_item.size_display)
        size_label.setStyleSheet("""
            background-color: #F3F4F6;
            color: #4B5563;
            border-radius: 5px;
            padding: 2px 8px;
            font-size: 11px;
            border: none;
        """)

        date_label = QLabel(self._result.file_item.modified_date)
        date_label.setStyleSheet("""
            background-color: #F3F4F6;
            color: #4B5563;
            border-radius: 5px;
            padding: 2px 8px;
            font-size: 11px;
            border: none;
        """)

        info_row.addWidget(type_label)
        info_row.addWidget(size_label)
        info_row.addWidget(date_label)
        info_row.addStretch()

        content_layout.addLayout(name_row)
        content_layout.addWidget(path_label)
        content_layout.addLayout(info_row)

        layout.addWidget(icon_label)
        layout.addLayout(content_layout)

        self.setLayout(layout)
        self.setObjectName("resultItemWidget")
        self.setStyleSheet("""
            QFrame#resultItemWidget {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid transparent;
            }
            QFrame#resultItemWidget:hover {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setMinimumHeight(72)