from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QAction, QFileDialog, QActionGroup
from ui.GLUI import GLWidget
from render.Thread import RenderThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Site Viewer V0.0.0")
        self.resize(800, 600)
        
        central_widget = QWidget(self)
        layout = QHBoxLayout(central_widget)
        self.glwidget = GLWidget(self, mainwindow=self)
        layout.addWidget(self.glwidget)
        self.setCentralWidget(central_widget)
        self.init_menu()
        self.renderthread = None

    def init_menu(self):
        menubar=self.menuBar()
        file_menu=menubar.addMenu("文件")
        render_menu=menubar.addMenu("渲染")

        open_action=QAction("打开", self)
        open_action.triggered.connect(self.Open_file)
        file_menu.addAction(open_action)

        _2DGS_rgb_action=QAction("2DGS 渲染",self)
        _2DGS_rgb_action.setCheckable(True)
        _2DGS_rgb_action.triggered.connect(self.set_2DGS_RGB)
        render_menu.addAction(_2DGS_rgb_action)

        _2DGS_disp_action=QAction("2D Ellipssoid 查看",self)
        _2DGS_disp_action.setCheckable(True)
        _2DGS_disp_action.triggered.connect(self.set_2DGS_Disp)
        render_menu.addAction(_2DGS_disp_action)

        _2DGS_depth_action=QAction("2DGS深度",self)
        _2DGS_depth_action.setCheckable(True)
        _2DGS_depth_action.triggered.connect(self.set_2DGS_Depth)
        render_menu.addAction(_2DGS_depth_action)

        mesh_rgb_action=QAction("Mesh 渲染",self)
        mesh_rgb_action.setCheckable(True)
        mesh_rgb_action.triggered.connect(self.set_mesh_RGB)
        render_menu.addAction(mesh_rgb_action)

        render_group = QActionGroup(self)
        render_group.setExclusive(True)
        render_group.addAction(_2DGS_rgb_action)
        render_group.addAction(_2DGS_disp_action)
        render_group.addAction(_2DGS_depth_action)
        render_group.addAction(mesh_rgb_action)

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