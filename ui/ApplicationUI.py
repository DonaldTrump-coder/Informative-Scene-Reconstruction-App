from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QAction, QFileDialog, QActionGroup, QTabWidget, QListWidget, QSplitter
from PyQt5.QtCore import Qt
from ui.GLUI import GLWidget
from render.Thread import RenderThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Site Viewer V0.0.0")
        self.resize(800, 600)

        self.tab_widget = QTabWidget(self)
        self.page1 = self.create_page_layout(1)
        self.page2 = self.create_page_layout(2)
        self.tab_widget.addTab(self.page1, "页面1")
        self.tab_widget.addTab(self.page2, "页面2")
        self.current_gl = getattr(self.page1, 'gl_widget', None)
        
        central_widget = QWidget(self)
        layout = QHBoxLayout(central_widget)
        layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)
        self.init_menu()
        self.renderthread = RenderThread()
        self.renderthread.frame_ready.connect(self.current_gl.set_image)
        self.renderthread.start()

    def create_page_layout(self, page):
        page_widget = QWidget()

        # 创建水平布局，左侧文件显示区，右侧是图像显示区
        layout = QHBoxLayout(page_widget)

        splitter = QSplitter(Qt.Horizontal)

        # 文件显示区：QListWidget
        file_list_widget = QListWidget(page_widget)
        splitter.addWidget(file_list_widget)  # 左侧显示文件列表

        # 图像显示区：GLWidget
        gl_widget = GLWidget(page_widget, mainwindow=self)
        splitter.addWidget(gl_widget)  # 右侧显示图像区域
        setattr(page_widget, 'gl_widget', gl_widget)

        textWidget = QWidget()
        if page == 2:
            splitter.addWidget(textWidget)
            splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.6), int(self.width() * 0.2)])
        else:
            splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.8)])
        layout.addWidget(splitter)

        return page_widget

    def init_menu(self):
        menubar=self.menuBar()
        file_menu=menubar.addMenu("文件")

        open_action=QAction("打开图像", self)
        open_action.triggered.connect(self.Open_images)
        file_menu.addAction(open_action)

    def Open_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        self.renderthread.image_folder = folder_path
        if folder_path:
            self.renderthread.get_images() # get all the images in thread
    
    def set_3DGS_RGB(self):
        self.renderthread.set_3DGS_RGB()