import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QFont, QFontMetrics, QIcon
from PySide6.QtCore import QSize, Qt
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


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header_widget = QWidget()
        header_widget.setFixedHeight(38)
        header_widget.setStyleSheet("""
            background-color: #FAFAFA;
            border-bottom: 1px solid #E5E7EB;
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(14, 0, 14, 0)

        self.title_icon = QLabel()
        self.title_icon.setPixmap(QIcon("icons/document(solid).svg").pixmap(QSize(20, 20)))

        self.title_label = QLabel("内容预览")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(13)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #1F2937;")
        self.title_label.setMinimumWidth(1)

        header_layout.addWidget(self.title_icon)
        header_layout.addWidget(self.title_label, 1)

        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        self.empty_placeholder = QLabel("无预览内容")
        self.empty_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_placeholder.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                color: #9CA3AF;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
        """)
        self.empty_placeholder.setVisible(True)
        layout.addWidget(self.empty_placeholder)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
            }
        """)

    def _get_icon_name(self, result: SearchResult) -> str:
        if result.file_item.is_directory:
            return 'folder-open.svg'
        ext = result.file_item.extension.lower()
        return FILE_ICON_MAP.get(ext, 'file(solid).svg')

    def show_result(self, result: SearchResult):
        self._current_result = result

        icon_name = self._get_icon_name(result)
        self.title_icon.setPixmap(QIcon(f"icons/{icon_name}").pixmap(QSize(20, 20)))

        name = result.file_item.name
        self.title_label.setText(name)
        self.title_label.setToolTip(result.file_item.path)

        font = self.title_label.font()
        fm = QFontMetrics(font)
        available_width = self.title_label.width()
        if available_width > 0:
            elided = fm.elidedText(name, Qt.TextElideMode.ElideRight, available_width)
            self.title_label.setText(elided)

        self.empty_placeholder.setText("预览功能将在后续版本中完善")
        self.empty_placeholder.setVisible(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_result:
            name = self._current_result.file_item.name
            font = self.title_label.font()
            fm = QFontMetrics(font)
            available_width = self.title_label.width()
            if available_width > 0:
                elided = fm.elidedText(name, Qt.TextElideMode.ElideRight, available_width)
                self.title_label.setText(elided)

    def clear(self):
        self._current_result = None
        self.title_icon.setPixmap(QIcon("icons/document(solid).svg").pixmap(QSize(20, 20)))
        self.title_label.setText("内容预览")
        self.title_label.setToolTip("")
        self.empty_placeholder.setText("无预览内容")
        self.empty_placeholder.setVisible(True)
