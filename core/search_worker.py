from PySide6.QtCore import QThread, Signal

from core.search_engine import SearchEngine


class SearchWorker(QThread):
    results_ready = Signal(object)

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self._query = query
        self._engine = SearchEngine()

    def run(self):
        try:
            results = self._engine.search(self._query)
            self.results_ready.emit(results)
        except Exception:
            self.results_ready.emit([])

    def cancel(self):
        self._engine.cancel()
