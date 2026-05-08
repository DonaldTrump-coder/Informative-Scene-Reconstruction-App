from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QScrollArea, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

class SceneItemWidget(QFrame):
    clicked = pyqtSignal(dict)
    def __init__(self, scene_data, parent=None):
        super().__init__(parent)
        self.scene_data = scene_data
        self.setObjectName("projectCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(90)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(16)
        self.name_label = QLabel(scene_data["object_name"])
        self.name_label.setObjectName("titleLabel")
        self.path_label = QLabel(scene_data["project_path"])
        self.path_label.setObjectName("subTitleLabel")
        self.path_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.name_label.setFixedWidth(140)
        layout.addWidget(self.name_label)
        layout.addWidget(self.path_label)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.scene_data)
        super().mousePressEvent(event)

class ServerProjectDialog(QWidget):
    request_signal = pyqtSignal()
    selected_scene_signal = pyqtSignal(dict)
    def __init__(self, parent=None):
        super(ServerProjectDialog, self).__init__(parent)
        self.setWindowTitle("我的场景")
        self.setFixedSize(480, 380)
        self.setWindowFlags(Qt.Window)
        self.setWindowModality(Qt.ApplicationModal)
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

        #projectCard:hover{
            border:1px solid #60a5fa;
            background:#edf4ff;
        }

        #titleLabel{
            font-size:18px;
            font-weight:700;
            color:#1e3a8a;
        }

        #subTitleLabel{
            font-size:12px;
            color:#64748b;
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

        #primaryBtn{
            background:#2563eb;
            color:white;
            border:none;
            font-weight:600;
        }

        #primaryBtn:hover{
            background:#1d4ed8;
        }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.header = QLabel("我的场景")
        self.header.setObjectName("titleLabel")
        self.main_layout.addWidget(self.header)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.scene_layout = QVBoxLayout(self.container)
        self.scene_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)
        btn_layout = QHBoxLayout()
        self.confirm_btn = QPushButton("确定")
        self.confirm_btn.setObjectName("primaryBtn")
        self.cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        self.main_layout.addLayout(btn_layout)
        self.confirm_btn.clicked.connect(self.confirm_selection)
        self.cancel_btn.clicked.connect(self.close)
        
    def disp_scenes(self, data):
        while self.scene_layout.count():
            item = self.scene_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for scene in data:
            item_widget = SceneItemWidget(scene)
            item_widget.clicked.connect(self.select_scene)
            self.scene_layout.addWidget(item_widget)
    
    def select_scene(self, scene_data):
        self.selected_scene = scene_data
        
    def confirm_selection(self):
        if self.selected_scene is not None:
            self.selected_scene_signal.emit(self.selected_scene)
        self.close()