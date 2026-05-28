WINDOW_TITLE = "FileFinder"
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 500
DEFAULT_WINDOW_WIDTH = 1100
DEFAULT_WINDOW_HEIGHT = 720
PREVIEW_PANEL_MIN_WIDTH = 200

SEARCH_DEBOUNCE_MS = 300
FILTER_DEBOUNCE_MS = 50
FS_REFRESH_DEBOUNCE_MS = 500
PREVIEW_DELAY_MS = 150

MAX_WORKERS = 4
MIN_CONTENT_WORKERS = 4
MAX_CONTENT_WORKERS = 8
BACKGROUND_TASK_WORKERS = 1

BATCH_SIZE = 500
CONTENT_INDEX_BATCH_SIZE = 50
CONTENT_SEARCH_BATCH_SIZE = 50
RENDER_BATCH_SIZE = 50
FILE_LOG_BATCH_SIZE = 50
TREE_EXPAND_BATCH_SIZE = 15

MAX_SEARCH_RESULTS = 1000
CONTENT_MAX_FILE_SIZE_MB = 10
INITIAL_DISPLAY_LIMIT = 200
LOAD_MORE_BATCH = 100

# 内容搜索参数
MAX_MATCHES_PER_FILE = 10
CONTEXT_LINES_BEFORE = 3
CONTEXT_LINES_AFTER = 3
SEARCH_TIMEOUT_SECONDS = 120
SINGLE_FILE_SEARCH_TIMEOUT = 30

# 预览参数
MAX_TEXT_PREVIEW_SIZE_MB = 2
MAX_PREVIEW_LINES = 500
MAX_DOC_PREVIEW_SIZE_MB = 10
DEFAULT_PDF_PAGES = 5
PDF_LOAD_MORE_PAGES = 10
PDF_RENDER_DPI = 150
MAX_DOC_CHARS = 50000
MAX_MEDIA_PREVIEW_SIZE_MB = 200
FORCE_PREVIEW_MAX_SIZE_MB = 50

# 扫描参数
SCAN_PROGRESS_INTERVAL = 0.3
FILE_LOG_INTERVAL = 0.1

# 数据库参数
DB_CACHE_SIZE_KB = 16000
DB_MMAP_SIZE = 67108864
DB_PAGE_SIZE = 4096

# 跳过的目录名（扫描时跳过）
SKIP_DIR_NAMES = frozenset({
    'node_modules', '__pycache__', '.git', '.svn', '.hg',
    '.venv', 'venv', '.tox', '.eggs', 'build', 'dist',
    '.idea', '.vscode', '.vs', '$RECYCLE.BIN',
    'System Volume Information',
})

TEXT_EXTENSIONS = {
    '.txt', '.md', '.log', '.csv', '.xml',
    '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml', '.env', '.gitignore'
}

CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.html', '.css', '.java',
    '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php',
    '.sh', '.bat', '.ps1', '.sql', '.json'
}

DOCUMENT_EXTENSIONS = {
    '.pdf', '.docx', '.xlsx', '.pptx', '.rtf', '.epub'
}

IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.ico'
}

VIDEO_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv'
}

AUDIO_EXTENSIONS = {
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'
}

ARCHIVE_EXTENSIONS = {
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tbz2'
}

EXCLUDED_EXTENSIONS = {
    '.dll', '.exe', '.sys', '.obj', '.lib', '.pdb', '.so', '.dylib'
}

FILE_TYPE_CATEGORIES = {
    'all': '全部类型',
    'folder': '文件夹',
    'document': '文档',
    'code': '代码',
    'image': '图片',
    'video': '视频',
    'audio': '音频',
    'archive': '压缩包',
    'other': '其他'
}

FILE_TYPE_SUBCATEGORIES = {
    'document': [
        ('all', '全部', TEXT_EXTENSIONS | DOCUMENT_EXTENSIONS),
        ('text', '文本', TEXT_EXTENSIONS),
        ('pdf', 'PDF', {'.pdf'}),
        ('word', 'Word', {'.docx', '.doc'}),
        ('excel', 'Excel', {'.xlsx', '.xls'}),
        ('ppt', 'PPT', {'.pptx', '.ppt'}),
        ('ebook', '电子书', {'.epub', '.rtf'}),
    ],
    'code': [
        ('all', '全部', CODE_EXTENSIONS),
        ('python', 'Python', {'.py'}),
        ('javascript', 'JS/TS', {'.js', '.ts'}),
        ('html_css', 'HTML/CSS', {'.html', '.css'}),
        ('java', 'Java', {'.java'}),
        ('c_cpp', 'C/C++', {'.c', '.cpp', '.h'}),
        ('go', 'Go', {'.go'}),
        ('rust', 'Rust', {'.rs'}),
        ('ruby', 'Ruby', {'.rb'}),
        ('php', 'PHP', {'.php'}),
        ('shell', 'Shell', {'.sh', '.bat', '.ps1'}),
        ('sql', 'SQL', {'.sql'}),
        ('json', 'JSON', {'.json'}),
    ],
    'image': [
        ('all', '全部', IMAGE_EXTENSIONS),
        ('jpg', 'JPG', {'.jpg', '.jpeg'}),
        ('png', 'PNG', {'.png'}),
        ('gif', 'GIF', {'.gif'}),
        ('bmp', 'BMP', {'.bmp'}),
        ('svg', 'SVG', {'.svg'}),
        ('icon', '图标', {'.ico', '.tiff'}),
    ],
    'video': [
        ('all', '全部', VIDEO_EXTENSIONS),
        ('mp4', 'MP4', {'.mp4'}),
        ('mkv', 'MKV', {'.mkv'}),
        ('avi', 'AVI', {'.avi'}),
        ('mov', 'MOV', {'.mov'}),
        ('other_video', '其他', {'.wmv', '.flv'}),
    ],
    'audio': [
        ('all', '全部', AUDIO_EXTENSIONS),
        ('mp3', 'MP3', {'.mp3'}),
        ('wav', 'WAV', {'.wav'}),
        ('flac', 'FLAC', {'.flac'}),
        ('other_audio', '其他', {'.aac', '.ogg', '.wma'}),
    ],
    'archive': [
        ('all', '全部', ARCHIVE_EXTENSIONS),
        ('zip', 'ZIP', {'.zip'}),
        ('rar', 'RAR', {'.rar'}),
        ('7z', '7Z', {'.7z'}),
        ('tar', 'TAR', {'.tar', '.gz', '.bz2'}),
    ],
}

def get_category_extensions(category: str) -> set:
    if category == 'document':
        return TEXT_EXTENSIONS | DOCUMENT_EXTENSIONS
    elif category == 'code':
        return CODE_EXTENSIONS
    elif category == 'image':
        return IMAGE_EXTENSIONS
    elif category == 'video':
        return VIDEO_EXTENSIONS
    elif category == 'audio':
        return AUDIO_EXTENSIONS
    elif category == 'archive':
        return ARCHIVE_EXTENSIONS
    else:
        return set()
