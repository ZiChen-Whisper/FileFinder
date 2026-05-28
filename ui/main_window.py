import os
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QStatusBar,
                             QLabel, QHBoxLayout, QMessageBox, QSplitter, QFrame,
                             QStackedWidget, QSizePolicy, QDialog, QProgressBar,
                             QPushButton, QMenu, QScrollArea,
                             QApplication)
from PySide6.QtCore import Qt, Signal, QTimer, QFileSystemWatcher
from PySide6.QtGui import QIcon, QAction
from models.search_query import SearchQuery
from core.search_engine import SearchEngine
from core.scan_worker import ScanWorker
from core.search_worker import SearchWorker
from .widgets import SearchBar, ResultListWidget, FilterBar, PreviewPanel, RoundedMenu
from .widgets.filter_bar import DirListWidget
from .widgets.common_widgets import LoadingSpinner, RoundedPanel
from .widgets.search_scope_panel import SearchScopePanel
from .dialogs import SettingsDialog, AboutDialog
from .pages.welcome_page import WelcomePage
from .pages.scan_progress import ScanProgressDialog
from .style_constants import COLORS, FONT, RADIUS, BTN, DIALOG, TRANSITION
from .modern_dialog import ModernDialogBase, ModernMessageBox, styled_msg_box
from .style_manager import (
    scrollbar_style, status_bar_style, status_divider_style,
    menubar_style, menu_style,
)
from config import (get_exclude_dirs, get_max_results, is_first_launch,
                    get_scanned_dirs, save_scanned_dirs, load_config, save_config,
                    get_default_search_dirs, reset_all_settings,
                    SCAN_STATUS_COMPLETE, SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED,
                    SCAN_STATUS_SCANNING, set_scan_status, set_scan_status_batch,
                    get_scan_status)
from constants import (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, WINDOW_MIN_WIDTH,
                       WINDOW_MIN_HEIGHT, PREVIEW_PANEL_MIN_WIDTH, CONTENT_MAX_FILE_SIZE_MB,
                       BACKGROUND_TASK_WORKERS, FS_REFRESH_DEBOUNCE_MS, FILTER_DEBOUNCE_MS,
                       INITIAL_DISPLAY_LIMIT)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    _fs_paths_ready = Signal(list)
    _startup_sync_done = Signal(int, int, int)  # added, deleted, updated

    def __init__(self):
        super().__init__()
        self._scan_worker = None
        self._search_worker = None
        self._current_file_types = []
        self._exclude_known_types = False
        self._all_results = []
        self._selected_dirs = set()
        self._fs_watcher = QFileSystemWatcher(self)
        self._fs_watcher.directoryChanged.connect(self._on_fs_directory_changed)
        self._fs_watcher.fileChanged.connect(self._on_fs_file_changed)
        self._fs_refresh_timer = QTimer(self)
        self._fs_refresh_timer.setSingleShot(True)
        self._fs_refresh_timer.setInterval(FS_REFRESH_DEBOUNCE_MS)
        self._fs_refresh_timer.timeout.connect(self._on_fs_refresh_timeout)
        self._pending_fs_changes = set()
        self._pending_file_changes = set()
        self._is_first_launch = is_first_launch()
        self._has_searched = False
        self._fs_paths_ready.connect(self._apply_fs_watcher_paths)
        self._startup_sync_done.connect(self._on_startup_sync_done)
        self._init_ui()
        self._connect_signals()
        self._check_index_on_startup()

    def _init_ui(self):
        self.setWindowTitle("FileFinder - 本地文件搜索工具")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        icon = QIcon("icons/FileFinder.png")
        self.setWindowIcon(icon)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS.BG_PRIMARY};
            }}
            QWidget {{
                font-family: {FONT.FAMILY};
            }}
        """ + scrollbar_style())

        self._init_menu_bar()

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._stacked = QStackedWidget()
        main_layout.addWidget(self._stacked)

        self._welcome_page = WelcomePage()
        self._scan_progress_page = ScanProgressDialog()
        self._main_page = self._create_main_page()

        self._stacked.addWidget(self._welcome_page)
        self._stacked.addWidget(self._scan_progress_page)
        self._stacked.addWidget(self._main_page)

        self._init_status_bar()

        central.setLayout(main_layout)

    def _create_main_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_bar = SearchBar()
        layout.addWidget(self.search_bar)

        content_split = QSplitter(Qt.Orientation.Horizontal)
        content_split.setContentsMargins(0, 8, 8, 8)
        content_split.setChildrenCollapsible(False)

        left_panel = QWidget()
        left_panel.setMinimumWidth(540)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(8, 0, 8, 0)
        left_layout.setSpacing(4)

        settings_wrapper = QWidget()
        settings_wrapper_layout = QVBoxLayout(settings_wrapper)
        settings_wrapper_layout.setContentsMargins(16, 0, 16, 0)
        settings_wrapper_layout.setSpacing(0)
        settings_wrapper_layout.addWidget(self.search_bar.get_settings_widget())
        left_layout.addWidget(settings_wrapper)

        self.filter_bar = FilterBar()
        left_layout.addWidget(self.filter_bar)

        self.result_list = ResultListWidget()

        self._loading_overlay = QFrame(self.result_list)
        self._loading_overlay.setStyleSheet(f"QFrame {{ background-color: {COLORS.BG_PRIMARY}; }}")
        overlay_layout = QVBoxLayout(self._loading_overlay)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.setSpacing(12)

        self._loading_spinner = LoadingSpinner(self._loading_overlay)
        loading_label = QLabel("正在初始化...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet(f"color: {COLORS.TEXT_TERTIARY}; font-size: {DIALOG.BODY_FONT_SIZE}; border: none; background: transparent;")

        overlay_layout.addStretch()
        overlay_layout.addWidget(self._loading_spinner, 0, Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(loading_label, 0, Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addStretch()

        left_layout.addWidget(self.result_list, 1)
        left_panel.setLayout(left_layout)

        right_panel = RoundedPanel()
        right_panel.setMinimumWidth(360)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(1, 1, 1, 1)
        right_layout.setSpacing(0)

        self._search_scope_panel = SearchScopePanel()
        right_layout.addWidget(self._search_scope_panel)

        self.preview_panel = PreviewPanel()
        self.preview_panel.setMinimumWidth(PREVIEW_PANEL_MIN_WIDTH)
        right_layout.addWidget(self.preview_panel, 1)

        right_panel.setLayout(right_layout)

        content_split.addWidget(left_panel)
        content_split.addWidget(right_panel)
        content_split.setStretchFactor(0, 3)
        content_split.setStretchFactor(1, 2)
        content_split.setSizes([660, 440])
        content_split.setHandleWidth(4)
        content_split.setStyleSheet(f"""
            QSplitter::handle {{
                background: transparent;
            }}
            QSplitter::handle:hover {{
                background: transparent;
            }}
        """)

        layout.addWidget(content_split, 1)

        page.setLayout(layout)
        return page

    def _init_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(status_bar_style())
        self.setStatusBar(self.status_bar)

        self.status_left = QLabel("就绪")
        self.status_left.setStyleSheet(f"color: {COLORS.TEXT_TERTIARY}; font-size: {BTN.SMALL_FONT_SIZE};")

        self.status_separator1 = QLabel("|")
        self.status_separator1.setStyleSheet(status_divider_style())

        self.status_size = QLabel("")
        self.status_separator2 = QLabel("|")
        self.status_separator2.setStyleSheet(status_divider_style())
        self.status_date = QLabel("")
        self.status_separator3 = QLabel("|")
        self.status_separator3.setStyleSheet(status_divider_style())
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

    def _show_loading(self):
        if self._loading_overlay:
            self._loading_overlay.setGeometry(self.result_list.rect())
            self._loading_overlay.raise_()
            self._loading_overlay.show()
            self._loading_spinner.start()

    def _hide_loading(self):
        if self._loading_spinner:
            self._loading_spinner.stop()
        if self._loading_overlay:
            self._loading_overlay.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_loading_overlay') and self._loading_overlay.isVisible():
            self._loading_overlay.setGeometry(self.result_list.rect())

    def _init_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(menubar_style())

        file_menu = RoundedMenu(self)
        file_menu.setTitle("文件")
        file_menu.setStyleSheet(menu_style(rounded=True))
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        menubar.addMenu(file_menu)

        settings_menu = RoundedMenu(self)
        settings_menu.setTitle("设置")
        settings_menu.setStyleSheet(menu_style(rounded=True))
        preferences_action = QAction("偏好设置", self)
        preferences_action.triggered.connect(self._on_open_settings)
        settings_menu.addAction(preferences_action)
        settings_menu.addSeparator()
        reset_action = QAction("恢复默认设置", self)
        reset_action.triggered.connect(self._on_reset_settings)
        settings_menu.addAction(reset_action)
        menubar.addMenu(settings_menu)

        help_menu = RoundedMenu(self)
        help_menu.setTitle("帮助")
        help_menu.setStyleSheet(menu_style(rounded=True))
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        menubar.addMenu(help_menu)

    def _on_reset_settings(self):
        reply = styled_msg_box(
            self, QMessageBox.Icon.Warning,
            "恢复默认设置",
            "此操作将删除所有用户自定义设置，包括：\n\n"
            "  - 所有搜索路径的记录\n"
            "  - 所有用户偏好设置\n"
            "  - 搜索历史记录\n"
            "  - 文件索引数据库\n"
            "  - 自定义搜索范围\n\n"
            "此操作不可恢复！确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
            self._scan_worker.wait(3000)
            if self._scan_worker.isRunning():
                self._scan_worker.terminate()
                self._scan_worker.wait()

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.results_ready.disconnect(self._on_search_finished)
            self._search_worker.progress_updated.disconnect(self._on_search_progress)
            self._search_worker.result_found.disconnect(self._on_search_result_found)
            self._search_worker.file_searching.disconnect(self._on_file_searching)
            self._search_worker.wait()

        reset_all_settings()

        self._all_results = []
        self._current_file_types = []
        self._exclude_known_types = False
        self._selected_dirs = set()
        self._is_first_launch = True
        self._has_searched = False

        self.result_list.clear_results()
        self.preview_panel.clear_preview()
        self.filter_bar._reload_scope()
        self._search_scope_panel.reset()
        self._search_scope_panel._reload_scope()
        self._welcome_page.reset()

        self.search_bar.search_input.clear()
        self.search_bar._set_mode('name')
        self.search_bar.case_sensitive_checkbox.setChecked(False)

        for key, btn in self.filter_bar.type_buttons.items():
            btn.setChecked(key == 'all')
        self.filter_bar._selected_category = 'all'
        self.filter_bar._selected_sub_extensions = set()
        self.filter_bar._sub_filter_widget.setVisible(False)

        self._switch_to_welcome()

        styled_msg_box(
            self, QMessageBox.Icon.Information,
            "操作成功", "所有设置已恢复为默认值。\n应用将重置为首次启动状态。"
        )

    def _on_open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _on_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def _connect_signals(self):
        self._welcome_page.scan_requested_with_dirs.connect(self._start_scan_with_dirs)
        self._scan_progress_page.scan_cancelled.connect(self._on_scan_cancelled)
        self._search_scope_panel.scope_changed.connect(self._on_scope_changed)
        self._search_scope_panel.scan_unscanned_requested.connect(self._on_scan_unscanned)
        self.search_bar.search_triggered.connect(self._on_search)
        self.search_bar.search_mode_changed.connect(self.filter_bar.set_search_mode)
        self.result_list.result_selected.connect(self._on_result_selected)
        self.result_list.status_info_requested.connect(self._update_status_info)
        self.filter_bar.filter_changed.connect(self._on_filter_changed)
        self.filter_bar.sort_changed.connect(self._on_sort_changed)
        self.filter_bar.sort_order_changed.connect(self._on_sort_order_changed)
        self._search_scope_panel.scan_requested.connect(self._on_scan_requested)
        QApplication.instance().installEventFilter(self)

    def _check_index_on_startup(self):
        if self._is_first_launch:
            self._switch_to_welcome()
            return

        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        count = db.get_index_count()

        if count == 0:
            scanned = get_scanned_dirs()
            if not scanned:
                self._switch_to_welcome()
                return

        self._switch_to_main()
        self._show_loading()
        QTimer.singleShot(100, self._deferred_index_check)

    def _switch_to_welcome(self):
        self._stacked.setCurrentWidget(self._welcome_page)
        self.status_left.setText("请选择要扫描的目录")
        self.status_right.setText("")

    def _switch_to_main(self):
        self._stacked.setCurrentWidget(self._main_page)
        self._hide_loading()
        scanned = get_scanned_dirs()
        if scanned:
            self._search_scope_panel.set_scanned_dirs(scanned)
        self._search_scope_panel.update_scope_info(self._search_scope_panel.get_indexed_count())
        # 显示空闲引导页面（不自动加载所有文件）
        if not hasattr(self, '_has_searched'):
            self._has_searched = False
        if not self._has_searched:
            self.result_list.clear_results()
            self.result_list.show_idle_state()
            self.preview_panel.set_result(None)
        elif not self._all_results and self._search_scope_panel.get_indexed_count() > 0:
            self._load_all_files()

    def _switch_to_scan_progress(self):
        self._scan_progress_page.reset_state()
        self._scan_progress_page.start_scan()
        self._stacked.setCurrentWidget(self._scan_progress_page)

    def _deferred_index_check(self):
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        count = db.get_index_count()
        self._search_scope_panel._indexed_count = count
        if count > 0 and not self._search_scope_panel._scanned_dirs:
            self._search_scope_panel._scanned_dirs = list(self._search_scope_panel.get_search_dirs())
        self._search_scope_panel._update_scope_info()
        self._search_scope_panel._update_status_dot()
        self._search_scope_panel._update_scan_btn_state()
        self._search_scope_panel.update_scope_info(count)
        if count == 0:
            self.status_left.setText("就绪 - 请点击[重新扫描]开始")
        else:
            self.status_left.setText(f"就绪 - 已索引 {count:,} 个文件")
            # 启动后台增量同步，检测程序关闭期间的文件变化
            self._startup_sync_async()
        self._hide_loading()
        self.search_bar.set_focus()

    def _start_scan_with_dirs(self, dirs: list):
        config = load_config()
        current_dirs = config.get("search", {}).get("default_dirs", [])
        for d in dirs:
            if d not in current_dirs:
                current_dirs.append(d)
        config["search"]["default_dirs"] = current_dirs
        save_config(config)

        self._search_scope_panel.set_search_dirs(get_default_search_dirs())
        self._search_scope_panel._scanned_dirs = list(current_dirs)
        self._search_scope_panel._search_dirs = list(current_dirs)

        self._switch_to_scan_progress()
        self._do_scan(list(current_dirs))

    def _on_scan_requested(self):
        self._switch_to_scan_progress()
        self.status_left.setText("正在扫描...")
        self.status_right.setText("")

        all_dirs = self._search_scope_panel.get_all_scanned_dirs()
        if not all_dirs:
            all_dirs = self._search_scope_panel.get_search_dirs()

        # 只扫描未完成的新增目录，已完成的目录不需要重新扫描
        from config import get_scan_status, SCAN_STATUS_COMPLETE
        dirs_to_scan = []
        for d in all_dirs:
            status = get_scan_status(d)
            if status != SCAN_STATUS_COMPLETE:
                dirs_to_scan.append(d)

        # 如果没有新增目录，则扫描所有目录（重新扫描）
        if not dirs_to_scan:
            dirs_to_scan = all_dirs

        self._do_scan(dirs_to_scan)

    def _do_scan(self, search_dirs: list, exclude_dirs: list = None):
        if exclude_dirs is None:
            exclude_dirs = get_exclude_dirs()

        self._scan_worker = ScanWorker(search_dirs, exclude_dirs)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.file_found.connect(self._on_scan_file_found)
        self._scan_worker.content_index_progress.connect(self._on_content_index_progress)
        self._scan_worker.start()

    def _on_scan_progress(self, count: int, percentage: int, current_dir: str):
        self._scan_progress_page.update_progress(count, percentage if percentage >= 0 else None, current_dir)
        self.status_left.setText(f"正在扫描... 已发现 {count:,} 个文件")

    def _on_content_index_progress(self, indexed: int, total: int, current_file: str):
        """处理内容索引进度信号。"""
        if total > 0:
            pct = int(indexed / total * 100)
            self._scan_progress_page.update_progress(
                indexed, pct,
                f"正在索引内容: {os.path.basename(current_file)}" if current_file else "正在索引内容..."
            )
            self.status_left.setText(f"正在索引内容... {indexed:,}/{total:,} 个文件")

    def _on_scan_file_found(self, file_path: str):
        self._scan_progress_page.append_file_log(file_path)

    def _on_scan_finished(self, total_files: int, elapsed: float):
        self._scan_progress_page.set_finishing()

        # 获取数据库中的实际索引总数（而非仅本次扫描数量）
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        actual_index_count = db.get_index_count()
        content_index_count = db.get_content_index_count()

        self._search_scope_panel.reset_scan_state(actual_index_count)

        all_dirs = self._search_scope_panel.get_all_scanned_dirs()
        if not all_dirs:
            all_dirs = self._search_scope_panel.get_search_dirs()
        save_scanned_dirs(all_dirs)
        self._search_scope_panel.set_scanned_dirs(all_dirs)
        self._search_scope_panel.update_scope_info(actual_index_count)

        config = load_config()
        existing_dirs = set(config.get("search", {}).get("default_dirs", []))
        for d in all_dirs:
            existing_dirs.add(d)
        config.setdefault("search", {})["default_dirs"] = list(existing_dirs)
        save_config(config)
        self._search_scope_panel.set_search_dirs(list(existing_dirs))
        self._search_scope_panel._scanned_dirs = list(existing_dirs)
        self._search_scope_panel._search_dirs = list(existing_dirs)

        # 状态栏显示文件索引数 + 内容索引数
        status_text = f"扫描完成 - 共 {actual_index_count:,} 个文件"
        if content_index_count > 0:
            status_text += f"，已索引 {content_index_count:,} 个文件内容"
        status_text += f"，耗时 {elapsed:.1f} 秒"
        self.status_left.setText(status_text)
        self.status_right.setText("")

        self._update_fs_watcher_async()

        self._is_first_launch = False

        self._hide_loading()
        QTimer.singleShot(800, self._switch_to_main)
        QTimer.singleShot(1200, self._load_all_files)

    def _on_scan_error(self, err_msg: str):
        self._scan_progress_page.set_error(err_msg)
        self._search_scope_panel.reset_scan_state()
        self.status_left.setText("扫描失败")
        logger.error(f"扫描失败: {err_msg}")

    def _on_scan_cancelled(self):
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
            self._scan_worker.wait(1000)
            if self._scan_worker.isRunning():
                logger.warning("扫描线程未在1秒内响应取消，强制终止")
                self._scan_worker.terminate()
                self._scan_worker.wait(2000)

        from database.db_manager import DatabaseManager
        DatabaseManager()._search_cache.invalidate()
        self._search_scope_panel.reset_scan_state()
        self.status_left.setText("扫描已取消")
        if self._is_first_launch:
            self._switch_to_welcome()
        else:
            self._switch_to_main()

    def _on_scan_unscanned(self, unscanned_dirs: list):
        reply = styled_msg_box(
            self, QMessageBox.Icon.Question,
            "扫描未扫描目录",
            "以下目录尚未扫描：\n\n" +
            "\n".join(f"  - {d}" for d in unscanned_dirs) +
            "\n\n是否立即扫描这些目录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._start_scan_with_dirs(unscanned_dirs)

    def _load_all_files(self):
        if self._search_worker and self._search_worker.isRunning():
            return
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        all_dirs = self._search_scope_panel.get_all_scanned_dirs()
        if not all_dirs:
            all_dirs = self._search_scope_panel.get_search_dirs()
        self._selected_dirs = set(self._search_scope_panel.get_selected_dirs())

        db_results = db.search_files(
            pattern="",
            case_sensitive=False,
            max_results=get_max_results()
        )

        from models.file_item import FileItem
        from models.search_result import SearchResult
        from datetime import datetime
        results = []
        for row in db_results:
            try:
                item = FileItem(
                    path=row["path"],
                    name=row["name"],
                    size=row["size"],
                    modified_time=datetime.fromtimestamp(row["modified_time"]),
                    extension=row["extension"] or "",
                    is_directory=bool(row.get("is_directory", 0)),
                    item_count=row.get("item_count", 0)
                )
                if self._selected_dirs and not any(
                    os.path.normcase(os.path.normpath(item.path)).startswith(
                        os.path.normcase(os.path.normpath(d)) + os.sep
                    ) or os.path.normcase(os.path.normpath(item.path)) == os.path.normcase(os.path.normpath(d))
                    for d in self._selected_dirs
                ):
                    continue
                results.append(SearchResult(file_item=item, match_reason='name', name_match_score=0))
            except Exception:
                continue

        self._all_results = results
        self._apply_current_filter()

    def _on_search(self, name_query, content_query):
        if not name_query.strip() and not content_query.strip():
            return

        has_name = bool(name_query.strip())
        has_content = bool(content_query.strip())

        # 文件名搜索需要索引，纯内容搜索不需要索引但需要搜索目录
        if has_name and self._search_scope_panel.get_indexed_count() == 0:
            reply = styled_msg_box(
                self, QMessageBox.Icon.Question,
                "尚未扫描",
                "尚未建立文件索引。是否立即扫描磁盘？\n\n"
                "扫描后搜索速度将大幅提升，只需扫描一次即可。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_scan_requested()
            return

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            # 断开旧 worker 的信号，使其结果不会干扰新搜索
            self._search_worker.results_ready.disconnect(self._on_search_finished)
            self._search_worker.progress_updated.disconnect(self._on_search_progress)
            self._search_worker.result_found.disconnect(self._on_search_result_found)
            self._search_worker.file_searching.disconnect(self._on_file_searching)
            # 等待旧线程结束，避免 "QThread: Destroyed while thread is still running"
            self._search_worker.wait()

        case_sensitive = self.search_bar.is_case_sensitive()
        all_dirs = self._search_scope_panel.get_all_scanned_dirs()
        selected_dirs = self._search_scope_panel.get_selected_dirs()
        self._selected_dirs = set(selected_dirs)

        if not all_dirs and not self._search_scope_panel.get_search_dirs():
            styled_msg_box(
                self, QMessageBox.Icon.Warning,
                "无可搜索目录",
                "当前没有可搜索的目录。请先添加扫描路径并完成扫描。"
            )
            return

        query = SearchQuery(
            name_query=name_query if name_query else None,
            name_mode=self.search_bar.get_name_mode(),
            content_query=content_query if content_query else None,
            content_mode='keyword',
            include_dirs=selected_dirs if selected_dirs else self._search_scope_panel.get_search_dirs(),
            exclude_dirs=get_exclude_dirs(),
            max_results=get_max_results(),
            name_case_sensitive=case_sensitive,
            content_case_sensitive=case_sensitive,
            file_types=[],
            exclude_file_types=[]
        )

        self.status_left.setText("正在搜索...")
        self.status_right.setText("")
        self._hide_loading()
        self._has_searched = True
        self._all_results = []
        self.result_list.clear_results()
        self.result_list.hide_idle_state()
        self.result_list.show_search_progress("正在搜索...")

        self._search_worker = SearchWorker(query)
        self._search_worker.results_ready.connect(self._on_search_finished)
        self._search_worker.progress_updated.connect(self._on_search_progress)
        self._search_worker.result_found.connect(self._on_search_result_found)
        self._search_worker.file_searching.connect(self._on_file_searching)
        self._search_worker.start()

    def _on_search_progress(self, processed: int, total: int):
        """处理搜索进度更新信号"""
        self.result_list.update_search_progress(processed, total)

    def _on_search_result_found(self, result):
        """处理实时搜索结果信号（流式显示）"""
        pass

    def _on_file_searching(self, file_path: str):
        """处理当前搜索文件信号"""
        self.result_list.update_searching_file(file_path)

    def _on_search_finished(self, results):
        self._all_results = results
        self._apply_current_filter()

    def _apply_current_filter(self):
        self.result_list.hide_search_progress()

        filtered = self._all_results

        if self._selected_dirs:
            filtered = [r for r in filtered
                       if self._is_path_in_selected_dirs(r.file_item.path)]

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

        filtered = self._sort_results(filtered)

        self.result_list.set_results(filtered)

        count = len(filtered)
        if count == 0:
            self.status_left.setText("未找到匹配的文件")
            self.status_right.setText("")
            if self._all_results is not None and len(self._all_results) > 0:
                self.result_list.show_empty_state("当前筛选下无匹配文件")
            else:
                self.result_list.show_empty_state("未找到匹配文件")
        else:
            self.result_list.hide_empty_state()
            self.status_left.setText(f"找到 {count} 个结果")
            self.status_right.setText(f"共 {count} 项")
            self.result_list.setFocus()

    def _on_result_selected(self, result):
        # 传递搜索关键词到预览面板以实现高亮
        content_query = self.search_bar.get_content_query() if hasattr(self.search_bar, 'get_content_query') else ""
        if content_query:
            case_sensitive = self.search_bar.is_case_sensitive()
            self.preview_panel.set_search_keyword(content_query, case_sensitive)
        else:
            self.preview_panel.set_search_keyword("", False)
        self.preview_panel.set_result(result)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Space:
            focus_widget = QApplication.focusWidget()
            if focus_widget and self.result_list.isAncestorOf(focus_widget):
                self.preview_panel.activate_preview()
                return True
        return super().eventFilter(obj, event)

    def _update_status_info(self, result):
        if result is None:
            for w in [self.status_separator1, self.status_size,
                      self.status_separator2, self.status_date,
                      self.status_separator3, self.status_path]:
                w.setVisible(False)
            return

        file_item = result.file_item

        self.status_size.setText(f"大小：{file_item.size_display}")
        self.status_date.setText(f"修改时间：{file_item.modified_date}")
        self.status_path.setText(f"路径：{file_item.path}")

        for w in [self.status_separator1, self.status_size,
                  self.status_separator2, self.status_date,
                  self.status_separator3, self.status_path]:
            w.setVisible(True)

    def _on_filter_changed(self, category, sub_extensions=None):
        from models.file_item import FILE_TYPE_MAP
        self._current_file_types = []
        self._exclude_known_types = False
        if category == 'other':
            self._exclude_known_types = True
        elif category == 'folder':
            pass
        elif category != 'all':
            if sub_extensions:
                self._current_file_types = list(sub_extensions)
            else:
                for ext, ftype in FILE_TYPE_MAP.items():
                    if ftype == category:
                        self._current_file_types.append(ext)

        if self._all_results and len(self._all_results) > INITIAL_DISPLAY_LIMIT:
            self.result_list.show_search_progress("正在筛选...")
            if hasattr(self, '_filter_timer'):
                self._filter_timer.stop()
            else:
                self._filter_timer = QTimer(self)
                self._filter_timer.setSingleShot(True)
                self._filter_timer.timeout.connect(self._apply_current_filter)
            self._filter_timer.start(FILTER_DEBOUNCE_MS)
        elif self._all_results:
            self._apply_current_filter()

    def _on_scope_changed(self, dirs):
        self._selected_dirs = set(dirs)
        if self._all_results:
            self._apply_current_filter()

    def _on_sort_changed(self, mode):
        if self._all_results:
            self._apply_current_filter()

    def _on_sort_order_changed(self, ascending):
        if self._all_results:
            self._apply_current_filter()

    def _sort_results(self, results):
        sort_mode = self.filter_bar.get_sort_mode()
        ascending = self.filter_bar.is_sort_ascending()

        def _sort_key(result):
            item = result.file_item
            if sort_mode == 'name':
                return item.name.lower()
            elif sort_mode == 'modified':
                return item.modified_time.timestamp() if item.modified_time else 0
            elif sort_mode == 'size':
                return item.size
            else:
                return result.score

        return sorted(results, key=_sort_key, reverse=not ascending)

    def _is_path_in_selected_dirs(self, file_path: str) -> bool:
        if not self._selected_dirs:
            return True
        normalized = os.path.normcase(os.path.normpath(file_path))
        for d in self._selected_dirs:
            norm_d = os.path.normcase(os.path.normpath(d))
            if normalized.startswith(norm_d + os.sep) or normalized == norm_d:
                return True
        return False

    def _startup_sync_async(self):
        """在后台线程中执行启动时的增量同步。

        检测程序关闭期间发生的文件变化（新增/删除/修改），
        自动更新索引，无需用户手动重新扫描。
        """
        from concurrent.futures import ThreadPoolExecutor
        from database.db_manager import DatabaseManager

        search_dirs = self._search_scope_panel.get_search_dirs()
        if not search_dirs:
            return

        self.status_left.setText("正在同步文件变更...")

        def _do_startup_sync():
            logger.info(f"启动增量同步，搜索目录: {search_dirs}")
            db = DatabaseManager()
            indexed_paths = db.get_all_indexed_paths()
            actual_paths = set()
            changed_files = set()
            added_count = 0
            deleted_count = 0
            updated_count = 0

            # 遍历所有搜索目录，收集实际存在的文件
            for d in search_dirs:
                if not os.path.isdir(d):
                    continue
                try:
                    for root, dirs, files in os.walk(d):
                        # 跳过排除目录
                        dirs[:] = [sub for sub in dirs if sub not in get_exclude_dirs()]
                        for name in files:
                            full_path = os.path.join(root, name)
                            actual_paths.add(full_path)
                            try:
                                stat = os.stat(full_path)
                                _, ext = os.path.splitext(name)
                                existing = db.get_file_entry(full_path)
                                if existing is None:
                                    # 新增的文件
                                    db.add_file_entry(
                                        path=full_path, name=name,
                                        ext=ext.lower() if ext else "",
                                        size=stat.st_size,
                                        mtime=stat.st_mtime
                                    )
                                    added_count += 1
                                    if stat.st_size <= CONTENT_MAX_FILE_SIZE_MB * 1024 * 1024:
                                        changed_files.add(full_path)
                                else:
                                    # 检查文件是否被修改（大小或修改时间变化）
                                    old_size = existing["size"] if isinstance(existing, dict) else existing[4]
                                    old_mtime = existing["modified_time"] if isinstance(existing, dict) else existing[5]
                                    if stat.st_size != old_size or stat.st_mtime != old_mtime:
                                        db.update_file_entry(
                                            old_path=full_path, new_name=name,
                                            new_ext=ext.lower() if ext else "",
                                            new_size=stat.st_size,
                                            new_mtime=stat.st_mtime
                                        )
                                        updated_count += 1
                                        if stat.st_size <= CONTENT_MAX_FILE_SIZE_MB * 1024 * 1024:
                                            changed_files.add(full_path)
                            except (PermissionError, OSError):
                                continue
                except Exception:
                    continue

            # 删除索引中存在但文件系统中不存在的条目
            stale_paths = indexed_paths - actual_paths
            for path in stale_paths:
                try:
                    db.delete_file_entry(path)
                    deleted_count += 1
                except Exception:
                    continue

            # 后台更新内容索引
            if changed_files:
                self._update_content_index_async(db, changed_files)

            logger.info(f"启动同步完成: 新增 {added_count}, 删除 {deleted_count}, 更新 {updated_count}, 内容待更新 {len(changed_files)}")
            return added_count, deleted_count, updated_count

        def _on_sync_done(future):
            try:
                added, deleted, updated = future.result()
                self._startup_sync_done.emit(added, deleted, updated)
            except Exception as e:
                logger.warning(f"启动同步失败: {e}")
                self._startup_sync_done.emit(0, 0, 0)

        executor = ThreadPoolExecutor(max_workers=BACKGROUND_TASK_WORKERS)
        future = executor.submit(_do_startup_sync)
        future.add_done_callback(_on_sync_done)

    def _on_startup_sync_done(self, added: int, deleted: int, updated: int):
        """启动同步完成后的 UI 更新（在主线程执行）。"""
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        count = db.get_index_count()
        self._search_scope_panel.update_scope_info(count)

        parts = []
        if added > 0:
            parts.append(f"新增 {added}")
        if deleted > 0:
            parts.append(f"删除 {deleted}")
        if updated > 0:
            parts.append(f"更新 {updated}")

        if parts:
            self.status_left.setText(
                f"同步完成 - {', '.join(parts)} 个文件变更，共索引 {count:,} 个文件"
            )
            if self._all_results:
                self._refresh_current_search()
        else:
            self.status_left.setText(f"就绪 - 已索引 {count:,} 个文件")

        # 同步完成后设置文件监控
        self._update_fs_watcher_async()

    def _update_fs_watcher_async(self):
        from concurrent.futures import ThreadPoolExecutor
        search_dirs = self._search_scope_panel.get_search_dirs()

        def _collect_watch_paths():
            paths = []
            for d in search_dirs:
                if os.path.isdir(d):
                    paths.append(d)
                    try:
                        for root, dirs, _ in os.walk(d):
                            for sub in dirs:
                                full = os.path.join(root, sub)
                                paths.append(full)
                    except Exception:
                        continue
            return paths

        def _on_paths_collected(future):
            try:
                paths = future.result()
                self._fs_paths_ready.emit(paths)
            except Exception as e:
                logger.warning(f"设置文件监控失败: {e}")

        executor = ThreadPoolExecutor(max_workers=BACKGROUND_TASK_WORKERS)
        future = executor.submit(_collect_watch_paths)
        future.add_done_callback(_on_paths_collected)

    def _apply_fs_watcher_paths(self, paths: list):
        try:
            self._fs_watcher.removePaths(self._fs_watcher.directories())
            for p in paths:
                try:
                    self._fs_watcher.addPath(p)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"应用文件监控路径失败: {e}")

    def _on_fs_directory_changed(self, path: str):
        logger.info(f"检测到目录变更: {path}")
        self._pending_fs_changes.add(path)
        self._fs_refresh_timer.start()

    def _on_fs_file_changed(self, path: str):
        """文件内容修改时触发，将文件所在目录加入待同步集合。

        注意：某些编辑器保存时会先删除旧文件再创建新文件，导致 QFileSystemWatcher
        不再监控该文件。需要重新添加监控。
        """
        logger.info(f"检测到文件变更: {path}")
        # 如果文件仍然存在，重新添加监控（防止编辑器删除重建后丢失监控）
        if os.path.isfile(path):
            try:
                self._fs_watcher.addPath(path)
            except Exception:
                pass

        dir_path = os.path.dirname(path)
        if dir_path:
            self._pending_fs_changes.add(dir_path)
        # 记录具体变更的文件，用于精准更新内容索引
        self._pending_file_changes.add(path)
        self._fs_refresh_timer.start()

    def _on_fs_refresh_timeout(self):
        if not self._pending_fs_changes:
            return

        from database.db_manager import DatabaseManager
        db = DatabaseManager()

        logger.info(f"开始同步 {len(self._pending_fs_changes)} 个目录变更")

        # 收集需要更新内容索引的文件路径
        changed_files = set(self._pending_file_changes)
        self._pending_file_changes.clear()

        for dir_path in self._pending_fs_changes:
            try:
                self._sync_directory(db, dir_path, changed_files)
            except Exception as e:
                logger.debug(f"同步目录变更失败: {dir_path}, {e}")

        self._pending_fs_changes.clear()

        logger.info(f"同步完成，{len(changed_files)} 个文件需要更新内容索引")

        # 在后台线程中更新变更文件的内容索引
        if changed_files:
            self._update_content_index_async(db, changed_files)

        if self._all_results:
            self._refresh_current_search()

    def _sync_directory(self, db, dir_path: str, changed_files: set = None):
        if not os.path.isdir(dir_path):
            try:
                deleted = db.delete_entries_by_prefix(dir_path)
                if deleted > 0:
                    logger.debug(f"目录已删除，清理 {deleted} 条索引: {dir_path}")
            except Exception as e:
                logger.warning(f"清理已删除目录索引失败: {dir_path}, {e}")
            return

        try:
            current_files = set()
            new_dirs = []
            for item in os.listdir(dir_path):
                full_path = os.path.join(dir_path, item)
                current_files.add(full_path)
                try:
                    stat = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)
                    _, ext = os.path.splitext(item)
                    existing = db.get_file_entry(full_path)
                    if existing is None:
                        db.add_file_entry(
                            path=full_path, name=item, ext=ext.lower() if ext else "",
                            size=stat.st_size if not is_dir else 0,
                            mtime=stat.st_mtime, is_dir=1 if is_dir else 0
                        )
                        # 新增文件：加入内容索引待更新集合
                        if not is_dir and stat.st_size <= CONTENT_MAX_FILE_SIZE_MB * 1024 * 1024 and changed_files is not None:
                            changed_files.add(full_path)
                        # 新增子目录：记录下来，后续加入监控
                        if is_dir:
                            new_dirs.append(full_path)
                    else:
                        # 检查文件是否真的发生了变化（大小或修改时间）
                        old_size = existing["size"] if isinstance(existing, dict) else existing[4]
                        old_mtime = existing["modified_time"] if isinstance(existing, dict) else existing[5]
                        file_changed = (stat.st_size != old_size or int(stat.st_mtime) != int(old_mtime))
                        db.update_file_entry(
                            old_path=full_path, new_name=item,
                            new_ext=ext.lower() if ext else "",
                            new_size=stat.st_size if not is_dir else 0,
                            new_mtime=stat.st_mtime
                        )
                        # 只有文件确实变化时才更新内容索引
                        if file_changed and not is_dir and stat.st_size <= CONTENT_MAX_FILE_SIZE_MB * 1024 * 1024 and changed_files is not None:
                            changed_files.add(full_path)
                            logger.debug(f"文件已修改: {full_path}")
                except (PermissionError, OSError):
                    continue

            # 将新增子目录加入 QFileSystemWatcher 监控
            if new_dirs:
                self._add_fs_watcher_paths(new_dirs)

            indexed_paths = db.get_paths_by_parent(dir_path)
            for ep in indexed_paths:
                parent = os.path.dirname(ep)
                if parent == dir_path and ep not in current_files:
                    if not os.path.exists(ep):
                        db.delete_file_entry(ep)
                        # 删除文件时同时删除内容索引（delete_file_entry 已包含）
        except (PermissionError, OSError):
            pass

    def _update_content_index_for_file(self, db, file_path: str, file_name: str):
        """更新单个文件的内容索引（增量索引）。

        当文件系统监控检测到文件新增或修改时调用。

        Args:
            db: DatabaseManager 实例
            file_path: 文件路径
            file_name: 文件名
        """
        try:
            from core.file_parser import ParserRegistry
            from utils.tokenizer import tokenize_for_fts5

            parser_registry = ParserRegistry()
            ext = os.path.splitext(file_name)[1].lower()

            # 只索引可解析的文件
            if not parser_registry.can_parse(file_path):
                return

            content_text = parser_registry.parse(file_path)
            if not content_text or not content_text.strip():
                # 文件无文本内容，删除旧索引
                db.delete_content_entry(file_path)
                return

            content_tokenized = tokenize_for_fts5(content_text)
            if not content_tokenized:
                db.delete_content_entry(file_path)
                return

            db.update_content_entry(file_path, file_name, content_text, content_tokenized)
        except Exception as e:
            logger.warning(f"增量内容索引失败: {file_path}, {type(e).__name__}: {e}")

    def _add_fs_watcher_paths(self, paths: list):
        """将新路径及其子目录添加到 QFileSystemWatcher 监控列表。

        Args:
            paths: 需要添加监控的目录路径列表
        """
        all_paths = list(paths)
        # 递归收集子目录
        for p in paths:
            if os.path.isdir(p):
                try:
                    for root, dirs, _ in os.walk(p):
                        for d in dirs:
                            all_paths.append(os.path.join(root, d))
                except Exception:
                    continue

        for p in all_paths:
            if os.path.isdir(p):
                try:
                    self._fs_watcher.addPath(p)
                    logger.debug(f"新增监控目录: {p}")
                except Exception:
                    pass

    def _update_content_index_async(self, db, file_paths: set):
        """在后台线程中批量更新文件内容索引。

        Args:
            db: DatabaseManager 实例
            file_paths: 需要更新内容索引的文件路径集合
        """
        from concurrent.futures import ThreadPoolExecutor

        logger.info(f"后台更新 {len(file_paths)} 个文件的内容索引")

        def _do_update():
            updated = 0
            for file_path in file_paths:
                if not os.path.isfile(file_path):
                    continue
                try:
                    file_name = os.path.basename(file_path)
                    self._update_content_index_for_file(db, file_path, file_name)
                    updated += 1
                except Exception as e:
                    logger.warning(f"后台内容索引更新失败: {file_path}, {type(e).__name__}: {e}")
            logger.info(f"内容索引更新完成: {updated}/{len(file_paths)} 个文件")

        executor = ThreadPoolExecutor(max_workers=BACKGROUND_TASK_WORKERS)
        executor.submit(_do_update)

    def _refresh_current_search(self):
        name_query = self.search_bar.get_name_query()
        content_query = self.search_bar.get_content_query()
        if name_query.strip() or content_query.strip():
            self._on_search(name_query, content_query)

    def closeEvent(self, event):
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
            self._scan_worker.wait(1000)
            if self._scan_worker.isRunning():
                self._scan_worker.terminate()
                self._scan_worker.wait(1000)

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.wait(2000)

        from database.db_manager import DatabaseManager
        DatabaseManager().close()

        super().closeEvent(event)
