import os

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QProgressBar, QTextEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..style_constants import COLORS, FONT, SPACING, DIALOG
from ..style_manager import (dialog_title_style, label_body_style,
                             progress_bar_style, progress_bar_success_style,
                             progress_bar_warning_style, progress_bar_error_style,
                             button_cancel_danger, scan_log_style)


class ScanProgressDialog(QWidget):
    scan_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_cancelling = False
        self._scan_start_time = 0.0
        self._last_logged_dir = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(60, 40, 60, 40)

        self._title = QLabel("正在扫描文件...")
        title_font = QFont()
        title_font.setPointSize(FONT.DISPLAY_PT)
        title_font.setBold(True)
        self._title.setFont(title_font)
        self._title.setStyleSheet(dialog_title_style())
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setWordWrap(True)

        self._percentage = QLabel("0%")
        pct_font = QFont()
        pct_font.setPointSize(FONT.DISPLAY_XL_PT)
        pct_font.setBold(True)
        self._percentage.setFont(pct_font)
        self._percentage.setStyleSheet(f"color: {COLORS.BRAND}; border: none; background: transparent;")
        self._percentage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(16)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(progress_bar_style(16, 8))

        detail_row = QHBoxLayout()
        detail_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._detail = QLabel("已发现 0 个文件")
        self._detail.setStyleSheet(label_body_style())

        self._eta_label = QLabel("")
        self._eta_label.setStyleSheet(f"font-size: {DIALOG.BODY_FONT_SIZE}; color: {COLORS.TEXT_PLACEHOLDER}; border: none; background: transparent; text-decoration: none;")

        detail_row.addWidget(self._detail)
        detail_row.addSpacing(16)
        detail_row.addWidget(self._eta_label)

        self._scan_log = QTextEdit()
        self._scan_log.setReadOnly(True)
        self._scan_log.setStyleSheet(scan_log_style())
        self._scan_log.setMinimumHeight(120)

        self._cancel_btn = QPushButton("取消扫描")
        self._cancel_btn.setFixedSize(140, 40)
        self._cancel_btn.setStyleSheet(button_cancel_danger())
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._on_cancel)

        layout.addWidget(self._title)
        layout.addWidget(self._percentage)
        layout.addWidget(self._progress_bar)
        layout.addLayout(detail_row)
        layout.addSpacing(8)
        layout.addWidget(self._scan_log, 1)
        layout.addSpacing(20)
        layout.addWidget(self._cancel_btn, 0, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        self.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; }}")

    def start_scan(self):
        import time
        self._scan_start_time = time.time()
        self._last_logged_dir = ""
        self._scan_log.clear()
        self._file_log_count = 0

    def update_progress(self, count: int, percentage: int = None, current_dir: str = ""):
        self._detail.setText(f"已发现 {count:,} 个文件")

        if current_dir and current_dir not in ("准备扫描...", "正在统计目录数量...", "扫描完成"):
            self._title.setText(f"正在扫描 {current_dir}")

            if current_dir != self._last_logged_dir:
                self._last_logged_dir = current_dir
                self._scan_log.append(f"{current_dir}  ({count:,} 个文件)")
                sb = self._scan_log.verticalScrollBar()
                sb.setValue(sb.maximum())

        if percentage is not None and percentage >= 0:
            self._progress_bar.setMaximum(100)
            pct_val = min(percentage, 100)
            self._progress_bar.setValue(pct_val)
            self._percentage.setText(f"{pct_val}%")

            if 0 < percentage < 100 and self._scan_start_time > 0:
                import time
                elapsed = time.time() - self._scan_start_time
                if elapsed > 0:
                    eta_seconds = elapsed * (100 - percentage) / percentage
                    if eta_seconds > 60:
                        self._eta_label.setText(f"预计剩余: {int(eta_seconds // 60)}分{int(eta_seconds % 60)}秒")
                    else:
                        self._eta_label.setText(f"预计剩余: {int(eta_seconds)}秒")
            elif percentage >= 100:
                self._eta_label.setText("")
        else:
            if self._progress_bar.maximum() == 0:
                self._progress_bar.setMaximum(100)
            if count < 1000:
                pct = min(int(count / 1000 * 30), 30)
            elif count < 5000:
                pct = 30 + min(int((count - 1000) / 4000 * 30), 30)
            elif count < 20000:
                pct = 60 + min(int((count - 5000) / 15000 * 20), 20)
            elif count < 100000:
                pct = 80 + min(int((count - 20000) / 80000 * 15), 15)
            else:
                pct = 95
            self._progress_bar.setValue(pct)
            self._percentage.setText(f"{pct}%")

    def append_file_log(self, file_path: str):
        """
        追加单个文件的扫描记录到日志。

        Args:
            file_path: 被扫描到的文件路径
        """
        self._file_log_count += 1
        filename = os.path.basename(file_path)
        # 使用 append 逐条添加，QTextEdit 会自动处理 HTML
        self._scan_log.append(
            f"<span style='color: {COLORS.TEXT_PLACEHOLDER}; font-size: {FONT.MICRO_PT}px;'>"
            f"[{self._file_log_count:,}]</span> {filename} "
            f"<span style='color: {COLORS.TEXT_PLACEHOLDER}; font-size: {FONT.MICRO_PT}px;'>"
            f"{file_path}</span>"
        )
        # 每隔一定数量自动滚动，避免频繁滚动影响性能
        if self._file_log_count % 10 == 0:
            sb = self._scan_log.verticalScrollBar()
            sb.setValue(sb.maximum())

    def set_finishing(self):
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(100)
        self._percentage.setText("100%")
        self._percentage.setStyleSheet(f"color: {COLORS.SUCCESS}; border: none; background: transparent;")
        self._title.setText("扫描完成！")
        self._detail.setText("正在加载索引...")
        self._eta_label.setText("")
        self._cancel_btn.setVisible(False)
        self._cancel_btn.setEnabled(False)
        self._progress_bar.setStyleSheet(progress_bar_success_style(16, 8))

    def set_cancelling(self):
        self._is_cancelling = True
        self._title.setText("正在取消扫描...")
        self._title.setStyleSheet(f"color: {COLORS.WARNING}; border: none; background: transparent;")
        self._detail.setText("请稍候，正在安全终止扫描进程")
        self._eta_label.setText("")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setText("取消中...")
        self._progress_bar.setStyleSheet(progress_bar_warning_style(16, 8))

    def set_error(self, err_msg: str):
        self._title.setText("扫描失败")
        self._title.setStyleSheet(f"color: {COLORS.ERROR}; border: none; background: transparent;")
        self._percentage.setText("!")
        self._percentage.setStyleSheet(f"color: {COLORS.ERROR}; border: none; background: transparent;")
        self._detail.setText(f"错误: {err_msg[:80]}")
        self._eta_label.setText("")
        self._cancel_btn.setText("返回")
        self._cancel_btn.setEnabled(True)
        self._cancel_btn.setVisible(True)
        self._progress_bar.setStyleSheet(progress_bar_error_style(16, 8))

    def reset_state(self):
        self._is_cancelling = False
        self._title.setText("正在扫描文件...")
        self._title.setStyleSheet(dialog_title_style())
        self._percentage.setStyleSheet(f"color: {COLORS.BRAND}; border: none; background: transparent;")
        self._progress_bar.setStyleSheet(progress_bar_style(16, 8))
        self._cancel_btn.setText("取消扫描")
        self._cancel_btn.setEnabled(True)
        self._cancel_btn.setVisible(True)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._percentage.setText("0%")
        self._detail.setText("已发现 0 个文件")
        self._eta_label.setText("")
        self._scan_log.clear()
        self._last_logged_dir = ""
        self._scan_start_time = 0.0

    def _on_cancel(self):
        if not self._is_cancelling:
            self.set_cancelling()
            self.scan_cancelled.emit()
