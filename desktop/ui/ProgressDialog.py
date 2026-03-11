from PyQt5.QtWidgets import QProgressDialog, QPushButton, QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

class SfM_ProgressDialog(QProgressDialog):
    cancelClicked = pyqtSignal()
    def __init__(self, labelText, cancelButtonText, minimum, maximum, parent=None):
        super(SfM_ProgressDialog, self).__init__(labelText, cancelButtonText, minimum, maximum, parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAutoClose(False)
        self.setAutoReset(False)
        
        btn = self.findChild(QPushButton) # find the cancel button
        btn.clicked.disconnect()
        btn.clicked.connect(self.cancel)
    
    def cancel(self):
        self.cancelClicked.emit()
        
class Message_Dialog(QDialog):
    def __init__(self, text="", parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.Dialog |
            Qt.CustomizeWindowHint
        )

        layout = QVBoxLayout(self)
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.resize(300, 100)

    def setText(self, text):
        self.label.setText(text)