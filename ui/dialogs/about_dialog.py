import webbrowser
from pathlib import Path

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QFont, QCursor

from ..style_constants import COLORS, FONT, RADIUS, BTN, DIALOG
from ..modern_dialog import ModernDialogBase


_ICONS_DIR = Path(__file__).resolve().parent.parent.parent / "icons"
_GITHUB_URL = "https://github.com/ZiChen-Whisper/FileFinder"
_CONTACT_EMAIL = "3331879873@qq.com"
_DOCS_PATH = _ICONS_DIR.parent / "docs" / "index.html"


class _LinkButton(QPushButton):
    def __init__(self, text: str, icon_path: str = None, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_path:
            icon = QIcon(icon_path)
            self.setIcon(icon)
            self.setIconSize(QSize(16, 16))
        self.setText(text)
        self.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                color: {COLORS.TEXT_BRAND};
                font-size: {FONT.BODY_PT}px;
                font-family: {FONT.FAMILY};
                padding: 4px 8px;
                border-radius: {RADIUS.MEDIUM}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BRAND_LIGHT_BG};
                color: {COLORS.BRAND};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.BG_TERTIARY};
            }}
        """)


class AboutDialog(ModernDialogBase):
    def __init__(self, parent=None):
        super().__init__(parent, title="关于 FileFinder", min_width=380, min_height=320, resizable=False)
        self._init_ui()

    def _init_ui(self):
        def build_content(content_widget):
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(0)
            layout.setContentsMargins(DIALOG.PADDING, 8, DIALOG.PADDING, DIALOG.PADDING)
            layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            layout.addSpacing(8)

            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("border: none; background: transparent;")
            app_icon_path = str(_ICONS_DIR / "FileFinder.png")
            pixmap = QPixmap(app_icon_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    QSize(96, 96),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                icon_label.setPixmap(scaled)
                icon_label.setFixedSize(96, 96)
            layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignHCenter)

            layout.addSpacing(12)

            name_label = QLabel("FileFinder")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet(f"""
                font-size: 22px;
                font-weight: bold;
                color: {COLORS.TEXT_PRIMARY};
                font-family: {FONT.FAMILY};
                border: none;
                background: transparent;
            """)
            layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignHCenter)

            layout.addSpacing(4)

            version_label = QLabel("v1.0")
            version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            version_label.setStyleSheet(f"""
                font-size: {FONT.CAPTION_PT}px;
                color: {COLORS.TEXT_TERTIARY};
                font-family: {FONT.FAMILY};
                border: none;
                background: transparent;
            """)
            layout.addWidget(version_label, 0, Qt.AlignmentFlag.AlignHCenter)

            layout.addSpacing(4)

            desc_label = QLabel("一款轻量级的本地文件搜索桌面工具")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setStyleSheet(f"""
                font-size: {FONT.BODY_PT}px;
                color: {COLORS.TEXT_SECONDARY};
                font-family: {FONT.FAMILY};
                border: none;
                background: transparent;
            """)
            layout.addWidget(desc_label, 0, Qt.AlignmentFlag.AlignHCenter)

            layout.addSpacing(20)

            separator = QWidget()
            separator.setFixedHeight(1)
            separator.setStyleSheet(f"background-color: {COLORS.BORDER_DEFAULT}; border: none;")
            layout.addWidget(separator)

            layout.addSpacing(16)

            links_layout = QVBoxLayout()
            links_layout.setSpacing(8)
            links_layout.setContentsMargins(0, 0, 0, 0)

            github_icon_path = str(_ICONS_DIR / "github.svg")
            github_btn = _LinkButton("GitHub", icon_path=github_icon_path)
            github_btn.clicked.connect(self._open_github)
            links_layout.addWidget(github_btn, 0, Qt.AlignmentFlag.AlignHCenter)

            email_btn = _LinkButton(_CONTACT_EMAIL)
            email_btn.clicked.connect(self._open_email)
            links_layout.addWidget(email_btn, 0, Qt.AlignmentFlag.AlignHCenter)

            docs_btn = _LinkButton("官方文档")
            docs_btn.clicked.connect(self._open_docs)
            links_layout.addWidget(docs_btn, 0, Qt.AlignmentFlag.AlignHCenter)

            layout.addLayout(links_layout)

            layout.addSpacing(20)

            close_btn = QPushButton("确定")
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setFixedSize(120, 36)
            close_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS.BRAND};
                    color: white;
                    border: none;
                    border-radius: {BTN.BORDER_RADIUS}px;
                    font-size: {FONT.BODY_PT}px;
                    font-weight: bold;
                    font-family: {FONT.FAMILY};
                }}
                QPushButton:hover {{
                    background-color: {COLORS.BRAND_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS.BRAND_PRESSED};
                }}
            """)
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        self._create_shadow_frame(build_content)

    def _open_github(self):
        webbrowser.open(_GITHUB_URL)

    def _open_email(self):
        webbrowser.open(f"mailto:{_CONTACT_EMAIL}")

    def _open_docs(self):
        docs_file = Path(_DOCS_PATH)
        if docs_file.exists():
            webbrowser.open(docs_file.as_uri())
        else:
            webbrowser.open(f"file:///{docs_file}")
