from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QLabel
from models import SearchResult
from utils.encoding import read_text_file

class PreviewPanel(QWidget):
    """内容预览面板（P0阶段仅显示文本内容，高亮功能为P1）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        
        self.title_label = QLabel("内容预览")
        layout.addWidget(self.title_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        self.setLayout(layout)

    def show_result(self, result: SearchResult):
        """显示文件内容预览"""
        self.title_label.setText(f"内容预览 - {result.file_item.name}")
        
        content = read_text_file(result.file_item.path)
        if content:
            self.text_edit.setPlainText(content)
        else:
            self.text_edit.setPlainText("无法预览此文件内容")

    def clear(self):
        """清空预览内容"""
        self.title_label.setText("内容预览")
        self.text_edit.clear()