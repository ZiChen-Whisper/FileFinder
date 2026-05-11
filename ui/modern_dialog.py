from PySide6.QtWidgets import QDialog, QVBoxLayout, QFrame, QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QFont
from .style_constants import COLORS, FONT, RADIUS, DIALOG
from .style_manager import dialog_frame_style, dialog_title_style


class ModernDialogBase(QDialog):
    def __init__(self, parent=None, title='', min_width=420, min_height=None, resizable=True):
        super().__init__(parent)
        self._title_text = title
        self._drag_pos = None
        self._resizable = resizable
        self._opacity_animation = None
        self._close_animation = None

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

    def _create_shadow_frame(self, content_layout_fn):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(DIALOG.OUTER_MARGIN, DIALOG.OUTER_MARGIN, DIALOG.OUTER_MARGIN, DIALOG.OUTER_MARGIN)

        shadow_frame = QFrame()
        shadow_frame.setObjectName("shadowFrame")
        shadow_frame.setStyleSheet(dialog_frame_style())

        frame_layout = QVBoxLayout(shadow_frame)
        frame_layout.setSpacing(0)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background: transparent;")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(DIALOG.PADDING, 12, DIALOG.PADDING, 0)
        title_bar_layout.setSpacing(8)

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
        return shadow_frame

    def _animate_close(self):
        self._close_animation = QPropertyAnimation(self, b"windowOpacity")
        self._close_animation.setDuration(150)
        self._close_animation.setStartValue(1.0)
        self._close_animation.setEndValue(0.0)
        self._close_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._close_animation.finished.connect(self.reject)
        self._close_animation.start()

    def showEvent(self, event):
        super().showEvent(event)
        self._opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_animation.setDuration(150)
        self._opacity_animation.setStartValue(0.0)
        self._opacity_animation.setEndValue(1.0)
        self._opacity_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self._opacity_animation.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            title_rect = QRectF(0, 0, self.width(), 52)
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
