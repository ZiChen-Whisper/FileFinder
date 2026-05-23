from PySide6.QtCore import QThread, Signal

from core.search_engine import SearchEngine


class SearchWorker(QThread):
    results_ready = Signal(object)
    # 转发 ContentSearcher 的实时信号
    progress_updated = Signal(int, int)    # (已处理文件数, 总文件数)
    result_found = Signal(object)          # 单个 SearchResult（实时结果）
    file_searching = Signal(str)           # 当前正在搜索的文件路径
    search_completed = Signal(int)         # 搜索的文件总数

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self._query = query
        self._engine = SearchEngine()
        # 连接 ContentSearcher 的信号到 Worker 的信号（跨线程自动转为队列连接）
        self._engine._content_searcher.progress_updated.connect(self.progress_updated.emit)
        self._engine._content_searcher.result_found.connect(self.result_found.emit)
        self._engine._content_searcher.file_searching.connect(self.file_searching.emit)
        self._engine._content_searcher.search_completed.connect(self.search_completed.emit)

    def run(self):
        try:
            results = self._engine.search(self._query)
            self.results_ready.emit(results)
        except Exception:
            self.results_ready.emit([])

    def cancel(self):
        self._engine.cancel()
