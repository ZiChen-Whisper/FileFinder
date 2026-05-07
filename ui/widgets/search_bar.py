from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QPushButton
from PySide6.QtCore import Signal, Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QFont
from utils import Debouncer

SEARCH_INPUT_STYLE = """
    QLineEdit {
        padding: 10px 14px;
        border: 2px solid #E5E7EB;
        border-radius: 12px;
        font-size: 14px;
        background-color: #FFFFFF;
        color: #1F2937;
    }
    QLineEdit:hover {
        border-color: #D1D5DB;
    }
    QLineEdit:focus {
        border-color: #7C3AED;
        background-color: #FFFFFF;
    }
"""

CHECKBOX_STYLE = """
    QCheckBox {
        spacing: 6px;
        font-size: 13px;
        color: #4B5563;
        padding: 4px 0;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 2px solid #D1D5DB;
        background-color: #FFFFFF;
    }
    QCheckBox::indicator:hover {
        border-color: #7C3AED;
    }
    QCheckBox::indicator:checked {
        background-color: #7C3AED;
        border-color: #7C3AED;
        image: url(icons/checkmark.svg);
    }
"""

class SearchBar(QWidget):
    search_triggered = Signal(str, str, bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._debouncer = Debouncer(delay_ms=300)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 14, 20, 8)
        main_layout.setSpacing(6)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入文件名关键词...")
        self.name_input.setClearButtonEnabled(True)
        self.name_input.setStyleSheet(SEARCH_INPUT_STYLE)
        self.name_input.returnPressed.connect(self._emit_search)

        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("输入文件内容关键词...")
        self.content_input.setClearButtonEnabled(True)
        self.content_input.setStyleSheet(SEARCH_INPUT_STYLE)
        self.content_input.returnPressed.connect(self._emit_search)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedSize(80, 42)
        search_font = QFont()
        search_font.setPointSize(14)
        search_font.setBold(True)
        self.search_btn.setFont(search_font)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #7C3AED;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #6D28D9;
            }
            QPushButton:pressed {
                background-color: #5B21B6;
            }
        """)
        self.search_btn.clicked.connect(self._emit_search)

        input_row.addWidget(self.name_input, 5)
        input_row.addWidget(self.content_input, 5)
        input_row.addWidget(self.search_btn)

        option_row = QHBoxLayout()
        option_row.setSpacing(20)

        self.regex_checkbox = QCheckBox("正则表达式")
        self.regex_checkbox.setStyleSheet(CHECKBOX_STYLE)

        self.case_sensitive_checkbox = QCheckBox("区分大小写")
        self.case_sensitive_checkbox.setStyleSheet(CHECKBOX_STYLE)

        option_row.addWidget(self.regex_checkbox)
        option_row.addWidget(self.case_sensitive_checkbox)
        option_row.addStretch()

        main_layout.addLayout(input_row)
        main_layout.addLayout(option_row)

        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
            }
        """)

        self.name_input.textChanged.connect(self._on_name_changed)
        self.content_input.textChanged.connect(self._on_content_changed)

    def _on_name_changed(self, text):
        self._debouncer.trigger(self._emit_search)

    def _on_content_changed(self, text):
        self._debouncer.trigger(self._emit_search)

    def _emit_search(self):
        self.search_triggered.emit(
            self.name_input.text(),
            self.content_input.text(),
            self.regex_checkbox.isChecked(),
            self.case_sensitive_checkbox.isChecked()
        )

    def get_name_query(self):
        return self.name_input.text().strip()

    def get_content_query(self):
        return self.content_input.text().strip()

    def is_regex_mode(self):
        return self.regex_checkbox.isChecked()

    def is_case_sensitive(self):
        return self.case_sensitive_checkbox.isChecked()

    def set_focus(self):
        self.name_input.setFocus()