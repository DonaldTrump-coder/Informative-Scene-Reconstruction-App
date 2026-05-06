from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.resize(300, 150)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        self.container = QWidget()
        self.container.setObjectName("container")
        outer_layout.addWidget(self.container)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        title = QLabel("注册 / 登录")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; font-family: 'SimHei'")
        layout.addWidget(title)
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("用户名")
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("密码")
        self.password.setEchoMode(QLineEdit.Password)
        
        self.login_btn = QPushButton("登录")
        self.register_btn = QPushButton("注册")
        self.close_btn = QPushButton("退出")
        
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addWidget(self.register_btn)
        btn_layout.addWidget(self.login_btn)
        layout.addLayout(btn_layout)
        layout.addWidget(self.close_btn)
        
        self.close_btn.clicked.connect(self.reject)
        
        self.user_id = None
        self.login_btn.clicked.connect(self.login)
        self.register_btn.clicked.connect(self.register)
        
        self.setStyleSheet("""
            #container {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e1f29,
                    stop:1 #2b2d42
                );
                border-radius: 12px;
            }
            QLabel {
                color: #e0e6ff;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #3a3f5a;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.05);
                color: #ffffff;
                selection-background-color: #00d4ff;
            }
            QLineEdit:focus {
                border: 1px solid #00d4ff;
                background-color: rgba(0, 212, 255, 0.08);
            }
            QPushButton {
                font-family: "SimHei";
                font-size: 18px;
                padding: 6px;
                border-radius: 3px;
                background-color: #2f354f;
                color: #ffffff;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #3a3f6a;
            }
            QPushButton:pressed {
                background-color: #1f2235;
            }
        """)
        self._drag_pos = None
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(self.pos() + event.globalPos() - self._drag_pos)
            self._drag_pos = event.globalPos()
        
    def login(self):
        pass
    
    def register(self):
        pass
    
    def closeEvent(self, event):
        self.reject()