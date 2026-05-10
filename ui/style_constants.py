from dataclasses import dataclass


@dataclass(frozen=True)
class ColorTokens:
    BRAND: str = "#7C3AED"
    BRAND_HOVER: str = "#6D28D9"
    BRAND_PRESSED: str = "#5B21B6"
    BRAND_DISABLED: str = "#C4B5FD"
    BRAND_LIGHT_BG: str = "#F5F3FF"
    BRAND_LIGHTER_BG: str = "#EDE9FE"

    TEXT_PRIMARY: str = "#1F2937"
    TEXT_SECONDARY: str = "#4B5563"
    TEXT_TERTIARY: str = "#6B7280"
    TEXT_PLACEHOLDER: str = "#9CA3AF"
    TEXT_BRAND: str = "#7C3AED"

    BORDER_DEFAULT: str = "#E5E7EB"
    BORDER_HOVER: str = "#D1D5DB"
    BORDER_FOCUS: str = "#7C3AED"

    BG_PRIMARY: str = "#FFFFFF"
    BG_SECONDARY: str = "#FAFAFA"
    BG_TERTIARY: str = "#F9FAFB"
    BG_HOVER: str = "#F3F4F6"

    SUCCESS: str = "#10B981"
    SUCCESS_HOVER: str = "#059669"
    SUCCESS_DISABLED: str = "#6EE7B7"
    WARNING: str = "#F59E0B"
    ERROR: str = "#EF4444"
    ERROR_HOVER: str = "#DC2626"
    ERROR_LIGHT_BG: str = "#FEE2E2"
    ERROR_BORDER: str = "#FCA5A5"
    ERROR_SURFACE: str = "#FEF2F2"
    INFO: str = "#3B82F6"

    SHADOW_COLOR: str = "rgba(0, 0, 0, 0.08)"
    SHADOW_COLOR_STRONG: str = "rgba(0, 0, 0, 0.12)"
    OVERLAY_LIGHT: str = "rgba(255, 255, 255, 220)"


COLORS = ColorTokens()


@dataclass(frozen=True)
class FontTokens:
    DISPLAY_PT: int = 18
    TITLE_PT: int = 14
    BODY_PT: int = 13
    CAPTION_PT: int = 12
    MICRO_PT: int = 11

    FAMILY: str = '"Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif'

    WEIGHT_NORMAL: int = 400
    WEIGHT_MEDIUM: int = 500
    WEIGHT_BOLD: int = 700


FONT = FontTokens()


@dataclass(frozen=True)
class RadiusTokens:
    SMALL: int = 4
    MEDIUM: int = 6
    DEFAULT: int = 8
    LARGE: int = 10
    XLARGE: int = 12
    DIALOG: int = 16


RADIUS = RadiusTokens()


@dataclass(frozen=True)
class SpacingTokens:
    XS: int = 4
    SM: int = 6
    MD: int = 8
    LG: int = 12
    XL: int = 16
    XXL: int = 20
    XXXL: int = 24
    DIALOG_PADDING: int = 28


SPACING = SpacingTokens()


@dataclass(frozen=True)
class ButtonTokens:
    PADDING_V: str = "8px"
    PADDING_H: str = "24px"
    PADDING_H_WIDE: str = "28px"
    BORDER_RADIUS: int = 8
    BORDER_WIDTH: str = "1px"
    BORDER_STYLE: str = "solid"
    FONT_SIZE: str = "13px"
    FONT_WEIGHT: str = "bold"
    MIN_WIDTH: str = "80px"

    SHADOW_OFFSET_X: int = 0
    SHADOW_OFFSET_Y: int = 2
    SHADOW_BLUR: int = 8
    SHADOW_COLOR: str = "rgba(0, 0, 0, 0.06)"

    SMALL_PADDING_V: str = "4px"
    SMALL_PADDING_H: str = "12px"
    SMALL_FONT_SIZE: str = "12px"
    SMALL_BORDER_RADIUS: int = 6

    TAG_PADDING_V: str = "4px"
    TAG_PADDING_H: str = "10px"
    TAG_FONT_SIZE: str = "11px"
    TAG_BORDER_RADIUS: int = 8


BTN = ButtonTokens()


@dataclass(frozen=True)
class DialogTokens:
    BORDER_RADIUS: int = 16
    BORDER_WIDTH: str = "1px"
    BORDER_COLOR: str = "#F3F4F6"
    BORDER_STYLE: str = "solid"
    PADDING: str = "28px"
    TITLE_FONT_SIZE: str = "14px"
    TITLE_FONT_WEIGHT: str = "bold"
    TITLE_COLOR: str = "#1F2937"
    BODY_FONT_SIZE: str = "14px"
    BODY_COLOR: str = "#4B5563"
    BODY_LINE_HEIGHT: str = "1.6"
    MIN_WIDTH: int = 420
    OUTER_MARGIN: int = 12
    CONTENT_SPACING: int = 16
    BUTTON_SPACING: int = 8


DIALOG = DialogTokens()


FILE_ICON_MAP = {
    '.py': 'doctype/code.svg', '.js': 'doctype/code.svg', '.ts': 'doctype/code.svg',
    '.java': 'doctype/code.svg', '.c': 'doctype/code.svg', '.cpp': 'doctype/code.svg',
    '.h': 'doctype/code.svg', '.go': 'doctype/code.svg', '.rs': 'doctype/code.svg',
    '.rb': 'doctype/code.svg', '.php': 'doctype/code.svg', '.html': 'doctype/code.svg',
    '.css': 'doctype/code.svg', '.sql': 'doctype/code.svg', '.sh': 'doctype/code.svg',
    '.bat': 'doctype/code.svg', '.ps1': 'doctype/code.svg',
    '.txt': 'doctype/TXT.svg', '.md': 'doctype/TXT.svg', '.log': 'doctype/TXT.svg',
    '.json': 'doctype/TXT.svg', '.xml': 'doctype/TXT.svg', '.csv': 'doctype/TXT.svg',
    '.yaml': 'doctype/TXT.svg', '.yml': 'doctype/TXT.svg', '.ini': 'doctype/TXT.svg',
    '.cfg': 'doctype/TXT.svg', '.conf': 'doctype/TXT.svg', '.toml': 'doctype/TXT.svg',
    '.pdf': 'doctype/PDF.svg', '.doc': 'doctype/Doc.svg', '.docx': 'doctype/Doc.svg',
    '.xls': 'doctype/Excel.svg', '.xlsx': 'doctype/Excel.svg',
    '.ppt': 'doctype/PPT.svg', '.pptx': 'doctype/PPT.svg',
    '.gif': 'doctype/Gif.svg', '.mp3': 'doctype/Mp3.svg', '.wav': 'doctype/Wav.svg',
    '.flac': 'doctype/Wav.svg', '.aac': 'doctype/Wav.svg',
    '.mov': 'doctype/Mov.svg', '.mp4': 'doctype/Mov.svg', '.avi': 'doctype/Mov.svg',
    '.mkv': 'doctype/Mov.svg',
    '.zip': 'doctype/Zip.svg', '.rar': 'doctype/Zip.svg', '.7z': 'doctype/Zip.svg',
    '.tar': 'doctype/Zip.svg', '.gz': 'doctype/Zip.svg',
    '.svg': 'doctype/Svg.svg', '.ai': 'doctype/Ai.svg', '.psd': 'doctype/Ps.svg',
    '.ae': 'doctype/Ae.svg', '.prproj': 'doctype/Pr.svg', '.xd': 'doctype/Xd.svg',
    '.rp': 'doctype/Rp.svg', '.swf': 'doctype/Swf.svg',
    '.jpg': 'doctype/图片.svg', '.jpeg': 'doctype/图片.svg', '.png': 'doctype/图片.svg',
    '.bmp': 'doctype/图片.svg', '.tiff': 'doctype/图片.svg', '.ico': 'doctype/图片.svg',
    '.epub': 'doctype/图书.svg', '.xmind': 'doctype/思维导图.svg',
}
