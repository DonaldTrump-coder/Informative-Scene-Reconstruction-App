from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QAction, QFileDialog, QActionGroup, QTabWidget, QListWidget, QSplitter, QListWidgetItem, QVBoxLayout, QPushButton, QToolButton, QSizePolicy, QButtonGroup, QDialog
from PyQt5.QtCore import Qt, QEvent, QTimer, QSize, QRect, QPoint
from PyQt5.QtGui import QIcon
from desktop.ui.GLUI import GLWidget
from desktop.ui.labelUI import LabelUI
from desktop.render.Thread import RenderThread
import os
from desktop.render.rendermode import Status_mode

class MainWindow(QMainWindow):
    def __init__(self, url):
        super().__init__()
        self.setWindowTitle("LLM Scene Viewer V0.0.0")
        self.resize(800, 600)
        self.renderthread = RenderThread()
        self.renderthread.local2server_url = url
        
        self.tool_button_group = QButtonGroup() # Tool group of toolbar
        self.tool_button_group.setExclusive(False)

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
        self.origin = QPoint()
        
        self.renderthread.frame_ready.connect(self.current_gl.set_image)
        self.renderthread.add_image_list.connect(self.add_Image_names)
        self.renderthread.start()
        
        self.pcd_display_mode = Status_mode.FREE

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
            button1.clicked.connect(self.start_sfm)
        elif page == 2:
            button1 = QPushButton("生成3DGS场景")
            left_layout.addWidget(button1)
            icon1 = QIcon("resources/play-button.png")
            button1.setIcon(icon1)
            button1.clicked.connect(self.start_server_training)
        splitter.addWidget(left_container)  # 左侧显示文件列表
        
        if page == 2:
            self.tool_buttons = []
            self.toolpanel = QWidget()
            tool_layout = QVBoxLayout(self.toolpanel)
            tool_layout.setContentsMargins(4,4,4,4)
            tool_layout.setSpacing(6)
            tool_layout.addStretch()
            self.add_tool("resources/select.png", "选择", self.selection_status, True, tool_layout)
            self.add_tool("resources/unselect.png", "取消选择", self.unselection_status, True, tool_layout)
            self.add_tool("resources/label.png", "标注", self.get_label, False, tool_layout)
            
            splitter.addWidget(self.toolpanel)

        # 图像显示区：GLWidget
        gl_widget = GLWidget(page_widget, mainwindow=self)
        splitter.addWidget(gl_widget)  # 右侧显示图像区域
        setattr(page_widget, 'gl_widget', gl_widget)
        setattr(page_widget,'list_widget', file_list_widget)

        textWidget = QWidget()
        if page == 3:
            splitter.addWidget(textWidget)
            splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.6), int(self.width() * 0.2)])
        elif page == 2:
            splitter.widget(1).setFixedWidth(30)
            splitter.setSizes([int(self.width() * 0.17), 30, int(self.width() * 0.7)])
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
        self.current_list.itemClicked.connect(self.on_item_clicked)

    def on_item_clicked(self, item):
        if self.current_page == self.page1:
            image = item.data(Qt.UserRole)   # 取完整路径
            self.renderthread.set_current_image(image)
        elif self.current_page == self.page2:
            pass
        elif self.current_page == self.page3:
            pass
        
    def set_image(self):
        self.renderthread.set_image()
    
    def set_3DGS_RGB(self):
        self.renderthread.set_3DGS_RGB()
        
    def set_pcd(self):
        self.renderthread.set_pcd()
        
    def closeEvent(self, event):
        self.renderthread.stop()
        event.accept()
        
    def set_status(self, status: Status_mode):
        self.pcd_display_mode = status
        self.renderthread.display_mode = status
        
    def selection_status(self):
        btn = self.sender()
        if btn.isChecked():
            for other_btn in self.tool_buttons:
                if other_btn != btn:
                    other_btn.setChecked(False)
            self.set_status(Status_mode.SELECT)
        else:
            self.set_status(Status_mode.FREE)
    
    def unselection_status(self):
        btn = self.sender()
        if btn.isChecked():
            for other_btn in self.tool_buttons:
                if other_btn != btn:
                    other_btn.setChecked(False)
            self.set_status(Status_mode.UNSELECT)
        else:
            self.set_status(Status_mode.FREE)
        
    def free_status(self):
        self.set_status(Status_mode.FREE)
        
    def get_label(self):
        inputdig = LabelUI(self)
        if inputdig.exec_() == QDialog.Accepted:
            name, description = inputdig.get_values()
            if name and description:
                self.renderthread.add_label(name, description)
                self.renderthread.unselect_all()
                self.update_current_list()
                
    def update_current_list(self):
        if self.current_page == self.page2:
            self.current_list.clear()
            for index, label in enumerate(self.renderthread.pcd_labels):
                item = QListWidgetItem(f"{index+1}," + label.name)
                item.setData(Qt.UserRole, index)
                self.current_list.addItem(item)
            self.current_list.itemClicked.connect(self.on_item_clicked)
        
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
            if self.pcd_display_mode == Status_mode.FREE:
                self.mouse_pressed = True
                self.last_mouse_pos = event.pos()
                self.mouse_button = event.button()
            elif self.pcd_display_mode == Status_mode.SELECT:
                if event.button() == Qt.LeftButton:
                    self.renderthread.select_bbox = None
                    self.mouse_pressed = True
                    self.origin = getattr(self.page2, 'gl_widget', None).mapFrom(self, event.pos())
            elif self.pcd_display_mode == Status_mode.UNSELECT:
                if event.button() == Qt.LeftButton:
                    self.renderthread.select_bbox = None
                    self.mouse_pressed = True
                    self.origin = getattr(self.page2, 'gl_widget', None).mapFrom(self, event.pos())
            return True
        elif event.type() == QEvent.MouseMove and self.mouse_pressed:
            if self.pcd_display_mode == Status_mode.FREE:
                pos = event.pos()
                dx = pos.x() - self.last_mouse_pos.x()
                dy = pos.y() - self.last_mouse_pos.y()
                self.last_mouse_pos = pos
                self.renderthread.rotate(dx, dy)
            elif self.pcd_display_mode == Status_mode.SELECT:
                pos = getattr(self.page2, 'gl_widget', None).mapFrom(self, event.pos())
                rect = QRect(self.origin, pos).normalized()
                self.renderthread.select_bbox = (rect.left(), rect.top(), rect.right(), rect.bottom())
                self.renderthread.display_bbox = True
                self.renderthread.add_new_select()
            elif self.pcd_display_mode == Status_mode.UNSELECT:
                pos = getattr(self.page2, 'gl_widget', None).mapFrom(self, event.pos())
                rect = QRect(self.origin, pos).normalized()
                self.renderthread.select_bbox = (rect.left(), rect.top(), rect.right(), rect.bottom())
                self.renderthread.display_bbox = True
                self.renderthread.add_new_unselect()
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            if self.pcd_display_mode == Status_mode.FREE:
                self.mouse_pressed = False
            elif self.pcd_display_mode == Status_mode.SELECT:
                pos = getattr(self.page2, 'gl_widget', None).mapFrom(self, event.pos())
                rect = QRect(self.origin, pos).normalized()
                self.renderthread.select_bbox = (rect.left(), rect.top(), rect.right(), rect.bottom())
                self.origin = QPoint()
                self.mouse_pressed = False
                self.renderthread.display_bbox = False
                self.renderthread.select()
            elif self.pcd_display_mode == Status_mode.UNSELECT:
                pos = getattr(self.page2, 'gl_widget', None).mapFrom(self, event.pos())
                rect = QRect(self.origin, pos).normalized()
                self.renderthread.select_bbox = (rect.left(), rect.top(), rect.right(), rect.bottom())
                self.origin = QPoint()
                self.mouse_pressed = False
                self.renderthread.display_bbox = False
                self.renderthread.unselect()
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
        if Qt.Key_Q in self.events:
            self.renderthread.rotate_in_z_anticlockwise()
        if Qt.Key_E in self.events:
            self.renderthread.rotate_in_z_clockwise()
            
    def add_tool(
                 self,
                 icon: str,
                 tip: str,
                 callback: callable,
                 checkable: bool = True,
                 tool_layout: QVBoxLayout = None
                 ):
        btn = QToolButton()
        btn.setIcon(QIcon(icon))
        btn.setToolTip(tip)
        btn.setAutoRaise(True)
        btn.setCheckable(checkable)
        btn.clicked.connect(callback)
        tool_layout.addWidget(btn)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tool_buttons.append(btn)
        self.tool_button_group.addButton(btn)
        btn.setAutoExclusive(False)
        
    def resizeEvent(self, event):
        for btn in self.tool_buttons:
            w = self.toolpanel.width()
            size = int(w * 0.9)
            btn.setIconSize(QSize(size, size))
            btn.setFixedHeight(int(w*1.1))
        self.renderthread.glwidget_width = self.current_gl.width()
        self.renderthread.glwidget_height = self.current_gl.height()
        return super().resizeEvent(event)
    
    def start_server_training(self):
        #self.renderthread.upload_floder()
        self.renderthread.scene_train()
        
    def start_sfm(self):
        self.renderthread.upload_floder()
        self.renderthread.scene_reconstruct()