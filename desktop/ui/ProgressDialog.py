from PyQt5.QtWidgets import QProgressDialog, QPushButton
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