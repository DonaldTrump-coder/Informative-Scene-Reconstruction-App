from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class MessageBubble(QWidget):
    def __init__(self, text = "", is_user = False):
        super().__init__()
        
        layout = QHBoxLayout(self)
        
        avatar = QLabel()
        pixmap = QPixmap("resources/user.png" if is_user else "resources/bot.png")
        pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        avatar.setPixmap(pixmap)
        
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(200)
        self.label.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Preferred
        )
        
        if is_user:
            self.label.setStyleSheet(
                """
                background: #ABFF81;
                padding: 8px;
                border-radius: 8px;
                """
            )
            layout.addStretch()
            layout.addWidget(self.label)
            layout.addWidget(avatar, alignment=Qt.AlignTop)
        else:
            self.label.setStyleSheet(
                """
                background:white;
                padding:8px;
                border-radius:8px;
                """
            )
            layout.addWidget(avatar, alignment=Qt.AlignTop)
            layout.addWidget(self.label)
            layout.addStretch()
    
    def update_text(self, text):
        self.label.setText(text)
        self.label.adjustSize()
        self.adjustSize()