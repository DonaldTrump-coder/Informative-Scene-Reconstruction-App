from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from desktop.ui.toast import Toast
import requests

class LoginDialog(QDialog):
    def __init__(self, config):
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
        self.url = config["url"]
        
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
        self.toast = Toast(self)
        
        self._worker = None
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(self.pos() + event.globalPos() - self._drag_pos)
            self._drag_pos = event.globalPos()
        
    def login(self):
        if self._worker is not None:
            return
        
        username = self.username.text().strip()
        password = self.password.text().strip()
        if not username or not password:
            self.toast.show_message("用户名或密码不能为空！", 2000)
            return
        
        self._set_loading(True)
        self._worker = AuthWorker(self.url, "login", username, password)
        self._worker.finished.connect(self._on_auth_finished)
        self._worker.start()
            
    def _on_auth_finished(self, success, message, data):
        self._set_loading(False)
        self.toast.show_message(message, 2000)
        if success:
            self.user_id = data.get("user_id")
            QTimer.singleShot(800, self.accept)
    
    def register(self):
        if self._worker is not None:
            return
        username = self.username.text().strip()
        password = self.password.text().strip()
        if not username or not password:
            self.toast.show_message("请输入用户名和密码")
            return
        
        self._set_loading(True)
        self._worker = AuthWorker(self.url, "register", username, password)
        self._worker.finished.connect(self._on_auth_finished)
        self._worker.start()
    
    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(1000)
        super().closeEvent(event)
    
    def _set_loading(self, loading):
        self.username.setEnabled(not loading)
        self.password.setEnabled(not loading)
        self.login_btn.setEnabled(not loading)
        self.register_btn.setEnabled(not loading)
        self.login_btn.setText("请稍候…" if loading else "登录")
        
from PyQt5.QtCore import QThread, pyqtSignal
class AuthWorker(QThread):
    finished = pyqtSignal(bool, str, dict)
    def __init__(self, url, mode, username, password):
        super().__init__()
        self.url = url
        self.mode = mode
        self.username = username
        self.password = password
        
    def run(self):
        try:
            endpoint = f"{self.url}/user/{self.mode}"
            r = requests.post(
                endpoint,
                params={"username": self.username, "password": self.password},
                timeout=5,
            )
            if r.status_code == 200:
                data = r.json()
                self.finished.emit(True, "登录成功" if self.mode == "login" else "注册成功", data)
            else:
                self.finished.emit(False, "操作失败", {})
        except Exception:
            self.finished.emit(False, "服务器连接失败", {})