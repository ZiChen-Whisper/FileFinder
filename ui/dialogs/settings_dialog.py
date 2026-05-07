from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QCheckBox, QLineEdit,
                             QGroupBox, QSpinBox, QWidget, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from config import load_config, save_config


DIALOG_STYLE = """
    QDialog {
        background-color: #FFFFFF;
    }
    QLabel {
        color: #1F2937;
        border: none;
        background: transparent;
    }
    QGroupBox {
        font-size: 14px;
        font-weight: bold;
        color: #1F2937;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        margin-top: 12px;
        padding: 16px 12px 8px 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
    }
"""

INPUT_STYLE = """
    QLineEdit {
        padding: 8px 12px;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        font-size: 13px;
        background-color: #FAFAFA;
        outline: none;
    }
    QLineEdit:focus {
        border-color: #7C3AED;
        background-color: #FFFFFF;
    }
"""

BTN_STYLE = """
    QPushButton {
        padding: 6px 16px;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        color: #4B5563;
        font-size: 12px;
        outline: none;
    }
    QPushButton:hover {
        background-color: #F3F4F6;
        border-color: #D1D5DB;
    }
"""

PRIMARY_BTN_STYLE = """
    QPushButton {
        padding: 8px 24px;
        border-radius: 8px;
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

CHECKBOX_STYLE = """
    QCheckBox {
        spacing: 6px;
        font-size: 13px;
        color: #4B5563;
        padding: 4px 0;
        outline: none;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 2px solid #D1D5DB;
        background-color: #FFFFFF;
        outline: none;
    }
    QCheckBox::indicator:hover {
        border-color: #7C3AED;
    }
    QCheckBox::indicator:checked {
        background-color: #7C3AED;
        border-color: #7C3AED;
    }
"""

SPINBOX_STYLE = """
    QSpinBox {
        padding: 6px 10px;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        font-size: 13px;
        background-color: #FAFAFA;
        outline: none;
    }
    QSpinBox:focus {
        border-color: #7C3AED;
    }
"""


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(520, 480)
        self.setStyleSheet(DIALOG_STYLE)
        self._config = load_config()
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 16, 20, 16)

        header = QLabel("设置")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        general_group = QGroupBox("通用设置")
        general_layout = QVBoxLayout()
        general_layout.setSpacing(10)

        self.auto_start_cb = QCheckBox("开机自动启动")
        self.auto_start_cb.setStyleSheet(CHECKBOX_STYLE)
        self.auto_start_cb.setChecked(self._config.get("general", {}).get("auto_start", False))

        self.minimize_tray_cb = QCheckBox("关闭窗口时最小化到系统托盘")
        self.minimize_tray_cb.setStyleSheet(CHECKBOX_STYLE)
        self.minimize_tray_cb.setChecked(self._config.get("general", {}).get("minimize_to_tray", True))

        shortcut_row = QHBoxLayout()
        shortcut_label = QLabel("全局快捷键：")
        shortcut_label.setStyleSheet("font-size: 13px; color: #4B5563;")
        self.shortcut_input = QLineEdit(
            self._config.get("general", {}).get("global_shortcut", "Ctrl+Alt+F")
        )
        self.shortcut_input.setStyleSheet(INPUT_STYLE)
        self.shortcut_input.setPlaceholderText("例如：Ctrl+Alt+F")
        shortcut_row.addWidget(shortcut_label)
        shortcut_row.addWidget(self.shortcut_input, 1)

        general_layout.addWidget(self.auto_start_cb)
        general_layout.addWidget(self.minimize_tray_cb)
        general_layout.addLayout(shortcut_row)
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        search_group = QGroupBox("搜索设置")
        search_layout = QVBoxLayout()
        search_layout.setSpacing(10)

        max_row = QHBoxLayout()
        max_label = QLabel("最大搜索结果数：")
        max_label.setStyleSheet("font-size: 13px; color: #4B5563;")
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(100, 10000)
        self.max_results_spin.setSingleStep(100)
        self.max_results_spin.setValue(
            self._config.get("search", {}).get("max_results", 1000)
        )
        self.max_results_spin.setStyleSheet(SPINBOX_STYLE)
        max_row.addWidget(max_label)
        max_row.addWidget(self.max_results_spin)

        size_row = QHBoxLayout()
        size_label = QLabel("内容搜索最大文件大小(MB)：")
        size_label.setStyleSheet("font-size: 13px; color: #4B5563;")
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 100)
        self.max_size_spin.setValue(
            self._config.get("search", {}).get("content_max_size_mb", 10)
        )
        self.max_size_spin.setStyleSheet(SPINBOX_STYLE)
        size_row.addWidget(size_label)
        size_row.addWidget(self.max_size_spin)

        exclude_row = QHBoxLayout()
        exclude_label = QLabel("排除扩展名：")
        exclude_label.setStyleSheet("font-size: 13px; color: #4B5563;")
        self.exclude_ext_input = QLineEdit(
            ", ".join(self._config.get("search", {}).get("exclude_extensions", []))
        )
        self.exclude_ext_input.setStyleSheet(INPUT_STYLE)
        self.exclude_ext_input.setPlaceholderText("例如：.dll, .exe, .sys")
        exclude_row.addWidget(exclude_label)
        exclude_row.addWidget(self.exclude_ext_input, 1)

        search_layout.addLayout(max_row)
        search_layout.addLayout(size_row)
        search_layout.addLayout(exclude_row)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        layout.addStretch()

        content.setLayout(layout)
        scroll.setWidget(content)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(BTN_STYLE)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(PRIMARY_BTN_STYLE)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll, 1)

        btn_widget = QWidget()
        btn_widget.setLayout(btn_row)
        btn_widget.setStyleSheet("background-color: #FFFFFF; padding: 12px 20px;")
        outer.addWidget(btn_widget)

        self.setLayout(outer)

    def _on_save(self):
        self._config["general"]["auto_start"] = self.auto_start_cb.isChecked()
        self._config["general"]["minimize_to_tray"] = self.minimize_tray_cb.isChecked()
        self._config["general"]["global_shortcut"] = self.shortcut_input.text().strip() or "Ctrl+Alt+F"
        self._config["search"]["max_results"] = self.max_results_spin.value()
        self._config["search"]["content_max_size_mb"] = self.max_size_spin.value()

        ext_text = self.exclude_ext_input.text().strip()
        if ext_text:
            self._config["search"]["exclude_extensions"] = [
                e.strip() for e in ext_text.split(",") if e.strip()
            ]

        save_config(self._config)
        self.accept()
