from PySide6.QtCore import QTimer, QObject
from typing import Callable, Any
from constants import SEARCH_DEBOUNCE_MS

class Debouncer(QObject):
    """
    防抖器：延迟执行，等待用户停止输入一段时间后再执行回调。
    
    Args:
        delay_ms: 延迟毫秒数，默认300ms
        parent: 父对象
    """
    
    def __init__(self, delay_ms: int = SEARCH_DEBOUNCE_MS, parent=None):
        super().__init__(parent)
        self._delay_ms = delay_ms
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute)

    def trigger(self, callback: Callable[..., Any], *args, **kwargs):
        """
        触发防抖，设置回调和参数。
        
        Args:
            callback: 要执行的回调函数
            *args: 回调函数的位置参数
            **kwargs: 回调函数的关键字参数
        """
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        self._timer.stop()
        self._timer.start(self._delay_ms)

    def _execute(self):
        """执行回调函数"""
        self._callback(*self._args, **self._kwargs)