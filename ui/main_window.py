import os
import time
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QStatusBar, QMessageBox, QLabel, QProgressBar)
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtGui import QFont, QIcon
from models import SearchQuery, SearchResult
from core import SearchEngine
from config import get_default_search_dirs, get_exclude_dirs, get_max_results
from .widgets import SearchBar, ResultListWidget, PreviewPanel, FilterBar

APP_THEME = """
    QMainWindow {
        background-color: #F8F9FA;
    }
    QToolTip {
        background-color: #FFFFFF;
        color: #1F2937;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }
"""

class SearchWorker(QObject):
    finished = Signal(list, float)
    error = Signal(str)

    def __init__(self, query: SearchQuery):
        super().__init__()
        self._query = query

    def run(self):
        try:
            engine = SearchEngine()
            start = time.time()
            results = engine.search(self._query)
            elapsed = time.time() - start
            self.finished.emit(results, elapsed)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._search_thread = None
        self._result_count = 0

    def _init_ui(self):
        self.setWindowTitle("FileFinder - 本地文件搜索工具")
        self.setWindowIcon(QIcon("icons/file(solid).svg"))
        self.setMinimumSize(1000, 680)
        self.resize(1280, 820)
        self.setStyleSheet(APP_THEME)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        top_area = QWidget()
        top_layout = QVBoxLayout(top_area)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        self.search_bar = SearchBar()
        self.search_bar.search_triggered.connect(self._on_search)
        top_layout.addWidget(self.search_bar)

        self.filter_bar = FilterBar()
        self.filter_bar.filter_changed.connect(self._on_filter_changed)
        top_layout.addWidget(self.filter_bar)

        bottom_area = QWidget()
        bottom_area.setStyleSheet("background-color: #FFFFFF;")
        bottom_layout = QVBoxLayout(bottom_area)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        self.result_header = QWidget()
        self.result_header.setFixedHeight(42)
        self.result_header.setStyleSheet("""
            background-color: #FAFAFA;
            border-bottom: 1px solid #E5E7EB;
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 0, 16, 0)

        self.result_count_label = QLabel("搜索结果")
        result_font = QFont()
        result_font.setBold(True)
        result_font.setPointSize(13)
        self.result_count_label.setFont(result_font)
        self.result_count_label.setStyleSheet("color: #1F2937;")

        self.match_mode_label = QLabel("")
        self.match_mode_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")

        header_layout.addWidget(self.result_count_label)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.match_mode_label)
        header_layout.addStretch()

        self.result_header.setLayout(header_layout)
        bottom_layout.addWidget(self.result_header)

        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.setHandleWidth(4)
        h_splitter.setStyleSheet("""
            QSplitter {
                background-color: #FFFFFF;
                border: none;
            }
            QSplitter::handle {
                background-color: #E5E7EB;
            }
            QSplitter::handle:hover {
                background-color: #7C3AED;
            }
        """)

        self.result_list = ResultListWidget()
        self.result_list.result_double_clicked.connect(self._on_result_double_clicked)
        self.result_list.currentItemChanged.connect(self._on_result_selected)
        h_splitter.addWidget(self.result_list)

        self.preview_panel = PreviewPanel()
        h_splitter.addWidget(self.preview_panel)

        h_splitter.setStretchFactor(0, 3)
        h_splitter.setStretchFactor(1, 2)

        bottom_layout.addWidget(h_splitter)

        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setHandleWidth(4)
        v_splitter.setStyleSheet("""
            QSplitter {
                background-color: #F8F9FA;
                border: none;
            }
            QSplitter::handle {
                background-color: #E5E7EB;
            }
            QSplitter::handle:hover {
                background-color: #7C3AED;
            }
        """)
        v_splitter.addWidget(top_area)
        v_splitter.addWidget(bottom_area)
        v_splitter.setStretchFactor(0, 1)
        v_splitter.setStretchFactor(1, 3)

        outer_layout.addWidget(v_splitter)

        self._init_status_bar()

    def _init_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #FAFAFA;
                border-top: 1px solid #E5E7EB;
                padding: 4px 16px;
                font-size: 12px;
                color: #6B7280;
            }
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #E5E7EB;
                max-height: 4px;
                text-align: center;
                font-size: 0px;
            }
            QProgressBar::chunk {
                background-color: #7C3AED;
                border-radius: 3px;
            }
        """)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        self.status_bar.addWidget(self.status_label, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.status_bar.showMessage("")

    def _on_search(self, name_query, content_query, use_regex, case_sensitive):
        if not name_query.strip() and not content_query.strip():
            return

        if self._search_thread and self._search_thread.isRunning():
            self._search_thread.quit()
            self._search_thread.wait()

        query = SearchQuery(
            name_query=name_query if name_query else None,
            content_query=content_query if content_query else None,
            content_mode='regex' if use_regex else 'keyword',
            include_dirs=get_default_search_dirs(),
            exclude_dirs=get_exclude_dirs(),
            max_results=get_max_results(),
            name_case_sensitive=case_sensitive,
            content_case_sensitive=case_sensitive
        )

        self.status_label.setText("搜索中...")
        self.progress_bar.setVisible(True)
        self.result_list.clear_results()
        self.preview_panel.clear()
        self._result_count = 0
        self.result_count_label.setText("搜索结果")
        self.match_mode_label.setText("")

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

    def _on_search_finished(self, results, elapsed):
        self.progress_bar.setVisible(False)
        self._result_count = len(results)

        if results:
            self.result_count_label.setText(f"搜索结果")
            self.match_mode_label.setText(f"共 {self._result_count} 个文件")
            self.status_label.setText(f"搜索完成，耗时 {elapsed:.2f}s")
            for result in results:
                self.result_list.add_result(result)
        else:
            self.result_count_label.setText("未找到匹配文件")
            self.match_mode_label.setText("")
            self.status_label.setText("未找到匹配的文件")

    def _on_search_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.status_label.setText("搜索出错")
        QMessageBox.warning(self, "搜索错误", f"搜索过程中发生错误: {error_msg}")

    def _on_filter_changed(self, category):
        self.status_label.setText(f"已筛选: {category}")

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