import os
import subprocess
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QStatusBar, QMessageBox)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from models import SearchQuery, SearchResult
from core import SearchEngine
from config import get_default_search_dirs, get_exclude_dirs, get_max_results
from .widgets import SearchBar, ResultListWidget, PreviewPanel, FilterBar

class SearchWorker(QObject):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, query: SearchQuery):
        super().__init__()
        self._query = query

    def run(self):
        try:
            engine = SearchEngine()
            results = engine.search(self._query)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._search_thread = None

    def _init_ui(self):
        self.setWindowTitle("FileFinder")
        self.setMinimumSize(800, 500)
        self.resize(900, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.search_bar = SearchBar()
        self.search_bar.search_triggered.connect(self._on_search)
        layout.addWidget(self.search_bar)

        self.filter_bar = FilterBar()
        layout.addWidget(self.filter_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.result_list = ResultListWidget()
        self.result_list.result_double_clicked.connect(self._on_result_double_clicked)
        self.result_list.currentItemChanged.connect(self._on_result_selected)
        splitter.addWidget(self.result_list)

        self.preview_panel = PreviewPanel()
        splitter.addWidget(self.preview_panel)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _on_search(self, name_query, content_query):
        if self._search_thread and self._search_thread.isRunning():
            self._search_thread.terminate()

        query = SearchQuery(
            name_query=name_query if name_query else None,
            content_query=content_query if content_query else None,
            content_mode='keyword',
            include_dirs=get_default_search_dirs(),
            exclude_dirs=get_exclude_dirs(),
            max_results=get_max_results()
        )

        self.status_bar.showMessage("搜索中...")
        self.result_list.clear_results()
        self.preview_panel.clear()

        self._worker = SearchWorker(query)
        self._search_thread = QThread()
        self._worker.moveToThread(self._search_thread)

        self._search_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_search_finished)
        self._worker.error.connect(self._on_search_error)
        self._worker.finished.connect(self._search_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._search_thread.finished.connect(self._search_thread.deleteLater)

        self._search_thread.start()

    def _on_search_finished(self, results):
        self.status_bar.showMessage(f"搜索完成，找到 {len(results)} 个结果")
        
        for result in results:
            self.result_list.add_result(result)
        
        if not results:
            self.status_bar.showMessage("未找到匹配的文件")

    def _on_search_error(self, error_msg):
        self.status_bar.showMessage("搜索出错")
        QMessageBox.warning(self, "搜索错误", f"搜索过程中发生错误: {error_msg}")

    def _on_result_selected(self, current, previous):
        result = self.result_list.get_selected_result()
        if result:
            self.preview_panel.show_result(result)
        else:
            self.preview_panel.clear()

    def _on_result_double_clicked(self, result: SearchResult):
        try:
            file_path = result.file_item.path
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                QMessageBox.warning(self, "文件不存在", f"文件已被删除或移动: {file_path}")
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开文件: {str(e)}")