import os
import math
import zipfile
import tarfile
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                               QScrollArea, QSizePolicy, QTextEdit, QPushButton,
                               QStackedWidget, QTextBrowser, QTableWidget,
                               QTableWidgetItem, QHeaderView, QGridLayout,
                               QFrame, QApplication)
from PySide6.QtGui import (QFont, QFontMetrics, QIcon, QPixmap, QColor,
                           QTextCharFormat, QTextCursor, QSyntaxHighlighter,
                           QTextDocument, QPainter, QPen)
from PySide6.QtCore import Qt, QSize, QRectF, QTimer, QThread, Signal

try:
    from PySide6.QtMultimediaWidgets import QVideoWidget
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    HAS_MULTIMEDIA = True
except ImportError:
    HAS_MULTIMEDIA = False
    QVideoWidget = None
    QMediaPlayer = None
    QAudioOutput = None
from constants import (TEXT_EXTENSIONS, CODE_EXTENSIONS, IMAGE_EXTENSIONS,
                       DOCUMENT_EXTENSIONS, ARCHIVE_EXTENSIONS, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS)
from ..style_constants import COLORS, FONT, RADIUS, FILE_ICON_MAP
from ..style_manager import (scrollbar_style, label_caption_style, label_micro_style,
                             badge_style, button_small_primary, button_small_secondary)

logger = logging.getLogger(__name__)

PREVIEWABLE_TEXT_EXTS = TEXT_EXTENSIONS | CODE_EXTENSIONS
PREVIEWABLE_IMAGE_EXTS = IMAGE_EXTENSIONS
MAX_TEXT_PREVIEW_SIZE_MB = 2
MAX_PREVIEW_LINES = 500
MAX_DOC_PREVIEW_SIZE_MB = 10
DEFAULT_PDF_PAGES = 5
MAX_DOC_CHARS = 50000
MAX_MEDIA_PREVIEW_SIZE_MB = 50
MAX_IMAGE_PREVIEW_PIXELS = 1920 * 1080
MARKDOWN_EXTS = {'.md'}
EXCEL_RENDER_PAGES = 3


class _PythonHighlighter(QSyntaxHighlighter):
    KEYWORDS = {'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
                'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
                'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
                'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
                'while', 'with', 'yield'}
    BUILTINS = {'print', 'len', 'range', 'int', 'str', 'list', 'dict', 'set', 'tuple',
                'float', 'bool', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr',
                'super', 'self', 'cls', 'open', 'input', 'abs', 'max', 'min', 'sum',
                'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed', 'any', 'all'}

    def highlightBlock(self, text):
        fmt_keyword = QTextCharFormat()
        fmt_keyword.setForeground(QColor("#c678dd"))
        fmt_keyword.setFontWeight(QFont.Weight.Bold)

        fmt_builtin = QTextCharFormat()
        fmt_builtin.setForeground(QColor("#e5c07b"))

        fmt_string = QTextCharFormat()
        fmt_string.setForeground(QColor("#98c379"))

        fmt_comment = QTextCharFormat()
        fmt_comment.setForeground(QColor("#5c6370"))
        fmt_comment.setFontItalic(True)

        fmt_number = QTextCharFormat()
        fmt_number.setForeground(QColor("#d19a66"))

        fmt_decorator = QTextCharFormat()
        fmt_decorator.setForeground(QColor("#e5c07b"))
        fmt_decorator.setFontItalic(True)

        i = 0
        while i < len(text):
            if text[i] == '#':
                self.setFormat(i, len(text) - i, fmt_comment)
                break
            elif text[i] in '"\'':
                quote = text[i]
                j = i + 1
                while j < len(text):
                    if text[j] == '\\':
                        j += 2
                        continue
                    if text[j] == quote:
                        j += 1
                        break
                    j += 1
                self.setFormat(i, j - i, fmt_string)
                i = j
            elif text[i].isalpha() or text[i] == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                word = text[i:j]
                if word in self.KEYWORDS:
                    self.setFormat(i, j - i, fmt_keyword)
                elif word in self.BUILTINS:
                    self.setFormat(i, j - i, fmt_builtin)
                i = j
            elif text[i] == '@':
                j = i + 1
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                self.setFormat(i, j - i, fmt_decorator)
                i = j
            elif text[i].isdigit() or (text[i] == '.' and i + 1 < len(text) and text[i + 1].isdigit()):
                j = i
                has_dot = False
                while j < len(text) and (text[j].isdigit() or (text[j] == '.' and not has_dot)):
                    if text[j] == '.':
                        has_dot = True
                    j += 1
                self.setFormat(i, j - i, fmt_number)
                i = j
            else:
                i += 1


class _JSHighlighter(QSyntaxHighlighter):
    KEYWORDS = {'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
                'default', 'delete', 'do', 'else', 'export', 'extends', 'finally',
                'for', 'function', 'if', 'import', 'in', 'instanceof', 'let', 'new',
                'of', 'return', 'super', 'switch', 'this', 'throw', 'try', 'typeof',
                'var', 'void', 'while', 'with', 'yield', 'async', 'await', 'from',
                'as', 'static', 'get', 'set'}
    BUILTINS = {'console', 'document', 'window', 'Math', 'JSON', 'Promise', 'Array',
                'Object', 'String', 'Number', 'Boolean', 'Map', 'Set', 'Date', 'Error',
                'true', 'false', 'null', 'undefined', 'NaN', 'Infinity'}

    def highlightBlock(self, text):
        fmt_keyword = QTextCharFormat()
        fmt_keyword.setForeground(QColor("#c678dd"))
        fmt_keyword.setFontWeight(QFont.Weight.Bold)
        fmt_string = QTextCharFormat()
        fmt_string.setForeground(QColor("#98c379"))
        fmt_comment = QTextCharFormat()
        fmt_comment.setForeground(QColor("#5c6370"))
        fmt_comment.setFontItalic(True)
        fmt_number = QTextCharFormat()
        fmt_number.setForeground(QColor("#d19a66"))

        i = 0
        while i < len(text):
            if text[i:i+2] == '//':
                self.setFormat(i, len(text) - i, fmt_comment)
                break
            elif text[i] in '"\'`':
                quote = text[i]
                j = i + 1
                while j < len(text):
                    if text[j] == '\\':
                        j += 2
                        continue
                    if text[j] == quote:
                        j += 1
                        break
                    j += 1
                self.setFormat(i, j - i, fmt_string)
                i = j
            elif text[i].isalpha() or text[i] == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                word = text[i:j]
                if word in self.KEYWORDS:
                    self.setFormat(i, j - i, fmt_keyword)
                elif word in self.BUILTINS:
                    fmt_b = QTextCharFormat()
                    fmt_b.setForeground(QColor("#e5c07b"))
                    self.setFormat(i, j - i, fmt_b)
                i = j
            elif text[i].isdigit():
                j = i
                while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                    j += 1
                self.setFormat(i, j - i, fmt_number)
                i = j
            else:
                i += 1


class _GenericCodeHighlighter(QSyntaxHighlighter):
    KEYWORDS_MAP = {
        '.java': {'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
                  'char', 'class', 'continue', 'default', 'do', 'double', 'else',
                  'enum', 'extends', 'final', 'finally', 'float', 'for', 'if',
                  'implements', 'import', 'instanceof', 'int', 'interface', 'long',
                  'native', 'new', 'package', 'private', 'protected', 'public',
                  'return', 'short', 'static', 'strictfp', 'super', 'switch',
                  'synchronized', 'this', 'throw', 'throws', 'transient', 'try',
                  'void', 'volatile', 'while', 'true', 'false', 'null'},
        '.c': {'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
               'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
               'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof',
               'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void',
               'volatile', 'while'},
        '.cpp': {'auto', 'break', 'case', 'char', 'class', 'const', 'continue',
                 'default', 'delete', 'do', 'double', 'else', 'enum', 'explicit',
                 'extern', 'float', 'for', 'friend', 'goto', 'if', 'inline', 'int',
                 'long', 'mutable', 'namespace', 'new', 'operator', 'private',
                 'protected', 'public', 'register', 'return', 'short', 'signed',
                 'sizeof', 'static', 'struct', 'switch', 'template', 'this', 'throw',
                 'try', 'typedef', 'typename', 'union', 'unsigned', 'using',
                 'virtual', 'void', 'volatile', 'while', 'nullptr', 'true', 'false'},
        '.h': {'auto', 'break', 'case', 'char', 'class', 'const', 'continue',
               'default', 'delete', 'do', 'double', 'else', 'enum', 'explicit',
               'extern', 'float', 'for', 'friend', 'goto', 'if', 'inline', 'int',
               'long', 'mutable', 'namespace', 'new', 'operator', 'private',
               'protected', 'public', 'register', 'return', 'short', 'signed',
               'sizeof', 'static', 'struct', 'switch', 'template', 'this', 'throw',
               'try', 'typedef', 'typename', 'union', 'unsigned', 'using',
               'virtual', 'void', 'volatile', 'while', 'nullptr', 'true', 'false'},
        '.go': {'break', 'case', 'chan', 'const', 'continue', 'default', 'defer',
                'else', 'fallthrough', 'for', 'func', 'go', 'goto', 'if', 'import',
                'interface', 'map', 'package', 'range', 'return', 'select', 'struct',
                'switch', 'type', 'var', 'true', 'false', 'nil'},
        '.rs': {'as', 'async', 'await', 'break', 'const', 'continue', 'crate', 'dyn',
                'else', 'enum', 'extern', 'fn', 'for', 'if', 'impl', 'in', 'let',
                'loop', 'match', 'mod', 'move', 'mut', 'pub', 'ref', 'return', 'self',
                'Self', 'static', 'struct', 'super', 'trait', 'type', 'unsafe', 'use',
                'where', 'while', 'true', 'false'},
        '.rb': {'BEGIN', 'END', 'alias', 'and', 'begin', 'break', 'case', 'class',
                'def', 'defined?', 'do', 'else', 'elsif', 'end', 'ensure', 'false',
                'for', 'if', 'in', 'module', 'next', 'nil', 'not', 'or', 'redo',
                'rescue', 'retry', 'return', 'self', 'super', 'then', 'true',
                'undef', 'unless', 'until', 'when', 'while', 'yield'},
        '.php': {'abstract', 'and', 'array', 'as', 'break', 'callable', 'case',
                 'catch', 'class', 'clone', 'const', 'continue', 'declare', 'default',
                 'die', 'do', 'echo', 'else', 'elseif', 'empty', 'enddeclare',
                 'endfor', 'endforeach', 'endif', 'endswitch', 'endwhile', 'eval',
                 'exit', 'extends', 'final', 'finally', 'fn', 'for', 'foreach',
                 'function', 'global', 'goto', 'if', 'implements', 'include',
                 'instanceof', 'interface', 'isset', 'list', 'namespace', 'new',
                 'or', 'print', 'private', 'protected', 'public', 'require',
                 'return', 'static', 'switch', 'throw', 'trait', 'try', 'unset',
                 'use', 'var', 'while', 'xor', 'yield', 'true', 'false', 'null'},
        '.sql': {'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE',
                 'SET', 'DELETE', 'CREATE', 'TABLE', 'ALTER', 'DROP', 'INDEX',
                 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AND', 'OR',
                 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'ORDER', 'BY', 'GROUP',
                 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'ALL', 'AS', 'DISTINCT',
                 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'NULL', 'IS', 'PRIMARY',
                 'KEY', 'FOREIGN', 'REFERENCES', 'CONSTRAINT', 'DEFAULT', 'CHECK',
                 'UNIQUE', 'AUTO_INCREMENT', 'IF', 'THEN', 'ELSE', 'END', 'CASE',
                 'WHEN', 'VIEW', 'TRIGGER', 'PROCEDURE', 'FUNCTION', 'BEGIN',
                 'COMMIT', 'ROLLBACK', 'GRANT', 'REVOKE'},
        '.sh': {'if', 'then', 'else', 'elif', 'fi', 'case', 'esac', 'for', 'while',
                'until', 'do', 'done', 'in', 'function', 'select', 'time', 'coproc',
                'return', 'exit', 'break', 'continue', 'declare', 'export', 'local',
                'readonly', 'typeset', 'unset', 'true', 'false'},
        '.bat': {'echo', 'set', 'if', 'else', 'for', 'do', 'goto', 'call', 'exit',
                 'pause', 'rem', 'start', 'title', 'color', 'cls', 'copy', 'del',
                 'move', 'ren', 'mkdir', 'rmdir', 'cd', 'dir', 'type', 'find',
                 'findstr', 'sort', 'more', 'choice', 'timeout', 'taskkill',
                 'not', 'exist', 'defined', 'equ', 'neq', 'lss', 'leq', 'gtr', 'geq'},
        '.ps1': {'if', 'else', 'elseif', 'switch', 'for', 'foreach', 'while', 'do',
                 'until', 'break', 'continue', 'return', 'throw', 'try', 'catch',
                 'finally', 'function', 'filter', 'workflow', 'class', 'enum',
                 'param', 'dynamicparam', 'begin', 'process', 'end', 'in',
                 'from', 'where', 'select', 'sort', 'group', 'measure', 'foreach-object',
                 'where-object', 'true', 'false', '$null'},
        '.html': {'html', 'head', 'body', 'div', 'span', 'p', 'a', 'img', 'ul', 'ol',
                  'li', 'table', 'tr', 'td', 'th', 'form', 'input', 'button',
                  'select', 'option', 'textarea', 'script', 'style', 'link', 'meta',
                  'title', 'header', 'footer', 'nav', 'section', 'article', 'aside',
                  'main', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'hr', 'strong',
                  'em', 'code', 'pre', 'blockquote'},
        '.css': {'color', 'background', 'margin', 'padding', 'border', 'font',
                 'display', 'position', 'width', 'height', 'top', 'left', 'right',
                 'bottom', 'flex', 'grid', 'align', 'justify', 'overflow', 'opacity',
                 'transition', 'transform', 'animation', 'box-shadow', 'text-align',
                 'line-height', 'font-size', 'font-weight', 'font-family', 'z-index',
                 'important', 'none', 'auto', 'inherit', 'initial', 'unset', 'relative',
                 'absolute', 'fixed', 'sticky', 'block', 'inline', 'flex', 'grid',
                 'hidden', 'visible', 'scroll', 'center', 'space-between', 'column',
                 'row', 'wrap', 'nowrap'},
    }

    def __init__(self, doc, ext):
        self._ext = ext
        super().__init__(doc)

    def highlightBlock(self, text):
        keywords = self.KEYWORDS_MAP.get(self._ext, set())
        if not keywords:
            return
        fmt_keyword = QTextCharFormat()
        fmt_keyword.setForeground(QColor("#c678dd"))
        fmt_keyword.setFontWeight(QFont.Weight.Bold)
        fmt_string = QTextCharFormat()
        fmt_string.setForeground(QColor("#98c379"))
        fmt_comment = QTextCharFormat()
        fmt_comment.setForeground(QColor("#5c6370"))
        fmt_comment.setFontItalic(True)
        fmt_number = QTextCharFormat()
        fmt_number.setForeground(QColor("#d19a66"))

        i = 0
        while i < len(text):
            if self._ext in ('.sh', '.bat', '.ps1') and text[i] == '#':
                self.setFormat(i, len(text) - i, fmt_comment)
                break
            elif self._ext in ('.sql',) and text[i:i+2] == '--':
                self.setFormat(i, len(text) - i, fmt_comment)
                break
            elif self._ext in ('.html',) and '<!--' in text[i:]:
                idx = text.index('<!--', i)
                end = text.find('-->', idx)
                if end == -1:
                    self.setFormat(idx, len(text) - idx, fmt_comment)
                else:
                    self.setFormat(idx, end + 3 - idx, fmt_comment)
                break
            elif self._ext in ('.css',) and text[i:i+2] == '/*':
                end = text.find('*/', i + 2)
                if end == -1:
                    self.setFormat(i, len(text) - i, fmt_comment)
                else:
                    self.setFormat(i, end + 2 - i, fmt_comment)
                i = end + 2 if end != -1 else len(text)
                continue
            elif text[i] in '"\'':
                quote = text[i]
                j = i + 1
                while j < len(text):
                    if text[j] == '\\':
                        j += 2
                        continue
                    if text[j] == quote:
                        j += 1
                        break
                    j += 1
                self.setFormat(i, j - i, fmt_string)
                i = j
            elif text[i].isalpha() or text[i] == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] in '_-'):
                    j += 1
                word = text[i:j]
                if self._ext in ('.sql',) and word.upper() in {k.upper() for k in keywords}:
                    self.setFormat(i, j - i, fmt_keyword)
                elif word in keywords:
                    self.setFormat(i, j - i, fmt_keyword)
                i = j
            elif text[i].isdigit():
                j = i
                while j < len(text) and (text[j].isdigit() or text[j] in '.%pxem'):
                    j += 1
                self.setFormat(i, j - i, fmt_number)
                i = j
            else:
                i += 1


def _create_highlighter(doc, ext):
    if ext in ('.py',):
        return _PythonHighlighter(doc)
    elif ext in ('.js', '.ts'):
        return _JSHighlighter(doc)
    elif ext in _GenericCodeHighlighter.KEYWORDS_MAP:
        return _GenericCodeHighlighter(doc, ext)
    return None


class ElidedFileNameLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full_text = text

    def setText(self, text):
        self._full_text = text
        super().setText(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self):
        fm = self.fontMetrics()
        available = self.width()
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideMiddle, available)
        super().setText(elided)

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self):
        return QSize(0, super().minimumSizeHint().height())


class _FolderEntryRow(QWidget):
    def __init__(self, name: str, is_dir: bool, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(6)

        icon_label = QLabel()
        icon_label.setFixedSize(16, 16)
        icon_label.setStyleSheet("border: none; background: transparent;")
        if is_dir:
            icon_label.setPixmap(QIcon("icons/doctype/Folder.svg").pixmap(QSize(16, 16)))
        else:
            ext = os.path.splitext(name)[1].lower()
            icon_name = FILE_ICON_MAP.get(ext, 'doctype/File.svg')
            icon_label.setPixmap(QIcon(f"icons/{icon_name}").pixmap(QSize(16, 16)))

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {COLORS.TEXT_SECONDARY};
            font-size: {FONT.MICRO_PT}px;
            border: none;
            background: transparent;
        """)

        layout.addWidget(icon_label)
        layout.addWidget(name_label, 1)
        self.setStyleSheet("QWidget { background: transparent; }")


class _PreviewLoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._rotate)
        self._dot_count = 8
        self._dot_radius = 3
        self._radius = 14
        self.setFixedSize(48, 48)
        self.setVisible(False)

    def start(self):
        self._angle = 0
        self.setVisible(True)
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.setVisible(False)

    def _rotate(self):
        self._angle = (self._angle + 45) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center_x = self.width() / 2
        center_y = self.height() / 2
        for i in range(self._dot_count):
            angle = (self._angle + i * (360 / self._dot_count)) % 360
            alpha = int(255 * (1 - i / self._dot_count))
            rad = angle * math.pi / 180
            x = center_x + self._radius * math.cos(rad)
            y = center_y + self._radius * math.sin(rad)
            color = QColor(COLORS.BRAND)
            color.setAlpha(alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(int(x - self._dot_radius), int(y - self._dot_radius),
                              self._dot_radius * 2, self._dot_radius * 2)
        painter.end()


class _PdfRenderWorker(QThread):
    page_rendered = Signal(int, QPixmap)
    render_finished = Signal(int)

    def __init__(self, file_path, max_pages, start_page=0, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._max_pages = max_pages
        self._start_page = start_page
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            import fitz
            doc = fitz.open(self._file_path)
            total = len(doc)
            end_page = min(self._start_page + self._max_pages, total)
            for i in range(self._start_page, end_page):
                if self._cancelled:
                    break
                page = doc[i]
                zoom = 2.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                pixmap = QPixmap()
                pixmap.loadFromData(img_data, "PNG")
                if not pixmap.isNull():
                    self.page_rendered.emit(i, pixmap)
            doc.close()
            self.render_finished.emit(total)
        except Exception as e:
            logger.warning(f"PDF render worker error: {e}")
            self.render_finished.emit(0)


class _ExcelRenderWorker(QThread):
    sheet_rendered = Signal(int, QPixmap, str)
    render_finished = Signal()

    def __init__(self, file_path, max_pages=EXCEL_RENDER_PAGES, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._max_pages = max_pages
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            from openpyxl import load_workbook
            from openpyxl.utils import get_column_letter
            wb = load_workbook(self._file_path, read_only=True, data_only=True)
            for idx, sheet_name in enumerate(wb.sheetnames):
                if self._cancelled or idx >= self._max_pages:
                    break
                ws = wb[sheet_name]
                rows_data = []
                max_cols = 0
                row_count = 0
                for row in ws.iter_rows(values_only=True):
                    if self._cancelled:
                        break
                    cells = [str(c) if c is not None else '' for c in row]
                    rows_data.append(cells)
                    max_cols = max(max_cols, len(cells))
                    row_count += 1
                    if row_count > 100:
                        break
                if not rows_data or self._cancelled:
                    continue
                max_cols = min(max_cols, 26)
                cell_w = 80
                cell_h = 24
                header_h = 28
                img_w = max_cols * cell_w + 40
                img_h = len(rows_data) * cell_h + header_h + 20
                img_w = min(img_w, 3000)
                img_h = min(img_h, 4000)
                pixmap = QPixmap(img_w, img_h)
                pixmap.fill(QColor(COLORS.BG_PRIMARY))
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                font = QFont("Microsoft YaHei", 9)
                painter.setFont(font)
                y = 10
                painter.setPen(QColor(COLORS.TEXT_PRIMARY))
                title_font = QFont("Microsoft YaHei", 10)
                title_font.setBold(True)
                painter.setFont(title_font)
                painter.drawText(10, y + 14, f"Sheet: {sheet_name}")
                y += header_h
                painter.setFont(font)
                col_header_h = 22
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(COLORS.BG_TERTIARY))
                painter.drawRect(10, y, max_cols * cell_w, col_header_h)
                painter.setPen(QColor(COLORS.TEXT_TERTIARY))
                for c in range(max_cols):
                    col_letter = get_column_letter(c + 1)
                    painter.drawText(10 + c * cell_w + 4, y + 16, col_letter)
                y += col_header_h
                for r_idx, row in enumerate(rows_data):
                    if y + cell_h > img_h - 10:
                        break
                    if r_idx % 2 == 1:
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(QColor(COLORS.BG_SECONDARY))
                        painter.drawRect(10, y, max_cols * cell_w, cell_h)
                    painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 1))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    for c in range(min(len(row), max_cols)):
                        rect = QRectF(10 + c * cell_w, y, cell_w, cell_h)
                        painter.drawRect(rect)
                        painter.setPen(QColor(COLORS.TEXT_SECONDARY))
                        text = row[c][:20] if len(row[c]) > 20 else row[c]
                        painter.drawText(rect.adjusted(4, 0, -4, 0),
                                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                                        text)
                        painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 1))
                    y += cell_h
                painter.end()
                self.sheet_rendered.emit(idx, pixmap, sheet_name)
            wb.close()
            self.render_finished.emit()
        except Exception as e:
            logger.warning(f"Excel render worker error: {e}")
            self.render_finished.emit()


class _PptRenderWorker(QThread):
    slide_rendered = Signal(int, QPixmap, str)
    render_finished = Signal(int)

    def __init__(self, file_path, max_pages=3, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._max_pages = max_pages
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            from pptx import Presentation
            from pptx.util import Inches, Emu
            prs = Presentation(self._file_path)
            slide_count = len(prs.slides)
            slide_width = prs.slide_width
            slide_height = prs.slide_height

            for idx, slide in enumerate(prs.slides):
                if self._cancelled or idx >= self._max_pages:
                    break

                scale = 2.0
                w_px = int(slide_width / 914400 * 96 * scale)
                h_px = int(slide_height / 914400 * 96 * scale)
                w_px = min(w_px, 3000)
                h_px = min(h_px, 2000)

                pixmap = QPixmap(w_px, h_px)
                if pixmap.isNull():
                    continue
                pixmap.fill(QColor("white"))
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

                font = QFont("Microsoft YaHei", int(11 * scale))
                painter.setFont(font)
                painter.setPen(QColor(COLORS.TEXT_PRIMARY))

                y = int(20 * scale)
                x_margin = int(30 * scale)
                max_w = w_px - 2 * x_margin

                title_font = QFont("Microsoft YaHei", int(14 * scale))
                title_font.setBold(True)
                painter.setFont(title_font)
                painter.drawText(x_margin, y + int(14 * scale),
                               f"Slide {idx + 1}")
                y += int(30 * scale)

                painter.setFont(font)
                for shape in slide.shapes:
                    if self._cancelled:
                        break
                    if shape.has_text_frame:
                        for para in shape.text_frame.paragraphs:
                            text = para.text.strip()
                            if text:
                                if y + int(20 * scale) > h_px - int(10 * scale):
                                    painter.setPen(QColor(COLORS.TEXT_TERTIARY))
                                    painter.drawText(x_margin, y + int(14 * scale), "...")
                                    y = h_px
                                    break
                                painter.setPen(QColor(COLORS.TEXT_SECONDARY))
                                elided = text[:80] + "..." if len(text) > 80 else text
                                painter.drawText(x_margin, y + int(14 * scale), elided)
                                y += int(22 * scale)

                painter.end()
                self.slide_rendered.emit(idx, pixmap, f"Slide {idx + 1}")

            self.render_finished.emit(slide_count)
        except Exception as e:
            logger.warning(f"PPT render worker error: {e}")
            self.render_finished.emit(0)


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result = None
        self._full_content = None
        self._showing_truncated = False
        self._current_file_item = None
        self._highlighter = None
        self._media_player = None
        self._audio_output = None
        self._video_widget = None
        self._md_source_mode = False
        self._pdf_doc = None
        self._pdf_total_pages = 0
        self._pdf_pages_loaded = 0
        self._pdf_render_worker = None
        self._excel_render_worker = None
        self._ppt_render_worker = None
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(100)
        self._preview_timer.timeout.connect(self._do_delayed_preview)
        self._pending_file_item = None
        self._pending_force = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        _inner_radius = RADIUS.LARGE - 1
        _gap = 4
        _cir = max(RADIUS.LARGE - _gap, 2)

        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setStyleSheet("border: none; background: transparent;")

        self.title_label = ElidedFileNameLabel("预览")
        title_font = QFont()
        title_font.setPointSize(FONT.BODY_PT)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; border: none; background: transparent;")

        self._file_info_label = QLabel("")
        self._file_info_label.setStyleSheet(f"""
            color: {COLORS.TEXT_TERTIARY};
            font-size: {FONT.MICRO_PT}px;
            border: none;
            background: transparent;
        """)

        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self._file_info_label)

        self.header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_SECONDARY};
                border-bottom: 1px solid {COLORS.BORDER_DEFAULT};
                border-top-left-radius: {_inner_radius}px;
                border-top-right-radius: {_inner_radius}px;
            }}
        """)

        self.empty_placeholder = QLabel("")
        self.empty_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_placeholder.setStyleSheet(f"""
            background-color: transparent; color: transparent;
            font-size: {FONT.DISPLAY_PT}px; border: none;
        """)

        self._content_stack = QStackedWidget()

        self._text_preview = QWidget()
        tp_layout = QVBoxLayout(self._text_preview)
        tp_layout.setContentsMargins(_gap, _gap, _gap, _gap)
        tp_layout.setSpacing(4)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS.BG_PRIMARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {_cir}px;
                padding: 12px 16px;
                color: {COLORS.TEXT_SECONDARY};
                font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
                font-size: {FONT.MICRO_PT}px;
                selection-background-color: {COLORS.BRAND_LIGHT_BG};
                selection-color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        self._text_edit.setFrameStyle(QTextEdit.Shape.NoFrame)

        self._show_more_btn = QPushButton("显示剩余内容 ▼")
        self._show_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_more_btn.setStyleSheet(button_small_secondary())
        self._show_more_btn.setVisible(False)
        self._show_more_btn.clicked.connect(self._on_show_more)

        self._md_toggle_btn = QPushButton("源码模式")
        self._md_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._md_toggle_btn.setStyleSheet(button_small_secondary())
        self._md_toggle_btn.setVisible(False)
        self._md_toggle_btn.clicked.connect(self._on_toggle_md_mode)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._md_toggle_btn)
        btn_row.addWidget(self._show_more_btn)

        self._md_browser = QTextBrowser()
        self._md_browser.setOpenExternalLinks(False)
        self._md_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {COLORS.BG_PRIMARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {_cir}px;
                padding: 16px 20px;
                color: {COLORS.TEXT_SECONDARY};
                font-size: {FONT.CAPTION_PT}px;
                selection-background-color: {COLORS.BRAND_LIGHT_BG};
            }}
        """)
        self._md_browser.setVisible(False)

        tp_layout.addWidget(self._md_browser, 1)
        tp_layout.addWidget(self._text_edit, 1)
        tp_layout.addLayout(btn_row)

        self._image_preview = QWidget()
        ip_layout = QVBoxLayout(self._image_preview)
        ip_layout.setContentsMargins(_gap, _gap, _gap, _gap)
        ip_layout.setSpacing(4)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._image_label.setStyleSheet(f"""
            border: 1px solid {COLORS.BORDER_DEFAULT};
            border-radius: {_cir}px;
            background-color: {COLORS.BG_PRIMARY};
        """)

        self._view_original_btn = QPushButton("查看原图")
        self._view_original_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._view_original_btn.setStyleSheet(button_small_primary())
        self._view_original_btn.setVisible(False)
        self._view_original_btn.clicked.connect(self._on_view_original_image)

        ip_btn_row = QHBoxLayout()
        ip_btn_row.addStretch()
        ip_btn_row.addWidget(self._view_original_btn)
        ip_layout.addWidget(self._image_label, 1)
        ip_layout.addLayout(ip_btn_row)

        self._pdf_preview = QWidget()
        pdf_layout = QVBoxLayout(self._pdf_preview)
        pdf_layout.setContentsMargins(_gap, _gap, _gap, _gap)
        pdf_layout.setSpacing(4)

        self._pdf_scroll = QScrollArea()
        self._pdf_scroll.setWidgetResizable(True)
        self._pdf_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {_cir}px;
                background-color: {COLORS.BG_PRIMARY};
            }}
        """ + scrollbar_style())

        self._pdf_pages_container = QWidget()
        self._pdf_pages_layout = QVBoxLayout(self._pdf_pages_container)
        self._pdf_pages_layout.setContentsMargins(8, 8, 8, 8)
        self._pdf_pages_layout.setSpacing(8)
        self._pdf_pages_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pdf_pages_container.setStyleSheet("QWidget { background: transparent; }")
        self._pdf_scroll.setWidget(self._pdf_pages_container)

        self._pdf_load_more_btn = QPushButton("加载更多页面")
        self._pdf_load_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pdf_load_more_btn.setStyleSheet(button_small_primary())
        self._pdf_load_more_btn.setVisible(False)
        self._pdf_load_more_btn.clicked.connect(self._on_pdf_load_more)

        pdf_btn_row = QHBoxLayout()
        pdf_btn_row.addStretch()
        pdf_btn_row.addWidget(self._pdf_load_more_btn)

        pdf_layout.addWidget(self._pdf_scroll, 1)
        pdf_layout.addLayout(pdf_btn_row)

        self._excel_preview = QWidget()
        excel_layout = QVBoxLayout(self._excel_preview)
        excel_layout.setContentsMargins(_gap, _gap, _gap, _gap)
        excel_layout.setSpacing(4)

        self._excel_render_scroll = QScrollArea()
        self._excel_render_scroll.setWidgetResizable(True)
        self._excel_render_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._excel_render_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {_cir}px;
                background-color: {COLORS.BG_PRIMARY};
            }}
        """ + scrollbar_style())

        self._excel_render_container = QWidget()
        self._excel_render_layout = QVBoxLayout(self._excel_render_container)
        self._excel_render_layout.setContentsMargins(4, 4, 4, 4)
        self._excel_render_layout.setSpacing(8)
        self._excel_render_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._excel_render_container.setStyleSheet("QWidget { background: transparent; }")
        self._excel_render_scroll.setWidget(self._excel_render_container)
        self._excel_render_scroll.setMinimumHeight(120)

        self._excel_text_label = QLabel("文本预览")
        self._excel_text_label.setStyleSheet(label_caption_style())

        self._excel_text_edit = QTextEdit()
        self._excel_text_edit.setReadOnly(True)
        self._excel_text_edit.setMaximumHeight(200)
        self._excel_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS.BG_PRIMARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {_cir}px;
                padding: 8px 12px;
                color: {COLORS.TEXT_TERTIARY};
                font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
                font-size: {FONT.MICRO_PT - 1}px;
            }}
        """)
        self._excel_text_edit.setFrameStyle(QTextEdit.Shape.NoFrame)

        excel_layout.addWidget(self._excel_render_scroll, 1)
        excel_layout.addWidget(self._excel_text_label)
        excel_layout.addWidget(self._excel_text_edit)

        self._media_preview = QWidget()
        mp_layout = QVBoxLayout(self._media_preview)
        mp_layout.setContentsMargins(_gap, _gap, _gap, _gap)
        mp_layout.setSpacing(0)

        if HAS_MULTIMEDIA:
            self._video_widget = QVideoWidget()
            self._video_widget.setStyleSheet(f"""
                QVideoWidget {{
                    border: 1px solid {COLORS.BORDER_DEFAULT};
                    border-radius: {_cir}px;
                    background-color: #000000;
                }}
            """)
            self._video_widget.setMinimumHeight(200)
        else:
            self._video_widget = None

        self._media_info_label = QLabel("")
        self._media_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._media_info_label.setStyleSheet(f"""
            color: {COLORS.TEXT_TERTIARY};
            font-size: {FONT.CAPTION_PT}px;
            border: none; background: transparent;
            padding: 8px;
        """)

        if self._video_widget:
            mp_layout.addWidget(self._video_widget, 1)
        mp_layout.addWidget(self._media_info_label)

        self._unsupported_preview = QWidget()
        us_layout = QVBoxLayout(self._unsupported_preview)
        us_layout.setContentsMargins(_gap, _gap, _gap, _gap)
        us_layout.setSpacing(0)

        us_box = QWidget()
        us_box.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_SECONDARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {_cir}px;
            }}
        """)
        us_box_layout = QVBoxLayout(us_box)
        us_box_layout.setContentsMargins(24, 24, 24, 24)
        us_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        us_box_layout.setSpacing(8)

        self._unsupported_icon = QLabel()
        self._unsupported_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._unsupported_icon.setStyleSheet("border: none; background: transparent;")

        self._unsupported_text = QLabel("此文件类型暂不支持预览")
        self._unsupported_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._unsupported_text.setStyleSheet(f"""
            color: {COLORS.TEXT_PLACEHOLDER};
            font-size: {FONT.BODY_PT}px;
            border: none; background: transparent;
        """)

        self._unsupported_hint = QLabel("")
        self._unsupported_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._unsupported_hint.setWordWrap(True)
        self._unsupported_hint.setStyleSheet(f"""
            color: {COLORS.TEXT_TERTIARY};
            font-size: {FONT.CAPTION_PT}px;
            border: none; background: transparent;
        """)

        self._force_preview_btn = QPushButton("仍然预览")
        self._force_preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._force_preview_btn.setStyleSheet(button_small_primary())
        self._force_preview_btn.setVisible(False)
        self._force_preview_btn.clicked.connect(self._on_force_preview)

        us_box_layout.addWidget(self._unsupported_icon)
        us_box_layout.addWidget(self._unsupported_text)
        us_box_layout.addWidget(self._unsupported_hint)
        us_box_layout.addWidget(self._force_preview_btn)

        us_layout.addStretch()
        us_layout.addWidget(us_box, 1)
        us_layout.addStretch()

        self._folder_preview = QWidget()
        fp_layout = QVBoxLayout(self._folder_preview)
        fp_layout.setContentsMargins(12, 8, 12, 12)
        fp_layout.setSpacing(6)

        self._folder_stats_label = QLabel("")
        self._folder_stats_label.setStyleSheet(label_caption_style())

        self._folder_scroll = QScrollArea()
        self._folder_scroll.setWidgetResizable(True)
        self._folder_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._folder_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._folder_scroll.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {COLORS.BORDER_DEFAULT}; border-radius: {_cir}px; background-color: {COLORS.BG_SECONDARY}; }}" + scrollbar_style()
        )

        self._folder_list_container = QWidget()
        self._folder_list_layout = QVBoxLayout(self._folder_list_container)
        self._folder_list_layout.setContentsMargins(4, 4, 4, 4)
        self._folder_list_layout.setSpacing(0)
        self._folder_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._folder_list_container.setStyleSheet("QWidget { background: transparent; }")
        self._folder_scroll.setWidget(self._folder_list_container)

        fp_layout.addWidget(self._folder_stats_label)
        fp_layout.addWidget(self._folder_scroll, 1)

        self._loading_preview = QWidget()
        ll_layout = QVBoxLayout(self._loading_preview)
        ll_layout.setContentsMargins(_gap, _gap, _gap, _gap)
        ll_layout.setSpacing(0)
        ll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ll_box = QWidget()
        ll_box.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BG_SECONDARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {_cir}px;
            }}
        """)
        ll_box_layout = QVBoxLayout(ll_box)
        ll_box_layout.setContentsMargins(24, 24, 24, 24)
        ll_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ll_box_layout.setSpacing(12)

        self._loading_spinner = _PreviewLoadingSpinner(ll_box)
        self._loading_text = QLabel("正在加载预览...")
        self._loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_text.setStyleSheet(f"""
            color: {COLORS.TEXT_TERTIARY};
            font-size: {FONT.CAPTION_PT}px;
            border: none; background: transparent;
        """)

        ll_box_layout.addWidget(self._loading_spinner, 0, Qt.AlignmentFlag.AlignCenter)
        ll_box_layout.addWidget(self._loading_text)

        ll_layout.addStretch()
        ll_layout.addWidget(ll_box, 0)
        ll_layout.addStretch()

        self._ppt_preview = QWidget()
        ppt_layout = QVBoxLayout(self._ppt_preview)
        ppt_layout.setContentsMargins(_gap, _gap, _gap, _gap)
        ppt_layout.setSpacing(4)

        self._ppt_render_scroll = QScrollArea()
        self._ppt_render_scroll.setWidgetResizable(True)
        self._ppt_render_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._ppt_render_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {_cir}px;
                background-color: {COLORS.BG_PRIMARY};
            }}
        """ + scrollbar_style())

        self._ppt_render_container = QWidget()
        self._ppt_render_layout = QVBoxLayout(self._ppt_render_container)
        self._ppt_render_layout.setContentsMargins(4, 4, 4, 4)
        self._ppt_render_layout.setSpacing(8)
        self._ppt_render_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._ppt_render_container.setStyleSheet("QWidget { background: transparent; }")
        self._ppt_render_scroll.setWidget(self._ppt_render_container)
        self._ppt_render_scroll.setMinimumHeight(120)

        self._ppt_text_label = QLabel("文本预览")
        self._ppt_text_label.setStyleSheet(label_caption_style())

        self._ppt_text_edit = QTextEdit()
        self._ppt_text_edit.setReadOnly(True)
        self._ppt_text_edit.setMaximumHeight(200)
        self._ppt_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS.BG_PRIMARY};
                border: 1px solid {COLORS.BORDER_DEFAULT};
                border-radius: {_cir}px;
                padding: 8px 12px;
                color: {COLORS.TEXT_TERTIARY};
                font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
                font-size: {FONT.MICRO_PT - 1}px;
            }}
        """)
        self._ppt_text_edit.setFrameStyle(QTextEdit.Shape.NoFrame)

        ppt_layout.addWidget(self._ppt_render_scroll, 1)
        ppt_layout.addWidget(self._ppt_text_label)
        ppt_layout.addWidget(self._ppt_text_edit)

        self._content_stack.addWidget(self._text_preview)
        self._content_stack.addWidget(self._image_preview)
        self._content_stack.addWidget(self._pdf_preview)
        self._content_stack.addWidget(self._excel_preview)
        self._content_stack.addWidget(self._ppt_preview)
        self._content_stack.addWidget(self._media_preview)
        self._content_stack.addWidget(self._unsupported_preview)
        self._content_stack.addWidget(self._folder_preview)
        self._content_stack.addWidget(self._loading_preview)

        layout.addWidget(self.header_widget)
        layout.addWidget(self.empty_placeholder, 1)
        layout.addWidget(self._content_stack, 1)

        self.setLayout(layout)
        self.setStyleSheet(f"""
            PreviewPanel {{
                background-color: {COLORS.BG_PRIMARY};
                border-bottom-left-radius: {_inner_radius}px;
                border-bottom-right-radius: {_inner_radius}px;
            }}
        """)

    def set_result(self, result):
        self._cancel_workers()
        self._stop_media()
        self._current_result = result
        self._full_content = None
        self._showing_truncated = False
        self._current_file_item = None
        self._highlighter = None
        self._md_source_mode = False
        self._pdf_doc = None
        self._pdf_total_pages = 0
        self._pdf_pages_loaded = 0
        if result is None:
            self._show_empty()
            return
        file_item = result.file_item
        if file_item.is_directory:
            self._show_folder_preview(file_item)
        else:
            self._show_file_preview(file_item)

    def _show_empty(self):
        self.title_label.setText("预览")
        self.icon_label.clear()
        self._file_info_label.setText("")
        self.empty_placeholder.setVisible(True)
        self._content_stack.setVisible(False)

    def _hide_all_content(self):
        self.empty_placeholder.setVisible(False)
        self._content_stack.setVisible(True)
        self._show_more_btn.setVisible(False)
        self._md_toggle_btn.setVisible(False)
        self._view_original_btn.setVisible(False)
        self._force_preview_btn.setVisible(False)
        self._pdf_load_more_btn.setVisible(False)
        self._loading_spinner.stop()

    def _show_file_preview(self, file_item, force=False):
        self._hide_all_content()
        self._current_file_item = file_item
        self.title_label.setText(file_item.name)
        self._file_info_label.setText(file_item.size_display)

        ext = file_item.extension.lower()
        icon_name = FILE_ICON_MAP.get(ext, 'doctype/File.svg')
        self.icon_label.setPixmap(QIcon(f"icons/{icon_name}").pixmap(QSize(20, 20)))

        if ext in MARKDOWN_EXTS:
            self._show_markdown_content(file_item, force)
        elif ext in PREVIEWABLE_TEXT_EXTS:
            self._show_text_content(file_item, force)
        elif ext in PREVIEWABLE_IMAGE_EXTS:
            self._show_image_content(file_item)
        elif ext == '.pdf':
            self._show_pdf_content(file_item, force)
        elif ext in {'.docx', '.doc'}:
            self._show_word_content(file_item, force)
        elif ext in {'.xlsx', '.xls'}:
            self._show_excel_content(file_item, force)
        elif ext in {'.pptx', '.ppt'}:
            self._show_ppt_content(file_item, force)
        elif ext in VIDEO_EXTENSIONS:
            self._show_video_content(file_item, force)
        elif ext in AUDIO_EXTENSIONS:
            self._show_audio_content(file_item, force)
        elif ext in ARCHIVE_EXTENSIONS:
            self._show_archive_content(file_item)
        else:
            self._show_unsupported(file_item, "此文件类型暂不支持预览\n可双击文件使用默认程序打开查看")

    def _check_file_size(self, file_item, max_mb, force, hint_suffix=""):
        try:
            file_size = os.path.getsize(file_item.path)
        except OSError:
            self._show_unsupported(file_item, "无法读取文件")
            return None
        if file_size > max_mb * 1024 * 1024 and not force:
            self._show_oversized(file_item, max_mb, hint_suffix)
            return None
        return file_size

    def _show_oversized(self, file_item, max_mb, hint_suffix=""):
        self._unsupported_icon.setPixmap(
            QIcon(f"icons/{FILE_ICON_MAP.get(file_item.extension.lower(), 'doctype/File.svg')}").pixmap(QSize(48, 48))
        )
        self._unsupported_text.setText("文件过大")
        self._unsupported_hint.setText(
            f"文件大小 {file_item.size_display}，超过预览限制 {max_mb}MB{hint_suffix}\n可点击下方按钮尝试预览"
        )
        self._force_preview_btn.setVisible(True)
        self._content_stack.setCurrentWidget(self._unsupported_preview)

    def _show_text_content(self, file_item, force=False):
        file_size = self._check_file_size(file_item, MAX_TEXT_PREVIEW_SIZE_MB, force)
        if file_size is None and not force:
            return

        from utils.encoding import read_text_file
        max_mb = MAX_TEXT_PREVIEW_SIZE_MB if not force else 50
        content = read_text_file(file_item.path, max_size_mb=max_mb)
        if content is None:
            self._show_unsupported(file_item, "无法读取文件内容")
            return

        self._full_content = content
        lines = content.splitlines()
        truncated = len(lines) > MAX_PREVIEW_LINES
        display_lines = lines[:MAX_PREVIEW_LINES] if truncated else lines
        self._showing_truncated = truncated

        display_content = '\n'.join(display_lines)
        self._text_edit.setPlainText(display_content)

        ext = file_item.extension.lower()
        self._highlighter = _create_highlighter(self._text_edit.document(), ext)

        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self._text_edit.setTextCursor(cursor)

        self._show_more_btn.setVisible(truncated)
        self._md_toggle_btn.setVisible(False)
        self._md_browser.setVisible(False)
        self._text_edit.setVisible(True)

        if truncated:
            self._file_info_label.setText(
                f"{file_item.size_display} · 显示前 {MAX_PREVIEW_LINES} 行（共 {len(lines)} 行）"
            )
        else:
            self._file_info_label.setText(f"{file_item.size_display} · {len(lines)} 行")

        self._content_stack.setCurrentWidget(self._text_preview)

    def _show_markdown_content(self, file_item, force=False):
        file_size = self._check_file_size(file_item, MAX_TEXT_PREVIEW_SIZE_MB, force)
        if file_size is None and not force:
            return

        from utils.encoding import read_text_file
        max_mb = MAX_TEXT_PREVIEW_SIZE_MB if not force else 50
        content = read_text_file(file_item.path, max_size_mb=max_mb)
        if content is None:
            self._show_unsupported(file_item, "无法读取文件内容")
            return

        self._full_content = content
        lines = content.splitlines()
        truncated = len(lines) > MAX_PREVIEW_LINES
        self._showing_truncated = truncated

        self._md_source_mode = False
        self._md_toggle_btn.setVisible(True)
        self._md_toggle_btn.setText("源码模式")
        self._show_more_btn.setVisible(truncated)

        self._render_markdown(content, truncated)

        if truncated:
            self._file_info_label.setText(
                f"{file_item.size_display} · 预览模式 · 显示前 {MAX_PREVIEW_LINES} 行"
            )
        else:
            self._file_info_label.setText(f"{file_item.size_display} · 预览模式")

        self._content_stack.setCurrentWidget(self._text_preview)

    def _render_markdown(self, content, truncated):
        lines = content.splitlines()
        display_lines = lines[:MAX_PREVIEW_LINES] if truncated else lines
        display_content = '\n'.join(display_lines)

        if self._md_source_mode:
            self._text_edit.setPlainText(display_content)
            self._text_edit.setVisible(True)
            self._md_browser.setVisible(False)
            self._highlighter = _create_highlighter(self._text_edit.document(), '.md')
        else:
            import markdown
            html = markdown.markdown(display_content, extensions=['tables', 'fenced_code', 'codehilite'])
            styled_html = f"""
            <style>
                body {{ font-family: "Microsoft YaHei", sans-serif; color: {COLORS.TEXT_SECONDARY};
                       font-size: {FONT.CAPTION_PT}px; line-height: 1.6; }}
                h1, h2, h3, h4, h5, h6 {{ color: {COLORS.TEXT_PRIMARY}; margin-top: 12px; margin-bottom: 6px; }}
                h1 {{ font-size: {FONT.DISPLAY_PT}px; }} h2 {{ font-size: {FONT.TITLE_PT}px; }}
                code {{ background-color: {COLORS.BG_TERTIARY}; padding: 2px 6px; border-radius: 3px;
                        font-family: "Cascadia Code", "Consolas", monospace; font-size: {FONT.MICRO_PT}px; }}
                pre {{ background-color: {COLORS.BG_TERTIARY}; padding: 12px; border-radius: 6px;
                       overflow-x: auto; }}
                pre code {{ background: transparent; padding: 0; }}
                blockquote {{ border-left: 3px solid {COLORS.BRAND}; padding-left: 12px;
                             color: {COLORS.TEXT_TERTIARY}; margin: 8px 0; }}
                a {{ color: {COLORS.BRAND}; text-decoration: none; }}
                table {{ border-collapse: collapse; margin: 8px 0; }}
                th, td {{ border: 1px solid {COLORS.BORDER_DEFAULT}; padding: 6px 12px; }}
                th {{ background-color: {COLORS.BG_TERTIARY}; }}
                ul, ol {{ padding-left: 20px; }}
                img {{ max-width: 100%; }}
            </style>
            {html}
            """
            self._md_browser.setHtml(styled_html)
            self._md_browser.setVisible(True)
            self._text_edit.setVisible(False)

    def _show_image_content(self, file_item):
        try:
            file_size = os.path.getsize(file_item.path)
        except OSError:
            self._show_unsupported(file_item, "无法读取文件")
            return

        if file_size > 50 * 1024 * 1024:
            self._show_oversized(file_item, 50)
            return

        pixmap = QPixmap()
        try:
            from PySide6.QtGui import QImageReader
            reader = QImageReader(file_item.path)
            reader.setAllocationLimit(128)
            img = reader.read()
            if img is not None and not img.isNull():
                pixmap = QPixmap.fromImage(img)
            else:
                pixmap = QPixmap(file_item.path)
        except Exception:
            pixmap = QPixmap(file_item.path)

        if pixmap.isNull():
            self._show_unsupported(file_item, "无法加载图片\n可能是图片过大或格式不受支持")
            return

        original_pixmap = pixmap
        is_scaled = False
        if pixmap.width() * pixmap.height() > MAX_IMAGE_PREVIEW_PIXELS:
            self._image_label._original_pixmap = pixmap
            scaled = pixmap.scaled(
                1920, 1080,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            if isinstance(scaled, QPixmap) and not scaled.isNull():
                pixmap = scaled
                is_scaled = True
            else:
                is_scaled = True

        self._fit_image_to_label(pixmap)
        self._view_original_btn.setVisible(is_scaled)

        if is_scaled:
            self._file_info_label.setText(
                f"{file_item.size_display} · {original_pixmap.width()}×{original_pixmap.height()} · 已缩放预览"
            )
        else:
            self._file_info_label.setText(
                f"{file_item.size_display} · {pixmap.width()}×{pixmap.height()}"
            )

        self._content_stack.setCurrentWidget(self._image_preview)

    def _fit_image_to_label(self, pixmap):
        if not isinstance(pixmap, QPixmap) or pixmap.isNull():
            return
        label_size = self._image_label.size()
        if label_size.width() < 10 or label_size.height() < 10:
            self._image_label.setPixmap(pixmap)
            return
        scaled = pixmap.scaled(
            label_size.width() - 4, label_size.height() - 4,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        if isinstance(scaled, QPixmap) and not scaled.isNull():
            self._image_label.setPixmap(scaled)
        else:
            self._image_label.setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if (self._content_stack.currentWidget() == self._image_preview
                and self._current_file_item
                and self._current_file_item.extension.lower() in PREVIEWABLE_IMAGE_EXTS):
            if hasattr(self._image_label, '_original_pixmap'):
                self._fit_image_to_label(self._image_label._original_pixmap)
            elif self._image_label.pixmap() and not self._image_label.pixmap().isNull():
                self._fit_image_to_label(self._image_label.pixmap())

    def _show_pdf_content(self, file_item, force=False):
        try:
            import fitz
        except ImportError:
            self._show_unsupported(file_item, "PDF 预览需要安装 PyMuPDF 库\n请运行: pip install PyMuPDF")
            return

        file_size = self._check_file_size(file_item, MAX_DOC_PREVIEW_SIZE_MB, force)
        if file_size is None and not force:
            return

        try:
            doc = fitz.open(file_item.path)
            self._pdf_total_pages = len(doc)
            doc.close()
        except Exception as e:
            logger.warning(f"PDF open failed: {file_item.path}, {type(e).__name__}")
            self._show_unsupported(file_item, "无法解析此 PDF 文件")
            return

        if self._pdf_total_pages == 0:
            self._show_unsupported(file_item, "PDF 文件为空")
            return

        while self._pdf_pages_layout.count():
            child = self._pdf_pages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._pdf_pages_loaded = 0
        self._pdf_load_more_btn.setVisible(False)

        info = f"{file_item.size_display} · 共 {self._pdf_total_pages} 页"
        self._file_info_label.setText(info)
        self._content_stack.setCurrentWidget(self._pdf_preview)

        self._loading_text.setText("正在渲染 PDF...")
        self._loading_spinner.start()
        self._content_stack.setCurrentWidget(self._loading_preview)

        self._start_pdf_render(file_item.path, 0, DEFAULT_PDF_PAGES)

    def _start_pdf_render(self, file_path, start_page, count):
        if self._pdf_render_worker and self._pdf_render_worker.isRunning():
            self._pdf_render_worker.cancel()
            self._pdf_render_worker.wait(2000)

        self._pdf_render_worker = _PdfRenderWorker(file_path, count, start_page)
        self._pdf_render_worker.page_rendered.connect(self._on_pdf_page_rendered)
        self._pdf_render_worker.render_finished.connect(self._on_pdf_render_finished)
        self._pdf_render_worker.start()

    def _on_pdf_page_rendered(self, page_idx, pixmap):
        if not self._current_file_item:
            return
        scroll_width = self._pdf_scroll.viewport().width() - 24
        if scroll_width > 100 and pixmap.width() > scroll_width:
            scaled = pixmap.scaledToWidth(scroll_width, Qt.TransformationMode.SmoothTransformation)
            pixmap = scaled

        page_label = QLabel()
        page_label.setPixmap(pixmap)
        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_label.setStyleSheet(f"""
            border: 1px solid {COLORS.BORDER_DEFAULT};
            border-radius: {RADIUS.SMALL}px;
            background-color: white;
        """)
        self._pdf_pages_layout.addWidget(page_label)
        self._pdf_pages_loaded = page_idx + 1

    def _on_pdf_render_finished(self, total_pages):
        self._loading_spinner.stop()
        if self._current_file_item:
            self._content_stack.setCurrentWidget(self._pdf_preview)
        if self._pdf_pages_loaded < self._pdf_total_pages:
            self._pdf_load_more_btn.setVisible(True)
            self._pdf_load_more_btn.setEnabled(True)
            self._pdf_load_more_btn.setText(
                f"加载更多页面（剩余 {self._pdf_total_pages - self._pdf_pages_loaded} 页）"
            )
        else:
            self._pdf_load_more_btn.setVisible(False)

    def _on_pdf_load_more(self):
        if not self._current_file_item:
            return
        self._pdf_load_more_btn.setText("正在加载...")
        self._pdf_load_more_btn.setEnabled(False)
        self._start_pdf_render(self._current_file_item.path, self._pdf_pages_loaded, 10)

    def _show_excel_content(self, file_item, force=False):
        file_size = self._check_file_size(file_item, MAX_DOC_PREVIEW_SIZE_MB, force)
        if file_size is None and not force:
            return

        while self._excel_render_layout.count():
            child = self._excel_render_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._excel_text_edit.clear()
        self._excel_text_label.setText("文本预览")

        self._loading_text.setText("正在渲染 Excel...")
        self._loading_spinner.start()
        self._content_stack.setCurrentWidget(self._loading_preview)

        if self._excel_render_worker and self._excel_render_worker.isRunning():
            self._excel_render_worker.cancel()
            self._excel_render_worker.wait(2000)

        self._excel_render_worker = _ExcelRenderWorker(file_item.path)
        self._excel_render_worker.sheet_rendered.connect(self._on_excel_sheet_rendered)
        self._excel_render_worker.render_finished.connect(self._on_excel_render_finished)
        self._excel_render_worker.start()

        try:
            from openpyxl import load_workbook
            wb = load_workbook(file_item.path, read_only=True, data_only=True)
            all_text = []
            total_chars = 0
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                all_text.append(f"=== {sheet_name} ===")
                for row in ws.iter_rows(values_only=True):
                    cells = [str(c) if c is not None else '' for c in row]
                    line = '\t'.join(cells)
                    all_text.append(line)
                    total_chars += len(line)
                    if total_chars > MAX_DOC_CHARS and not force:
                        all_text.append("... 已截断")
                        break
                if total_chars > MAX_DOC_CHARS and not force:
                    break
            wb.close()
            self._excel_text_edit.setPlainText('\n'.join(all_text))
            cursor = self._excel_text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._excel_text_edit.setTextCursor(cursor)
        except Exception as e:
            logger.warning(f"Excel text preview failed: {file_item.path}, {type(e).__name__}")
            self._excel_text_edit.setPlainText("无法读取文本内容")

        self._file_info_label.setText(f"{file_item.size_display} · Excel 文档")
        self._content_stack.setCurrentWidget(self._excel_preview)

    def _on_excel_sheet_rendered(self, idx, pixmap, sheet_name):
        if not self._current_file_item:
            return
        scroll_width = self._excel_render_scroll.viewport().width() - 24
        if scroll_width > 100 and pixmap.width() > scroll_width:
            scaled = pixmap.scaledToWidth(scroll_width, Qt.TransformationMode.SmoothTransformation)
            pixmap = scaled

        sheet_label = QLabel()
        sheet_label.setPixmap(pixmap)
        sheet_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        sheet_label.setStyleSheet("border: none; background: transparent;")
        self._excel_render_layout.addWidget(sheet_label)

    def _on_excel_render_finished(self):
        self._loading_spinner.stop()
        if self._current_file_item:
            self._content_stack.setCurrentWidget(self._excel_preview)

    def _show_word_content(self, file_item, force=False):
        file_size = self._check_file_size(file_item, MAX_DOC_PREVIEW_SIZE_MB, force)
        if file_size is None and not force:
            return

        try:
            from docx import Document
            doc = Document(file_item.path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = '\n'.join(paragraphs)

            if len(content) > MAX_DOC_CHARS and not force:
                content = content[:MAX_DOC_CHARS]
                content += f"\n\n... 已截断，共 {len(''.join(p.text for p in doc.paragraphs))} 字符"

            self._text_edit.setPlainText(content)
            self._show_more_btn.setVisible(False)
            self._md_toggle_btn.setVisible(False)
            self._md_browser.setVisible(False)
            self._text_edit.setVisible(True)

            cursor = self._text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._text_edit.setTextCursor(cursor)

            self._file_info_label.setText(f"{file_item.size_display} · Word 文档 · 纯文本预览")
            self._content_stack.setCurrentWidget(self._text_preview)
        except Exception as e:
            logger.warning(f"Word 预览失败: {file_item.path}, {type(e).__name__}")
            self._show_unsupported(file_item, "无法解析此 Word 文件\n可能是不受支持的格式")

    def _show_ppt_content(self, file_item, force=False):
        file_size = self._check_file_size(file_item, MAX_DOC_PREVIEW_SIZE_MB, force)
        if file_size is None and not force:
            return

        while self._ppt_render_layout.count():
            child = self._ppt_render_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._ppt_text_edit.clear()
        self._ppt_text_label.setText("文本预览")

        self._loading_text.setText("正在渲染 PPT...")
        self._loading_spinner.start()
        self._content_stack.setCurrentWidget(self._loading_preview)

        if self._ppt_render_worker and self._ppt_render_worker.isRunning():
            self._ppt_render_worker.cancel()
            self._ppt_render_worker.wait(2000)

        self._ppt_render_worker = _PptRenderWorker(file_item.path)
        self._ppt_render_worker.slide_rendered.connect(self._on_ppt_slide_rendered)
        self._ppt_render_worker.render_finished.connect(self._on_ppt_render_finished)
        self._ppt_render_worker.start()

        try:
            from pptx import Presentation
            prs = Presentation(file_item.path)
            all_text = []
            total_chars = 0
            slide_count = len(prs.slides)

            for i, slide in enumerate(prs.slides):
                all_text.append(f"=== 第 {i + 1} 页 ===")
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for para in shape.text_frame.paragraphs:
                            text = para.text.strip()
                            if text:
                                all_text.append(text)
                                total_chars += len(text)
                if total_chars > MAX_DOC_CHARS and not force:
                    all_text.append("... 已截断")
                    break

            content = '\n'.join(all_text)
            self._ppt_text_edit.setPlainText(content)
            cursor = self._ppt_text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._ppt_text_edit.setTextCursor(cursor)

            self._file_info_label.setText(f"{file_item.size_display} · PPT 文档 · 共 {slide_count} 页")
        except Exception as e:
            logger.warning(f"PPT text preview failed: {file_item.path}, {type(e).__name__}")
            self._ppt_text_edit.setPlainText("无法读取文本内容")

        self._content_stack.setCurrentWidget(self._ppt_preview)

    def _on_ppt_slide_rendered(self, idx, pixmap, slide_name):
        if not self._current_file_item:
            return
        scroll_width = self._ppt_render_scroll.viewport().width() - 24
        if scroll_width > 100 and pixmap.width() > scroll_width:
            scaled = pixmap.scaledToWidth(scroll_width, Qt.TransformationMode.SmoothTransformation)
            if isinstance(scaled, QPixmap) and not scaled.isNull():
                pixmap = scaled

        slide_label = QLabel()
        slide_label.setPixmap(pixmap)
        slide_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        slide_label.setStyleSheet(f"""
            border: 1px solid {COLORS.BORDER_DEFAULT};
            border-radius: {RADIUS.SMALL}px;
            background-color: white;
        """)
        self._ppt_render_layout.addWidget(slide_label)

    def _on_ppt_render_finished(self, slide_count):
        self._loading_spinner.stop()
        if self._current_file_item:
            self._content_stack.setCurrentWidget(self._ppt_preview)

    def _show_video_content(self, file_item, force=False):
        if not HAS_MULTIMEDIA:
            self._show_unsupported(file_item, "视频预览需要 PySide6 多媒体组件\n可双击使用默认播放器打开")
            return

        file_size = self._check_file_size(file_item, MAX_MEDIA_PREVIEW_SIZE_MB, force)
        if file_size is None and not force:
            return

        try:
            self._media_player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._media_player.setAudioOutput(self._audio_output)
            if self._video_widget:
                self._video_widget.setVisible(True)
                self._media_player.setVideoOutput(self._video_widget)

            from PySide6.QtCore import QUrl
            self._media_player.setSource(QUrl.fromLocalFile(file_item.path))
            self._media_player.play()

            self._media_info_label.setText(f"{file_item.size_display} · 视频预览")
            self._file_info_label.setText(f"{file_item.size_display} · 视频文件")
            self._content_stack.setCurrentWidget(self._media_preview)
        except Exception as e:
            logger.warning(f"视频预览失败: {file_item.path}, {type(e).__name__}")
            self._show_unsupported(file_item, "无法播放此视频文件\n可双击使用默认播放器打开")

    def _show_audio_content(self, file_item, force=False):
        if not HAS_MULTIMEDIA:
            self._show_unsupported(file_item, "音频预览需要 PySide6 多媒体组件\n可双击使用默认播放器打开")
            return

        file_size = self._check_file_size(file_item, MAX_MEDIA_PREVIEW_SIZE_MB, force)
        if file_size is None and not force:
            return

        try:
            self._media_player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._media_player.setAudioOutput(self._audio_output)

            from PySide6.QtCore import QUrl
            self._media_player.setSource(QUrl.fromLocalFile(file_item.path))
            self._media_player.play()

            if self._video_widget:
                self._video_widget.setVisible(False)
            self._media_info_label.setText(f"{file_item.size_display} · 音频播放中...")
            self._file_info_label.setText(f"{file_item.size_display} · 音频文件")
            self._content_stack.setCurrentWidget(self._media_preview)
        except Exception as e:
            logger.warning(f"音频预览失败: {file_item.path}, {type(e).__name__}")
            self._show_unsupported(file_item, "无法播放此音频文件\n可双击使用默认播放器打开")

    def _show_archive_content(self, file_item):
        ext = file_item.extension.lower()
        entries = []
        dir_count = 0
        file_count = 0

        try:
            if ext in {'.zip', '.rar', '.7z'}:
                if ext == '.zip':
                    with zipfile.ZipFile(file_item.path, 'r') as zf:
                        try:
                            zf.testzip()
                        except RuntimeError:
                            self._show_unsupported(file_item, "此压缩包有密码保护\n无法预览加密的压缩包")
                            return
                        for info in zf.infolist():
                            name = info.filename
                            if name.endswith('/'):
                                dir_count += 1
                                entries.append((name.rstrip('/'), True))
                            else:
                                file_count += 1
                                entries.append((os.path.basename(name), False))
                elif ext in {'.rar', '.7z'}:
                    self._show_unsupported(file_item, f".{ext} 格式暂不支持预览\n可双击使用解压软件打开")
                    return
            elif ext in {'.tar', '.gz', '.bz2'}:
                try:
                    with tarfile.open(file_item.path, 'r:*') as tf:
                        for member in tf.getmembers():
                            if member.isdir():
                                dir_count += 1
                                entries.append((os.path.basename(member.name) or member.name, True))
                            else:
                                file_count += 1
                                entries.append((os.path.basename(member.name), False))
                except tarfile.TarError:
                    self._show_unsupported(file_item, "无法解析此压缩包")
                    return
        except Exception as e:
            logger.warning(f"压缩包预览失败: {file_item.path}, {type(e).__name__}")
            self._show_unsupported(file_item, "无法读取压缩包内容")
            return

        self._show_archive_list(file_item, entries, dir_count, file_count)

    def _show_archive_list(self, file_item, entries, dir_count, file_count):
        self.title_label.setText(file_item.name)
        self.icon_label.setPixmap(
            QIcon(f"icons/{FILE_ICON_MAP.get(file_item.extension.lower(), 'doctype/Zip.svg')}").pixmap(QSize(20, 20))
        )

        while self._folder_list_layout.count():
            child = self._folder_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        entries.sort(key=lambda e: (not e[1], e[0].lower()))

        stats_parts = []
        if dir_count > 0:
            stats_parts.append(f"{dir_count} 个文件夹")
        if file_count > 0:
            stats_parts.append(f"{file_count} 个文件")
        stats_text = " · ".join(stats_parts) if stats_parts else "空压缩包"
        self._folder_stats_label.setText(f"压缩包内容 · {stats_text}")
        self._folder_stats_label.setStyleSheet(label_caption_style())

        max_entries = 50
        display_entries = entries[:max_entries]
        for name, is_dir in display_entries:
            row = _FolderEntryRow(name, is_dir)
            self._folder_list_layout.addWidget(row)

        if len(entries) > max_entries:
            more_label = QLabel(f"  ... 还有 {len(entries) - max_entries} 项未显示")
            more_label.setStyleSheet(f"""
                color: {COLORS.TEXT_PLACEHOLDER}; font-size: {FONT.MICRO_PT}px;
                border: none; background: transparent; padding: 4px 6px;
            """)
            self._folder_list_layout.addWidget(more_label)

        if not entries:
            empty_label = QLabel("压缩包为空")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                color: {COLORS.TEXT_PLACEHOLDER}; font-size: {FONT.CAPTION_PT}px;
                border: none; background: transparent; padding: 16px;
            """)
            self._folder_list_layout.addWidget(empty_label)

        self._file_info_label.setText(file_item.size_display)
        self._content_stack.setCurrentWidget(self._folder_preview)

    def _show_unsupported(self, file_item, hint_text=""):
        self._unsupported_icon.setPixmap(
            QIcon(f"icons/{FILE_ICON_MAP.get(file_item.extension.lower(), 'doctype/File.svg')}").pixmap(QSize(48, 48))
        )
        self._unsupported_hint.setText(hint_text)
        self._force_preview_btn.setVisible(False)
        self._content_stack.setCurrentWidget(self._unsupported_preview)

    def _show_folder_preview(self, file_item):
        self._hide_all_content()
        self.title_label.setText(file_item.name)
        self._file_info_label.setText(file_item.item_count_display)
        self.icon_label.setPixmap(QIcon("icons/doctype/Folder.svg").pixmap(QSize(20, 20)))

        while self._folder_list_layout.count():
            child = self._folder_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        dir_path = file_item.path
        dir_count = 0
        file_count = 0
        entries = []

        try:
            for entry in os.scandir(dir_path):
                try:
                    if entry.is_dir(follow_symlinks=False):
                        dir_count += 1
                        entries.append((entry.name, True))
                    elif entry.is_file(follow_symlinks=False):
                        file_count += 1
                        entries.append((entry.name, False))
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            self._folder_stats_label.setText("无法访问此目录")
            self._folder_stats_label.setStyleSheet(f"color: {COLORS.TEXT_TERTIARY}; font-size: {FONT.CAPTION_PT}px; border: none; background: transparent;")
            self._content_stack.setCurrentWidget(self._folder_preview)
            return

        entries.sort(key=lambda e: (not e[1], e[0].lower()))

        stats_parts = []
        if dir_count > 0:
            stats_parts.append(f"{dir_count} 个文件夹")
        if file_count > 0:
            stats_parts.append(f"{file_count} 个文件")
        stats_text = " · ".join(stats_parts) if stats_parts else "空文件夹"
        self._folder_stats_label.setText(stats_text)
        self._folder_stats_label.setStyleSheet(label_caption_style())

        max_entries = 50
        display_entries = entries[:max_entries]
        for name, is_dir in display_entries:
            row = _FolderEntryRow(name, is_dir)
            self._folder_list_layout.addWidget(row)

        if len(entries) > max_entries:
            more_label = QLabel(f"  ... 还有 {len(entries) - max_entries} 项未显示")
            more_label.setStyleSheet(f"""
                color: {COLORS.TEXT_PLACEHOLDER}; font-size: {FONT.MICRO_PT}px;
                border: none; background: transparent; padding: 4px 6px;
            """)
            self._folder_list_layout.addWidget(more_label)

        if not entries:
            empty_label = QLabel("此文件夹为空")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                color: {COLORS.TEXT_PLACEHOLDER}; font-size: {FONT.CAPTION_PT}px;
                border: none; background: transparent; padding: 16px;
            """)
            self._folder_list_layout.addWidget(empty_label)

        self._content_stack.setCurrentWidget(self._folder_preview)

    def _on_show_more(self):
        if self._full_content:
            self._text_edit.setPlainText(self._full_content)
            self._showing_truncated = False
            self._show_more_btn.setVisible(False)
            ext = self._current_file_item.extension.lower() if self._current_file_item else ''
            self._highlighter = _create_highlighter(self._text_edit.document(), ext)
            self._file_info_label.setText(
                f"{self._current_file_item.size_display} · 显示全部内容"
            )

    def _on_toggle_md_mode(self):
        self._md_source_mode = not self._md_source_mode
        self._md_toggle_btn.setText("预览模式" if self._md_source_mode else "源码模式")

        if self._full_content:
            lines = self._full_content.splitlines()
            truncated = len(lines) > MAX_PREVIEW_LINES
            self._render_markdown(self._full_content, truncated)

            if self._md_source_mode:
                self._file_info_label.setText(
                    f"{self._current_file_item.size_display} · 源码模式"
                )
            else:
                self._file_info_label.setText(
                    f"{self._current_file_item.size_display} · 预览模式"
                )

    def _on_view_original_image(self):
        if hasattr(self._image_label, '_original_pixmap'):
            pm = self._image_label._original_pixmap
            if not isinstance(pm, QPixmap) or pm.isNull():
                return
            self._fit_image_to_label(pm)
            self._view_original_btn.setVisible(False)
            self._file_info_label.setText(
                f"{self._current_file_item.size_display} · {pm.width()}×{pm.height()} · 原始尺寸"
            )

    def _on_force_preview(self):
        if self._current_file_item:
            self._show_file_preview(self._current_file_item, force=True)

    def _do_delayed_preview(self):
        if self._pending_file_item:
            self._show_file_preview(self._pending_file_item, self._pending_force)
            self._pending_file_item = None

    def _cancel_workers(self):
        if self._pdf_render_worker and self._pdf_render_worker.isRunning():
            self._pdf_render_worker.cancel()
            self._pdf_render_worker.wait(2000)
            self._pdf_render_worker = None
        if self._excel_render_worker and self._excel_render_worker.isRunning():
            self._excel_render_worker.cancel()
            self._excel_render_worker.wait(2000)
            self._excel_render_worker = None
        if self._ppt_render_worker and self._ppt_render_worker.isRunning():
            self._ppt_render_worker.cancel()
            self._ppt_render_worker.wait(2000)
            self._ppt_render_worker = None

    def _stop_media(self):
        if self._media_player:
            self._media_player.stop()
            self._media_player = None
        self._audio_output = None

    def clear_preview(self):
        self._cancel_workers()
        self._stop_media()
        self._loading_spinner.stop()
        self._current_result = None
        self._full_content = None
        self._showing_truncated = False
        self._current_file_item = None
        self._highlighter = None
        self._pdf_doc = None
        self._show_empty()
