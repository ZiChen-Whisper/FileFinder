import os
import logging
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
                               QTreeWidget, QTreeWidgetItem, QLineEdit, QFileDialog,
                               QApplication, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ..modern_dialog import ModernDialogBase, styled_msg_box
from ..style_constants import COLORS, RADIUS, DIALOG
from ..style_manager import (button_primary, button_secondary, button_small_primary,
                             button_small_secondary, input_style, label_caption_style,
                             label_micro_style, tree_widget_style)
from constants import TREE_EXPAND_BATCH_SIZE
from config import get_scan_status, SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED

logger = logging.getLogger(__name__)


class ScopeSelectionDialog(ModernDialogBase):
    _PLACEHOLDER_KEY = "__placeholder__"

    def __init__(self, scanned_dirs: list, current_selected: set, parent=None):
        super().__init__(parent, title="自定义搜索范围", min_width=560, min_height=540, resizable=True)
        self._scanned_dirs = list(scanned_dirs)
        self._selected_dirs = set(current_selected)
        self._unscanned_dirs = []
        self._updating_tree = False
        self._loaded_items = set()
        self._init_ui()

    def _init_ui(self):
        def build_content(content_widget):
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(12)
            layout.setContentsMargins(DIALOG.PADDING, 4, DIALOG.PADDING, 20)

            desc = QLabel("FileFinder将在指定的搜索范围中进行搜索")
            desc.setStyleSheet(label_caption_style())
            desc.setWordWrap(True)

            select_row = QHBoxLayout()
            select_row.setSpacing(6)

            select_all_btn = QPushButton("全选")
            select_all_btn.setStyleSheet(button_small_secondary())
            select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            select_all_btn.clicked.connect(self._on_select_all)

            deselect_all_btn = QPushButton("全不选")
            deselect_all_btn.setStyleSheet(button_small_secondary())
            deselect_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            deselect_all_btn.clicked.connect(self._on_deselect_all)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setStyleSheet(f"color: {COLORS.BORDER_DEFAULT}; border: none; background: transparent;")

            expand_all_btn = QPushButton("全部展开")
            expand_all_btn.setStyleSheet(button_small_secondary())
            expand_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            expand_all_btn.clicked.connect(self._on_expand_all)

            collapse_all_btn = QPushButton("全部折叠")
            collapse_all_btn.setStyleSheet(button_small_secondary())
            collapse_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            collapse_all_btn.clicked.connect(self._on_collapse_all)

            self._count_label = QLabel("")
            self._count_label.setStyleSheet(label_micro_style())

            select_row.addWidget(select_all_btn)
            select_row.addWidget(deselect_all_btn)
            select_row.addWidget(sep)
            select_row.addWidget(expand_all_btn)
            select_row.addWidget(collapse_all_btn)
            select_row.addStretch()
            select_row.addWidget(self._count_label)

            self._tree = QTreeWidget()
            self._tree.setHeaderLabel("选择目录")
            self._tree.setAnimated(True)
            self._tree.setIndentation(16)
            self._tree.setExpandsOnDoubleClick(True)

            tree_style = tree_widget_style()
            self._tree.setStyleSheet(tree_style)
            self._tree.header().setStretchLastSection(True)
            self._tree.itemChanged.connect(self._on_tree_item_changed)
            self._tree.itemExpanded.connect(self._on_item_expanded)
            self._populate_tree()

            browse_row = QHBoxLayout()
            browse_row.setSpacing(8)

            self._path_input = QLineEdit()
            self._path_input.setPlaceholderText("输入目标路径，如 D:\\Projects 或 C:\\Users")
            self._path_input.setFixedHeight(36)
            self._path_input.setStyleSheet(input_style())

            browse_btn = QPushButton("浏览...")
            browse_btn.setFixedHeight(36)
            browse_btn.setStyleSheet(button_small_secondary())
            browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            browse_btn.clicked.connect(self._on_browse)

            add_btn = QPushButton("+ 添加")
            add_btn.setFixedHeight(36)
            add_btn.setStyleSheet(button_small_primary())
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.clicked.connect(self._on_add)

            browse_row.addWidget(self._path_input, 1)
            browse_row.addWidget(browse_btn)
            browse_row.addWidget(add_btn)

            btn_row = QHBoxLayout()
            btn_row.addStretch()

            cancel_btn = QPushButton("取消")
            cancel_btn.setStyleSheet(button_secondary())
            cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cancel_btn.clicked.connect(self.reject)

            confirm_btn = QPushButton("确定")
            confirm_btn.setStyleSheet(button_primary())
            confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            confirm_btn.clicked.connect(self._on_confirm)

            btn_row.addWidget(cancel_btn)
            btn_row.addSpacing(8)
            btn_row.addWidget(confirm_btn)

            layout.addWidget(desc)
            layout.addLayout(select_row)
            layout.addWidget(self._tree, 1)
            layout.addLayout(browse_row)
            layout.addLayout(btn_row)

        self._create_shadow_frame(build_content)
        self._update_count_label()

    def _populate_tree(self):
        self._updating_tree = True
        self._tree.clear()
        self._loaded_items.clear()
        for d in self._scanned_dirs:
            name = os.path.basename(d.rstrip(os.sep)) or d
            scan_status = get_scan_status(d)
            if scan_status == SCAN_STATUS_INCOMPLETE:
                name = f"{name} (扫描未完成)"
            elif scan_status == SCAN_STATUS_FAILED:
                name = f"{name} (扫描失败)"
            item = QTreeWidgetItem(self._tree, [name])
            d_norm = os.path.normcase(os.path.normpath(d.rstrip(os.sep)))
            if d in self._selected_dirs:
                item.setCheckState(0, Qt.CheckState.Checked)
            elif any(
                os.path.normcase(os.path.normpath(s.rstrip(os.sep))).startswith(d_norm + os.sep)
                for s in self._selected_dirs
            ):
                item.setCheckState(0, Qt.CheckState.PartiallyChecked)
            else:
                item.setCheckState(0, Qt.CheckState.Unchecked)
            item.setData(0, Qt.ItemDataRole.UserRole, d)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, 'scanned')
            item.setToolTip(0, d)
            if scan_status == SCAN_STATUS_INCOMPLETE:
                item.setForeground(0, QColor(COLORS.WARNING))
                item.setToolTip(0, f"{d}\n扫描未完成，搜索结果可能不完整")
            elif scan_status == SCAN_STATUS_FAILED:
                item.setForeground(0, QColor(COLORS.ERROR))
                item.setToolTip(0, f"{d}\n扫描失败，请重新扫描此目录")
            if self._has_subdirectories(d):
                self._add_placeholder(item)
            else:
                item.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
        self._updating_tree = False
        self._update_count_label()

    def _has_subdirectories(self, dir_path: str) -> bool:
        try:
            for name in os.listdir(dir_path):
                full = os.path.join(dir_path, name)
                try:
                    if os.path.isdir(full) and not os.path.islink(full):
                        return True
                except Exception:
                    continue
        except (PermissionError, OSError, TypeError):
            return False
        return False

    def _add_placeholder(self, item: QTreeWidgetItem):
        placeholder = QTreeWidgetItem(item, ["加载中..."])
        placeholder.setData(0, Qt.ItemDataRole.UserRole, self._PLACEHOLDER_KEY)
        placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
        placeholder.setForeground(0, QColor(156, 163, 175))

    def _has_placeholder(self, item: QTreeWidgetItem) -> bool:
        if item.childCount() == 0:
            return False
        first = item.child(0)
        return first.data(0, Qt.ItemDataRole.UserRole) == self._PLACEHOLDER_KEY

    def _on_item_expanded(self, item: QTreeWidgetItem):
        if not self._has_placeholder(item):
            return
        self._updating_tree = True
        try:
            item.takeChild(0)
            dir_path = item.data(0, Qt.ItemDataRole.UserRole)
            if not dir_path or not os.path.isdir(dir_path):
                item.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
                self._updating_tree = False
                return
            parent_state = item.checkState(0)
            self._load_children(item, dir_path)
            if parent_state == Qt.CheckState.Checked:
                for i in range(item.childCount()):
                    self._cascade_check(item.child(i), True)
            elif parent_state == Qt.CheckState.PartiallyChecked:
                self._apply_partial_inherit(item)
            self._loaded_items.add(id(item))
        except Exception:
            logger.debug("Error loading tree children", exc_info=True)
        self._updating_tree = False
        self._update_count_label()

    def _load_children(self, parent_item: QTreeWidgetItem, dir_path: str):
        try:
            entries = sorted(os.listdir(dir_path))
        except (PermissionError, OSError, TypeError):
            parent_item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
            return
        has_dirs = False
        for name in entries:
            full = os.path.join(dir_path, name)
            try:
                if not os.path.isdir(full) or os.path.islink(full):
                    continue
            except Exception:
                continue
            has_dirs = True
            child = QTreeWidgetItem(parent_item, [name])
            child.setCheckState(0, Qt.CheckState.Unchecked)
            child.setData(0, Qt.ItemDataRole.UserRole, full)
            child.setData(0, Qt.ItemDataRole.UserRole + 1, 'scanned')
            child.setToolTip(0, full)
            if self._has_subdirectories(full):
                self._add_placeholder(child)
            else:
                child.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
        if not has_dirs:
            parent_item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)

    def _cascade_check(self, item: QTreeWidgetItem, checked: bool):
        item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        if not self._has_placeholder(item):
            for i in range(item.childCount()):
                self._cascade_check(item.child(i), checked)

    def _apply_partial_inherit(self, item: QTreeWidgetItem):
        for i in range(item.childCount()):
            child = item.child(i)
            child_path = child.data(0, Qt.ItemDataRole.UserRole) or ''
            if child_path in self._selected_dirs:
                child.setCheckState(0, Qt.CheckState.Checked)
            else:
                child.setCheckState(0, Qt.CheckState.Unchecked)

    def _on_expand_all(self):
        self._expand_queue = []
        self._expand_depth = 0
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._expand_queue.append((root.child(i), 0))
        if self._expand_queue:
            self._count_label.setText("正在展开...")
            self._expand_index = 0
            self._expand_timer = QTimer(self)
            self._expand_timer.timeout.connect(self._expand_next_batch)
            self._expand_timer.start(0)

    def _expand_next_batch(self):
        batch_size = TREE_EXPAND_BATCH_SIZE
        new_queue = []
        for _ in range(batch_size):
            if self._expand_index >= len(self._expand_queue):
                self._expand_queue = new_queue
                self._expand_index = 0
                if not self._expand_queue:
                    self._expand_timer.stop()
                    self._update_count_label()
                    return
                return
            item, depth = self._expand_queue[self._expand_index]
            self._expand_index += 1
            if depth >= 3:
                continue
            self._tree.expandItem(item)
            if not self._has_placeholder(item):
                for i in range(item.childCount()):
                    new_queue.append((item.child(i), depth + 1))
        if self._expand_index >= len(self._expand_queue):
            self._expand_queue = new_queue
            self._expand_index = 0
            if not self._expand_queue:
                self._expand_timer.stop()
                self._update_count_label()
        QApplication.processEvents()

    def _on_collapse_all(self):
        self._collapse_all_items(self._tree.invisibleRootItem())

    def _collapse_all_items(self, parent: QTreeWidgetItem):
        for i in range(parent.childCount()):
            child = parent.child(i)
            self._collapse_all_items(child)
            self._tree.collapseItem(child)

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int):
        if self._updating_tree:
            return
        self._updating_tree = True
        state = item.checkState(0)
        if state == Qt.CheckState.Checked:
            self._cascade_check(item, True)
        elif state == Qt.CheckState.Unchecked:
            self._cascade_check(item, False)
        self._update_parent_check_state(item)
        self._updating_tree = False
        self._update_count_label()

    def _update_parent_check_state(self, item: QTreeWidgetItem):
        parent = item.parent()
        if parent is None:
            return
        checked_count = 0
        partial_count = 0
        total = parent.childCount()
        for i in range(total):
            cs = parent.child(i).checkState(0)
            if cs == Qt.CheckState.Checked:
                checked_count += 1
            elif cs == Qt.CheckState.PartiallyChecked:
                partial_count += 1
        if checked_count == 0 and partial_count == 0:
            parent.setCheckState(0, Qt.CheckState.Unchecked)
        elif checked_count == total:
            parent.setCheckState(0, Qt.CheckState.Checked)
        else:
            parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
        self._update_parent_check_state(parent)

    def _on_select_all(self):
        self._updating_tree = True
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._cascade_check(root.child(i), True)
        self._updating_tree = False
        self._update_count_label()

    def _on_deselect_all(self):
        self._updating_tree = True
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._cascade_check(root.child(i), False)
        self._updating_tree = False
        self._update_count_label()

    def _update_count_label(self):
        checked = 0
        total = 0
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            c = root.child(i)
            total += 1
            if c.checkState(0) == Qt.CheckState.Checked:
                checked += 1
        self._count_label.setText(f"已选 {checked}/{total} 个根目录")

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择目录")
        if not path:
            return
        self._path_input.setText(path)
        self._add_path_to_tree(path)

    def _on_add(self):
        path = self._path_input.text().strip()
        if not path:
            return
        if not os.path.isdir(path):
            styled_msg_box(
                self, QMessageBox.Icon.Warning,
                "路径无效", f"目录不存在或无法访问：\n{path}"
            )
            return
        self._add_path_to_tree(path)
        self._path_input.clear()

    def _add_path_to_tree(self, path: str):
        existing = self._find_tree_item_by_path(path)
        if existing is not None:
            self._updating_tree = True
            self._cascade_check(existing, True)
            self._update_parent_check_state(existing)
            self._updating_tree = False
            self._update_count_label()
            self._tree.scrollToItem(existing)
            self._path_input.clear()
            return

        visible = self._ensure_path_visible(path)
        if visible is not None:
            self._updating_tree = True
            self._cascade_check(visible, True)
            self._update_parent_check_state(visible)
            self._updating_tree = False
            self._update_count_label()
            self._tree.scrollToItem(visible)
            self._path_input.clear()
            return

        is_scanned = any(
            os.path.normcase(os.path.normpath(path)).startswith(
                os.path.normcase(os.path.normpath(d)) + os.sep)
            or os.path.normcase(os.path.normpath(path)) == os.path.normcase(os.path.normpath(d))
            for d in self._scanned_dirs
        )

        tag = 'scanned'
        if not is_scanned:
            reply = styled_msg_box(
                self, QMessageBox.Icon.Question,
                "目录未扫描",
                f"目录不在已索引范围内：\n{path}\n\n"
                "是否添加到扫描路径并扫描？\n"
                "（选择\"否\"则仅添加到选择列表，不会索引其中的文件）",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._unscanned_dirs.append(path)
                self._scanned_dirs.append(path)
                tag = 'unscanned'

        self._updating_tree = True
        name = os.path.basename(path.rstrip(os.sep)) or path
        item = QTreeWidgetItem(self._tree, [name])
        item.setCheckState(0, Qt.CheckState.Checked)
        item.setData(0, Qt.ItemDataRole.UserRole, path)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, tag)
        item.setToolTip(0, path)
        if not is_scanned:
            item.setForeground(0, QColor(COLORS.ERROR))
        if self._has_subdirectories(path):
            self._add_placeholder(item)
        else:
            item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
        self._tree.scrollToItem(item)
        self._updating_tree = False
        self._update_count_label()
        self._path_input.clear()

    def _ensure_path_visible(self, target_path: str):
        norm_target = os.path.normcase(os.path.normpath(target_path))
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            root_item = root.child(i)
            root_path = os.path.normcase(os.path.normpath(
                root_item.data(0, Qt.ItemDataRole.UserRole) or ''))
            if norm_target == root_path:
                return root_item
            if norm_target.startswith(root_path + os.sep):
                return self._expand_to_path(root_item, root_path, norm_target)
        return None

    def _expand_to_path(self, parent_item: QTreeWidgetItem, parent_path: str, target_path: str):
        rel = target_path[len(parent_path):].lstrip(os.sep)
        if not rel:
            return parent_item
        parts = rel.split(os.sep)
        current_item = parent_item
        current_path = parent_path
        for part in parts:
            if self._has_placeholder(current_item):
                self._updating_tree = True
                current_item.takeChild(0)
                dir_path = current_item.data(0, Qt.ItemDataRole.UserRole)
                parent_state = current_item.checkState(0)
                self._load_children(current_item, dir_path)
                if parent_state == Qt.CheckState.Checked:
                    for j in range(current_item.childCount()):
                        self._cascade_check(current_item.child(j), True)
                self._loaded_items.add(id(current_item))
                self._updating_tree = False
                current_item.setExpanded(True)
            found = None
            norm_part = os.path.normcase(part)
            for j in range(current_item.childCount()):
                child = current_item.child(j)
                if os.path.normcase(child.text(0)) == norm_part:
                    found = child
                    break
            if found is None:
                return None
            current_item = found
            current_path = os.path.join(current_path, part)
        return current_item

    def _find_tree_item_by_path(self, path: str):
        norm = os.path.normcase(os.path.normpath(path))
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            result = self._search_item(root.child(i), norm)
            if result is not None:
                return result
        return None

    def _search_item(self, item: QTreeWidgetItem, norm_path: str):
        item_path = os.path.normcase(os.path.normpath(
            item.data(0, Qt.ItemDataRole.UserRole) or ''))
        if item_path == norm_path:
            return item
        if not self._has_placeholder(item):
            for i in range(item.childCount()):
                result = self._search_item(item.child(i), norm_path)
                if result is not None:
                    return result
        return None

    def _on_confirm(self):
        self._selected_dirs = set()
        self._unscanned_dirs = []
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._collect_checked(root.child(i))
        self.accept()

    def _collect_checked(self, item: QTreeWidgetItem):
        if item.checkState(0) == Qt.CheckState.Checked:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            tag = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if path:
                self._selected_dirs.add(path)
                if tag == 'unscanned' and path not in self._unscanned_dirs:
                    self._unscanned_dirs.append(path)
        elif item.checkState(0) == Qt.CheckState.PartiallyChecked:
            for i in range(item.childCount()):
                self._collect_checked(item.child(i))
        else:
            for i in range(item.childCount()):
                self._collect_checked(item.child(i))

    def get_selected_dirs(self) -> list:
        return list(self._selected_dirs)

    def get_unscanned_dirs(self) -> list:
        return list(self._unscanned_dirs)
