from .style_constants import COLORS, FONT, RADIUS, SPACING, BTN, DIALOG


def scrollbar_style() -> str:
    return f"""
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS.BORDER_HOVER};
        min-height: 40px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS.TEXT_PLACEHOLDER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px; background: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLORS.BORDER_HOVER};
        min-width: 40px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS.TEXT_PLACEHOLDER};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px; background: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
"""


def button_primary(extra: str = "") -> str:
    base = f"""
    QPushButton {{
        padding: {BTN.PADDING_V} {BTN.PADDING_H_WIDE};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        outline: none;
        min-width: {BTN.MIN_WIDTH};
    }}
    QPushButton:hover {{
        background-color: {COLORS.BRAND_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {COLORS.BRAND_PRESSED};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BRAND_DISABLED};
    }}
    """
    if extra:
        base = base.rstrip() + "\n    " + extra + "\n"
    return base


def button_secondary(extra: str = "") -> str:
    base = f"""
    QPushButton {{
        padding: {BTN.PADDING_V} {BTN.PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_SECONDARY};
        font-size: {BTN.FONT_SIZE};
        outline: none;
        min-width: {BTN.MIN_WIDTH};
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {COLORS.BORDER_DEFAULT};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BG_HOVER};
        color: {COLORS.TEXT_PLACEHOLDER};
        border-color: {COLORS.BORDER_DEFAULT};
    }}
    """
    if extra:
        base = base.rstrip() + "\n    " + extra + "\n"
    return base


def button_danger(extra: str = "") -> str:
    base = f"""
    QPushButton {{
        padding: {BTN.PADDING_V} {BTN.PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.ERROR};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.ERROR_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.ERROR_BORDER};
    }}
    """
    if extra:
        base = base.rstrip() + "\n    " + extra + "\n"
    return base


def button_small_primary() -> str:
    return f"""
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.SMALL_BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BRAND_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BRAND_DISABLED};
    }}
"""


def button_small_secondary() -> str:
    return f"""
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.SMALL_BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_TERTIARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
        color: {COLORS.TEXT_SECONDARY};
    }}
"""


def button_tag() -> str:
    return f"""
    QPushButton {{
        padding: {BTN.TAG_PADDING_V} {BTN.TAG_PADDING_H};
        border-radius: {BTN.TAG_BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_TERTIARY};
        font-size: {BTN.TAG_FONT_SIZE};
        outline: none;
        text-align: left;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
        color: {COLORS.TEXT_PRIMARY};
    }}
    QPushButton:checked {{
        background-color: {COLORS.BRAND};
        border-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
    }}
    QPushButton:checked:hover {{
        background-color: {COLORS.BRAND_HOVER};
        border-color: {COLORS.BRAND_HOVER};
    }}
"""


def button_cancel_danger() -> str:
    return f"""
    QPushButton {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.LARGE}px;
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_TERTIARY};
        font-size: {BTN.FONT_SIZE};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.ERROR_LIGHT_BG};
        border-color: {COLORS.ERROR_BORDER};
        color: {COLORS.ERROR};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BG_HOVER};
        color: {COLORS.TEXT_PLACEHOLDER};
        border-color: {COLORS.BORDER_DEFAULT};
    }}
"""


def button_filter() -> str:
    return f"""
    QPushButton {{
        outline: none;
    }}
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} 16px;
        border-radius: {BTN.BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_SECONDARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        font-weight: {FONT.WEIGHT_MEDIUM};
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
    }}
    QPushButton:checked {{
        background-color: {COLORS.BRAND};
        border-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
    }}
    QPushButton:checked:hover {{
        background-color: {COLORS.BRAND_HOVER};
        border-color: {COLORS.BRAND_HOVER};
    }}
"""


def button_scan() -> str:
    return f"""
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        min-height: 24px;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BRAND_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.BRAND_DISABLED};
    }}
"""


def button_scan_green() -> str:
    return f"""
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: none;
        background-color: {COLORS.SUCCESS};
        color: {COLORS.BG_PRIMARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        min-height: 24px;
    }}
    QPushButton:hover {{
        background-color: {COLORS.SUCCESS_HOVER};
    }}
    QPushButton:disabled {{
        background-color: {COLORS.SUCCESS_DISABLED};
    }}
"""


def dialog_frame_style() -> str:
    return f"""
    QFrame#shadowFrame {{
        background-color: {COLORS.BG_PRIMARY};
        border-radius: {DIALOG.BORDER_RADIUS}px;
        border: {DIALOG.BORDER_WIDTH} {DIALOG.BORDER_STYLE} {DIALOG.BORDER_COLOR};
    }}
"""


def dialog_title_style() -> str:
    return f"color: {DIALOG.TITLE_COLOR}; border: none; background: transparent;"


def dialog_body_style() -> str:
    return f"color: {DIALOG.BODY_COLOR}; font-size: {DIALOG.BODY_FONT_SIZE}; line-height: {DIALOG.BODY_LINE_HEIGHT}; border: none; background: transparent;"


def dialog_style() -> str:
    return f"""
    QDialog {{
        background-color: {COLORS.BG_PRIMARY};
    }}
    QLabel {{
        color: {COLORS.TEXT_PRIMARY};
        border: none;
        background: transparent;
    }}
"""


def msg_box_style() -> str:
    return f"""
    QMessageBox {{
        background-color: {COLORS.BG_PRIMARY};
    }}
    QMessageBox QLabel {{
        color: {COLORS.TEXT_PRIMARY};
        font-size: {DIALOG.BODY_FONT_SIZE};
        border: none;
        background: transparent;
    }}
    QPushButton {{
        padding: {BTN.PADDING_V} {BTN.PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_SECONDARY};
        font-size: {BTN.FONT_SIZE};
        outline: none;
        min-width: {BTN.MIN_WIDTH};
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
    }}
"""


def input_style() -> str:
    return f"""
    QLineEdit {{
        padding: 0px 12px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        font-size: {BTN.FONT_SIZE};
        background-color: {COLORS.BG_SECONDARY};
        outline: none;
    }}
    QLineEdit:focus {{
        border-color: {COLORS.BORDER_FOCUS};
        background-color: {COLORS.BG_PRIMARY};
    }}
    QLineEdit:hover {{
        border-color: {COLORS.BORDER_HOVER};
    }}
"""


def search_input_style() -> str:
    return f"""
    QLineEdit {{
        padding: 10px 14px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.XLARGE}px;
        font-size: {DIALOG.BODY_FONT_SIZE};
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_PRIMARY};
        outline: none;
    }}
    QLineEdit:hover {{
        border-color: {COLORS.BORDER_HOVER};
    }}
    QLineEdit:focus {{
        border-color: {COLORS.BORDER_FOCUS};
        background-color: {COLORS.BG_PRIMARY};
    }}
"""


def search_button_style() -> str:
    return f"""
    QPushButton {{
        background-color: {COLORS.BRAND};
        color: {COLORS.BG_PRIMARY};
        border: none;
        border-radius: {RADIUS.XLARGE}px;
        padding: 10px 20px;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BRAND_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {COLORS.BRAND_PRESSED};
    }}
"""


def radio_button_style() -> str:
    return f"""
    QRadioButton {{
        font-size: {BTN.SMALL_FONT_SIZE};
        color: {COLORS.TEXT_TERTIARY};
        spacing: 4px;
        outline: none;
        border: none;
        background: transparent;
        text-decoration: none;
    }}
    QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 7px;
        border: 2px solid {COLORS.BORDER_HOVER};
        background-color: {COLORS.BG_PRIMARY};
    }}
    QRadioButton::indicator:hover {{
        border-color: {COLORS.BRAND};
    }}
    QRadioButton::indicator:checked {{
        border-color: {COLORS.BRAND};
        background-color: {COLORS.BRAND};
    }}
"""


def checkbox_style() -> str:
    return f"""
    QCheckBox {{
        spacing: 6px;
        font-size: {BTN.SMALL_FONT_SIZE};
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
"""


def progress_bar_style(height: int = 8, radius: int = 4) -> str:
    return f"""
    QProgressBar {{
        border: none;
        background-color: {COLORS.BORDER_DEFAULT};
        border-radius: {radius}px;
        height: {height}px;
        text-align: center;
        font-size: 10px;
        color: {COLORS.TEXT_TERTIARY};
        outline: none;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS.BRAND};
        border-radius: {radius}px;
    }}
"""


def progress_bar_success_style(height: int = 8, radius: int = 4) -> str:
    return f"""
    QProgressBar {{
        border: none;
        background-color: {COLORS.BORDER_DEFAULT};
        border-radius: {radius}px;
        height: {height}px;
        text-align: center;
        outline: none;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS.SUCCESS};
        border-radius: {radius}px;
    }}
"""


def progress_bar_warning_style(height: int = 8, radius: int = 4) -> str:
    return f"""
    QProgressBar {{
        border: none;
        background-color: {COLORS.BORDER_DEFAULT};
        border-radius: {radius}px;
        height: {height}px;
        text-align: center;
        outline: none;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS.WARNING};
        border-radius: {radius}px;
    }}
"""


def progress_bar_error_style(height: int = 8, radius: int = 4) -> str:
    return f"""
    QProgressBar {{
        border: none;
        background-color: {COLORS.BORDER_DEFAULT};
        border-radius: {radius}px;
        height: {height}px;
        text-align: center;
        outline: none;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS.ERROR};
        border-radius: {radius}px;
    }}
"""


def status_bar_style() -> str:
    return f"""
    QStatusBar {{
        background-color: {COLORS.BG_SECONDARY};
        border-top: 1px solid {COLORS.BORDER_DEFAULT};
        padding: 4px 12px;
        min-height: 36px;
    }}
    QStatusBar QLabel {{
        color: {COLORS.TEXT_SECONDARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        padding: 0 6px;
        border: none;
        background: transparent;
    }}
"""


def status_divider_style() -> str:
    return f"""
    QLabel {{
        color: {COLORS.BORDER_HOVER};
        padding: 0 2px;
        font-size: {BTN.SMALL_FONT_SIZE};
        border: none;
        background: transparent;
    }}
"""


def list_style() -> str:
    return f"""
    QListWidget {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        background-color: {COLORS.BG_SECONDARY};
        padding: 4px;
        font-size: {BTN.FONT_SIZE};
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px 32px 8px 10px;
        border-radius: {RADIUS.SMALL}px;
        border: none;
    }}
    QListWidget::item:hover {{
        background-color: {COLORS.BG_HOVER};
    }}
    QListWidget::item:selected {{
        background-color: {COLORS.BRAND_LIGHT_BG};
        color: {COLORS.TEXT_PRIMARY};
        border: none;
    }}
    """ + scrollbar_style()


def menu_style() -> str:
    return f"""
    QMenu {{
        background-color: {COLORS.BG_PRIMARY};
        border: none;
        padding: 6px 4px;
    }}
    QMenu::item {{
        padding: 8px 28px 8px 20px;
        border-radius: {RADIUS.MEDIUM}px;
        font-size: {BTN.FONT_SIZE};
        color: {COLORS.TEXT_PRIMARY};
        background: transparent;
        margin: 1px 4px;
    }}
    QMenu::item:selected {{
        background-color: {COLORS.BRAND_LIGHT_BG};
        color: {COLORS.BRAND};
    }}
    QMenu::icon {{
        padding-left: 8px;
    }}
    QMenu::separator {{
        height: 1px;
        background: {COLORS.BG_HOVER};
        margin: 4px 12px;
    }}
    QMenu::right-arrow {{
        width: 12px;
        height: 12px;
    }}
"""


def group_box_style() -> str:
    return f"""
    QGroupBox {{
        font-size: {DIALOG.TITLE_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        color: {COLORS.TEXT_PRIMARY};
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        margin-top: 12px;
        padding-top: 20px;
        background-color: {COLORS.BG_SECONDARY};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
    }}
"""


def danger_zone_style() -> str:
    return f"""
    QGroupBox {{
        font-size: {DIALOG.TITLE_FONT_SIZE};
        font-weight: {BTN.FONT_WEIGHT};
        color: {COLORS.ERROR};
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.ERROR_BORDER};
        border-radius: {BTN.BORDER_RADIUS}px;
        margin-top: 12px;
        padding-top: 20px;
        background-color: {COLORS.ERROR_SURFACE};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
    }}
"""


def label_caption_style() -> str:
    return f"font-size: {BTN.SMALL_FONT_SIZE}; color: {COLORS.TEXT_TERTIARY}; border: none; background: transparent; text-decoration: none;"


def label_micro_style() -> str:
    return f"font-size: {BTN.TAG_FONT_SIZE}; color: {COLORS.TEXT_TERTIARY}; border: none; background: transparent; text-decoration: none;"


def label_body_style() -> str:
    return f"font-size: {BTN.FONT_SIZE}; color: {COLORS.TEXT_TERTIARY}; border: none; background: transparent; text-decoration: none;"


def label_header_style() -> str:
    return f"font-size: {BTN.SMALL_FONT_SIZE}; font-weight: bold; color: {COLORS.TEXT_PRIMARY}; border: none; background: transparent; text-decoration: none;"


def badge_style(bg_color: str = COLORS.BG_HOVER, text_color: str = COLORS.TEXT_SECONDARY) -> str:
    return f"""
        background-color: {bg_color};
        color: {text_color};
        border-radius: 5px;
        padding: 2px 8px;
        font-size: {BTN.TAG_FONT_SIZE};
        border: none;
    """


def badge_brand_style() -> str:
    return badge_style(COLORS.BRAND_LIGHTER_BG, COLORS.BRAND) + f"font-weight: {BTN.FONT_WEIGHT};"


def splitter_style() -> str:
    return f"""
    QSplitter::handle {{
        background-color: {COLORS.BORDER_DEFAULT};
    }}
    QSplitter::handle:hover {{
        background-color: {COLORS.BRAND};
    }}
"""


def menubar_style() -> str:
    return f"""
    QMenuBar {{
        background-color: {COLORS.BG_SECONDARY};
        border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
        padding: 2px 8px;
        font-size: {BTN.FONT_SIZE};
    }}
    QMenuBar::item {{
        padding: 4px 12px;
        border-radius: {RADIUS.SMALL}px;
        color: {COLORS.TEXT_SECONDARY};
    }}
    QMenuBar::item:selected {{
        background-color: {COLORS.BG_HOVER};
        color: {COLORS.TEXT_PRIMARY};
    }}
"""


def remove_button_style() -> str:
    return f"""
    QPushButton {{
        border: none;
        background: transparent;
        outline: none;
        padding: 2px 8px;
        color: {COLORS.TEXT_PLACEHOLDER};
        font-size: {BTN.SMALL_FONT_SIZE};
        border-radius: {RADIUS.SMALL}px;
    }}
    QPushButton:hover {{
        background-color: {COLORS.ERROR_LIGHT_BG};
        color: {COLORS.ERROR};
    }}
"""


def icon_button_style() -> str:
    return f"""
    QPushButton {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.MEDIUM}px;
        background-color: {COLORS.BG_PRIMARY};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
    }}
"""


def config_button_style() -> str:
    return f"""
    QPushButton {{
        outline: none;
    }}
    QPushButton {{
        padding: {BTN.SMALL_PADDING_V} {BTN.SMALL_PADDING_H};
        border-radius: {BTN.BORDER_RADIUS}px;
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        background-color: {COLORS.BG_PRIMARY};
        color: {COLORS.TEXT_TERTIARY};
        font-size: {BTN.SMALL_FONT_SIZE};
        text-decoration: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS.BG_HOVER};
        border-color: {COLORS.BORDER_HOVER};
        color: {COLORS.TEXT_SECONDARY};
    }}
"""


def scope_info_scroll_style() -> str:
    return f"""
    QScrollArea {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {RADIUS.MEDIUM}px;
        background-color: {COLORS.BG_SECONDARY};
    }}
    """ + scrollbar_style()


def tree_widget_style(checkmark_path: str, partial_path: str,
                      branch_closed_path: str, branch_open_path: str) -> str:
    return f"""
    QTreeWidget {{
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        background-color: {COLORS.BG_SECONDARY};
        font-size: {BTN.FONT_SIZE};
        outline: none;
        padding: 4px;
    }}
    QTreeWidget::item {{
        padding: 4px 2px;
        border-radius: {RADIUS.SMALL}px;
        border: none;
    }}
    QTreeWidget::item:hover {{
        background-color: {COLORS.BG_HOVER};
    }}
    QTreeWidget::item:selected {{
        background-color: {COLORS.BRAND_LIGHT_BG};
        color: {COLORS.TEXT_PRIMARY};
    }}
    QTreeWidget::branch {{
        background: transparent;
    }}
    QTreeWidget::branch:has-children:!closed {{
        image: url({branch_open_path});
        background: transparent;
    }}
    QTreeWidget::branch:closed:has-children {{
        image: url({branch_closed_path});
        background: transparent;
    }}
    QTreeWidget::indicator {{
        width: 16px;
        height: 16px;
        border-radius: {RADIUS.SMALL}px;
        border: 2px solid {COLORS.BORDER_HOVER};
        background-color: {COLORS.BG_PRIMARY};
    }}
    QTreeWidget::indicator:hover {{
        border-color: {COLORS.BRAND};
        background-color: {COLORS.BRAND_LIGHT_BG};
    }}
    QTreeWidget::indicator:unchecked {{
        image: none;
    }}
    QTreeWidget::indicator:checked {{
        background-color: {COLORS.BRAND};
        border-color: {COLORS.BRAND};
        image: url({checkmark_path});
    }}
    QTreeWidget::indicator:checked:hover {{
        background-color: {COLORS.BRAND_HOVER};
        border-color: {COLORS.BRAND_HOVER};
        image: url({checkmark_path});
    }}
    QTreeWidget::indicator:indeterminate {{
        background-color: {COLORS.BRAND};
        border-color: {COLORS.BRAND};
        image: url({partial_path});
    }}
    QTreeWidget::indicator:indeterminate:hover {{
        background-color: {COLORS.BRAND_HOVER};
        border-color: {COLORS.BRAND_HOVER};
        image: url({partial_path});
    }}
    """ + scrollbar_style()


def scan_log_style() -> str:
    return f"""
    QTextEdit {{
        background-color: {COLORS.BG_TERTIARY};
        border: {BTN.BORDER_WIDTH} {BTN.BORDER_STYLE} {COLORS.BORDER_DEFAULT};
        border-radius: {BTN.BORDER_RADIUS}px;
        padding: 8px;
        font-size: {BTN.TAG_FONT_SIZE};
        color: {COLORS.TEXT_TERTIARY};
    }}
"""
