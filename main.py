import sys
from PyQt5.QtWidgets import QApplication
from desktop.ui.ApplicationUI import MainWindow

local2server_url = "localhost:8000"

app = QApplication(sys.argv)
window = MainWindow(local2server_url)
window.show()
sys.exit(app.exec_())