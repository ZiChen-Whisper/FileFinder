from PySide6.QtWidgets import (QWidget, QLineEdit, QHBoxLayout, QVBoxLayout,
                             QCheckBox, QPushButton, QLabel, QRadioButton,
                             QButtonGroup, QDialog, QSizePolicy)
from PySide6.QtCore import (Signal, Qt, QPropertyAnimation, QEasingCurve, QSize,
                           QTimer, QRectF, Property, QPoint, QParallelAnimationGroup)
from PySide6.QtGui import (QFont, QFontMetrics, QIcon, QPainter, QPen, QColor,
                          QPalette, QBrush, QPixmap)

from constants import SEARCH_DEBOUNCE_MS
from utils.thread_helper import Debouncer
from ..style_constants import COLORS, FONT, RADIUS, BTN
from ..style_manager import (
    search_input_style, search_button_style, radio_button_style,
    checkbox_style, dialog_frame_style, dialog_title_style,
    button_primary, label_caption_style, label_micro_style,
)


class SegmentedControl(QWidget):
    mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments = ['文件名', '文件内容']
        self._current_index = 0
        self._slider_pos = 0.0
        self.setFixedHeight(32)
        self._slider_anim = QPropertyAnimation(self, b"slider_pos")
        self._slider_anim.setDuration(200)
        self._slider_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def get_slider_pos(self):
        return self._slider_pos

    def set_slider_pos(self, pos):
        self._slider_pos = pos
        self.update()

    slider_pos = Property(float, get_slider_pos, set_slider_pos)

    def set_current_index(self, index: int):
        if index == self._current_index:
            return
        self._current_index = index
        self._slider_anim.stop()
        self._slider_anim.setStartValue(self._slider_pos)
        self._slider_anim.setEndValue(float(index))
        self._slider_anim.start()
        self.mode_changed.emit('name' if index == 0 else 'content')

    def current_index(self) -> int:
        return self._current_index

    def minimumSizeHint(self):
        fm = QFontMetrics(QFont("Microsoft YaHei", 12))
        w = 0
        for s in self._segments:
            w += fm.horizontalAdvance(s) + 32
        return QSize(w + 8, 32)

    def sizeHint(self):
        return self.minimumSizeHint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        r = 8

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS.BG_HOVER))
        painter.drawRoundedRect(0, 0, w, h, r, r)

        painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, w, h, r, r)

        seg_w = w / len(self._segments)
        slider_x = self._slider_pos * seg_w + 2
        slider_w = seg_w - 4
        slider_h = h - 4
        slider_y = 2
        slider_r = 6

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS.BRAND))
        painter.drawRoundedRect(int(slider_x), slider_y, int(slider_w), slider_h, slider_r, slider_r)

        font = QFont()
        font.setPointSize(FONT.MICRO_PT)
        painter.setFont(font)

        for i, seg in enumerate(self._segments):
            cx = seg_w * i + seg_w / 2
            if i == self._current_index:
                painter.setPen(QColor(COLORS.BG_PRIMARY))
                font.setBold(True)
                painter.setFont(font)
            else:
                painter.setPen(QColor(COLORS.TEXT_TERTIARY))
                font.setBold(False)
                painter.setFont(font)
            painter.drawText(QRectF(seg_w * i, 0, seg_w, h), Qt.AlignmentFlag.AlignCenter, seg)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            seg_w = self.width() / len(self._segments)
            idx = int(event.position().x() / seg_w)
            idx = max(0, min(idx, len(self._segments) - 1))
            self.set_current_index(idx)
        super().mousePressEvent(event)


class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._orig_size = None
        self._press_anim = QPropertyAnimation(self, b"minimumSize")
        self._press_anim.setDuration(80)
        self._press_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._release_anim = QPropertyAnimation(self, b"minimumSize")
        self._release_anim.setDuration(180)
        self._release_anim.setEasingCurve(QEasingCurve.Type.OutBack)

    def showEvent(self, event):
        super().showEvent(event)
        self._orig_size = self.size()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._orig_size is None:
            self._orig_size = self.size()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._release_anim.stop()
            self._press_anim.stop()
            cur = self.size()
            target = QSize(int(cur.width() * 1.06), int(cur.height() * 1.06))
            self._press_anim.setStartValue(cur)
            self._press_anim.setEndValue(target)
            self._press_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_anim.stop()
            self._release_anim.stop()
            self._release_anim.setStartValue(self.size())
            self._release_anim.setEndValue(self._orig_size if self._orig_size else self.size())
            self._release_anim.start()
        super().mouseReleaseEvent(event)


class AnimatedCheckBox(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._check_opacity = 0.0
        self._anim = QPropertyAnimation(self, b"check_opacity")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.stateChanged.connect(self._on_state_changed)

    def _on_state_changed(self, state):
        self._anim.stop()
        self._anim.setStartValue(self._check_opacity)
        self._anim.setEndValue(1.0 if state == Qt.CheckState.Checked.value else 0.0)
        self._anim.start()

    def get_check_opacity(self):
        return self._check_opacity

    def set_check_opacity(self, opacity):
        self._check_opacity = opacity
        self.update()

    check_opacity = Property(float, get_check_opacity, set_check_opacity)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        indicator_rect = QRectF(0, (self.height() - 18) / 2, 18, 18)
        painter.setPen(QPen(QColor(COLORS.BORDER_HOVER), 2))
        painter.setBrush(QColor(COLORS.BG_PRIMARY))
        painter.drawRoundedRect(indicator_rect, 5, 5)

        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            bg_color = QColor(COLORS.BRAND)
            bg_color.setAlphaF(self._check_opacity)
            painter.setBrush(bg_color)
            painter.drawRoundedRect(indicator_rect, 5, 5)

            if self._check_opacity > 0.1:
                check_alpha = int(self._check_opacity * 255)
                pen = QPen(QColor(255, 255, 255, check_alpha))
                pen.setWidth(2)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawLine(int(indicator_rect.left() + 4), int(indicator_rect.center().y() + 1),
                               int(indicator_rect.center().x() - 1), int(indicator_rect.bottom() - 5))
                painter.drawLine(int(indicator_rect.center().x() - 1), int(indicator_rect.bottom() - 5),
                               int(indicator_rect.right() - 4), int(indicator_rect.top() + 5))

        text_x = 26
        painter.setPen(QColor(COLORS.TEXT_SECONDARY))
        font = QFont()
        font.setPointSize(FONT.CAPTION_PT)
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_rect = QRectF(text_x, 0, fm.horizontalAdvance(self.text()) + 4, self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        painter.end()

    def minimumSizeHint(self):
        font = QFont()
        font.setPointSize(FONT.CAPTION_PT)
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self.text())
        return QSize(26 + text_width + 16, 26)

    def sizeHint(self):
        return self.minimumSizeHint()


class HelpIconLabel(QLabel):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("了解匹配模式")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS.TEXT_PLACEHOLDER))
        painter.drawEllipse(1, 1, 16, 16)

        painter.setPen(QColor(COLORS.BG_PRIMARY))
        font = QFont()
        font.setPointSize(FONT.MICRO_PT)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(1, 1, 16, 16), Qt.AlignmentFlag.AlignCenter, "?")
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MatchModeHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("匹配模式说明")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(380)
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        shadow_frame = QWidget()
        shadow_frame.setObjectName("shadowFrame")
        shadow_frame.setStyleSheet(dialog_frame_style().replace("QFrame#shadowFrame", "QWidget#shadowFrame"))

        layout = QVBoxLayout(shadow_frame)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        title_label = QLabel("匹配模式说明")
        title_font = QFont()
        title_font.setPointSize(FONT.TITLE_PT)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(dialog_title_style())

        modes = [
            ("模糊匹配", "输入关键词，在文件名中任意位置匹配。例如输入\"read\"可匹配\"README.md\"、\"spreadsheet.xlsx\"。"),
            ("精确匹配", "输入完整文件名（含扩展名），必须完全一致才匹配。例如输入\"main.py\"只匹配\"main.py\"。"),
            ("通配符匹配", "使用通配符 * 和 ? 进行匹配。* 匹配任意多个字符，? 匹配单个字符。例如\"*.py\"匹配所有Python文件。"),
            ("正则表达式", "使用正则表达式进行高级匹配，适合有经验的用户。例如\"\\d+\\.py\"匹配以数字开头的Python文件。"),
        ]

        layout.addWidget(title_label)

        for name, desc in modes:
            mode_layout = QVBoxLayout()
            mode_layout.setSpacing(2)
            mode_layout.setContentsMargins(0, 0, 0, 0)

            name_label = QLabel(name)
            name_label.setStyleSheet(f"color: {COLORS.BRAND}; font-size: {BTN.FONT_SIZE}; font-weight: bold; border: none; background: transparent;")

            desc_label = QLabel(desc)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(label_caption_style())

            mode_layout.addWidget(name_label)
            mode_layout.addWidget(desc_label)
            layout.addLayout(mode_layout)

        close_btn = QPushButton("我知道了")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(button_primary("padding: 8px 28px; border-radius: 10px; min-width: 80px;"))
        close_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        btn_row.addStretch()

        layout.addSpacing(4)
        layout.addLayout(btn_row)

        outer.addWidget(shadow_frame)


class SearchBar(QWidget):
    search_triggered = Signal(str, str)

    MATCH_MODES = ['fuzzy', 'exact', 'wildcard', 'regex']
    MATCH_MODE_LABELS = {'fuzzy': '模糊', 'exact': '精确', 'wildcard': '通配符', 'regex': '正则'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_mode = 'name'
        self._name_match_mode = 'fuzzy'
        self._debouncer = Debouncer(delay_ms=SEARCH_DEBOUNCE_MS, parent=self)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        search_area = QWidget()
        search_layout = QVBoxLayout()
        search_layout.setContentsMargins(20, 14, 20, 10)
        search_layout.setSpacing(0)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入文件名关键词搜索...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet(search_input_style())
        self.search_input.returnPressed.connect(self._emit_search)
        self.search_input.textChanged.connect(self._on_text_changed)

        self.search_btn = AnimatedButton("搜索")
        self.search_btn.setFixedSize(80, 42)
        search_font = QFont()
        search_font.setPointSize(FONT.TITLE_PT)
        search_font.setBold(True)
        self.search_btn.setFont(search_font)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setStyleSheet(search_button_style())
        self.search_btn.clicked.connect(self._emit_search)

        input_row.addWidget(self.search_input, 1)
        input_row.addWidget(self.search_btn)

        search_layout.addLayout(input_row)
        search_area.setLayout(search_layout)
        search_area.setStyleSheet(f"QWidget {{ background-color: {COLORS.BG_PRIMARY}; }}")

        settings_area = QWidget()
        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(20, 6, 20, 6)
        settings_layout.setSpacing(12)

        self.segmented_control = SegmentedControl()
        self.segmented_control.mode_changed.connect(self._set_mode)

        settings_layout.addWidget(self.segmented_control)

        self.case_sensitive_checkbox = AnimatedCheckBox("区分大小写")
        self.case_sensitive_checkbox.setStyleSheet(checkbox_style())

        settings_layout.addWidget(self.case_sensitive_checkbox)

        self.match_mode_label = QLabel("匹配模式:")
        self.match_mode_label.setStyleSheet(label_caption_style())
        settings_layout.addWidget(self.match_mode_label)

        self.help_icon = HelpIconLabel()
        self.help_icon.clicked.connect(self._show_match_mode_help)
        settings_layout.addWidget(self.help_icon)

        self._match_mode_group = QButtonGroup(self)
        self._match_mode_radios = {}
        for mode in self.MATCH_MODES:
            radio = QRadioButton(self.MATCH_MODE_LABELS[mode])
            radio.setCursor(Qt.CursorShape.PointingHandCursor)
            radio.setStyleSheet(radio_button_style())
            if mode == self._name_match_mode:
                radio.setChecked(True)
            radio.clicked.connect(lambda checked, m=mode: self._set_match_mode(m))
            self._match_mode_group.addButton(radio)
            self._match_mode_radios[mode] = radio
            settings_layout.addWidget(radio)

        settings_layout.addStretch()

        settings_area.setLayout(settings_layout)
        settings_area.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_TERTIARY};
                border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
            }}
        """)

        main_layout.addWidget(search_area)
        main_layout.addWidget(settings_area)

        self.setLayout(main_layout)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_PRIMARY};
                border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
            }}
        """)

    def _set_mode(self, mode: str):
        self._search_mode = mode
        if mode == 'name':
            self.search_input.setPlaceholderText("输入文件名关键词搜索...")
            self.match_mode_label.setVisible(True)
            self.help_icon.setVisible(True)
            for radio in self._match_mode_radios.values():
                radio.setVisible(True)
        else:
            self.search_input.setPlaceholderText("输入文件内容关键词搜索...")
            self.match_mode_label.setVisible(False)
            self.help_icon.setVisible(False)
            for radio in self._match_mode_radios.values():
                radio.setVisible(False)

    def _set_match_mode(self, mode: str):
        self._name_match_mode = mode
        if mode in self._match_mode_radios:
            self._match_mode_radios[mode].setChecked(True)

    def _show_match_mode_help(self):
        dialog = MatchModeHelpDialog(self)
        dialog.exec()

    def _on_text_changed(self, text: str):
        if text.strip():
            self._debouncer.trigger(self._emit_search)
        else:
            self._debouncer._timer.stop()

    def _emit_search(self):
        text = self.search_input.text()
        if self._search_mode == 'name':
            self.search_triggered.emit(text, "")
        else:
            self.search_triggered.emit("", text)

    def is_case_sensitive(self):
        return self.case_sensitive_checkbox.isChecked()

    def get_name_mode(self) -> str:
        return self._name_match_mode

    def get_name_query(self) -> str:
        if self._search_mode == 'name':
            return self.search_input.text()
        return ""

    def get_content_query(self) -> str:
        if self._search_mode == 'content':
            return self.search_input.text()
        return ""

    def set_focus(self):
        self.search_input.setFocus()
