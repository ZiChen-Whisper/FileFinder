from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox
from constants import FILE_TYPE_CATEGORIES

class FilterBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_category = 'all'
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        
        self.type_buttons = {}
        for key, label in FILE_TYPE_CATEGORIES.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            if key == 'all':
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, k=key: self._on_type_clicked(k))
            self.type_buttons[key] = btn
            layout.addWidget(btn)
        
        self.directory_combo = QComboBox()
        self.directory_combo.addItem("选择搜索目录...")
        layout.addWidget(self.directory_combo)
        
        self.setLayout(layout)

    def _on_type_clicked(self, category):
        self._selected_category = category
        for key, btn in self.type_buttons.items():
            btn.setChecked(key == category)
        
        if hasattr(self, 'filter_changed'):
            self.filter_changed.emit(category)

    def get_selected_category(self):
        return self._selected_category