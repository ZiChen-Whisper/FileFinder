WINDOW_TITLE = "FileFinder"
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 500
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 600

SEARCH_DEBOUNCE_MS = 300
MAX_WORKERS = 4
BATCH_SIZE = 500

TEXT_EXTENSIONS = {
    '.txt', '.md', '.log', '.csv', '.json', '.xml',
    '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml', '.env', '.gitignore'
}

CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.html', '.css', '.java',
    '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php',
    '.sh', '.bat', '.ps1', '.sql'
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
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'
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
