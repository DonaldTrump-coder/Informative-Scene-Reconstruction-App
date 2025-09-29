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
        page1 = self.create_page_layout()
        page2 = self.create_page_layout()
        self.tab_widget.addTab(page1, "页面1")
        self.tab_widget.addTab(page2, "页面2")
        
        central_widget = QWidget(self)
        layout = QHBoxLayout(central_widget)
        layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)
        self.init_menu()
        self.renderthread = None

    def create_page_layout(self):
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

        splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.8)])
        layout.addWidget(splitter)

        return page_widget

    def init_menu(self):
        menubar=self.menuBar()
        file_menu=menubar.addMenu("文件")

        open_action=QAction("打开", self)
        open_action.triggered.connect(self.Open_file)
        file_menu.addAction(open_action)

    def Open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self,
                                                   "Open File",
                                                   "",
                                                   "PointCloudFile (*.ply *.pcd *.obj);;2DGS CheckPoint (*.ckpt);;All (*)")
        if file_path:
            self.renderthread = RenderThread(file_path)
            self.renderthread.frame_ready.connect(self.glwidget.set_image)
            self.renderthread.start()
    
    def set_2DGS_RGB(self, checked):
        if hasattr(self, 'renderthread'):
            self.renderthread.set_2DGS_RGB(checked)

    def set_2DGS_Disp(self, checked):
        if hasattr(self, 'renderthread'):
            self.renderthread.set_2DGS_Disp(checked)

    def set_2DGS_Depth(self, checked):
        if hasattr(self, 'renderthread'):
            self.renderthread.set_2DGS_Depth(checked)

    def set_mesh_RGB(self, checked):
        if hasattr(self, 'renderthread'):
            self.renderthread.set_mesh_RGB(checked)