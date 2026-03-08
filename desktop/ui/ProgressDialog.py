from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import QThread, pyqtSignal

class SfM_ProgressDialog(QProgressDialog):
    def __init__(self, labelText, cancelButtonText, minimum, maximum, parent=None):
        super(SfM_ProgressDialog, self).__init__(labelText, cancelButtonText, minimum, maximum, parent)