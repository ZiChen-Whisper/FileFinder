import os
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QProgressBar, QScrollArea, QButtonGroup, QDialog,
                               QMessageBox)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

from ..style_constants import COLORS, FONT, RADIUS, BTN, DIALOG
from ..style_manager import (scrollbar_style, button_primary, button_secondary,
                             button_small_primary, button_small_secondary,
                             button_tag, button_scan, button_scan_green,
                             config_button_style, progress_bar_style,
                             label_micro_style, label_caption_style)
from ..modern_dialog import styled_msg_box
from .animated_radio_button import AnimatedRadioButton
from .common_widgets import CollapsibleSection, ElidedPathLabel, HoverInfoIcon
from ..dialogs.scope_selection_dialog import ScopeSelectionDialog
from .filter_bar import _make_colored_icon, SearchScopeDialog
from utils.flow_layout import FlowLayout
from config import (get_scan_status, SCAN_STATUS_COMPLETE, SCAN_STATUS_INCOMPLETE,
                    SCAN_STATUS_FAILED, SCAN_STATUS_SCANNING, load_config, save_config,
                    get_default_search_dirs, get_scanned_dirs, save_scanned_dirs)

logger = logging.getLogger(__name__)


class SearchScopePanel(QWidget):
    scope_changed = Signal(list)
    scan_unscanned_requested = Signal(list)
    scan_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scanned_dirs = []
        self._selected_dirs = set()
        self._custom_dir_list = []
        self._scope_mode = 'all'
        self._indexed_count = 0
        self._is_scanning = False
        self._search_dirs = []
        self._init_ui()
        self._reload_scope()

    def _reload_scope(self):
        self._search_dirs = get_default_search_dirs()
        self._scanned_dirs = get_scanned_dirs()
        self._update_scope_info()
        self._update_status_dot()
        self._update_scan_btn_state()

    def _init_ui(self):
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(12, 8, 12, 8)
        self._main_layout.setSpacing(4)

        self._scope_collapsible = CollapsibleSection("指定搜索范围", default_expanded=True)
        scope_content = QWidget()
        scope_content.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; border-radius: {RADIUS.LARGE}px; }}")
        scope_content_layout = QVBoxLayout()
        scope_content_layout.setContentsMargins(10, 6, 10, 6)
        scope_content_layout.setSpacing(4)

        self._scope_detail = QLabel("")
        self._scope_detail.setStyleSheet(label_micro_style())
        scope_content_layout.addWidget(self._scope_detail)

        radio_row = QHBoxLayout()
        radio_row.setSpacing(12)

        self._scope_radio_group = QButtonGroup(self)
        self._all_radio = AnimatedRadioButton("全部搜索路径", font_pt=FONT.MICRO_PT)
        self._all_radio.setChecked(True)
        self._all_radio.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scope_radio_group.addButton(self._all_radio)

        self._custom_radio = AnimatedRadioButton("自定义搜索范围", font_pt=FONT.MICRO_PT)
        self._custom_radio.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scope_radio_group.addButton(self._custom_radio)

        custom_settings_icon = _make_colored_icon("icons/settings.svg", COLORS.TEXT_SECONDARY, 16)
        self._custom_settings_btn = QPushButton()
        self._custom_settings_btn.setIcon(custom_settings_icon)
        self._custom_settings_btn.setIconSize(QSize(14, 14))
        self._custom_settings_btn.setFixedSize(28, 28)
        self._custom_settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._custom_settings_btn.setStyleSheet(f"""
            QPushButton {{
                border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
                border-radius: {RADIUS.MEDIUM}px;
                background-color: transparent;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_HOVER};
                border-color: {COLORS.BORDER_HOVER};
            }}
        """)
        self._custom_settings_btn.clicked.connect(self._on_custom_settings_clicked)
        self._custom_settings_btn.setVisible(False)

        radio_row.addWidget(self._all_radio)
        radio_row.addWidget(self._custom_radio)
        radio_row.addWidget(self._custom_settings_btn)
        radio_row.addStretch()
        scope_content_layout.addLayout(radio_row)

        self._scope_radio_group.buttonClicked.connect(self._on_scope_radio_clicked)

        self._dir_flow_layout = FlowLayout(spacing=6)

        self._dir_scroll_content = QWidget()
        self._dir_scroll_content.setLayout(self._dir_flow_layout)
        self._dir_scroll_content.setStyleSheet("QWidget { background: transparent; }")

        self._scroll = QScrollArea()
        self._scroll.setWidget(self._dir_scroll_content)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setMinimumHeight(32)
        self._scroll.setMaximumHeight(80)
        self._scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {COLORS.BG_SECONDARY}; border-radius: {RADIUS.SMALL}px; }}" + scrollbar_style())
        self._scroll.setVisible(False)

        scope_content_layout.addWidget(self._scroll)
        scope_content.setLayout(scope_content_layout)
        self._scope_collapsible.set_content(scope_content)

        self._main_layout.addWidget(self._scope_collapsible)

        self._manage_collapsible = CollapsibleSection("管理扫描路径", default_expanded=True)
        manage_content = QWidget()
        manage_content.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; border-radius: {RADIUS.LARGE}px; }}")
        manage_content_layout = QVBoxLayout()
        manage_content_layout.setContentsMargins(10, 6, 10, 6)
        manage_content_layout.setSpacing(4)

        self._scope_status_widget = QWidget()
        self._scope_status_widget.setStyleSheet("QWidget { background: transparent; }")
        self._scope_status_layout = QHBoxLayout(self._scope_status_widget)
        self._scope_status_layout.setContentsMargins(0, 0, 0, 4)
        self._scope_status_layout.setSpacing(4)

        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(f"""
            QLabel {{
                border-radius: {RADIUS.SMALL}px;
                background-color: {COLORS.ERROR};
                border: none;
            }}
        """)
        self._scope_status_layout.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self._status_label = QLabel("0 个目录 · 未扫描")
        self._status_label.setStyleSheet(label_micro_style())
        self._scope_status_layout.addWidget(self._status_label, 1, Qt.AlignmentFlag.AlignVCenter)

        manage_content_layout.addWidget(self._scope_status_widget)

        self._scope_info_scroll = QScrollArea()
        self._scope_info_scroll.setWidgetResizable(True)
        self._scope_info_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scope_info_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scope_info_scroll.setMinimumHeight(40)
        self._scope_info_scroll.setMaximumHeight(120)
        self._scope_info_scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {COLORS.BG_SECONDARY}; border-radius: {RADIUS.SMALL}px; }}" + scrollbar_style())
        self._scope_info_container = QWidget()
        self._scope_info_layout = QVBoxLayout(self._scope_info_container)
        self._scope_info_layout.setContentsMargins(8, 4, 8, 4)
        self._scope_info_layout.setSpacing(2)
        self._scope_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scope_info_container.setStyleSheet("QWidget { background: transparent; }")
        self._scope_info_scroll.setWidget(self._scope_info_container)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        gray_settings = _make_colored_icon("icons/settings.svg", COLORS.TEXT_SECONDARY, 16)
        self.configure_btn = QPushButton("  管理扫描路径")
        self.configure_btn.setIcon(gray_settings)
        self.configure_btn.setIconSize(QSize(14, 14))
        self.configure_btn.setFixedHeight(28)
        self.configure_btn.setStyleSheet(config_button_style())
        self.configure_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.configure_btn.clicked.connect(self._on_configure_scope)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(progress_bar_style(6, 3))
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        self.scan_btn = QPushButton()
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.setFixedHeight(28)
        self.scan_btn.clicked.connect(self._on_scan_clicked)
        self._update_scan_btn_state()

        action_row.addStretch()
        action_row.addWidget(self.configure_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        action_row.addWidget(self.scan_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        manage_content_layout.addWidget(self._scope_info_scroll, 1)
        manage_content_layout.addLayout(action_row)
        manage_content.setLayout(manage_content_layout)
        self._manage_collapsible.set_content(manage_content)

        self._main_layout.addWidget(self._manage_collapsible)
        self._main_layout.addWidget(self.progress_bar)

        self.setLayout(self._main_layout)
        self.setStyleSheet(f"""
            SearchScopePanel {{
                background-color: transparent;
            }}
        """)

    def _get_display_path(self, path: str) -> str:
        path_clean = path.rstrip(os.sep)
        for scan_dir in self._scanned_dirs:
            scan_clean = scan_dir.rstrip(os.sep)
            if os.path.normcase(os.path.normpath(path_clean)) == os.path.normcase(os.path.normpath(scan_clean)):
                return os.path.basename(scan_clean) or scan_dir
            try:
                rel = os.path.relpath(path_clean, scan_clean)
                if not rel.startswith('..'):
                    return rel
            except ValueError:
                pass
        return os.path.basename(path_clean) or path

    def set_scanned_dirs(self, dirs: list):
        self._scanned_dirs = list(dirs)
        if self._scope_mode == 'all':
            self._selected_dirs = set(dirs)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self._update_scope_info()
        self.scope_changed.emit(list(self._selected_dirs))

    def update_scope_info(self, file_count: int = 0):
        self._indexed_count = file_count
        self._update_scope_info()

    def _update_scope_info(self):
        while self._scope_info_layout.count():
            item = self._scope_info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dir_count = len(self._scanned_dirs)
        if dir_count == 0:
            self._status_dot.setStyleSheet(f"""
                QLabel {{
                    border-radius: {RADIUS.SMALL}px;
                    background-color: {COLORS.ERROR};
                    border: none;
                }}
            """)
            self._status_label.setText("0 个目录 · 未扫描")
            self._status_label.setStyleSheet(label_micro_style())
            return

        incomplete_count = 0
        for d in self._scanned_dirs:
            status = get_scan_status(d)
            if status is None or status in (SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED, SCAN_STATUS_SCANNING):
                incomplete_count += 1

        if self._indexed_count == 0:
            dot_color = COLORS.ERROR
            dot_tip = "未扫描"
        elif incomplete_count > 0:
            dot_color = COLORS.WARNING
            dot_tip = "部分目录未完成扫描"
        else:
            dot_color = COLORS.SUCCESS
            dot_tip = "已索引"
        self._status_dot.setStyleSheet(f"""
            QLabel {{
                border-radius: {RADIUS.SMALL}px;
                background-color: {dot_color};
                border: none;
            }}
        """)
        self._status_dot.setToolTip(dot_tip)

        status_text = ""
        if incomplete_count > 0:
            status_text = f" · {incomplete_count} 个目录未完成扫描"

        header_text = f"{dir_count} 个目录" + (f" · 已索引 {self._indexed_count:,} 个文件（索引可加速搜索）" if self._indexed_count > 0 else " · 未索引（扫描可加速文件名搜索）") + status_text
        self._status_label.setText(header_text)
        if incomplete_count > 0:
            self._status_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.WARNING}; border: none; background: transparent;")
        else:
            self._status_label.setStyleSheet(label_micro_style())

        for d in self._scanned_dirs:
            status = get_scan_status(d)
            dir_label = ElidedPathLabel(d)
            if status is None:
                dir_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.WARNING}; border: none; background: transparent; padding: 1px 2px; margin: 0px;")
                dir_label.setToolTip(f"{d} (未扫描)")
            elif status == SCAN_STATUS_INCOMPLETE:
                dir_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.WARNING}; border: none; background: transparent; padding: 1px 2px; margin: 0px;")
                dir_label.setToolTip(f"{d} (扫描未完成)")
            elif status == SCAN_STATUS_FAILED:
                dir_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.ERROR}; border: none; background: transparent; padding: 1px 2px; margin: 0px;")
                dir_label.setToolTip(f"{d} (扫描失败)")
            else:
                dir_label.setStyleSheet(f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.TEXT_SECONDARY}; border: none; background: transparent; padding: 1px 2px; margin: 0px;")
                dir_label.setToolTip(d)
            self._scope_info_layout.addWidget(dir_label)

    def _update_scope_detail(self):
        if self._scope_mode == 'all':
            self._scope_detail.setText(f"搜索所有路径（共 {len(self._scanned_dirs)} 个）")
        else:
            count = len(self._selected_dirs)
            total = len(self._custom_dir_list)
            self._scope_detail.setText(f"已选择 {count}/{total} 个目录")

    def _rebuild_dir_buttons(self):
        while self._dir_flow_layout.count():
            item = self._dir_flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dirs_to_show = self._custom_dir_list if self._scope_mode == 'custom' else list(self._selected_dirs)
        tag_style = button_tag()
        for d in dirs_to_show:
            display_name = self._get_display_path(d)
            btn = QPushButton(display_name)
            btn.setCheckable(True)
            is_selected = d in self._selected_dirs
            btn.setChecked(is_selected)
            btn.setToolTip(d)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(tag_style)
            btn.clicked.connect(lambda checked, path=d: self._on_dir_toggled(path, checked))
            self._dir_flow_layout.addWidget(btn)

    def _on_scope_radio_clicked(self, btn):
        if btn == self._all_radio:
            self._on_all_clicked()
        elif btn == self._custom_radio:
            self._on_custom_radio_selected()

    def _on_all_clicked(self):
        self._scope_mode = 'all'
        self._all_radio.setChecked(True)
        self._custom_radio.setChecked(False)
        self._selected_dirs = set(self._scanned_dirs)
        self._custom_dir_list = []
        self._scroll.setVisible(False)
        self._custom_settings_btn.setVisible(False)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self.scope_changed.emit(list(self._selected_dirs))

    def _on_custom_radio_selected(self):
        self._scope_mode = 'custom'
        self._all_radio.setChecked(False)
        self._custom_radio.setChecked(True)
        if not self._custom_dir_list:
            self._custom_dir_list = list(self._scanned_dirs)
            self._selected_dirs = set(self._scanned_dirs)
        self._scroll.setVisible(True)
        self._custom_settings_btn.setVisible(True)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self.scope_changed.emit(list(self._selected_dirs))

    def _on_custom_settings_clicked(self):
        self._all_radio.setChecked(False)
        self._custom_radio.setChecked(True)

        dialog = ScopeSelectionDialog(self._scanned_dirs, self._selected_dirs, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_dirs()
            unscanned = dialog.get_unscanned_dirs()

            def _is_under_scanned_dir(path: str) -> bool:
                norm_p = os.path.normcase(os.path.normpath(path))
                for sd in self._scanned_dirs:
                    norm_sd = os.path.normcase(os.path.normpath(sd))
                    if norm_p == norm_sd or norm_p.startswith(norm_sd + os.sep):
                        status = get_scan_status(sd)
                        if status == SCAN_STATUS_COMPLETE:
                            return True
                return False

            incomplete_selected = []
            for d in selected:
                if _is_under_scanned_dir(d):
                    continue
                status = get_scan_status(d)
                if status is None or status in (SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED):
                    incomplete_selected.append(d)

            if incomplete_selected:
                reply = styled_msg_box(
                    self, QMessageBox.Icon.Warning,
                    "目录扫描未完成",
                    "以下目录扫描未完成或失败，搜索结果可能不完整：\n\n" +
                    "\n".join(f"  - {d}" for d in incomplete_selected) +
                    "\n\n建议重新扫描这些目录。是否仍要将其加入搜索范围？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    selected = [d for d in selected if d not in incomplete_selected]

            if unscanned:
                reply = styled_msg_box(
                    self, QMessageBox.Icon.Question,
                    "发现未扫描目录",
                    "以下目录尚未扫描：\n\n" +
                    "\n".join(f"  - {d}" for d in unscanned) +
                    "\n\n是否立即扫描这些目录？\n（选择\"取消\"则不会将这些目录加入搜索范围）",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._scope_mode = 'custom'
                    self.scan_unscanned_requested.emit(unscanned)
                    return

            self._scope_mode = 'custom'
            self._selected_dirs = set(selected)
            if not self._selected_dirs:
                styled_msg_box(
                    self, QMessageBox.Icon.Warning,
                    "搜索范围为空",
                    "未选择任何目录作为搜索范围，搜索将不会返回结果。\n建议至少选择一个目录。"
                )
            self._custom_dir_list = list(selected)
            self._scroll.setVisible(True)
            self._custom_settings_btn.setVisible(True)
            self._rebuild_dir_buttons()
            self._update_scope_detail()
            self.scope_changed.emit(list(self._selected_dirs))
        else:
            if not self._selected_dirs:
                self._on_all_clicked()
            else:
                self._scope_mode = 'custom'
                self._all_radio.setChecked(False)
                self._custom_radio.setChecked(True)
                self._custom_settings_btn.setVisible(True)

    def _on_dir_toggled(self, path: str, checked: bool):
        if checked:
            self._selected_dirs.add(path)
        else:
            self._selected_dirs.discard(path)
        self._update_scope_detail()
        self.scope_changed.emit(list(self._selected_dirs))

    def get_selected_dirs(self) -> list:
        if self._scope_mode == 'all':
            return list(self._scanned_dirs)
        return list(self._selected_dirs)

    def get_all_scanned_dirs(self) -> list:
        return list(self._scanned_dirs)

    def add_scanned_dir(self, dirs: list):
        for d in dirs:
            if d not in self._scanned_dirs:
                self._scanned_dirs.append(d)
            self._selected_dirs.add(d)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self._update_scope_info()
        self._update_status_dot()
        self._update_scan_btn_state()
        self.scope_changed.emit(list(self._selected_dirs))

    def _update_status_dot(self):
        self._update_scope_info()

    def _has_unscanned_dirs(self) -> bool:
        for d in self._scanned_dirs:
            status = get_scan_status(d)
            if status is None or status in (SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED):
                return True
        if not self._scanned_dirs and hasattr(self, '_search_dirs'):
            return bool(self._search_dirs)
        return False

    def _update_scan_btn_state(self):
        if self._indexed_count == 0:
            self.scan_btn.setText("开始扫描")
            self.scan_btn.setStyleSheet(button_scan_green())
            self.scan_btn.setFixedHeight(28)
        elif self._has_unscanned_dirs():
            self.scan_btn.setText("新增扫描")
            self.scan_btn.setStyleSheet(button_scan_green())
            self.scan_btn.setFixedHeight(28)
        else:
            self.scan_btn.setText("重新扫描")
            self.scan_btn.setStyleSheet(button_scan())
            self.scan_btn.setFixedHeight(28)

    def _on_configure_scope(self):
        dialog = SearchScopeDialog(self._scanned_dirs, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_dirs = dialog.get_dirs()
            if not new_dirs:
                styled_msg_box(
                    self, QMessageBox.Icon.Warning,
                    "配置错误", "扫描路径不能为空"
                )
                return
            old_dirs = set(self._scanned_dirs)
            new_set = set(new_dirs)
            added = new_set - old_dirs
            removed = old_dirs - new_set

            # 删除被移除路径的索引记录和扫描状态
            if removed:
                from database.db_manager import DatabaseManager
                db = DatabaseManager()
                for d in removed:
                    db.delete_entries_by_prefix(d)
                # 更新索引计数
                self._indexed_count = db.get_index_count()
                # 清除被移除路径的扫描状态，以便加回时需要重新扫描
                config = load_config()
                scan_status = config.get("search", {}).get("scan_status", {})
                for d in removed:
                    normalized = os.path.normpath(d)
                    scan_status.pop(normalized, None)
                config["search"]["scan_status"] = scan_status
                save_config(config)

            self._scanned_dirs = new_dirs
            self._search_dirs = list(new_dirs)
            if self._scope_mode == 'all':
                self._selected_dirs = set(new_dirs)
            self._update_scope_info()
            self._update_status_dot()
            self._update_scan_btn_state()
            self._update_scope_info()
            self.scope_changed.emit(list(self._selected_dirs))

            config = load_config()
            config["search"]["default_dirs"] = list(new_dirs)
            save_config(config)

            if added or removed:
                msg_parts = []
                if added:
                    msg_parts.append(f"新增 {len(added)} 个目录")
                if removed:
                    msg_parts.append(f"移除 {len(removed)} 个目录（索引已删除）")
                scan_btn_text = "新增扫描" if added else "重新扫描"
                styled_msg_box(
                    self, QMessageBox.Icon.Information,
                    "路径已更新",
                    f"扫描路径已更新（{'，'.join(msg_parts)}）。\n请点击「{scan_btn_text}」以更新文件索引。"
                )

    def _on_scan_clicked(self):
        if self._is_scanning:
            return

        if self._indexed_count == 0:
            title = "开始扫描"
            text = "将扫描所选目录/驱动器以建立文件索引，这可能需要几分钟时间。\n确定要开始扫描吗？"
        elif self._has_unscanned_dirs():
            title = "新增扫描"
            text = "发现新增的未扫描目录，需要扫描以建立文件索引。\n确定要开始新增扫描吗？"
        else:
            title = "重新扫描"
            text = "将重新扫描所有目录/驱动器，更新文件索引。\n这可能需要几分钟时间，确定要继续吗？"

        reply = styled_msg_box(
            self, QMessageBox.Icon.Question,
            title, text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._is_scanning = True
        self.scan_btn.setEnabled(False)
        self.scan_btn.setIcon(QIcon())
        self.scan_btn.setText("正在扫描")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.scan_requested.emit()

    def reset_scan_state(self, file_count: int = 0):
        self._is_scanning = False
        self.scan_btn.setEnabled(True)
        self.scan_btn.setIcon(QIcon())
        self._indexed_count = file_count
        self.progress_bar.setVisible(False)
        self._update_scan_btn_state()
        self._update_scope_info()
        self._update_status_dot()

        save_scanned_dirs(self._scanned_dirs)

    def set_search_dirs(self, dirs: list):
        self._search_dirs = dirs
        self._update_scope_info()
        self._update_status_dot()
        self._update_scan_btn_state()

    def get_search_dirs(self) -> list:
        return list(getattr(self, '_search_dirs', self._scanned_dirs))

    def get_indexed_count(self) -> int:
        return self._indexed_count

    def is_scanning(self) -> bool:
        return self._is_scanning

    def show_search_progress(self):
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setVisible(True)

    def hide_search_progress(self):
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)

    def reset(self):
        self._scope_mode = 'all'
        self._selected_dirs = set()
        self._custom_dir_list = []
        self._scanned_dirs = []
        self._indexed_count = 0
        self._all_radio.setChecked(True)
        self._custom_radio.setChecked(False)
        self._scroll.setVisible(False)
        self._custom_settings_btn.setVisible(False)
        self._rebuild_dir_buttons()
        self._update_scope_detail()
        self._update_scope_info()
        self._update_status_dot()
        self._update_scan_btn_state()
