from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QLabel, QHBoxLayout, QScrollBar
from PySide6.QtGui import QFont, QIcon, QColor, QTextCharFormat, QTextCursor, QPalette
from PySide6.QtCore import QSize, Qt
from models import SearchResult
from utils.encoding import read_text_file

PREVIEW_SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        background: #1E1E1E;
        width: 12px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: #424242;
        min-height: 30px;
        border-radius: 6px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background: #555555;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
        background: none;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    QScrollBar:horizontal {
        background: #1E1E1E;
        height: 12px;
        margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: #424242;
        min-width: 30px;
        border-radius: 6px;
        margin: 2px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #555555;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
        background: none;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
"""

class LineNumberArea(QWidget):
    def __init__(self, editor, painter):
        super().__init__(editor)
        self._editor = editor
        self._painter = painter
        self.setFixedWidth(50)
        self.setStyleSheet("background-color: #252526;")

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._painter:
            self._painter.draw_line_numbers(self, event.rect())

    def sizeHint(self):
        return QSize(50, 0)


class LineNumberPainter:
    def __init__(self, text_edit: QTextEdit):
        self._text_edit = text_edit
        self._font = QFont("Consolas", 11)
        self._color = QColor("#858585")

    def draw_line_numbers(self, widget, rect):
        from PySide6.QtGui import QPainter
        painter = QPainter(widget)
        painter.setFont(self._font)
        painter.setPen(self._color)

        block = self._text_edit.document().firstBlock()
        top = self._text_edit.viewport().geometry().top()
        bottom = top + self._text_edit.viewport().height()

        line_number = 1
        while block.isValid():
            block_rect = self._text_edit.document().documentLayout().blockBoundingRect(block)
            y = int(block_rect.top()) - self._text_edit.verticalScrollBar().value() + int(self._text_edit.document().documentMargin())

            if y + int(block_rect.height()) >= top and y <= bottom:
                painter.drawText(
                    0, y,
                    widget.width() - 8, int(block_rect.height()),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    str(line_number)
                )

            block = block.next()
            line_number += 1

        painter.end()


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_number_painter = None
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

        header_layout.addWidget(self.title_icon)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        editor_container = QWidget()
        editor_container.setStyleSheet("background-color: #1E1E1E;")
        editor_layout = QHBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', 'Monaco', 'Courier New', 'Source Code Pro', monospace;
                font-size: 13px;
                padding: 12px 16px;
                border: none;
                selection-background-color: #264F78;
                selection-color: #FFFFFF;
            }}
            {PREVIEW_SCROLLBAR_STYLE}
        """)
        self.text_edit.verticalScrollBar().valueChanged.connect(self._update_line_numbers)
        self.text_edit.textChanged.connect(self._update_line_numbers)

        self._line_number_painter = LineNumberPainter(self.text_edit)
        self.line_number_area = LineNumberArea(self.text_edit, self._line_number_painter)

        editor_layout.addWidget(self.line_number_area)
        editor_layout.addWidget(self.text_edit)

        editor_container.setLayout(editor_layout)
        layout.addWidget(editor_container)

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

        self.editor_container = editor_container
        self.editor_container.setVisible(False)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
            }
        """)

    def _update_line_numbers(self):
        if self.line_number_area:
            self.line_number_area.update()

    def show_result(self, result: SearchResult):
        self.title_label.setText(result.file_item.name)
        self.title_label.setToolTip(result.file_item.path)

        if result.file_item.is_directory:
            self.empty_placeholder.setText("文件夹，无法预览内容")
            self.empty_placeholder.setVisible(True)
            self.editor_container.setVisible(False)
            return

        content = read_text_file(result.file_item.path)
        if content:
            self.empty_placeholder.setVisible(False)
            self.editor_container.setVisible(True)
            self.text_edit.setPlainText(content)
            self.line_number_area.setVisible(True)
        else:
            self.empty_placeholder.setText("无法预览此文件")
            self.empty_placeholder.setVisible(True)
            self.editor_container.setVisible(False)

    def clear(self):
        self.title_label.setText("内容预览")
        self.title_label.setToolTip("")
        self.empty_placeholder.setText("无预览内容")
        self.empty_placeholder.setVisible(True)
        self.editor_container.setVisible(False)
        self.text_edit.clear()
        self.line_number_area.setVisible(False)