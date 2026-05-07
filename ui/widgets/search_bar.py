from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Signal
from utils import Debouncer

class SearchBar(QWidget):
    """搜索栏组件（P0阶段仅支持关键词搜索）"""
    
    search_triggered = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._debouncer = Debouncer(delay_ms=300)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        
        name_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("搜索文件名...")
        self.name_input.setClearButtonEnabled(True)
        name_layout.addWidget(self.name_input)
        
        content_layout = QHBoxLayout()
        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("搜索文件内容...")
        self.content_input.setClearButtonEnabled(True)
        content_layout.addWidget(self.content_input)
        
        layout.addLayout(name_layout)
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
        
        self.name_input.textChanged.connect(self._on_name_changed)
        self.content_input.textChanged.connect(self._on_content_changed)

    def _on_name_changed(self, text):
        """文件名输入变化时触发搜索"""
        self._debouncer.trigger(self._emit_search)

    def _on_content_changed(self, text):
        """内容输入变化时触发搜索"""
        self._debouncer.trigger(self._emit_search)

    def _emit_search(self):
        """触发搜索信号"""
        self.search_triggered.emit(
            self.name_input.text(),
            self.content_input.text()
        )

    def get_name_query(self):
        """获取文件名搜索词"""
        return self.name_input.text().strip()

    def get_content_query(self):
        """获取内容搜索词"""
        return self.content_input.text().strip()

    def set_focus(self):
        """聚焦到文件名输入框"""
        self.name_input.setFocus()