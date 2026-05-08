from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


DIALOG_STYLE = """
    QDialog {
        background-color: #FFFFFF;
    }
    QLabel {
        color: #1F2937;
        border: none;
        background: transparent;
    }
"""

BTN_STYLE = """
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
"""

PRIMARY_BTN_STYLE = """
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
"""


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(520, 400)
        self.setStyleSheet(DIALOG_STYLE)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 20)

        header = QLabel("设置")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        placeholder = QLabel("偏好设置功能将在后续版本中完善")
        placeholder.setStyleSheet("font-size: 14px; color: #9CA3AF; border: none; background: transparent;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(BTN_STYLE)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        self.setLayout(layout)
