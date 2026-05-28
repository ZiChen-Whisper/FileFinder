from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QMessageBox, QWidget, QApplication)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from ..style_constants import COLORS, FONT, RADIUS, BTN, DIALOG
from ..modern_dialog import ModernDialogBase, styled_msg_box
from ..style_manager import button_secondary, label_caption_style


def _make_settings_icon(color_hex: str, size: int = 48) -> QIcon:
    """使用 settings.svg 生成指定颜色的设置图标"""
    screen = QApplication.primaryScreen()
    dpr = screen.devicePixelRatio() if screen else 1.0
    source_size = int(size * 4 * dpr)
    pixmap = QIcon("icons/settings.svg").pixmap(QSize(source_size, source_size))
    if pixmap.isNull():
        return QIcon("icons/settings.svg")
    colored = QPixmap(pixmap.size())
    colored.fill(Qt.GlobalColor.transparent)
    colored.setDevicePixelRatio(dpr)
    painter = QPainter(colored)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored.rect(), QColor(color_hex))
    painter.end()
    target_size = int(size * 2 * dpr)
    scaled = colored.scaled(target_size, target_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)
    scaled.setDevicePixelRatio(dpr)
    return QIcon(scaled)


class SettingsDialog(ModernDialogBase):
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, title="偏好设置", min_width=420, min_height=280, resizable=False)
        self._init_ui()

    def _init_ui(self):
        def build_content(content_widget):
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(DIALOG.CONTENT_SPACING)
            layout.setContentsMargins(DIALOG.PADDING, 4, DIALOG.PADDING, DIALOG.PADDING)

            # 图标
            icon_label = QLabel()
            icon_label.setFixedSize(48, 48)
            icon_label.setStyleSheet("border: none; background: transparent;")
            settings_icon = _make_settings_icon(COLORS.TEXT_TERTIARY, 48)
            icon_label.setPixmap(settings_icon.pixmap(QSize(48, 48)))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # 标题
            title_label = QLabel("偏好设置功能开发中")
            title_label.setStyleSheet(f"""
                font-size: {FONT.TITLE_PT}px;
                font-weight: {BTN.FONT_WEIGHT};
                color: {COLORS.TEXT_PRIMARY};
                border: none;
                background: transparent;
            """)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # 描述
            desc_label = QLabel(
                "主题切换、语言设置、快捷键配置等功能\n"
                "将在后续版本中陆续上线，敬请期待。"
            )
            desc_label.setStyleSheet(f"""
                font-size: {FONT.BODY_PT}px;
                color: {COLORS.TEXT_TERTIARY};
                border: none;
                background: transparent;
                line-height: {DIALOG.BODY_LINE_HEIGHT};
            """)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setWordWrap(True)

            # 关闭按钮
            btn_row = QHBoxLayout()
            btn_row.addStretch()

            close_btn = QPushButton("知道了")
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setStyleSheet(button_secondary(
                f"padding: {BTN.PADDING_V} {BTN.PADDING_H_WIDE}; border-radius: {BTN.BORDER_RADIUS}px; min-width: {BTN.MIN_WIDTH};"
            ))
            close_btn.clicked.connect(self.accept)

            btn_row.addWidget(close_btn)
            btn_row.addStretch()

            layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(desc_label, 0, Qt.AlignmentFlag.AlignHCenter)
            layout.addSpacing(8)
            layout.addLayout(btn_row)

        self._create_shadow_frame(build_content)
