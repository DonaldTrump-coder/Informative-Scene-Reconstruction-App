from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont

class Toast(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("SimHei", 12))
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(60, 60, 60, 230);
                color: red;
                padding: 10px 18px;
                border-radius: 12px;
            }
        """)

        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)

        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(self.close)
        
    def show_message(self, text, duration=2000):
        self.setText(text)
        self.adjustSize()
        
        self._center_to_parent()
        self.setWindowOpacity(0)
        self.show()
        self.fade_in.start()
        QTimer.singleShot(duration, self.fade_out.start)
    
    def _center_to_parent(self):
        if self.parent():
            parent = self.parent().geometry()
            x = parent.x() + (parent.width() - self.width()) // 2
            y = parent.y() + parent.height() * 0.5
            self.move(x, y)
        else:
            screen = QApplication.primaryScreen().geometry()
            self.move(
                (screen.width() - self.width()) // 2,
                int(screen.height() * 0.8)
            )