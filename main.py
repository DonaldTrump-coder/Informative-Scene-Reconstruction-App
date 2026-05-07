import sys
from PyQt5.QtWidgets import QApplication, QDialog, QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from desktop.ui.ApplicationUI import MainWindow
from desktop.Apptools.load_thread import LoaderThread
from desktop.ui.LoginDialog import LoginDialog

app = QApplication(sys.argv)

pixmap = QPixmap("./resources/splash.jpg")
pixmap = pixmap.scaled(
    400, 300,
    Qt.KeepAspectRatio,
    Qt.SmoothTransformation
)
splash = QSplashScreen(pixmap)
splash.setWindowFlag(Qt.WindowStaysOnTopHint)
splash.show()
app.processEvents()

app.loader = LoaderThread()

def on_login_finished(result, dialog, window):
    if result == QDialog.Accepted:
        window.user_id = dialog.user_id
        window.setEnabled(True)
    else:
        QApplication.quit()
def on_finished(config):
    app.window = MainWindow(config)
    app.window.show()
    app.login_dialog = LoginDialog(config)
    #login_dialog.setWindowModality(Qt.ApplicationModal)
    app.login_dialog.finished.connect(
        lambda result: on_login_finished(result, app.login_dialog, app.window)
    )
    app.login_dialog.show()
    splash.finish(app.window)

app.loader.finished.connect(on_finished, Qt.QueuedConnection)
app.loader.start()
sys.exit(app.exec_())