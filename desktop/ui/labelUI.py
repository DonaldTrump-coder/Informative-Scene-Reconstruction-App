from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QWidget

class LabelUI(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入标签信息")
        self.resize(350, 200)
        
        v_layout = QVBoxLayout(self)
        
        self.widget1, self.name_edit = self.add_h_layout("输入名称：")
        self.widget2, self.description_edit = self.add_h_layout("输入描述：")
        v_layout.addWidget(self.widget1)
        v_layout.addWidget(self.widget2)
        
        self.widget_buttons, self.button_ok, self.button_cancel = self.add_button_layout()
        v_layout.addWidget(self.widget_buttons)
        
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel.clicked.connect(self.reject)
        
    def add_h_layout(self, label_text):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        label = QLabel(label_text)
        line_edit = QLineEdit()
        layout.addWidget(label)
        layout.addWidget(line_edit)
        return widget, line_edit
    
    def add_button_layout(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        button1 = QPushButton("确定")
        button2 = QPushButton("取消")
        layout.addWidget(button1)
        layout.addWidget(button2)
        return widget, button1, button2
    
    def get_values(self):
        return self.name_edit.text(), self.description_edit.text()