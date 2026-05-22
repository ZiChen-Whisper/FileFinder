from PySide6.QtWidgets import QRadioButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, Property, QSize
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QPen, QColor
from ..style_constants import COLORS, FONT


class AnimatedRadioButton(QRadioButton):
    """带动画的单选按钮，自定义绘制圆形指示器 + 选中动画"""

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
