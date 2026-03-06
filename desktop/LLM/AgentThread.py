from PyQt5.QtCore import QThread

class AgentThread(QThread):
    def __init__(self):
        super().__init__()
        