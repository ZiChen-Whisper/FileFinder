import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QStatusBar,
                             QLabel, QHBoxLayout, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon, QAction
from models.search_query import SearchQuery
from core.search_engine import SearchEngine
from .widgets import SearchBar, ResultListWidget, FilterBar, PreviewPanel, RoundedMenu
from .dialogs import SettingsDialog
from config import get_exclude_dirs, get_max_results


STATUS_BAR_STYLE = """
    QStatusBar {
        background-color: #FAFAFA;
        border-top: 1px solid #E5E7EB;
        padding: 4px 12px;
        min-height: 36px;
    }
    QStatusBar QLabel {
        color: #4B5563;
        font-size: 12px;
        padding: 0 6px;
        border: none;
        background: transparent;
    }
"""

STATUS_DIVIDER = """
    QLabel {
        color: #D1D5DB;
        padding: 0 2px;
        font-size: 12px;
        border: none;
        background: transparent;
    }
"""


class ScanWorker(QThread):
    progress = Signal(int)
    finished = Signal(int, float)
    error = Signal(str)

    def __init__(self, search_dirs, exclude_dirs, parent=None):
        super().__init__(parent)
        self._search_dirs = search_dirs
        self._exclude_dirs = exclude_dirs

    def run(self):
        import time
        start_time = time.time()
        try:
            from database.db_manager import DatabaseManager
            from utils.path_helper import normalize_path

            db = DatabaseManager()
            db.clear_index()

            total_files = 0
            batch = []
            batch_size = 500
            dir_sizes = {}

            normalized_dirs = [normalize_path(d) for d in self._search_dirs]

            for base_dir in normalized_dirs:
                if not os.path.isdir(base_dir):
                    continue

                for root, dirs, files in os.walk(base_dir):
                    dirs[:] = [d for d in dirs
                              if d not in self._exclude_dirs
                              and not d.startswith('.')
                              and not d.startswith('$')]

                    for d in dirs:
                        try:
                            dir_path = os.path.join(root, d)
                            try:
                                dir_items = os.listdir(dir_path)
                                item_count = len(dir_items)
                            except (PermissionError, OSError):
                                item_count = 0
                            try:
                                dir_stat = os.stat(dir_path)
                                dir_mtime = dir_stat.st_mtime
                            except (PermissionError, OSError):
                                dir_mtime = 0
                            batch.append((dir_path, d, None, 0, dir_mtime, 1, item_count))
                            total_files += 1
                            dir_sizes.setdefault(dir_path, 0)
                        except Exception:
                            continue

                    for filename in files:
                        try:
                            file_path = os.path.join(root, filename)
                            stat = os.stat(file_path)
                            _, ext = os.path.splitext(filename)

                            batch.append((
                                file_path,
                                filename,
                                ext.lower() if ext else None,
                                stat.st_size,
                                stat.st_mtime,
                                0,
                                0
                            ))
                            total_files += 1

                            parent = root
                            dir_sizes.setdefault(parent, 0)
                            dir_sizes[parent] += stat.st_size

                            if len(batch) >= batch_size:
                                db.insert_file_batch(batch)
                                batch.clear()
                                self.progress.emit(total_files)
                        except Exception:
                            continue

            if batch:
                db.insert_file_batch(batch)

            all_dirs_sorted = sorted(dir_sizes.keys(), key=lambda p: -p.count(os.sep))
            for dir_path in all_dirs_sorted:
                parent = os.path.dirname(dir_path)
                if parent and parent != dir_path:
                    dir_sizes.setdefault(parent, 0)
                    dir_sizes[parent] += dir_sizes[dir_path]

            if dir_sizes:
                db.update_folder_sizes(dir_sizes)

            elapsed = time.time() - start_time
            self.finished.emit(total_files, elapsed)
        except Exception as e:
            self.error.emit(str(e))


class SearchWorker(QThread):
    finished = Signal(object)

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self._query = query
        self._engine = SearchEngine()

    def run(self):
        try:
            results = self._engine.search(self._query)
            self.finished.emit(results)
        except Exception:
            self.finished.emit([])

    def cancel(self):
        self._engine.cancel()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._scan_worker = None
        self._search_worker = None
        self._current_file_types = []
        self._exclude_known_types = False
        self._all_results = []
        self._init_ui()
        self._connect_signals()
        self._check_index_on_startup()

    def _init_ui(self):
        self.setWindowTitle("FileFinder - 本地文件搜索工具")
        self.setMinimumSize(900, 600)
        self.resize(1100, 720)

        icon = QIcon("icons/search-alt.svg")
        self.setWindowIcon(icon)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QWidget {
                font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
            }
        """)

        self._init_menu_bar()

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.search_bar = SearchBar()
        main_layout.addWidget(self.search_bar)

        self.filter_bar = FilterBar()
        main_layout.addWidget(self.filter_bar)

        content_split = QSplitter(Qt.Orientation.Horizontal)
        content_split.setContentsMargins(0, 0, 0, 0)

        self.result_list = ResultListWidget()

        self.preview_panel = PreviewPanel()
        self.preview_panel.setMinimumWidth(200)

        content_split.addWidget(self.result_list)
        content_split.addWidget(self.preview_panel)
        content_split.setStretchFactor(0, 3)
        content_split.setStretchFactor(1, 2)
        content_split.setSizes([700, 400])
        content_split.setHandleWidth(2)
        content_split.setStyleSheet("""
            QSplitter::handle {
                background-color: #E5E7EB;
            }
            QSplitter::handle:hover {
                background-color: #7C3AED;
            }
        """)

        main_layout.addWidget(content_split, 1)

        self._init_status_bar()

        central.setLayout(main_layout)

    def _init_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(STATUS_BAR_STYLE)
        self.setStatusBar(self.status_bar)

        self.status_left = QLabel("就绪")
        self.status_left.setStyleSheet("color: #6B7280; font-size: 12px;")

        self.status_separator1 = QLabel("|")
        self.status_separator1.setStyleSheet(STATUS_DIVIDER)

        self.status_size = QLabel("")
        self.status_separator2 = QLabel("|")
        self.status_separator2.setStyleSheet(STATUS_DIVIDER)
        self.status_date = QLabel("")
        self.status_separator3 = QLabel("|")
        self.status_separator3.setStyleSheet(STATUS_DIVIDER)
        self.status_path = QLabel("")

        hide_detail_widgets = [
            self.status_separator1, self.status_separator2, self.status_separator3,
            self.status_size, self.status_date, self.status_path
        ]
        for w in hide_detail_widgets:
            w.setVisible(False)

        self.status_right = QLabel("")

        self.status_bar.addWidget(self.status_left, 1)
        self.status_bar.addWidget(self.status_separator1)
        self.status_bar.addWidget(self.status_size)
        self.status_bar.addWidget(self.status_separator2)
        self.status_bar.addWidget(self.status_date)
        self.status_bar.addWidget(self.status_separator3)
        self.status_bar.addWidget(self.status_path)
        self.status_bar.addWidget(self.status_right)

    def _init_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #FAFAFA;
                border-bottom: 1px solid #E5E7EB;
                padding: 2px 8px;
                font-size: 13px;
            }
            QMenuBar::item {
                padding: 4px 12px;
                border-radius: 4px;
                color: #4B5563;
            }
            QMenuBar::item:selected {
                background-color: #F3F4F6;
                color: #1F2937;
            }
            QMenu {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QMenu::item {
                padding: 8px 32px 8px 36px;
                border-radius: 8px;
                font-size: 13px;
                color: #1F2937;
                background: transparent;
            }
            QMenu::item:selected {
                background-color: #F5F3FF;
                color: #7C3AED;
            }
            QMenu::icon {
                padding-left: 10px;
            }
            QMenu::separator {
                height: 1px;
                background: #E5E7EB;
                margin: 3px 8px;
            }
        """)

        file_menu = RoundedMenu(self)
        file_menu.setTitle("文件")
        scan_action = QAction(QIcon("icons/refresh.svg"), "重新扫描", self)
        scan_action.triggered.connect(self._on_scan_requested)
        file_menu.addAction(scan_action)
        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        menubar.addMenu(file_menu)

        settings_menu = RoundedMenu(self)
        settings_menu.setTitle("设置")
        preferences_action = QAction(QIcon("icons/settings.svg"), "偏好设置", self)
        preferences_action.triggered.connect(self._on_open_settings)
        settings_menu.addAction(preferences_action)
        menubar.addMenu(settings_menu)

        help_menu = RoundedMenu(self)
        help_menu.setTitle("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        menubar.addMenu(help_menu)

    def _on_open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _on_about(self):
        QMessageBox.about(self, "关于 FileFinder",
                          "FileFinder v1.0\n\n一款轻量级的本地文件搜索桌面工具\n"
                          "帮助您通过文件名或文件内容快速定位电脑中的文件。")

    def _connect_signals(self):
        self.search_bar.search_triggered.connect(self._on_search)
        self.result_list.result_selected.connect(self._on_result_selected)
        self.result_list.status_info_requested.connect(self._update_status_info)
        self.filter_bar.filter_changed.connect(self._on_filter_changed)
        self.filter_bar.scope_changed.connect(self._on_scope_changed)
        self.filter_bar.scan_requested.connect(self._on_scan_requested)

    def _check_index_on_startup(self):
        QTimer.singleShot(50, self._deferred_index_check)

    def _deferred_index_check(self):
        self.filter_bar._check_index()
        count = self.filter_bar.get_indexed_count()
        if count == 0:
            self.status_left.setText("就绪 - 请点击[重新扫描]开始")
        else:
            self.status_left.setText(f"就绪 - 已索引 {count:,} 个文件")
        self.search_bar.set_focus()

    def _on_scan_requested(self):
        exclude_dirs = [
            'node_modules', '__pycache__', '.git', '.svn', '.hg',
            '.venv', 'venv', '.tox', '.eggs', 'build', 'dist',
            '.idea', '.vscode', '.vs', '$RECYCLE.BIN',
            'System Volume Information', 'Windows', 'Program Files',
            'Program Files (x86)', 'ProgramData'
        ]

        self.status_left.setText("正在扫描...")
        self.status_right.setText("")

        self._scan_worker = ScanWorker(
            self.filter_bar.get_search_dirs(),
            exclude_dirs
        )
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

    def _on_scan_progress(self, count: int):
        self.status_left.setText(f"正在扫描... 已发现 {count:,} 个文件")

    def _on_scan_finished(self, total_files: int, elapsed: float):
        self.filter_bar.reset_scan_state(total_files)
        self.status_left.setText(f"扫描完成 - 共 {total_files:,} 个文件，耗时 {elapsed:.1f} 秒")
        self.status_right.setText("")

    def _on_scan_error(self, err_msg: str):
        self.filter_bar.reset_scan_state()
        self.status_left.setText("扫描失败")
        QMessageBox.critical(self, "扫描错误", f"扫描过程中发生错误：\n{err_msg}")

    def _on_search(self, name_query, content_query):
        if not name_query.strip() and not content_query.strip():
            return

        if self.filter_bar.get_indexed_count() == 0:
            reply = QMessageBox.question(
                self, "尚未扫描",
                "尚未建立文件索引。是否立即扫描磁盘？\n\n"
                "扫描后搜索速度将大幅提升，只需扫描一次即可。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_scan_requested()
            return

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.terminate()
            self._search_worker.wait()

        case_sensitive = self.search_bar.is_case_sensitive()

        query = SearchQuery(
            name_query=name_query if name_query else None,
            content_query=content_query if content_query else None,
            content_mode='keyword',
            include_dirs=self.filter_bar.get_search_dirs(),
            exclude_dirs=get_exclude_dirs(),
            max_results=get_max_results(),
            name_case_sensitive=case_sensitive,
            content_case_sensitive=case_sensitive,
            file_types=[],
            exclude_file_types=[]
        )

        self.status_left.setText("正在搜索...")
        self.status_right.setText("")
        self.result_list.clear_results()
        self.result_list.show_search_progress("正在搜索...")

        self._search_worker = SearchWorker(query)
        self._search_worker.finished.connect(self._on_search_finished)
        self._search_worker.start()

    def _on_search_finished(self, results):
        self._all_results = results
        self._apply_current_filter()

    def _apply_current_filter(self):
        self.result_list.hide_search_progress()

        filtered = self._all_results

        if self._exclude_known_types:
            from models.file_item import FILE_TYPE_MAP
            known_exts = set(FILE_TYPE_MAP.keys())
            filtered = [r for r in filtered
                       if r.file_item.extension.lower() not in known_exts
                       and not r.file_item.is_directory]
        elif self._current_file_types:
            filtered = [r for r in filtered
                       if r.file_item.extension.lower() in self._current_file_types
                       and not r.file_item.is_directory]
        elif self.filter_bar.get_selected_category() == 'folder':
            filtered = [r for r in filtered if r.file_item.is_directory]

        self.result_list.clear_results()
        for result in filtered:
            self.result_list.add_result(result)

        count = len(filtered)
        if count == 0:
            self.status_left.setText("未找到匹配的文件")
            self.status_right.setText("")
        else:
            self.status_left.setText(f"找到 {count} 个结果")
            self.status_right.setText(f"共 {count} 项")
            self.result_list.setFocus()

    def _on_result_selected(self, result):
        self.preview_panel.show_result(result)

    def _update_status_info(self, result):
        file_item = result.file_item

        self.status_size.setText(f"大小：{file_item.size_display}")
        self.status_date.setText(f"修改时间：{file_item.modified_date}")
        self.status_path.setText(f"路径：{file_item.path}")

        for w in [self.status_separator1, self.status_size,
                  self.status_separator2, self.status_date,
                  self.status_separator3, self.status_path]:
            w.setVisible(True)

    def _on_filter_changed(self, category):
        from models.file_item import FILE_TYPE_MAP
        self._current_file_types = []
        self._exclude_known_types = False
        if category == 'other':
            self._exclude_known_types = True
        elif category == 'folder':
            pass
        elif category != 'all':
            for ext, ftype in FILE_TYPE_MAP.items():
                if ftype == category:
                    self._current_file_types.append(ext)

        if self._all_results:
            self._apply_current_filter()

    def _on_scope_changed(self, dirs):
        pass

    def closeEvent(self, event):
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.terminate()
            self._scan_worker.wait()

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.terminate()
            self._search_worker.wait()

        from database.db_manager import DatabaseManager
        DatabaseManager().close()

        super().closeEvent(event)
