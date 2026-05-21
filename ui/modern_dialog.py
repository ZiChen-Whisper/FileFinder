from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFrame, QWidget, QHBoxLayout,
                             QLabel, QPushButton, QSizePolicy, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, QParallelAnimationGroup, Property, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QPixmap
from .style_constants import COLORS, FONT, RADIUS, DIALOG
from .style_manager import dialog_frame_style, dialog_title_style


class _DialogShadowFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("shadowFrame")
        self.setStyleSheet(dialog_frame_style())

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(0, 0)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = DIALOG.BORDER_RADIUS
        rect = QRectF(self.rect())

        painter.setBrush(QColor(COLORS.BG_PRIMARY))
        painter.setPen(QPen(QColor(DIALOG.BORDER_COLOR), 1))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), r, r)

        painter.end()

        super().paintEvent(event)


class ModernDialogBase(QDialog):
    def __init__(self, parent=None, title='', min_width=420, min_height=None, resizable=True):
        super().__init__(parent)
        self._title_text = title
        self._drag_pos = None
        self._resizable = resizable
        self._shadow_frame = None
        self._open_anim_group = None
        self._close_anim_group = None
        self._scale_factor = 1.0

        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(min_width)
        if min_height:
            self.setMinimumHeight(min_height)
        if resizable:
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        else:
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def get_scale_factor(self):
        return self._scale_factor

    def set_scale_factor(self, factor):
        self._scale_factor = factor
        if self._shadow_frame:
            self._shadow_frame.update()

    scale_factor = Property(float, get_scale_factor, set_scale_factor)

    def _create_shadow_frame(self, content_layout_fn, icon_pixmap=None):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(DIALOG.OUTER_MARGIN, DIALOG.OUTER_MARGIN, DIALOG.OUTER_MARGIN, DIALOG.OUTER_MARGIN)

        shadow_frame = _DialogShadowFrame()

        frame_layout = QVBoxLayout(shadow_frame)
        frame_layout.setSpacing(0)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet("background: transparent;")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(DIALOG.PADDING, 16, DIALOG.PADDING, 4)
        title_bar_layout.setSpacing(8)

        if icon_pixmap:
            icon_label = QLabel()
            scaled = icon_pixmap.scaled(QSize(22, 22), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled)
            icon_label.setFixedSize(22, 22)
            icon_label.setStyleSheet("border: none; background: transparent;")
            title_bar_layout.addWidget(icon_label)

        title_label = QLabel(self._title_text)
        title_font = QFont()
        title_font.setPointSize(FONT.TITLE_PT)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(dialog_title_style())
        title_bar_layout.addWidget(title_label, 1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-radius: {RADIUS.MEDIUM}px;
                background: transparent;
                color: {COLORS.TEXT_TERTIARY};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_HOVER};
                color: {COLORS.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.BG_TERTIARY};
            }}
        """)
        close_btn.clicked.connect(self._animate_close)
        title_bar_layout.addWidget(close_btn)

        frame_layout.addWidget(title_bar)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout_fn(content_widget)
        frame_layout.addWidget(content_widget)

        outer.addWidget(shadow_frame)
        self._shadow_frame = shadow_frame
        return shadow_frame

    def _animate_close(self):
        self._close_anim_group = QParallelAnimationGroup(self)

        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(180)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._close_anim_group.addAnimation(opacity_anim)

        geo_anim = QPropertyAnimation(self, b"geometry")
        cur_geo = self.geometry()
        shrink = 12
        target_geo = cur_geo.adjusted(shrink, shrink, -shrink, -shrink)
        # 确保缩小后的几何不小于最小尺寸，避免 QWindowsWindow::setGeometry 警告
        min_w = max(self.minimumWidth(), self.minimumSizeHint().width())
        min_h = max(self.minimumHeight() if self.minimumHeight() > 0 else 0, self.minimumSizeHint().height())
        if target_geo.width() < min_w:
            target_geo.setWidth(min_w)
        if min_h > 0 and target_geo.height() < min_h:
            target_geo.setHeight(min_h)
        geo_anim.setDuration(180)
        geo_anim.setStartValue(cur_geo)
        geo_anim.setEndValue(target_geo)
        geo_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._close_anim_group.addAnimation(geo_anim)

        self._close_anim_group.finished.connect(self.reject)
        self._close_anim_group.start()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._shadow_frame:
            return

        self.setWindowOpacity(0.0)

        final_geo = self.geometry()
        shrink = 12
        start_geo = final_geo.adjusted(shrink, shrink, -shrink, -shrink)
        # 确保起始几何不小于最小尺寸，避免 QWindowsWindow::setGeometry 警告
        min_w = max(self.minimumWidth(), self.minimumSizeHint().width())
        min_h = max(self.minimumHeight() if self.minimumHeight() > 0 else 0, self.minimumSizeHint().height())
        if start_geo.width() < min_w:
            start_geo.setWidth(min_w)
        if min_h > 0 and start_geo.height() < min_h:
            start_geo.setHeight(min_h)
        self.setGeometry(start_geo)

        self._open_anim_group = QParallelAnimationGroup(self)

        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(200)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._open_anim_group.addAnimation(opacity_anim)

        geo_anim = QPropertyAnimation(self, b"geometry")
        geo_anim.setDuration(200)
        geo_anim.setStartValue(start_geo)
        geo_anim.setEndValue(final_geo)
        geo_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._open_anim_group.addAnimation(geo_anim)

        self._open_anim_group.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            title_rect = QRectF(0, 0, self.width(), 60)
            if title_rect.contains(event.position()):
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
