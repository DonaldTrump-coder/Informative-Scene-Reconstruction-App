from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QGraphicsDropShadowEffect, QLabel, QHBoxLayout, QFileDialog, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class CreateProjectWindow(QWidget):
    project_selected = pyqtSignal(str, str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_folder = ""
        self.project_name = ""
        self.setWindowTitle("设置项目")
        self.setFixedSize(480, 380)
        
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)
        card = QFrame()
        card.setObjectName("projectCard")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(30, 64, 175, 50))
        card.setGraphicsEffect(shadow)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        
        title = QLabel("创建项目")
        title.setObjectName("titleLabel")
        
        path_label = QLabel("项目文件夹")
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(
            "选择项目文件夹..."
        )
        self.path_edit.setReadOnly(True)
        
        name_label = QLabel("项目名称")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(
            "键入项目名称..."
        )
        
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.select_folder)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        ok_btn = QPushButton("确定")
        
        cancel_btn.clicked.connect(self.close)
        ok_btn.clicked.connect(self.confirm_project)
        ok_btn.setObjectName("primaryBtn")
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        card_layout.addWidget(title)
        card_layout.addSpacing(10)
        card_layout.addWidget(path_label)
        card_layout.addLayout(path_layout)
        card_layout.addWidget(name_label)
        card_layout.addWidget(self.name_edit)
        card_layout.addStretch()
        card_layout.addLayout(btn_layout)
        root_layout.addWidget(card)
        
        self.setStyleSheet("""
        #projectCard{
            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:1,
                stop:0 #ffffff,
                stop:1 #f4f8ff
            );
            border:1px solid #dbe7ff;
            border-radius:24px;
        }
        #titleLabel{
            font-size:24px;
            font-weight:700;
            color:#1e3a8a;
        }
        #subTitleLabel{
            font-size:13px;
            color:#64748b;
        }
        QLabel{
            font-size:14px;
            font-weight:600;
            color:#334155;
        }
        QLineEdit{
            background:white;
            border:1px solid #d6e2f0;
            border-radius:14px;
            padding:10px 14px;
            font-size:14px;
        }
        QLineEdit:focus{
            border:1px solid #60a5fa;
            background:#f8fbff;
        }
        QPushButton{
            background:white;
            border:1px solid #d6e2f0;
            border-radius:14px;
            padding:10px 18px;
            font-size:14px;
        }
        QPushButton:hover{
            background:#edf4ff;
            border:1px solid #7aa2ff;
        }
        QPushButton:pressed{
            background:#dbeafe;
        }
        #primaryBtn{
            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:1,
                stop:0 #2563eb,
                stop:1 #3b82f6
            );
            color:white;
            border:none;
            font-weight:600;
        }
        #primaryBtn:hover{
            background:#1d4ed8;
        }
        """)
        
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "请选择项目文件夹"
        )
        if folder:
            self.project_folder = folder
            self.path_edit.setText(folder)
            
    def confirm_project(self):
        self.project_name = self.name_edit.text().strip()
        if not self.project_folder:
            return
        if not self.project_name:
            return
        self.project_selected.emit(
            self.project_folder,
            self.project_name
        )
        self.close()