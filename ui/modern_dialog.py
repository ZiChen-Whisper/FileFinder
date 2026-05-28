from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFrame, QWidget, QHBoxLayout,
                             QLabel, QPushButton, QSizePolicy, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, QParallelAnimationGroup, Property, QSize, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QPixmap, QPolygonF
from .style_constants import COLORS, FONT, RADIUS, BTN, DIALOG
from .style_manager import dialog_frame_style, dialog_title_style, button_primary, button_secondary, dialog_body_style


class _CloseButton(QPushButton):
    """使用 QPainter 绘制 X 关闭图标的按钮，支持 hover 变色"""

    def __init__(self, parent=None):
        super().__init__(parent)
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
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(COLORS.TEXT_PRIMARY) if self._hovered else QColor(COLORS.TEXT_TERTIARY)
        pen = QPen(color, 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(9, 9, 19, 19)
        painter.drawLine(19, 9, 9, 19)
        painter.end()


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

        close_btn = _CloseButton()
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-radius: {RADIUS.MEDIUM}px;
                background: transparent;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BG_HOVER};
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

        if self._resizable:
            geo_anim = QPropertyAnimation(self, b"geometry")
            cur_geo = self.geometry()
            shrink = 12
            target_geo = cur_geo.adjusted(shrink, shrink, -shrink, -shrink)
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
        self.adjustSize()

        final_geo = self.geometry()

        self._open_anim_group = QParallelAnimationGroup(self)

        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(200)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._open_anim_group.addAnimation(opacity_anim)

        if self._resizable:
            shrink = 12
            start_geo = final_geo.adjusted(shrink, shrink, -shrink, -shrink)
            min_w = max(self.minimumWidth(), self.minimumSizeHint().width())
            min_h = max(self.minimumHeight() if self.minimumHeight() > 0 else 0, self.minimumSizeHint().height())
            if start_geo.width() < min_w:
                start_geo.setWidth(min_w)
            if min_h > 0 and start_geo.height() < min_h:
                start_geo.setHeight(min_h)
            self.setGeometry(start_geo)

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


class ModernMessageBox(ModernDialogBase):
    """现代化消息对话框，支持 info/warning/error/question 四种图标类型"""

    def __init__(self, parent=None, icon_type='info', title='', text='', buttons=None):
        super().__init__(parent, title=title, min_width=DIALOG.MIN_WIDTH, resizable=False)
        self._result = None
        self._buttons = buttons or {}
        self._icon_type = icon_type
        self._text = text
        self._init_ui()

    def _init_ui(self):
        icon_pixmap = self._create_icon_pixmap()

        def build_content(content_widget):
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(DIALOG.CONTENT_SPACING)
            layout.setContentsMargins(DIALOG.PADDING, 4, DIALOG.PADDING, DIALOG.PADDING)

            text_label = QLabel(self._text)
            text_label.setStyleSheet(dialog_body_style())
            text_label.setWordWrap(True)

            layout.addWidget(text_label)

            btn_row = QHBoxLayout()
            btn_row.addStretch()

            for key, (label, style_type) in self._buttons.items():
                btn = QPushButton(label)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                if style_type == 'primary':
                    btn.setStyleSheet(button_primary(f"padding: {BTN.PADDING_V} {BTN.PADDING_H_WIDE}; border-radius: {BTN.BORDER_RADIUS}px; min-width: {BTN.MIN_WIDTH};"))
                else:
                    btn.setStyleSheet(button_secondary(f"padding: {BTN.PADDING_V} {BTN.PADDING_H_WIDE}; border-radius: {BTN.BORDER_RADIUS}px; min-width: {BTN.MIN_WIDTH};"))
                btn.clicked.connect(lambda checked, k=key: self._on_button(k))
                btn_row.addWidget(btn)
                btn_row.addSpacing(DIALOG.BUTTON_SPACING)

            layout.addSpacing(8)
            layout.addLayout(btn_row)

        self._create_shadow_frame(build_content, icon_pixmap=icon_pixmap)

    def _create_icon_pixmap(self) -> QPixmap:
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._icon_type == 'warning':
            painter.setBrush(QColor(COLORS.WARNING))
            painter.setPen(Qt.PenStyle.NoPen)
            tri = QPolygonF()
            tri.append(QPointF(24, 6))
            tri.append(QPointF(44, 42))
            tri.append(QPointF(4, 42))
            painter.drawPolygon(tri)
            painter.setPen(QPen(QColor(COLORS.BG_PRIMARY), 3))
            painter.drawLine(24, 18, 24, 30)
            painter.drawPoint(24, 35)
        elif self._icon_type == 'error':
            painter.setBrush(QColor(COLORS.ERROR))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(4, 4, 40, 40, RADIUS.LARGE, RADIUS.LARGE)
            painter.setPen(QPen(QColor(COLORS.BG_PRIMARY), 3))
            painter.drawLine(16, 16, 32, 32)
            painter.drawLine(32, 16, 16, 32)
        elif self._icon_type == 'question':
            painter.setBrush(QColor(COLORS.INFO))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(4, 4, 40, 40, RADIUS.LARGE, RADIUS.LARGE)
            painter.setPen(QColor(COLORS.BG_PRIMARY))
            font = QFont()
            font.setPointSize(FONT.ICON_LARGE_PT)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRectF(4, 4, 40, 40), Qt.AlignmentFlag.AlignCenter, "?")
        else:
            painter.setBrush(QColor(COLORS.SUCCESS))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(4, 4, 40, 40, RADIUS.LARGE, RADIUS.LARGE)
            painter.setPen(QPen(QColor(COLORS.BG_PRIMARY), 3))
            painter.drawLine(14, 24, 21, 32)
            painter.drawLine(21, 32, 34, 16)

        painter.end()
        return pixmap

    def _on_button(self, key):
        self._result = key
        self.accept()

    def exec(self):
        super().exec()
        return self._result


def styled_msg_box(parent, icon, title, text, buttons=None):
    """创建 ModernMessageBox 的便捷函数，将 QMessageBox 标准按钮映射为自定义按钮"""
    from PySide6.QtWidgets import QMessageBox

    if buttons is None:
        buttons = QMessageBox.StandardButton.Ok

    icon_map = {
        QMessageBox.Icon.Information: 'info',
        QMessageBox.Icon.Warning: 'warning',
        QMessageBox.Icon.Critical: 'error',
        QMessageBox.Icon.Question: 'question',
        QMessageBox.Icon.NoIcon: 'info',
    }
    icon_type = icon_map.get(icon, 'info')

    btn_defs = {}
    if buttons == QMessageBox.StandardButton.Ok:
        btn_defs['ok'] = ('确定', 'primary')
    elif buttons == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
        btn_defs['no'] = ('否', 'secondary')
        btn_defs['yes'] = ('是', 'primary')
    elif buttons == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                     QMessageBox.StandardButton.Cancel):
        btn_defs['cancel'] = ('取消', 'secondary')
        btn_defs['no'] = ('否', 'secondary')
        btn_defs['yes'] = ('是', 'primary')
    else:
        btn_defs['ok'] = ('确定', 'primary')

    dlg = ModernMessageBox(parent, icon_type, title, text, btn_defs)
    result = dlg.exec()

    if result == 'yes':
        return QMessageBox.StandardButton.Yes
    elif result == 'no':
        return QMessageBox.StandardButton.No
    elif result == 'cancel':
        return QMessageBox.StandardButton.Cancel
    return QMessageBox.StandardButton.Ok
