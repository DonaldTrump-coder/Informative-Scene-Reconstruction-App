from desktop.render.Thread import VideoFrameExtractThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel, QSpinBox, QProgressBar, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt

class VideoWindow(QWidget):
    finish_signal = pyqtSignal(str)
    def __init__(self, output_dir, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            self.windowFlags() | Qt.Window
        )
        self.extract_thread = None
        self.output_dir = output_dir
        self.setStyleSheet("""
        QWidget{
            background:#f8fbff;
        }
        #titleLabel{
            font-size:18px;
            font-weight:700;
            color:#1e3a8a;
        }
        QLabel{
            font-size:13px;
            color:#334155;
        }
        QLineEdit{
            background:white;
            border:1px solid #d6e2f0;
            border-radius:12px;
            padding:8px 12px;
            font-size:13px;
        }
        QLineEdit:focus{
            border:1px solid #60a5fa;
        }
        QSpinBox{
            background:white;
            border:1px solid #d6e2f0;
            border-radius:12px;
            padding:6px 10px;
            font-size:13px;
        }
        QSpinBox:focus{
            border:1px solid #60a5fa;
        }
        QSpinBox::up-button{
            width:18px;
            background:white;
            border:none;
            margin-right:4px;
            border-top-right-radius:8px;
        }
        QSpinBox::down-button{
            width:18px;
            background:white;
            border:none;
            margin-right:4px;
            border-bottom-right-radius:8px;
        }
        QSpinBox::up-button:hover,
        QSpinBox::down-button:hover{
            background:#edf4ff;
        }
        QSpinBox::up-button:pressed,
        QSpinBox::down-button:pressed{
            background:#dbeafe;
        }
        QSpinBox::up-arrow{
            image: url(resources/icons/chevron-up.svg);
            width:8px;
            height:8px;
        }
        QSpinBox::down-arrow{
            image: url(resources/icons/chevron-down.svg);
            width:8px;
            height:8px;
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
        QProgressBar{
            background:white;
            border:1px solid #dbe7ff;
            border-radius:10px;
            text-align:center;
            height:18px;
        }
        QProgressBar::chunk{
            background:#2563eb;
            border-radius:8px;
        }
        """)
        
        self.setWindowTitle("视频抽帧")
        self.resize(540, 220)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)
        
        video_file_layout = QHBoxLayout()
        self.video_edit = QLineEdit()
        self.video_edit.setReadOnly(True)
        self.browse_btn = QPushButton("选择视频")
        self.browse_btn.clicked.connect(
            self.choose_video
        )
        video_file_layout.addWidget(QLabel("视频:"))
        video_file_layout.addWidget(self.video_edit)
        video_file_layout.addWidget(self.browse_btn)
        main_layout.addLayout(video_file_layout)
        
        interval_layout = QHBoxLayout()
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(100000)
        self.interval_spin.setValue(30)
        interval_layout.addWidget(QLabel("Frame Interval:"))
        interval_layout.addWidget(self.interval_spin)
        main_layout.addLayout(interval_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        btn_layout = QHBoxLayout()
        self.extract_btn = QPushButton("导入")
        self.cancel_btn = QPushButton("取消")
        self.extract_btn.clicked.connect(self.start_extract)
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.extract_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)
        self.extract_btn.setObjectName("primaryBtn")
    
    def choose_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_path:
            self.video_edit.setText(
                file_path
            )
            
    def start_extract(self):
        video_path = self.video_edit.text()
        if not video_path:
            QMessageBox.warning(None, "Warning", "当前未选择视频！")
            return
        interval = self.interval_spin.value()
        self.extract_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.extract_thread = (VideoFrameExtractThread(
            video_path=video_path,
            output_dir=self.output_dir,
            interval=interval
        ))
        self.extract_thread.progress_signal.connect(self.progress_bar.setValue)
        self.extract_thread.finished_signal.connect(self.on_finished)
        self.extract_thread.error_signal.connect(self.on_error)
        self.extract_thread.start()
        
    def on_finished(self, video_name):
        self.finish_signal.emit(video_name)
        self.close()
        
    def on_error(self):
        QMessageBox.warning(self, "Warning", "导入错误！")
        self.extract_btn.setEnabled(True)
        
    def closeEvent(self, event):
        if self.extract_thread:
            self.extract_thread.stop()
            self.extract_thread.wait()
        event.accept()