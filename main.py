import sys
import os
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.screen=false'
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui import MainWindow

def main():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(application_path)

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    font = app.font()
    font.setStyleStrategy(font.styleStrategy() | QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()