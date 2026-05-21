"""
样式常量定义文件
================
本文件集中定义了 FileFinder 所有视觉样式的底层令牌（Token）。
修改任何视觉样式时，只需修改本文件中的对应值，所有引用该令牌的组件会自动更新。

修改指南：
  - 修改品牌主色：改 ColorTokens.BRAND 系列（L6-L11）
  - 修改文字颜色：改 ColorTokens.TEXT_* 系列（L13-L17）
  - 修改字号大小：改 FontTokens.*_PT 系列（L49-L53）
  - 修改按钮圆角：改 ButtonTokens.BORDER_RADIUS（L98）
  - 修改弹窗圆角：改 DialogTokens.BORDER_RADIUS（L126）

注意：所有 dataclass 使用 frozen=True，运行时不可修改，确保样式一致性。
"""

from dataclasses import dataclass


# ============================================================================
# 颜色令牌（Color Tokens）
# ============================================================================
# 全局颜色系统，严格限制为以下几类：
#   - 品牌色（6 个）：蓝紫色系，用于主按钮、选中态、焦点等
#   - 文字色（5 个）：从深到浅的灰阶，用于标题/正文/辅助/占位/品牌强调
#   - 边框色（3 个）：默认/悬停/焦点
#   - 背景色（4 个）：从白到浅灰的层级
#   - 语义色（11 个）：成功/警告/错误/信息 + 各状态变体
#   - 阴影/遮罩（3 个）：用于弹窗阴影和加载遮罩
# ============================================================================

@dataclass(frozen=True)
class ColorTokens:

    # --- 品牌色（蓝紫色系）---
    # 主色，贯穿整个应用的视觉标识。用于：主按钮背景、选中态、焦点边框、进度条等
    BRAND: str = "#2233ff"
    # 鼠标悬停时的品牌色，比主色略深
    BRAND_HOVER: str = "#1a29d4"
    # 鼠标按下时的品牌色，比悬停色更深
    BRAND_PRESSED: str = "#1520a8"
    # 禁用状态的品牌色，用于禁用态主按钮背景
    BRAND_DISABLED: str = "#ebf5ff"
    # 品牌色浅背景，用于选中项背景、菜单悬停背景
    BRAND_LIGHT_BG: str = "#ebf5ff"
    # 品牌色更浅背景，用于徽章背景（如搜索匹配数标签）
    BRAND_LIGHTER_BG: str = "#ebf5ff"

    # --- 文字色（灰阶，5 级）---
    # 一级文字色：最深，用于标题、文件名
    TEXT_PRIMARY: str = "#060927"
    # 二级文字色：较深，用于正文、次要按钮文字
    TEXT_SECONDARY: str = "#222222"
    # 三级文字色：中等，用于描述文字、辅助信息
    TEXT_TERTIARY: str = "#666666"
    # 四级文字色：较浅，用于占位符文字、禁用态文字
    TEXT_PLACEHOLDER: str = "#b5b5b5"
    # 品牌强调文字色：用于需要品牌色突出的文字（如匹配数标签）
    TEXT_BRAND: str = "#7580ff"

    # --- 边框色 ---
    # 默认边框色：用于输入框、按钮描边、分割线
    BORDER_DEFAULT: str = "#f2f2f2"
    # 悬停边框色：比默认色略深，鼠标悬停时使用
    BORDER_HOVER: str = "#E5E7EB"
    # 焦点边框色：输入框获得焦点时的边框颜色（品牌色）
    BORDER_FOCUS: str = "#2233ff"

    # --- 背景色（4 级层级）---
    # 一级背景：纯白，用于主背景、卡片背景、弹窗背景
    BG_PRIMARY: str = "#FFFFFF"
    # 二级背景：极浅灰，用于状态栏、列表背景、预览面板头部
    BG_SECONDARY: str = "#f7f7f9"
    # 三级背景：浅灰，用于设置区域背景、扫描日志背景
    BG_TERTIARY: str = "#f0f0f2"
    # 悬停背景：用于按钮/列表项的鼠标悬停背景
    BG_HOVER: str = "#f0f0f2"  # #eaeaec

    # --- 语义色：成功（绿色系）---
    # 成功色：用于扫描完成、状态点绿色
    SUCCESS: str = "#10B981"
    # 成功悬停色
    SUCCESS_HOVER: str = "#059669"
    # 成功禁用色
    SUCCESS_DISABLED: str = "#6EE7B7"

    # --- 语义色：警告（橙色系）---
    # 警告色：用于扫描未完成、取消中等状态
    WARNING: str = "#F59E0B"

    # --- 语义色：错误/危险（红色系）---
    # 错误色：用于扫描失败、危险按钮、删除悬停
    ERROR: str = "#EF4444"
    # 错误悬停色
    ERROR_HOVER: str = "#DC2626"
    # 错误浅背景：用于取消按钮悬停、删除按钮悬停的背景
    ERROR_LIGHT_BG: str = "#FEE2E2"
    # 错误边框色：用于错误态的边框
    ERROR_BORDER: str = "#FCA5A5"
    # 错误表面色：用于危险区域 GroupBox 的背景
    ERROR_SURFACE: str = "#FEF2F2"

    # --- 语义色：信息（蓝色系）---
    # 信息色：用于问题图标
    INFO: str = "#3B82F6"

    # --- 阴影与遮罩 ---
    # 常规阴影色：用于弹窗轻微阴影
    SHADOW_COLOR: str = "rgba(0, 0, 0, 0.08)"
    # 强阴影色：用于需要更明显阴影的场景
    SHADOW_COLOR_STRONG: str = "rgba(0, 0, 0, 0.12)"
    # 半透明白色遮罩：用于搜索进度叠加层
    OVERLAY_LIGHT: str = "rgba(255, 255, 255, 220)"


# 全局颜色令牌单例，所有组件通过 COLORS.XXX 引用
COLORS = ColorTokens()


# ============================================================================
# 字号令牌（Font Tokens）
# ============================================================================
# 全局字号系统，严格限制为 5 种尺寸：
#   DISPLAY > TITLE > BODY > CAPTION > MICRO
# 修改字号时，确保层级关系不变（大标题 > 小标题 > 正文 > 辅助 > 微型）
# ============================================================================

@dataclass(frozen=True)
class FontTokens:
    # 展示字号（18pt）：用于页面大标题，如欢迎页标题、扫描对话框标题
    DISPLAY_PT: int = 18
    # 标题字号（14pt）：用于对话框标题、区段标题
    TITLE_PT: int = 14
    # 正文字号（13pt）：用于按钮文字、列表文字、输入框文字
    BODY_PT: int = 13
    # 辅助字号（12pt）：用于单选按钮、复选框、筛选栏文字
    CAPTION_PT: int = 12
    # 微型字号（11pt）：用于标签按钮、徽章、目录路径标签
    MICRO_PT: int = 11

    # 全局字体族，按优先级降序排列：
    #   Microsoft YaHei（Windows 中文）> PingFang SC（macOS 中文）> Segoe UI（Windows 英文）> sans-serif
    FAMILY: str = '"Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif'

    # 字重常量，用于 QSS font-weight 属性
    # 正常字重（400）：用于正文、描述文字
    WEIGHT_NORMAL: int = 400
    # 中等字重（500）：用于筛选按钮文字
    WEIGHT_MEDIUM: int = 500
    # 粗体字重（700）：用于标题、主按钮文字
    WEIGHT_BOLD: int = 700


# 全局字号令牌单例
FONT = FontTokens()


# ============================================================================
# 圆角令牌（Radius Tokens）
# ============================================================================
# 全局圆角系统，从小到大共 6 级：
#   SMALL(4) < MEDIUM(6) < DEFAULT(8) < LARGE(10) < XLARGE(12) < DIALOG(16)
# ============================================================================

@dataclass(frozen=True)
class RadiusTokens:
    # 小圆角（4px）：用于列表项、树形控件指示器
    SMALL: int = 4
    # 中圆角（6px）：用于菜单项、图标按钮、滚动区域
    MEDIUM: int = 6
    # 默认圆角（8px）：用于标准按钮、输入框、列表、分组框
    DEFAULT: int = 8
    # 大圆角（10px）：用于结果列表项、对话框按钮、取消按钮
    LARGE: int = 10
    # 超大圆角（12px）：用于搜索输入框、搜索按钮、开始扫描按钮
    XLARGE: int = 12
    # 弹窗圆角（16px）：用于所有弹窗/对话框的外框
    DIALOG: int = 16


# 全局圆角令牌单例
RADIUS = RadiusTokens()


# ============================================================================
# 间距令牌（Spacing Tokens）
# ============================================================================
# 全局间距系统，用于组件内部和组件之间的留白。
# 修改间距时注意保持视觉节奏的一致性。
# ============================================================================

@dataclass(frozen=True)
class SpacingTokens:
    # 极小间距（4px）
    XS: int = 4
    # 小间距（6px）
    SM: int = 6
    # 中间距（8px）
    MD: int = 8
    # 大间距（12px）
    LG: int = 12
    # 超大间距（16px）
    XL: int = 16
    # 2XL 间距（20px）
    XXL: int = 20
    # 3XL 间距（24px）
    XXXL: int = 24
    # 弹窗内边距（28px）：对话框内容区域与边框的距离
    DIALOG_PADDING: int = 28


# 全局间距令牌单例
SPACING = SpacingTokens()


# ============================================================================
# 按钮令牌（Button Tokens）
# ============================================================================
# 按钮的统一视觉参数，分为三组：
#   1. 标准按钮：用于对话框中的主要/次要操作按钮
#   2. 小按钮：用于行内操作（浏览、添加、全选等）
#   3. 标签按钮：用于目录标签、筛选标签等可选中标签
# ============================================================================

@dataclass(frozen=True)
class ButtonTokens:
    # --- 标准按钮参数 ---
    # 上下内边距
    PADDING_V: str = "8px"
    # 左右内边距（次要按钮）
    PADDING_H: str = "24px"
    # 左右内边距（主要按钮，略宽以视觉平衡）
    PADDING_H_WIDE: str = "28px"
    # 圆角半径
    BORDER_RADIUS: int = 10
    # 描边宽度
    BORDER_WIDTH: str = "1px"
    # 描边样式
    BORDER_STYLE: str = "solid"
    # 按钮字号
    FONT_SIZE: str = "13px"
    # 按钮字重
    FONT_WEIGHT: str = "bold"
    # 按钮最小宽度
    MIN_WIDTH: str = "80px"

    # --- 按钮阴影参数 ---
    # 阴影水平偏移（目前未使用，预留）
    SHADOW_OFFSET_X: int = 0
    # 阴影垂直偏移（目前未使用，预留）
    SHADOW_OFFSET_Y: int = 2
    # 阴影模糊半径（目前未使用，预留）
    SHADOW_BLUR: int = 8
    # 阴影颜色（目前未使用，预留）
    SHADOW_COLOR: str = "rgba(0, 0, 0, 0.06)"

    # --- 小按钮参数 ---
    # 小按钮上下内边距
    SMALL_PADDING_V: str = "4px"
    # 小按钮左右内边距
    SMALL_PADDING_H: str = "12px"
    # 小按钮字号
    SMALL_FONT_SIZE: str = "12px"
    # 小按钮圆角半径
    SMALL_BORDER_RADIUS: int = 6

    # --- 标签按钮参数 ---
    # 标签上下内边距
    TAG_PADDING_V: str = "4px"
    # 标签左右内边距
    TAG_PADDING_H: str = "10px"
    # 标签字号
    TAG_FONT_SIZE: str = "11px"
    # 标签圆角半径
    TAG_BORDER_RADIUS: int = 8


# 全局按钮令牌单例
BTN = ButtonTokens()


@dataclass(frozen=True)
class TransitionTokens:
    COLOR_FADE_MS: int = 150
    PRESS_SCALE_MS: int = 80
    RELEASE_SCALE_MS: int = 180
    CHECK_FADE_MS: int = 150


TRANSITION = TransitionTokens()


# ============================================================================
# 弹窗令牌（Dialog Tokens）
# ============================================================================
# 所有弹窗/对话框的统一视觉参数。
# 修改弹窗样式时，同时检查 dialog_frame_style() 和 dialog_title_style()。
# ============================================================================

@dataclass(frozen=True)
class DialogTokens:
    # 弹窗外框圆角半径
    BORDER_RADIUS: int = 10
    # 弹窗外框描边宽度
    BORDER_WIDTH: str = "1px"
    # 弹窗外框描边颜色（极浅灰，营造柔和边界感）
    BORDER_COLOR: str = "#F3F4F6"
    # 弹窗外框描边样式
    BORDER_STYLE: str = "solid"
    # 弹窗内容区域内边距
    PADDING: int = 28
    # 弹窗标题字号
    TITLE_FONT_SIZE: str = "14px"
    # 弹窗标题字重
    TITLE_FONT_WEIGHT: str = "bold"
    # 弹窗标题颜色
    TITLE_COLOR: str = "#1F2937"
    # 弹窗正文字号
    BODY_FONT_SIZE: str = "14px"
    # 弹窗正文颜色
    BODY_COLOR: str = "#4B5563"
    # 弹窗正文行高
    BODY_LINE_HEIGHT: str = "1.6"
    # 弹窗最小宽度
    MIN_WIDTH: int = 420
    # 弹窗外层阴影边距（半透明背景的 margin）
    OUTER_MARGIN: int = 24
    # 内容区域元素之间的间距
    CONTENT_SPACING: int = 16
    # 按钮之间的间距
    BUTTON_SPACING: int = 8


# 全局弹窗令牌单例
DIALOG = DialogTokens()


# ============================================================================
# 文件图标映射表
# ============================================================================
# 将文件扩展名映射到对应的 SVG 图标路径（相对于 icons/ 目录）。
# 添加新文件类型支持时，在此表中添加映射即可。
# 未在此表中的扩展名会回退到 'file(solid).svg' 默认图标。
# ============================================================================

FILE_ICON_MAP = {
    # --- 代码文件 → 各语言专属图标 ---
    '.py': 'doctype/Python.svg', '.js': 'doctype/JS.svg', '.ts': 'doctype/TS.svg',
    '.java': 'doctype/Java.svg', '.c': 'doctype/Cpp.svg', '.cpp': 'doctype/Cpp.svg',
    '.h': 'doctype/Cpp.svg', '.go': 'doctype/Go.svg', '.rs': 'doctype/Rust.svg',
    '.rb': 'doctype/Ruby.svg', '.php': 'doctype/PHP.svg', '.html': 'doctype/HTML.svg',
    '.css': 'doctype/CSS.svg', '.sql': 'doctype/SQL.svg', '.sh': 'doctype/Shell.svg',
    '.bat': 'doctype/Shell.svg', '.ps1': 'doctype/Shell.svg', '.json': 'doctype/JSON.svg',
    # --- 文本文件 → 各类型专属图标 ---
    '.txt': 'doctype/TXT.svg', '.md': 'doctype/Markdown.svg', '.log': 'doctype/Log.svg',
    '.xml': 'doctype/XML.svg', '.csv': 'doctype/CSV.svg',
    '.yaml': 'doctype/YAML.svg', '.yml': 'doctype/YAML.svg', '.ini': 'doctype/INI.svg',
    '.cfg': 'doctype/INI.svg', '.conf': 'doctype/INI.svg', '.toml': 'doctype/INI.svg',
    '.env': 'doctype/Env.svg', '.gitignore': 'doctype/INI.svg',
    # --- 文档文件 ---
    '.pdf': 'doctype/PDF.svg', '.doc': 'doctype/Doc.svg', '.docx': 'doctype/Doc.svg',
    '.xls': 'doctype/Excel.svg', '.xlsx': 'doctype/Excel.svg',
    '.ppt': 'doctype/PPT.svg', '.pptx': 'doctype/PPT.svg',
    # --- 音频文件 → 各格式专属图标 ---
    '.mp3': 'doctype/Mp3.svg', '.wav': 'doctype/Wav.svg',
    '.flac': 'doctype/FLAC.svg', '.aac': 'doctype/AAC.svg',
    '.ogg': 'doctype/OGG.svg', '.wma': 'doctype/WMA.svg',
    # --- 视频文件 → 各格式专属图标 ---
    '.mp4': 'doctype/MP4.svg', '.mkv': 'doctype/MKV.svg',
    '.avi': 'doctype/AVI.svg', '.mov': 'doctype/MOV.svg',
    '.wmv': 'doctype/WMV.svg', '.flv': 'doctype/FLV.svg',
    # --- 图片文件 → 各格式专属图标 ---
    '.jpg': 'doctype/JPG.svg', '.jpeg': 'doctype/JPG.svg', '.png': 'doctype/PNG.svg',
    '.bmp': 'doctype/BMP.svg', '.tiff': 'doctype/BMP.svg', '.ico': 'doctype/ICO.svg',
    '.gif': 'doctype/Gif.svg', '.svg': 'doctype/Svg.svg',
    # --- 压缩文件 → Zip.svg ---
    '.zip': 'doctype/Zip.svg', '.rar': 'doctype/Zip.svg', '.7z': 'doctype/Zip.svg',
    '.tar': 'doctype/Zip.svg', '.gz': 'doctype/Zip.svg', '.bz2': 'doctype/Zip.svg',
    '.xz': 'doctype/Zip.svg', '.tgz': 'doctype/Zip.svg', '.tbz2': 'doctype/Zip.svg',
    # --- 设计文件 ---
    '.ai': 'doctype/Ai.svg', '.psd': 'doctype/Ps.svg',
    '.ae': 'doctype/Ae.svg', '.prproj': 'doctype/Pr.svg', '.xd': 'doctype/Xd.svg',
    '.rp': 'doctype/Rp.svg', '.swf': 'doctype/Swf.svg',
    # --- 其他 ---
    '.epub': 'doctype/图书.svg', '.xmind': 'doctype/思维导图.svg',
}
