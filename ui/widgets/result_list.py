from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QFont, QColor, QIcon
from PySide6.QtCore import Qt, Signal
from models import SearchResult

class ResultListWidget(QListWidget):
    result_double_clicked = Signal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.itemDoubleClicked.connect(self._on_double_click)

    def add_result(self, result: SearchResult):
        self._results.append(result)
        item = QListWidgetItem(self)
        widget = ResultItemWidget(result)
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)

    def clear_results(self):
        self._results.clear()
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

class ResultItemWidget(QWidget):
    def __init__(self, result: SearchResult, parent=None):
        super().__init__(parent)
        self._result = result
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        
        name_label = QLabel(self._result.file_item.name)
        name_font = QFont()
        name_font.setBold(True)
        name_label.setFont(name_font)
        
        path_label = QLabel(self._result.file_item.path)
        path_font = QFont()
        path_font.setPointSize(10)
        path_label.setFont(path_font)
        path_label.setStyleSheet("color: #666666")
        
        info_layout = QHBoxLayout()
        size_label = QLabel(self._result.file_item.size_display)
        date_label = QLabel(self._result.file_item.modified_date)
        size_label.setFont(path_font)
        date_label.setFont(path_font)
        size_label.setStyleSheet("color: #888888")
        date_label.setStyleSheet("color: #888888")
        info_layout.addWidget(size_label)
        info_layout.addWidget(date_label)
        
        layout.addWidget(name_label)
        layout.addWidget(path_label)
        layout.addLayout(info_layout)
        
        self.setLayout(layout)