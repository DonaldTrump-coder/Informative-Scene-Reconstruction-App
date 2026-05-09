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
        
        self.setWindowTitle("视频抽帧")
        self.resize(500, 180)
        main_layout = QVBoxLayout(self)
        
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