from PySide6.QtWidgets import (QWidget, QLineEdit, QHBoxLayout, QVBoxLayout,
                             QCheckBox, QPushButton, QLabel, QRadioButton,
                             QComboBox, QDialog, QSizePolicy, QStyleOptionButton)
from PySide6.QtCore import (Signal, Qt, QPropertyAnimation, QEasingCurve, QSize,
                           QTimer, QRectF, Property, QPoint, QParallelAnimationGroup)
from PySide6.QtGui import (QFont, QFontMetrics, QIcon, QPainter, QPen, QColor,
                          QPalette, QBrush, QPixmap)

from constants import SEARCH_DEBOUNCE_MS
from utils.thread_helper import Debouncer
from utils.flow_layout import FlowLayout
from ..style_constants import COLORS, FONT, RADIUS, BTN, TRANSITION
from ..modern_dialog import ModernDialogBase
from ..style_manager import (
    search_input_style, search_button_style, radio_button_style,
    dialog_frame_style, dialog_title_style,
    button_primary, label_caption_style, label_micro_style,
    combo_box_style,
)


class AnimatedRadioButton(QRadioButton):
    _INDICATOR_MARGIN = 3

    def __init__(self, text="", parent=None, font_pt=None):
        super().__init__(text, parent)
        self._check_opacity = 0.0
        self._hovered = False
        self._font_pt = font_pt or FONT.CAPTION_PT
        self._anim = QPropertyAnimation(self, b"check_opacity")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._check_opacity)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def get_check_opacity(self):
        return self._check_opacity

    def set_check_opacity(self, opacity):
        self._check_opacity = opacity
        self.update()

    check_opacity = Property(float, get_check_opacity, set_check_opacity)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        m = self._INDICATOR_MARGIN
        indicator_size = 14
        indicator_y = (self.height() - indicator_size) / 2
        indicator_rect = QRectF(m, indicator_y, indicator_size, indicator_size)
        center = indicator_rect.center()
        outer_radius = indicator_size / 2

        if self.isEnabled():
            if self.isChecked():
                border_color = QColor(COLORS.BRAND)
                border_color.setAlphaF(max(0.3, self._check_opacity))
                if self._hovered:
                    border_color = QColor(COLORS.BRAND_HOVER)
                    border_color.setAlphaF(max(0.5, self._check_opacity))
                painter.setPen(QPen(border_color, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, outer_radius, outer_radius)

                inner_radius = outer_radius * 0.4
                dot_color = QColor(COLORS.BRAND_HOVER if self._hovered else COLORS.BRAND)
                dot_color.setAlphaF(self._check_opacity)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(dot_color)
                painter.drawEllipse(center, inner_radius, inner_radius)
            else:
                hover_border = QColor(COLORS.BRAND) if self._hovered else QColor(COLORS.BORDER_HOVER)
                painter.setPen(QPen(hover_border, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, outer_radius, outer_radius)
        else:
            if self.isChecked():
                painter.setPen(QPen(QColor(COLORS.BORDER_HOVER), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, outer_radius, outer_radius)

                inner_radius = outer_radius * 0.4
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(COLORS.BORDER_HOVER))
                painter.drawEllipse(center, inner_radius, inner_radius)
            else:
                painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, outer_radius, outer_radius)

        text_x = m + indicator_size + 6
        text_color = QColor(COLORS.TEXT_SECONDARY if self.isEnabled() else COLORS.TEXT_PLACEHOLDER)
        if self._hovered and self.isEnabled():
            text_color = QColor(COLORS.TEXT_PRIMARY)
        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(self._font_pt)
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_rect = QRectF(text_x, 0, fm.horizontalAdvance(self.text()) + 4, self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        painter.end()

    def minimumSizeHint(self):
        font = QFont()
        font.setPointSize(self._font_pt)
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self.text())
        return QSize(self._INDICATOR_MARGIN + 14 + 6 + text_width + 4, 26)

    def sizeHint(self):
        return self.minimumSizeHint()


class SegmentedControl(QWidget):
    mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments = ['文件名', '文件内容']
        self._current_index = 0
        self._slider_pos = 0.0
        self._hovered_segment = -1
        self.setFixedHeight(30)
        self._slider_anim = QPropertyAnimation(self, b"slider_pos")
        self._slider_anim.setDuration(200)
        self._slider_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

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
        fm = QFontMetrics(QFont("Microsoft YaHei", 11))
        w = 0
        for s in self._segments:
            w += fm.horizontalAdvance(s) + 32
        return QSize(w + 8, 30)

    def sizeHint(self):
        return self.minimumSizeHint()

    def mouseMoveEvent(self, event):
        seg_w = self.width() / len(self._segments)
        idx = int(event.position().x() / seg_w)
        idx = max(0, min(idx, len(self._segments) - 1))
        if idx != self._hovered_segment:
            self._hovered_segment = idx
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hovered_segment = -1
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        r = BTN.BORDER_RADIUS

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS.BG_SECONDARY))
        painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        seg_w = w / len(self._segments)
        slider_x = self._slider_pos * seg_w + 2
        slider_w = seg_w - 4
        slider_h = h - 4
        slider_y = 2
        slider_r = max(r - 2, 2)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS.BRAND))
        painter.drawRoundedRect(QRectF(slider_x, slider_y, slider_w, slider_h), slider_r, slider_r)

        font = QFont()
        font.setPointSize(FONT.MICRO_PT)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)

        for i, seg in enumerate(self._segments):
            if i == self._current_index:
                painter.setPen(QColor(COLORS.BG_PRIMARY))
                font.setBold(True)
                painter.setFont(font)
            elif i == self._hovered_segment:
                painter.setPen(QColor(COLORS.TEXT_PRIMARY))
                font.setBold(False)
                font.setWeight(QFont.Weight.Medium)
                painter.setFont(font)
            else:
                painter.setPen(QColor(COLORS.TEXT_TERTIARY))
                font.setBold(False)
                font.setWeight(QFont.Weight.Medium)
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


class SettingsArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_vlayout = QVBoxLayout(self)
        self._main_vlayout.setContentsMargins(16, 6, 16, 6)
        self._main_vlayout.setSpacing(2)

        self._flow_layout = FlowLayout(spacing=10)
        self._main_vlayout.addLayout(self._flow_layout)

    def add_to_line1(self, widget):
        self._flow_layout.addWidget(widget)

    def set_line2(self, widget):
        pass

    def add_stretch_to_line1(self):
        pass

    def set_line2_content_visible(self, visible):
        pass


class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._orig_size = None
        self._hover_opacity = 0.0
        self._hover_anim = QPropertyAnimation(self, b"hover_opacity")
        self._hover_anim.setDuration(TRANSITION.COLOR_FADE_MS)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._press_anim = QPropertyAnimation(self, b"minimumSize")
        self._press_anim.setDuration(TRANSITION.PRESS_SCALE_MS)
        self._press_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._release_anim = QPropertyAnimation(self, b"minimumSize")
        self._release_anim.setDuration(TRANSITION.RELEASE_SCALE_MS)
        self._release_anim.setEasingCurve(QEasingCurve.Type.OutBack)

    def get_hover_opacity(self):
        return self._hover_opacity

    def set_hover_opacity(self, opacity):
        self._hover_opacity = opacity
        self.update()

    hover_opacity = Property(float, get_hover_opacity, set_hover_opacity)

    def enterEvent(self, event):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_opacity)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_opacity)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(event)

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
    _INDICATOR_MARGIN = 3

    def __init__(self, text="", parent=None, font_pt=None):
        super().__init__(text, parent)
        self._check_opacity = 0.0
        self._hovered = False
        self._font_pt = font_pt or FONT.CAPTION_PT
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

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        m = self._INDICATOR_MARGIN
        indicator_rect = QRectF(m, (self.height() - 18) / 2, 18, 18)
        border_color = QColor(COLORS.BRAND if self._hovered else COLORS.BORDER_HOVER)
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(indicator_rect, 5, 5)

        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            bg_color = QColor(COLORS.BRAND_HOVER if self._hovered else COLORS.BRAND)
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

        text_x = m + 18 + 8
        text_color = QColor(COLORS.TEXT_PRIMARY if self._hovered else COLORS.TEXT_SECONDARY)
        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(self._font_pt)
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_rect = QRectF(text_x, 0, fm.horizontalAdvance(self.text()) + 4, self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        painter.end()

    def minimumSizeHint(self):
        font = QFont()
        font.setPointSize(self._font_pt)
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self.text())
        return QSize(self._INDICATOR_MARGIN + 18 + 8 + text_width + 4, 26)

    def sizeHint(self):
        return self.minimumSizeHint()


class HelpIconLabel(QLabel):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setToolTip("了解匹配模式")
        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg_color = QColor(COLORS.BRAND_LIGHT_BG) if self._hovered else QColor(COLORS.BG_TERTIARY)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, 16, 16)
        text_color = QColor(COLORS.BRAND) if self._hovered else QColor(COLORS.TEXT_TERTIARY)
        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, 18, 18), Qt.AlignmentFlag.AlignCenter, "?")
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MatchModeHelpDialog(ModernDialogBase):
    def __init__(self, parent=None):
        super().__init__(parent, title="匹配模式说明", min_width=380, resizable=False)
        self._init_ui()

    def _init_ui(self):
        def build_content(content_widget):
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(12)
            layout.setContentsMargins(24, 4, 24, 24)

            modes = [
                ("模糊匹配", "输入关键词，在文件名中任意位置匹配。例如输入\"read\"可匹配\"README.md\"、\"spreadsheet.xlsx\"。"),
                ("精确匹配", "输入完整文件名（含扩展名），必须完全一致才匹配。例如输入\"main.py\"只匹配\"main.py\"。"),
                ("通配符匹配", "使用通配符 * 和 ? 进行匹配。* 匹配任意多个字符，? 匹配单个字符。例如\"*.py\"匹配所有Python文件。"),
                ("正则表达式", "使用正则表达式进行高级匹配，适合有经验的用户。例如\"\\d+\\.py\"匹配以数字开头的Python文件。"),
            ]

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

        self._create_shadow_frame(build_content)


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

        self._settings_area = SettingsArea()

        self.segmented_control = SegmentedControl()
        self.segmented_control.mode_changed.connect(self._set_mode)

        self._settings_area.add_to_line1(self.segmented_control)

        settings_font_size = f"{FONT.MICRO_PT}px"

        self.case_sensitive_checkbox = AnimatedCheckBox("区分大小写", font_pt=FONT.MICRO_PT)
        self.case_sensitive_checkbox.setStyleSheet(f"""
            QCheckBox {{
                spacing: 6px;
                font-size: {settings_font_size};
                color: {COLORS.TEXT_SECONDARY};
                outline: none;
                text-decoration: none;
                border: none;
                background: transparent;
            }}
            QCheckBox:focus {{
                outline: none;
                border: none;
            }}
        """)

        self._settings_area.add_to_line1(self.case_sensitive_checkbox)

        self.match_mode_label = QLabel("匹配模式:")
        self.match_mode_label.setStyleSheet(f"font-size: {settings_font_size}; color: {COLORS.TEXT_SECONDARY}; border: none; background: transparent; text-decoration: none;")
        self._settings_area.add_to_line1(self.match_mode_label)

        self._match_mode_combo = QComboBox()
        for mode in self.MATCH_MODES:
            self._match_mode_combo.addItem(self.MATCH_MODE_LABELS[mode], mode)
        self._match_mode_combo.setCurrentIndex(0)
        self._match_mode_combo.setFixedHeight(28)
        self._match_mode_combo.setStyleSheet(combo_box_style())
        self._match_mode_combo.currentIndexChanged.connect(self._on_match_mode_changed)
        self._settings_area.add_to_line1(self._match_mode_combo)

        self.help_icon = HelpIconLabel()
        self.help_icon.clicked.connect(self._show_match_mode_help)
        self._settings_area.add_to_line1(self.help_icon)

        self._settings_area.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_SECONDARY};
                border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
            }}
        """)

        main_layout.addWidget(search_area)

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
            self._match_mode_combo.setVisible(True)
            self.help_icon.setVisible(True)
        else:
            self.search_input.setPlaceholderText("输入文件内容关键词搜索...")
            self.match_mode_label.setVisible(False)
            self._match_mode_combo.setVisible(False)
            self.help_icon.setVisible(False)

    def _set_match_mode(self, mode: str):
        self._name_match_mode = mode
        idx = self.MATCH_MODES.index(mode) if mode in self.MATCH_MODES else 0
        self._match_mode_combo.setCurrentIndex(idx)

    def _on_match_mode_changed(self, index: int):
        if 0 <= index < len(self.MATCH_MODES):
            self._name_match_mode = self.MATCH_MODES[index]

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

    def get_settings_widget(self):
        return self._settings_area

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
