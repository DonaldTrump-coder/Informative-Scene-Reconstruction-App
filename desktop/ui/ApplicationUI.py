from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QAction, QFileDialog, QActionGroup, QTabWidget, QListWidget, QSplitter, QListWidgetItem, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QIcon
from desktop.ui.GLUI import GLWidget
from desktop.render.Thread import RenderThread
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Scene Viewer V0.0.0")
        self.resize(800, 600)
        self.renderthread = RenderThread()

        self.tab_widget = QTabWidget(self)
        self.page1 = self.create_page_layout(1)
        self.page2 = self.create_page_layout(2)
        self.page3 = self.create_page_layout(3)
        self.tab_widget.addTab(self.page1, "图像输入")
        self.tab_widget.addTab(self.page2, "点云标注查看")
        self.tab_widget.addTab(self.page3, "实景生成")
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        self.current_gl = getattr(self.page1, 'gl_widget', None)
        self.current_list = getattr(self.page1, 'list_widget', None)
        self.current_page = self.page1
        
        central_widget = QWidget(self)
        layout = QHBoxLayout(central_widget)
        layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)
        self.init_menu()
        
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        
        self.events = set()
        self.installEventFilter(self)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)
        self.timer.start(16)
        
        self.mouse_pressed = False
        self.last_mouse_pos = None
        self.mouse_button = None
        
        self.renderthread.frame_ready.connect(self.current_gl.set_image)
        self.renderthread.add_image_list.connect(self.add_Image_names)
        self.renderthread.start()

    def create_page_layout(self, page):
        page_widget = QWidget()

        # 创建水平布局，左侧文件显示区，右侧是图像显示区
        layout = QHBoxLayout(page_widget)

        splitter = QSplitter(Qt.Horizontal)

        # 文件显示区：QListWidget
        file_list_widget = QListWidget(page_widget)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.addWidget(file_list_widget)
        if page == 1:
            Button_widget = QWidget()
            left_layout.addWidget(Button_widget)
            button_layout = QHBoxLayout(Button_widget)
            button1 = QPushButton("按钮1")
            button_layout.addWidget(button1)
            icon1 = QIcon("resources/play.png")
            button1.setIcon(icon1)
            button1.clicked.connect(self.renderthread.start_sfm)
        splitter.addWidget(left_container)  # 左侧显示文件列表

        # 图像显示区：GLWidget
        gl_widget = GLWidget(page_widget, mainwindow=self)
        splitter.addWidget(gl_widget)  # 右侧显示图像区域
        setattr(page_widget, 'gl_widget', gl_widget)
        setattr(page_widget,'list_widget', file_list_widget)

        textWidget = QWidget()
        if page == 3:
            splitter.addWidget(textWidget)
            splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.6), int(self.width() * 0.2)])
        else:
            splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.8)])
        layout.addWidget(splitter)

        return page_widget
    
    def on_tab_changed(self, index):
        if index == 0:
            self.set_image()
            self.current_gl = getattr(self.page1, 'gl_widget', None)
            self.current_list = getattr(self.page1, 'list_widget', None)
            self.current_page = self.page1
            self.renderthread.frame_ready.connect(self.current_gl.set_image)
        elif index == 1:
            self.set_pcd()
            self.current_gl = getattr(self.page2, 'gl_widget', None)
            self.current_list = getattr(self.page2, 'list_widget', None)
            self.current_page = self.page2
            self.renderthread.frame_ready.connect(self.current_gl.set_image)
        elif index == 2:
            self.set_3DGS_RGB()
            self.current_gl = getattr(self.page3, 'gl_widget', None)
            self.current_list = getattr(self.page3, 'list_widget', None)
            self.current_page = self.page3
            self.renderthread.frame_ready.connect(self.current_gl.set_image)

    def init_menu(self):
        menubar=self.menuBar()
        file_menu=menubar.addMenu("文件")

        project_action = QAction("创建项目", self)
        open_project_action = QAction("打开项目", self)
        open_action=QAction("打开图像", self)
        open_action.triggered.connect(self.Open_images)
        project_action.triggered.connect(self.renderthread.set_project_path)
        open_project_action.triggered.connect(self.renderthread.open_project)
        file_menu.addAction(open_action)
        file_menu.addAction(project_action)
        file_menu.addAction(open_project_action)

    def Open_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        self.renderthread.image_folder = folder_path
        if folder_path:
            self.renderthread.get_images() # get all the images in thread

    def add_Image_names(self, images:list[str]):
        for image in images:
            item = QListWidgetItem(os.path.basename(image))
            item.setData(Qt.UserRole, image)
            self.current_list.addItem(item)
            self.current_list.itemClicked.connect(self.on_image_item_clicked)

    def on_image_item_clicked(self, item):
        image = item.data(Qt.UserRole)   # 取完整路径
        self.renderthread.set_current_image(image)
        
    def set_image(self):
        self.renderthread.set_image()
    
    def set_3DGS_RGB(self):
        self.renderthread.set_3DGS_RGB()
        
    def set_pcd(self):
        self.renderthread.set_pcd()
        
    def closeEvent(self, event):
        self.renderthread.stop()
        event.accept()
        
    def eventFilter(self, source, event):
        if self.current_page == self.page1:
            return False
        if event.type() == QEvent.KeyPress:
            self.events.add(event.key())
            return True
        elif event.type() == QEvent.KeyRelease:
            self.events.discard(event.key())
            return True
        elif event.type() == QEvent.MouseButtonPress:
            self.mouse_pressed = True
            self.last_mouse_pos = event.pos()
            self.mouse_button = event.button()
            return True
        elif event.type() == QEvent.MouseMove and self.mouse_pressed:
            pos = event.pos()
            dx = pos.x() - self.last_mouse_pos.x()
            dy = pos.y() - self.last_mouse_pos.y()
            self.last_mouse_pos = pos
            self.renderthread.rotate(dx, dy)
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            self.mouse_pressed = False
            return True
        
        return False
    
    def update_camera(self):
        if Qt.Key_W in self.events:
            self.renderthread.move_forward()
        if Qt.Key_S in self.events:
            self.renderthread.move_back()
        if Qt.Key_A in self.events:
            self.renderthread.move_left()
        if Qt.Key_D in self.events:
            self.renderthread.move_right()