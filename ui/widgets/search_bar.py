from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QCheckBox, QPushButton
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer, QRectF, Property
from PySide6.QtGui import QFont, QIcon, QPainter, QPen, QColor, QPalette

SEARCH_INPUT_STYLE = """
    QLineEdit {
        padding: 10px 14px;
        border: 2px solid #E5E7EB;
        border-radius: 12px;
        font-size: 14px;
        background-color: #FFFFFF;
        color: #1F2937;
        outline: none;
    }
    QLineEdit:hover {
        border-color: #D1D5DB;
    }
    QLineEdit:focus {
        border-color: #7C3AED;
        background-color: #FFFFFF;
    }
"""

MODE_BTN_NORMAL = """
    QPushButton {
        padding: 8px 16px;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        color: #4B5563;
        font-size: 13px;
        font-weight: 500;
        outline: none;
    }
    QPushButton:hover {
        background-color: #F3F4F6;
        border-color: #D1D5DB;
    }
"""

MODE_BTN_ACTIVE = """
    QPushButton {
        padding: 8px 16px;
        border-radius: 10px;
        border: none;
        background-color: #7C3AED;
        color: #FFFFFF;
        font-size: 13px;
        font-weight: bold;
        outline: none;
    }
    QPushButton:hover {
        background-color: #6D28D9;
    }
"""

SEARCH_BTN_STYLE = """
    QPushButton {
        background-color: #7C3AED;
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        padding: 10px 20px;
        outline: none;
    }
    QPushButton:hover {
        background-color: #6D28D9;
    }
    QPushButton:pressed {
        background-color: #5B21B6;
    }
"""


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
        painter.setPen(QPen(QColor("#D1D5DB"), 2))
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRoundedRect(indicator_rect, 5, 5)

        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            bg_color = QColor("#7C3AED")
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
        painter.setPen(QColor("#4B5563"))
        font = QFont()
        font.setPointSize(13)
        painter.setFont(font)
        painter.drawText(int(text_x), int(self.height() / 2 + 5), self.text())
        painter.end()


class SearchBar(QWidget):
    search_triggered = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_mode = 'name'
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 14, 20, 8)
        main_layout.setSpacing(6)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入文件名关键词搜索...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet(SEARCH_INPUT_STYLE)
        self.search_input.returnPressed.connect(self._emit_search)

        self.mode_name_btn = QPushButton("文件名")
        self.mode_name_btn.setStyleSheet(MODE_BTN_ACTIVE)
        self.mode_name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_name_btn.clicked.connect(lambda: self._set_mode('name'))

        self.mode_content_btn = QPushButton("内容")
        self.mode_content_btn.setStyleSheet(MODE_BTN_NORMAL)
        self.mode_content_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_content_btn.clicked.connect(lambda: self._set_mode('content'))

        self.search_btn = AnimatedButton("搜索")
        self.search_btn.setFixedSize(80, 42)
        search_font = QFont()
        search_font.setPointSize(14)
        search_font.setBold(True)
        self.search_btn.setFont(search_font)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setStyleSheet(SEARCH_BTN_STYLE)
        self.search_btn.clicked.connect(self._emit_search)

        input_row.addWidget(self.search_input, 1)
        input_row.addWidget(self.mode_name_btn)
        input_row.addWidget(self.mode_content_btn)
        input_row.addWidget(self.search_btn)

        option_row = QHBoxLayout()
        option_row.setSpacing(20)

        self.case_sensitive_checkbox = AnimatedCheckBox("区分大小写")
        self.case_sensitive_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 6px;
                font-size: 13px;
                color: #4B5563;
                padding: 4px 0;
                outline: none;
            }
        """)

        option_row.addWidget(self.case_sensitive_checkbox)
        option_row.addStretch()

        main_layout.addLayout(input_row)
        main_layout.addLayout(option_row)

        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
            }
        """)

    def _set_mode(self, mode: str):
        self._search_mode = mode
        if mode == 'name':
            self.mode_name_btn.setStyleSheet(MODE_BTN_ACTIVE)
            self.mode_content_btn.setStyleSheet(MODE_BTN_NORMAL)
            self.search_input.setPlaceholderText("输入文件名关键词搜索...")
        else:
            self.mode_name_btn.setStyleSheet(MODE_BTN_NORMAL)
            self.mode_content_btn.setStyleSheet(MODE_BTN_ACTIVE)
            self.search_input.setPlaceholderText("输入文件内容关键词搜索...")

    def _emit_search(self):
        text = self.search_input.text()
        if self._search_mode == 'name':
            self.search_triggered.emit(text, "")
        else:
            self.search_triggered.emit("", text)

    def is_case_sensitive(self):
        return self.case_sensitive_checkbox.isChecked()

    def set_focus(self):
        self.search_input.setFocus()
