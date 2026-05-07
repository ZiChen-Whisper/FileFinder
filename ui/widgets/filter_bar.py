from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel
from PySide6.QtCore import Signal, Qt
from constants import FILE_TYPE_CATEGORIES

FILTER_BTN_STYLE = """
    QPushButton {
        padding: 6px 14px;
        border-radius: 16px;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        color: #4B5563;
        font-size: 12px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #F3F4F6;
        border-color: #D1D5DB;
    }
    QPushButton:checked {
        background-color: #7C3AED;
        border-color: #7C3AED;
        color: #FFFFFF;
    }
    QPushButton:checked:hover {
        background-color: #6D28D9;
        border-color: #6D28D9;
    }
"""

COMBO_STYLE = """
    QComboBox {
        padding: 6px 12px;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        background-color: #FFFFFF;
        color: #4B5563;
        font-size: 13px;
        min-height: 20px;
    }
    QComboBox:hover {
        border-color: #D1D5DB;
    }
    QComboBox:focus {
        border-color: #7C3AED;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left: 1px solid #E5E7EB;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        selection-background-color: #F5F3FF;
        selection-color: #1F2937;
        padding: 4px;
        outline: none;
    }
"""

class FilterBar(QWidget):
    filter_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_category = 'all'
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 4, 20, 4)
        main_layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self.type_buttons = {}
        for key, label in FILE_TYPE_CATEGORIES.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(FILTER_BTN_STYLE)
            if key == 'all':
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, k=key: self._on_type_clicked(k))
            self.type_buttons[key] = btn
            top_row.addWidget(btn)

        top_row.addStretch()

        main_layout.addLayout(top_row)

        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FAFAFA;
                border-bottom: 1px solid #E5E7EB;
            }
        """)

    def _on_type_clicked(self, category):
        self._selected_category = category
        for key, btn in self.type_buttons.items():
            btn.setChecked(key == category)
        self.filter_changed.emit(category)

    def get_selected_category(self):
        return self._selected_category