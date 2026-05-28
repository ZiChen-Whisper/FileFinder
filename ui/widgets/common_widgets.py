import os
import math
import logging
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                             QSplitter, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPixmap, QIcon

from ..style_constants import COLORS, FONT, RADIUS

logger = logging.getLogger(__name__)


class ElidedPathLabel(QLabel):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self._full_path = path
        self._update_display()
        self.setToolTip(path)

    def _update_display(self):
        path = self._full_path.rstrip(os.sep)
        name = os.path.basename(path) or path
        parent_part = path[:len(path) - len(name)] if name != path else ""
        if parent_part and name != path:
            self.setText(f"{parent_part}<b>{name}</b>")
        else:
            self.setText(f"<b>{name}</b>")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self):
        fm = self.fontMetrics()
        available = self.width()
        path = self._full_path.rstrip(os.sep)
        name = os.path.basename(path) or path
        parent_part = path[:len(path) - len(name)] if name != path else ""
        full_text = f"{parent_part}{name}"
        elided = fm.elidedText(full_text, Qt.TextElideMode.ElideMiddle, available)
        if elided.endswith('…') or elided != full_text:
            super().setText(elided)
        else:
            if parent_part and name != path:
                super().setText(f"{parent_part}<b>{name}</b>")
            else:
                super().setText(f"<b>{name}</b>")

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self):
        return QSize(0, super().minimumSizeHint().height())


class CollapsibleSection(QWidget):
    def __init__(self, title: str, default_expanded: bool = True, parent=None):
        super().__init__(parent)
        self._expanded = default_expanded
        self._title = title
        self._content_widget = None
        self._toggle_btn = None
        self._header_widget = None
        self._animation = None
        self._content_height = 0
        self._init_header()

    def _init_header(self):
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._header_widget = QWidget()
        self._header_widget.setObjectName("sectionHeader")
        self._header_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header_widget.setStyleSheet(f"""
            QWidget#sectionHeader {{
                background-color: {COLORS.BG_PRIMARY};
                border-radius: {RADIUS.LARGE}px;
                border: none;
            }}
            QWidget#sectionHeader:hover {{
                background-color: {COLORS.BG_HOVER};
            }}
        """)
        header_row = QHBoxLayout(self._header_widget)
        header_row.setContentsMargins(10, 6, 10, 6)
        header_row.setSpacing(6)

        self._toggle_btn = QPushButton()
        self._toggle_btn.setFixedSize(16, 16)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                outline: none;
                border-radius: {RADIUS.SMALL}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_HOVER};
            }}
        """)
        self._toggle_btn.clicked.connect(self._toggle)
        self._update_toggle_icon()

        title_label = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(FONT.BODY_PT)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; border: none; background: transparent;")

        header_row.addWidget(self._toggle_btn)
        header_row.addWidget(title_label)
        header_row.addStretch()

        self._header_widget.mousePressEvent = lambda e: self._toggle() if e.button() == Qt.MouseButton.LeftButton else None

        self._main_layout.addWidget(self._header_widget)
        self.setLayout(self._main_layout)

    def _update_toggle_icon(self):
        painter = QPainter()
        dpr = self.devicePixelRatio() if hasattr(self, 'devicePixelRatio') else 1.0
        pixmap = QPixmap(int(16 * dpr), int(16 * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(COLORS.BRAND), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        cx, cy = 8, 8
        if self._expanded:
            painter.drawLine(4, 6, 8, 10)
            painter.drawLine(8, 10, 12, 6)
        else:
            painter.drawLine(6, 4, 10, 8)
            painter.drawLine(10, 8, 6, 12)
        painter.end()
        self._toggle_btn.setIcon(QIcon(pixmap))

    def _toggle(self):
        self._expanded = not self._expanded
        self._update_toggle_icon()
        if self._content_widget:
            if self._animation:
                self._animation.stop()
                self._animation = None
            if self._expanded:
                self._content_widget.setVisible(True)
                content_height = self._content_widget.sizeHint().height()
                self._content_widget.setMaximumHeight(0)
                self._animation = QPropertyAnimation(self._content_widget, b"maximumHeight")
                self._animation.setDuration(200)
                self._animation.setStartValue(0)
                self._animation.setEndValue(content_height)
                self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                self._animation.finished.connect(self._on_expand_finished)
                self._animation.start()
            else:
                current_height = self._content_widget.height()
                self._animation = QPropertyAnimation(self._content_widget, b"maximumHeight")
                self._animation.setDuration(200)
                self._animation.setStartValue(current_height)
                self._animation.setEndValue(0)
                self._animation.setEasingCurve(QEasingCurve.Type.InCubic)
                self._animation.finished.connect(self._on_collapse_finished)
                self._animation.start()

    def _on_expand_finished(self):
        if self._content_widget:
            self._content_widget.setMaximumHeight(16777215)

    def _on_collapse_finished(self):
        if self._content_widget and not self._expanded:
            self._content_widget.setVisible(False)
            self._content_widget.setMaximumHeight(0)

    def set_content(self, widget: QWidget):
        self._content_widget = widget
        self._content_widget.setVisible(self._expanded)
        if not self._expanded:
            self._content_widget.setMaximumHeight(0)
        self._main_layout.addWidget(self._content_widget)


class HoverInfoIcon(QLabel):
    def __init__(self, tooltip_text: str, parent=None):
        super().__init__(parent)
        self._tooltip_text = tooltip_text
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setToolTip(tooltip_text)
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
        painter.setPen(Qt.PenStyle.NoPen)
        bg_color = QColor(COLORS.BRAND) if self._hovered else QColor(COLORS.BORDER_HOVER)
        painter.setBrush(bg_color)
        painter.drawEllipse(0, 0, 16, 16)
        painter.setPen(QColor(COLORS.BG_PRIMARY))
        font = QFont()
        font.setPointSize(FONT.ICON_PT)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, 16, 16), Qt.AlignmentFlag.AlignCenter, "!")
        painter.end()


class InfoIconLabel(QLabel):
    """静态信息图标（"!"圆形），无悬停效果"""

    def __init__(self, tooltip_text: str, parent=None):
        super().__init__(parent)
        self._tooltip_text = tooltip_text
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setToolTip(tooltip_text)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS.BORDER_HOVER))
        painter.drawEllipse(0, 0, 16, 16)
        painter.setPen(QColor(COLORS.BG_PRIMARY))
        font = QFont()
        font.setPointSize(FONT.ICON_PT)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, 16, 16), Qt.AlignmentFlag.AlignCenter, "!")
        painter.end()


class LoadingSpinner(QWidget):
    """旋转点加载动画控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._rotate)
        self._dot_count = 8
        self._dot_radius = 3
        self._radius = 14
        self.setFixedSize(48, 48)
        self.setVisible(False)

    def start(self):
        self._angle = 0
        self.setVisible(True)
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.setVisible(False)

    def _rotate(self):
        self._angle = (self._angle + 45) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center_x = self.width() / 2
        center_y = self.height() / 2

        for i in range(self._dot_count):
            angle = (self._angle + i * (360 / self._dot_count)) % 360
            alpha = int(255 * (1 - i / self._dot_count))
            rad = angle * 3.14159265 / 180
            x = center_x + self._radius * math.cos(rad)
            y = center_y + self._radius * math.sin(rad)
            color = QColor(COLORS.BRAND)
            color.setAlpha(alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(int(x - self._dot_radius), int(y - self._dot_radius),
                              self._dot_radius * 2, self._dot_radius * 2)
        painter.end()


class RoundedPanel(QWidget):
    """圆角面板，带阴影效果和左侧边缘拖拽调整宽度功能"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._resize_edge_width = 6
        self._hovering_edge = False
        self._dragging = False
        self._drag_start_x = 0
        self._drag_start_sizes = []
        self.setMouseTracking(True)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(0, 0)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = RADIUS.LARGE
        rect = QRectF(self.rect())

        painter.setBrush(QColor(COLORS.BG_PRIMARY))
        painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 1))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), r, r)

        painter.end()

    def _get_splitter(self):
        splitter = self.parent()
        if isinstance(splitter, QSplitter):
            return splitter
        return None

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and event.position().x() < self._resize_edge_width):
            splitter = self._get_splitter()
            if splitter:
                self._dragging = True
                self._drag_start_x = event.globalPosition().x()
                self._drag_start_sizes = splitter.sizes()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            splitter = self._get_splitter()
            if splitter:
                delta = self._drag_start_x - event.globalPosition().x()
                my_index = splitter.indexOf(self)
                new_width = max(self.minimumWidth(),
                                self._drag_start_sizes[my_index] + delta)
                total = sum(self._drag_start_sizes)
                other_index = 1 - my_index
                other_width = max(splitter.widget(other_index).minimumWidth(),
                                  total - new_width)
                if new_width + other_width <= total:
                    splitter.setSizes([other_width, new_width]
                                      if my_index == 1 else [new_width, other_width])
            event.accept()
            return
        if event.position().x() < self._resize_edge_width:
            if not self._hovering_edge:
                self._hovering_edge = True
                self.setCursor(Qt.CursorShape.SplitHCursor)
        else:
            if self._hovering_edge:
                self._hovering_edge = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        if not self._dragging:
            if self._hovering_edge:
                self._hovering_edge = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)
