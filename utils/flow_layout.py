from PySide6.QtWidgets import QLayout, QLayoutItem
from PySide6.QtCore import QRect, QPoint, QSize, Qt


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=6):
        super().__init__(parent)
        self._items = []
        self._spacing = spacing
        if margin > 0:
            self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        if not self._items:
            return m.top() + m.bottom()
        rows = []
        current_row = []
        x = eff.x()
        row_height = 0
        for item in self._items:
            w = item.sizeHint()
            next_x = x + w.width() + self._spacing
            if next_x - self._spacing > eff.right() and current_row:
                rows.append((list(current_row), row_height))
                current_row = []
                x = eff.x()
                next_x = x + w.width() + self._spacing
                row_height = 0
            current_row.append((item, x, w))
            x = next_x
            row_height = max(row_height, w.height())
        if current_row:
            rows.append((list(current_row), row_height))
        y = eff.y()
        for row_items, row_h in rows:
            if not test_only:
                for item, item_x, item_size in row_items:
                    item_y = y + (row_h - item_size.height()) // 2
                    item.setGeometry(QRect(QPoint(item_x, item_y), item_size))
            y += row_h + self._spacing
        return y - self._spacing - rect.y() + m.bottom()
