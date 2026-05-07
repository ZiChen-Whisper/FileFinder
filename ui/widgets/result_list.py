import os
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QWidget, QVBoxLayout,
                             QLabel, QHBoxLayout, QFrame, QMenu, QApplication, QAbstractItemView)
from PySide6.QtGui import QFont, QIcon, QFontMetrics, QDrag, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QUrl, QPoint
from models import SearchResult

FILE_ICON_MAP = {
    '.py': 'doctype/code.svg', '.js': 'doctype/code.svg', '.ts': 'doctype/code.svg',
    '.java': 'doctype/code.svg', '.c': 'doctype/code.svg', '.cpp': 'doctype/code.svg',
    '.h': 'doctype/code.svg', '.go': 'doctype/code.svg', '.rs': 'doctype/code.svg',
    '.rb': 'doctype/code.svg', '.php': 'doctype/code.svg', '.html': 'doctype/code.svg',
    '.css': 'doctype/code.svg', '.sql': 'doctype/code.svg', '.sh': 'doctype/code.svg',
    '.bat': 'doctype/code.svg', '.ps1': 'doctype/code.svg',
    '.txt': 'doctype/TXT.svg', '.md': 'doctype/TXT.svg', '.log': 'doctype/TXT.svg',
    '.json': 'doctype/TXT.svg', '.xml': 'doctype/TXT.svg', '.csv': 'doctype/TXT.svg',
    '.yaml': 'doctype/TXT.svg', '.yml': 'doctype/TXT.svg', '.ini': 'doctype/TXT.svg',
    '.cfg': 'doctype/TXT.svg', '.conf': 'doctype/TXT.svg', '.toml': 'doctype/TXT.svg',
    '.pdf': 'doctype/PDF.svg', '.doc': 'doctype/Doc.svg', '.docx': 'doctype/Doc.svg',
    '.xls': 'doctype/Excel.svg', '.xlsx': 'doctype/Excel.svg',
    '.ppt': 'doctype/PPT.svg', '.pptx': 'doctype/PPT.svg',
    '.gif': 'doctype/Gif.svg', '.mp3': 'doctype/Mp3.svg', '.wav': 'doctype/Wav.svg',
    '.flac': 'doctype/Wav.svg', '.aac': 'doctype/Wav.svg',
    '.mov': 'doctype/Mov.svg', '.mp4': 'doctype/Mov.svg', '.avi': 'doctype/Mov.svg',
    '.mkv': 'doctype/Mov.svg',
    '.zip': 'doctype/Zip.svg', '.rar': 'doctype/Zip.svg', '.7z': 'doctype/Zip.svg',
    '.tar': 'doctype/Zip.svg', '.gz': 'doctype/Zip.svg',
    '.svg': 'doctype/Svg.svg', '.ai': 'doctype/Ai.svg', '.psd': 'doctype/Ps.svg',
    '.ae': 'doctype/Ae.svg', '.prproj': 'doctype/Pr.svg', '.xd': 'doctype/Xd.svg',
    '.rp': 'doctype/Rp.svg', '.swf': 'doctype/Swf.svg',
    '.jpg': 'doctype/图片.svg', '.jpeg': 'doctype/图片.svg', '.png': 'doctype/图片.svg',
    '.bmp': 'doctype/图片.svg', '.tiff': 'doctype/图片.svg', '.ico': 'doctype/图片.svg',
    '.epub': 'doctype/图书.svg', '.xmind': 'doctype/思维导图.svg',
}

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
        background: transparent; height: 6px; margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: #D1D5DB; min-width: 40px; border-radius: 3px;
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

LIST_STYLE = f"""
    QListWidget {{
        background-color: #FFFFFF;
        border: none;
        outline: none;
        padding: 8px 6px;
    }}
    QListWidget::item {{
        border-radius: 10px;
        margin: 2px 4px;
        padding: 0px;
        background: transparent;
        border: none;
        outline: none;
    }}
    QListWidget::item:selected {{
        background: transparent;
        border: none;
        outline: none;
    }}
    {SCROLLBAR_STYLE}
"""


class ResultItemWidget(QFrame):
    def __init__(self, result: SearchResult, selected: bool = False, parent=None):
        super().__init__(parent)
        self._result = result
        self._selected = selected
        self._init_ui()
        if selected:
            self._apply_selected_style()

    def _get_icon_name(self) -> str:
        if self._result.file_item.is_directory:
            return 'folder-open.svg'
        ext = self._result.file_item.extension.lower()
        return FILE_ICON_MAP.get(ext, 'file(solid).svg')

    def _get_type_label(self) -> str:
        if self._result.file_item.is_directory:
            return '文件夹'
        file_type = self._result.file_item.file_type
        labels = {
            'document': '文档', 'code': '代码', 'image': '图片',
            'video': '视频', 'audio': '音频', 'archive': '压缩包', 'other': '其他'
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
        icon_label.setStyleSheet("border: none; background: transparent;")

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
        self.setMinimumHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_default_style()

    def _apply_default_style(self):
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

    def _apply_selected_style(self):
        self.setStyleSheet("""
            QFrame#resultItemWidget {
                background-color: #F5F3FF;
                border-radius: 10px;
                border: 2px solid #7C3AED;
            }
        """)

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self._apply_selected_style()
        else:
            self._apply_default_style()

    def get_result(self) -> SearchResult:
        return self._result


class ResultListWidget(QListWidget):
    result_activated = Signal(object)
    result_selected = Signal(object)
    status_info_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []
        self._item_widgets = {}
        self._anchor_index = -1
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setStyleSheet(LIST_STYLE)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.setDragEnabled(True)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_double_click)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def add_result(self, result: SearchResult):
        idx = len(self._results)
        self._results.append(result)
        item = QListWidgetItem(self)
        widget = ResultItemWidget(result)
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)
        self._item_widgets[idx] = widget

    def clear_results(self):
        self._results.clear()
        self._item_widgets.clear()
        self._anchor_index = -1
        self.clear()

    def get_selected_result(self):
        items = self.selectedItems()
        if items:
            index = self.row(items[0])
            if 0 <= index < len(self._results):
                return self._results[index]
        return None

    def get_selected_results(self):
        results = []
        for item in self.selectedItems():
            index = self.row(item)
            if 0 <= index < len(self._results):
                results.append(self._results[index])
        return results

    def _on_selection_changed(self):
        selected_rows = {self.row(item) for item in self.selectedItems()}
        for idx, widget in self._item_widgets.items():
            widget.set_selected(idx in selected_rows)

        if selected_rows:
            last_idx = max(selected_rows)
            if 0 <= last_idx < len(self._results):
                self.result_selected.emit(self._results[last_idx])
                self.status_info_requested.emit(self._results[last_idx])

    def _on_item_clicked(self, item):
        index = self.row(item)
        if index == self._anchor_index and len(self.selectedItems()) == 1:
            self.result_activated.emit(self._results[index])
        self._anchor_index = index

    def _on_double_click(self, item):
        index = self.row(item)
        if 0 <= index < len(self._results):
            result = self._results[index]
            if result.file_item.is_directory:
                os.startfile(result.file_item.path)
            else:
                os.startfile(result.file_item.path)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item is None:
            self.clearSelection()
            for w in self._item_widgets.values():
                w.set_selected(False)
        super().mousePressEvent(event)

    def _on_context_menu(self, pos: QPoint):
        item = self.itemAt(pos)
        if item is not None:
            if not item.isSelected():
                self.clearSelection()
                item.setSelected(True)

        result = self.get_selected_result()
        if not result:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 32px 8px 36px;
                border-radius: 6px;
                font-size: 13px;
                color: #1F2937;
                background: transparent;
            }
            QMenu::item:selected {
                background-color: #F5F3FF;
                color: #7C3AED;
            }
            QMenu::icon {
                padding-left: 10px;
            }
            QMenu::separator {
                height: 1px;
                background: #E5E7EB;
                margin: 3px 8px;
            }
        """)

        open_action = menu.addAction(QIcon("icons/folder-open.svg"), "打开")
        open_path_action = menu.addAction(QIcon("icons/folder-open.svg"), "打开文件所在目录")
        menu.addSeparator()
        copy_path_action = menu.addAction(QIcon("icons/copy.svg"), "复制完整路径和文件名")

        action = menu.exec(self.mapToGlobal(pos))

        if action == open_action:
            self._open_file(result)
        elif action == open_path_action:
            self._open_file_path(result)
        elif action == copy_path_action:
            self._copy_path(result)

    def _open_file(self, result: SearchResult):
        try:
            file_path = result.file_item.path
            if os.path.exists(file_path):
                os.startfile(file_path)
        except Exception:
            pass

    def _open_file_path(self, result: SearchResult):
        try:
            directory = os.path.dirname(result.file_item.path)
            if directory and os.path.exists(directory):
                os.system(f'explorer /select,"{result.file_item.path}"')
        except Exception:
            pass

    def _copy_path(self, result: SearchResult):
        clipboard = QApplication.clipboard()
        clipboard.setText(result.file_item.path)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            result = self.get_selected_result()
            if result:
                if result.file_item.is_directory:
                    os.startfile(result.file_item.path)
                else:
                    os.startfile(result.file_item.path)
            return

        if event.key() == Qt.Key.Key_Down:
            if not self.selectedItems() and self.count() > 0:
                self.item(0).setSelected(True)
                self.setCurrentRow(0)
                self._scroll_to_index(0)
                return
            current = self.currentRow()
            if current < self.count() - 1:
                new_idx = current + 1
                if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.clearSelection()
                self.item(new_idx).setSelected(True)
                self.setCurrentRow(new_idx)
                self._scroll_to_index(new_idx)
            return

        if event.key() == Qt.Key.Key_Up:
            current = self.currentRow()
            if current > 0:
                new_idx = current - 1
                if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.clearSelection()
                self.item(new_idx).setSelected(True)
                self.setCurrentRow(new_idx)
                self._scroll_to_index(new_idx)
            return

        super().keyPressEvent(event)

    def _scroll_to_index(self, index):
        self.scrollToItem(self.item(index), QAbstractItemView.ScrollHint.EnsureVisible)

    def mimeData(self, items):
        results = self.get_selected_results()
        if not results:
            return None
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(r.file_item.path) for r in results]
        mime_data.setUrls(urls)
        return mime_data

    def startDrag(self, supportedActions):
        results = self.get_selected_results()
        if not results:
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(r.file_item.path) for r in results]
        mime_data.setUrls(urls)
        drag.setMimeData(mime_data)

        pixmap = QPixmap(160, 40)
        pixmap.fill(QColor("#7C3AED"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#FFFFFF"))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        text = results[0].file_item.name if len(results) == 1 else f"{len(results)} 个文件"
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(80, 20))
        drag.exec(Qt.DropAction.CopyAction)
