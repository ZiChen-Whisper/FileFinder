"""
圆角菜单组件
============
提供带圆角和阴影的 QMenu 子类，用于顶栏下拉菜单和右键菜单。

实现原理：
  1. FramelessWindowHint + NoDropShadowWindowHint 去除系统原生边框和阴影
  2. WA_TranslucentBackground + WA_NoSystemBackground 使窗口背景透明
  3. setMask(QBitmap) 将窗口裁剪为圆角矩形，彻底阻止原生灰色背景露出
  4. QGraphicsDropShadowEffect 提供与右侧面板一致的阴影效果
  5. paintEvent 只负责绘制白色圆角背景 + 菜单项内容 + 边框

阴影参数与右侧面板 _RoundedPanel 一致：blurRadius=36, color=QColor(0,0,0,20)
"""

from PySide6.QtWidgets import QMenu, QGraphicsDropShadowEffect
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QBitmap
from PySide6.QtCore import Qt, QRectF

from ..style_constants import COLORS, RADIUS


class RoundedMenu(QMenu):
    """圆角菜单：setMask 裁剪原生背景 + QGraphicsDropShadowEffect 阴影。"""

    _BORDER_RADIUS = RADIUS.DEFAULT  # 8px

    def __init__(self, parent=None):
        super().__init__(parent)
        # 去除系统原生窗口装饰和阴影
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        # 透明背景：阻止系统绘制灰色底
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        pal = self.palette()
        pal.setColor(pal.ColorRole.Window, QColor(0, 0, 0, 0))
        pal.setColor(pal.ColorRole.Base, QColor(0, 0, 0, 0))
        self.setPalette(pal)
        self._capture = False

        # 阴影效果，参数与右侧面板 _RoundedPanel 一致
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(0, 0)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

    # ------------------------------------------------------------------
    # 遮罩：将窗口形状裁剪为圆角矩形，彻底消除原生灰色直角背景
    # ------------------------------------------------------------------

    def _update_mask(self):
        """根据当前尺寸生成圆角矩形遮罩并应用到窗口。"""
        size = self.size()
        if size.width() <= 0 or size.height() <= 0:
            return
        bitmap = QBitmap(size)
        bitmap.fill(Qt.GlobalColor.color0)  # 全透明
        p = QPainter(bitmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(Qt.GlobalColor.color1)  # 不透明
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(self.rect()), self._BORDER_RADIUS, self._BORDER_RADIUS)
        p.end()
        self.setMask(bitmap)

    def showEvent(self, event):
        super().showEvent(event)
        self._update_mask()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_mask()

    # ------------------------------------------------------------------
    # 绘制：白色圆角背景 → 菜单项 → 边框（阴影由 QGraphicsDropShadowEffect 提供）
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        # 捕获阶段：QMenu.paintEvent 只绘制菜单项（文字、图标、分隔线）
        if self._capture:
            QMenu.paintEvent(self, event)
            return

        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 清除原生背景
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # 绘制白色圆角背景
        inner = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS.BG_PRIMARY))
        painter.drawRoundedRect(inner, self._BORDER_RADIUS, self._BORDER_RADIUS)

        # 裁剪圆角区域后绘制菜单项
        clip = QPainterPath()
        clip.addRoundedRect(inner, self._BORDER_RADIUS, self._BORDER_RADIUS)
        painter.setClipPath(clip)
        self._capture = True
        QMenu.paintEvent(self, event)
        self._capture = False
        painter.setClipping(False)

        # 绘制圆角边框
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(COLORS.BORDER_DEFAULT), 1))
        painter.drawRoundedRect(inner, self._BORDER_RADIUS, self._BORDER_RADIUS)

        painter.end()
