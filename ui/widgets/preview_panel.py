from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import QSize, Qt
from models import SearchResult


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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

    def show_result(self, result: SearchResult):
        self.title_label.setText(result.file_item.name)
        self.title_label.setToolTip(result.file_item.path)
        self.empty_placeholder.setText("预览功能将在后续版本中完善")
        self.empty_placeholder.setVisible(True)

    def clear(self):
        self.title_label.setText("内容预览")
        self.title_label.setToolTip("")
        self.empty_placeholder.setText("无预览内容")
        self.empty_placeholder.setVisible(True)
