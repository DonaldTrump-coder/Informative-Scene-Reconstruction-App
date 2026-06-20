from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QAction, QFileDialog, QActionGroup, QTabWidget, QListWidget, QSplitter, QListWidgetItem, QVBoxLayout, QPushButton, QToolButton, QSizePolicy, QButtonGroup, QDialog, QScrollArea, QLineEdit, QLabel, QApplication, QMessageBox, QMenu
from PyQt5.QtCore import Qt, QEvent, QTimer, QSize, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QIcon
from desktop.ui.GLUI import GLWidget
from desktop.ui.labelUI import LabelUI
from desktop.ui.ProgressDialog import SfM_ProgressDialog, Message_Dialog
from desktop.render.Thread import RenderThread
import os
from desktop.render.rendermode import Status_mode
import numpy as np
from desktop.ui.MessageBubble import MessageBubble
from desktop.ui.createprojectUI import CreateProjectWindow
from desktop.ui.serverprojectsUI import ServerProjectDialog
from desktop.ui.Videowindow import VideoWindow
from desktop.ui.CollapsibleLabelPanel import CollapsibleLabelPanel

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle("Scene Reconstructor with Guidance Agent V0.0.2")
        self.setWindowIcon(QIcon("resources/app.png"))
        self.resize(800, 600)
        self.renderthread = RenderThread()
        url = config["url"]
        self.renderthread.local2server_url = url
        self.renderthread.rendering_url = url + "/ws/render"
        
        self.tool_button_group = QButtonGroup() # Tool group of toolbar
        self.tool_button_group.setExclusive(False)

        self.tab_widget = QTabWidget(self)
        self.page1 = self.create_page_layout(1)
        self.page2 = self.create_page_layout(2)
        self.page3 = self.create_page_layout(3)
        self.tab_widget.addTab(self.page1, "影像输入")
        self.tab_widget.addTab(self.page2, "点云标注")
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
        self.renderthread.clear_image_list.connect(self.clear_all_images)
        self.renderthread.start_new_signal.connect(self.start_bot_message)
        self.renderthread.update_text_signal.connect(self.update_bot_message)
        self.renderthread.request_project_path.connect(self.open_project_window)
        self.renderthread.update_list.connect(self.update_current_list)
        self.renderthread.agentthread.navigate_signal.connect(self.renderthread.navigate_to)
        self.renderthread.start()
        
        self.pcd_display_mode = Status_mode.FREE
        self.user_id = None
        
        GLOBAL_QSS = """
        QMainWindow{
            background:#eef3f8;
        }dddd
        QWidget{
            font-family: "Microsoft YaHei";
            font-size:14px;
            color:#2c3e50;
        }
        QTabWidget::pane{
            border:none;
            background:transparent;
        }
        QTabBar::tab{
            background:#dfe7f2;
            padding:10px 22px;
            border-radius:8px;
            margin:4px;
            min-width:120px;
        }
        QTabBar::tab:selected{
            background:white;
            color:#1f6feb;
            font-weight:bold;
        }
        QMenuBar{
            background:white;
            border-bottom:1px solid #d0d7de;
        }
        QMenuBar::item:selected{
            background:#eaf2ff;
            border-radius:5px;
        }
        QMenu{
            background:white;
            border:1px solid #d0d7de;
        }
        QMenu::item:selected{
            background:#eaf2ff;
        }
        QPushButton{
            background:white;
            border:1px solid #c9d4e2;
            border-radius:10px;
            padding:8px 5px;
        }
        QPushButton:hover{
            background:#eaf2ff;
            border:1px solid #7aa2ff;
        }
        QPushButton:pressed{
            background:#d6e6ff;
        }
        QListWidget{
            background:white;
            border:none;
            border-radius:12px;
            padding:8px;
        }
        QListWidget::item{
            padding:8px;
            border-radius:8px;
        }
        QListWidget::item:selected{
            background:#dbeafe;
            color:#2563eb;
        }
        QLineEdit{
            background:white;
            border:1px solid #cbd5e1;
            border-radius:10px;
            padding:8px;
        }
        QScrollArea{
            border:none;
            background:transparent;
        }
        QSplitter::handle{
            background:#d0d7de;
            width:2px;
        }
        QToolTip{
            background:white;
            border:1px solid #cbd5e1;
            color:#2c3e50;
        }
        """
        self.setStyleSheet(GLOBAL_QSS)
        
        self._current_label_index = -1

    def create_page_layout(self, page):
        page_widget = QWidget()

        layout = QHBoxLayout(page_widget)

        splitter = QSplitter(Qt.Horizontal)

        if page == 1 or page == 2:
            file_list_widget = QListWidget(page_widget)

            left_container = QWidget()
            left_layout = QVBoxLayout(left_container)
            left_layout.addWidget(file_list_widget)
        if page == 1:
            Button_widget = QWidget()
            left_layout.addWidget(Button_widget)
            btn_outer = QVBoxLayout(Button_widget)
            btn_outer.setContentsMargins(0, 0, 0, 0)
            btn_outer.setSpacing(6)
            
            row1 = QHBoxLayout()
            button1 = QPushButton("稀疏重建")
            button1.setIcon(QIcon("resources/play.png"))
            button1.clicked.connect(self.start_sfm)
            row1.addWidget(button1)
            btn_outer.addLayout(row1)
            
            row2 = QHBoxLayout()
            row2.setSpacing(6)
            self.delete_selected_btn = QPushButton("删除选定图像")
            self.delete_selected_btn.clicked.connect(self.on_delete_selected_image)
            row2.addWidget(self.delete_selected_btn)
            self.delete_all_btn = QPushButton("删除所有图像")
            self.delete_all_btn.clicked.connect(self.on_delete_all_images)
            row2.addWidget(self.delete_all_btn)
            btn_outer.addLayout(row2)
            
            splitter.addWidget(left_container)
            
        elif page == 2:
            Button_widget = QWidget()
            left_layout.addWidget(Button_widget)
            btn_outer = QVBoxLayout(Button_widget)
            btn_outer.setContentsMargins(0, 0, 0, 0)
            btn_outer.setSpacing(6)
            row1 = QHBoxLayout()
            button1 = QPushButton("生成实景")
            button1.setIcon(QIcon("resources/play-button.png"))
            button1.clicked.connect(self.start_server_training)
            row1.addWidget(button1)
            btn_outer.addLayout(row1)
            
            row2 = QHBoxLayout()
            row2.setSpacing(6)
            self.delete_label_btn = QPushButton("删除选定标注")
            self.delete_label_btn.clicked.connect(self.on_delete_selected_label)
            row2.addWidget(self.delete_label_btn)
            self.delete_all_labels_btn = QPushButton("删除所有标注")
            self.delete_all_labels_btn.clicked.connect(self.on_delete_all_labels)
            row2.addWidget(self.delete_all_labels_btn)
            
            btn_outer.addLayout(row2)
            splitter.addWidget(left_container)
        
        if page == 2:
            self.tool_buttons = []
            self.toolpanel = QWidget()
            tool_layout = QVBoxLayout(self.toolpanel)
            tool_layout.setContentsMargins(4,4,4,4)
            tool_layout.setSpacing(6)
            self.add_tool("resources/select.png", "选择", self.selection_status, True, tool_layout)
            self.add_tool("resources/unselect.png", "取消选择", self.unselection_status, True, tool_layout)
            self.add_tool("resources/label.png", "标注", self.get_label, False, tool_layout)
            self.add_tool("resources/delete.png", "删除标注", self.on_delete_selected_label, False, tool_layout)
            tool_layout.addStretch()
            
            splitter.addWidget(self.toolpanel)

        gl_widget = GLWidget(page_widget, mainwindow=self)
        splitter.addWidget(gl_widget)
        setattr(page_widget, 'gl_widget', gl_widget)
        if page == 1 or page == 2:
            setattr(page_widget,'list_widget', file_list_widget)

        textWidget = QWidget()
        if page == 3:
            self.label_panel = CollapsibleLabelPanel()
            splitter.insertWidget(0, self.label_panel)
            splitter.addWidget(textWidget)
            splitter.setSizes([int(self.width() * 0.8), int(self.width() * 0.2)])
            
            textlayout = QVBoxLayout(textWidget)
            
            title_widget = QWidget()
            textlayout.addWidget(title_widget)
            title_layout = QHBoxLayout(title_widget)
            icon_label = QLabel()
            icon = QIcon("resources/bot_title.png")
            icon_label.setPixmap(icon.pixmap(QSize(30, 30)))
            title_label = QLabel("智能体导览")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet(
                """
                QLabel{
                    font-size:25px;
                    font-weight:bold;
                    font-family: SimHei;
                }
                """
            )
            title_layout.addStretch(1)
            title_layout.addWidget(icon_label)
            title_layout.addWidget(title_label)
            title_layout.addStretch(1)
            
            self.chat_scroll = QScrollArea()
            self.chat_scroll.setWidgetResizable(True)
            self.chat_container = QWidget()
            self.chat_layout = QVBoxLayout(self.chat_container)
            self.chat_layout.setAlignment(Qt.AlignTop)
            self.chat_scroll.setWidget(self.chat_container)
            textlayout.addWidget(self.chat_scroll)
            self.chat_input = QLineEdit()
            send_button = QPushButton("发送")
            send_button.setFixedWidth(50)
            input_layout = QHBoxLayout()
            input_layout.addWidget(self.chat_input)
            input_layout.addWidget(send_button)
            input_layout.setStretch(0, 6)
            input_layout.setStretch(1, 1)
            textlayout.addLayout(input_layout)
            send_button.clicked.connect(self.send_message)
            self.label_panel.navigate_requested.connect(self.renderthread.navigate_to)
        elif page == 2:
            splitter.widget(1).setFixedWidth(30)
            splitter.setSizes([int(self.width() * 0.17), 30, int(self.width() * 0.7)])
        else:
            splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.8)])
        layout.addWidget(splitter)

        return page_widget
    
    def on_tab_changed(self, index):
        self.renderthread.hide_label_bbox()
        self._current_label_index = -1
        if index == 0:
            self.set_image()
            self.current_gl = getattr(self.page1, 'gl_widget', None)
            self.current_list = getattr(self.page1, 'list_widget', None)
            self.current_page = self.page1
            self.renderthread.frame_ready.connect(self.current_gl.set_image)
            self.renderthread.agentthread.llm_using = False
            self.choose_action.setEnabled(False)
            self.unchoose_action.setEnabled(False)
            self.label_action.setEnabled(False)
        elif index == 1:
            self.set_pcd()
            self.current_gl = getattr(self.page2, 'gl_widget', None)
            self.current_list = getattr(self.page2, 'list_widget', None)
            self.current_page = self.page2
            self.renderthread.frame_ready.connect(self.current_gl.set_image)
            self.renderthread.agentthread.llm_using = False
            self.choose_action.setEnabled(True)
            self.unchoose_action.setEnabled(True)
            self.label_action.setEnabled(True)
            self.delete_label_action.setEnabled(True)
            self.update_current_list()
        elif index == 2:
            self.set_3DGS_RGB()
            self.current_gl = getattr(self.page3, 'gl_widget', None)
            self.current_list = getattr(self.page3, 'list_widget', None)
            self.current_page = self.page3
            self.renderthread.frame_ready.connect(self.current_gl.set_image)
            self.renderthread.agentthread.llm_using = True
            self.choose_action.setEnabled(False)
            self.unchoose_action.setEnabled(False)
            self.label_action.setEnabled(False)
        QTimer.singleShot(100, self.current_gl.clear)

    def init_menu(self):
        menubar=self.menuBar()
        file_menu=menubar.addMenu("文件")
        option_menu = menubar.addMenu("选项")
        pcd_menu = menubar.addMenu("点云")

        project_action = QAction("创建项目", self)
        open_project_action = QAction("打开本地项目", self)
        open_server_project_action = QAction("从云端选择项目", self)
        open_action=QAction("导入影像", self)
        open_video_action = QAction("导入视频", self)
        open_action.triggered.connect(self.Open_images)
        project_action.triggered.connect(self.renderthread.set_project_path)
        open_project_action.triggered.connect(self.renderthread.open_project)
        open_server_project_action.triggered.connect(self.server_project_window)
        open_video_action.triggered.connect(self.open_video_window)
        file_menu.addAction(open_action)
        file_menu.addAction(project_action)
        file_menu.addAction(open_project_action)
        file_menu.addAction(open_server_project_action)
        file_menu.addAction(open_video_action)
        
        self.choose_action = QAction("选择", self)
        self.unchoose_action = QAction("取消选择", self)
        self.label_action = QAction("标注", self)
        self.delete_label_action = QAction("删除标注", self)
        self.choose_action.triggered.connect(self.tool_buttons[0].click)
        self.unchoose_action.triggered.connect(self.tool_buttons[1].click)
        self.label_action.triggered.connect(self.tool_buttons[2].click)
        self.delete_label_action.triggered.connect(self.tool_buttons[3].click)
        pcd_menu.addAction(self.choose_action)
        pcd_menu.addAction(self.unchoose_action)
        pcd_menu.addAction(self.label_action)
        pcd_menu.addAction(self.delete_label_action)
        
        language_menu = option_menu.addMenu("语言")
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        action_cn = QAction("中文", self, checkable=True, checked=True)
        action_en = QAction("English", self, checkable=True)
        language_menu.addAction(action_cn)
        language_menu.addAction(action_en)
        lang_group.addAction(action_cn)
        lang_group.addAction(action_en)
        action_cn.triggered.connect(lambda: self.change_language("zh"))
        action_en.triggered.connect(lambda: self.change_language("en"))
        
        self.choose_action.setEnabled(False)
        self.unchoose_action.setEnabled(False)
        self.label_action.setEnabled(False)
        self.delete_label_action.setEnabled(False)
        
    def change_language(self, language):
        print(f"change language to {language}")

    def Open_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        self.renderthread.image_folder = folder_path
        if folder_path:
            self.renderthread.get_images() # get all the images in thread

    def add_Image_names(self, images:list[str]):
        self.current_list.clear()
        for image in images:
            item = QListWidgetItem(os.path.basename(image))
            item.setData(Qt.UserRole, image)
            self.current_list.addItem(item)
        self.current_list.itemClicked.connect(self.on_item_clicked)
    
    def clear_all_images(self):
        if self.current_page == self.page1:
            self.current_list.clear()
            
    def server_project_window(self):
        self.server_project_objects_window = ServerProjectDialog(self)
        self.server_project_objects_window.request_signal.connect(self.renderthread.get_server_objects)
        self.server_project_objects_window.delete_signal.connect(self.renderthread.delete_server_object)
        self.renderthread.objects_ready.connect(self.server_project_objects_window.disp_scenes)
        self.server_project_objects_window.selected_scene_signal.connect(self.renderthread.set_scene)
        self.server_project_objects_window.show()
        self.server_project_objects_window.request_signal.emit()

    def on_item_clicked(self, item):
        if self.current_page == self.page1:
            image = item.data(Qt.UserRole)
            self.renderthread.set_current_image(image)
        elif self.current_page == self.page2:
            index = item.data(Qt.UserRole)
            if index == self._current_label_index:
                self.renderthread.hide_label_bbox()
                self._current_label_index = -1
            else:
                self.renderthread.show_label_bbox(index)
                self._current_label_index = index
        elif self.current_page == self.page3:
            pass
        
    def set_image(self):
        self.renderthread.set_image()
    
    def set_3DGS_RGB(self):
        self.renderthread.set_3DGS_RGB()
        
    def set_pcd(self):
        self.pcd_loader_dialog = Message_Dialog("正在加载点云...", self)
        self.pcd_loader_dialog.setWindowTitle("加载点云")
        self.pcd_loader_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.renderthread.pcd_loading_started.connect(self.pcd_loader_dialog.show)
        self.renderthread.pcd_loading_finished.connect(self.pcd_loader_dialog.close)
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
            
        if hasattr(self, 'label_panel'):
            self.label_panel.update_labels(self.renderthread.pcd_labels)
        
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
            if self.current_page == self.page2:
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
            else:
                self.mouse_pressed = True
                self.last_mouse_pos = event.pos()
            return True
        elif event.type() == QEvent.MouseMove and self.mouse_pressed:
            if self.current_page == self.page2:
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
            else:
                dir = event.pos() - self.last_mouse_pos
                self.last_mouse_pos = event.pos()
                self.renderthread.rotate_in_dir(np.array([dir.x(), dir.y()]))
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            if self.current_page == self.page2:
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
            else:
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
    
    def start_server_training(self): # upload files
        self.uploaded = False
        self.upload_progressdialog = SfM_ProgressDialog(
            "上传中...",
            "取消",
            0,
            100,
            self
        )
        self.upload_progressdialog.setWindowTitle("上传本地文件")
        self.upload_progressdialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.upload_progressdialog.cancelClicked.connect(self.on_cancel_upload)
        self.renderthread.upload_progress.connect(
            self.upload_progressdialog.setValue
        )
        self.renderthread.upload_finished.connect(
            self.on_upload_finished
        )
        self.renderthread.upload_canceled.connect(self.upload_progressdialog.close)
        self.renderthread.uploaded.connect(self.on_uploaded)
        self.upload_progressdialog.show()
        self.renderthread.upload_folder()
        
    def training(self): # start training
        if self.uploaded:
            self.training_progressdialog = SfM_ProgressDialog(
                "正在训练...",
                "取消",
                0,
                100,
                self
            )
            self.training_progressdialog.setWindowTitle("正在训练...")
            self.training_progressdialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.training_progressdialog.cancelClicked.connect(self.on_cancel_training)
            self.renderthread.train_progress.connect(
                self.training_progressdialog.setValue
            )
            self.renderthread.train_finished.connect(
                self.on_train_finished
            )
            self.renderthread.train_canceled.connect(self.training_progressdialog.close)
            self.training_progressdialog.show()
            self.renderthread.scene_train()
            
    def on_train_finished(self):
        self.training_progressdialog.close()
        self.training_progressdialog.deleteLater()
        
    def on_cancel_training(self):
        self.training_progressdialog.setLabelText("正在取消...")
        btn = self.training_progressdialog.findChild(QPushButton)
        if btn:
            btn.setEnabled(False)
        QApplication.processEvents()
        QTimer.singleShot(0, self.renderthread.train_cancel)
        
    def on_cancel_upload(self):
        self.uploaded = False
        self.upload_progressdialog.setLabelText("正在取消...")
        btn = self.upload_progressdialog.findChild(QPushButton)
        if btn:
            btn.setEnabled(False)
        QApplication.processEvents()
        QTimer.singleShot(0, self.renderthread.upload_cancel)
    
    def on_upload_finished(self):
        self.uploaded = True
        if self.upload_progressdialog:
            self.upload_progressdialog.close()
        self.training()
        
    def on_uploaded(self):
        btn = self.upload_progressdialog.findChild(QPushButton)
        if btn:
            btn.setEnabled(False)
        QApplication.processEvents()
        
    def start_sfm(self):
        self.sfm_progressdialog = SfM_ProgressDialog("Running SfM...", "Cancel", 0, 100, self)
        self.sfm_progressdialog.setWindowTitle("SfM Progress")
        self.sfm_progressdialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.sfm_progressdialog.cancelClicked.connect(self.on_cancel_sfm)
        self.sfm_progressdialog.show()
        
        self.renderthread.sfm_progress.connect(self.sfm_progressdialog.setValue)
        self.renderthread.sfm_canceled.connect(self.sfm_progressdialog.close)
        self.renderthread.sfm_finished.connect(self.on_sfm_finished)
        
        self.renderthread.start_sfm()
        
    def on_cancel_sfm(self):
        self.sfm_progressdialog.setLabelText("正在结束...")
        btn = self.sfm_progressdialog.findChild(QPushButton)
        if btn:
            btn.setEnabled(False)
        QApplication.processEvents()
        QTimer.singleShot(0, self.renderthread.sfm_stop)
    
    def on_sfm_finished(self):
        self.sfm_progressdialog.close()
        
    def add_user_message(self, text):
        bubble = MessageBubble(text, True)
        self.chat_layout.addWidget(bubble)
        
    def start_bot_message(self):
        self.current_bot_bubble = MessageBubble("", False)
        self.chat_layout.addWidget(self.current_bot_bubble)
        self.current_text = ""
        
    def update_bot_message(self, token):
        self.current_text += token
        self.current_bot_bubble.update_text(self.current_text)
        
        # scroll automatically
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )
        
    def send_message(self):
        text = self.chat_input.text().strip()
        if not text:
            return
        self.chat_input.clear()
        self.add_user_message(text)
        self.renderthread.agentthread.send_message_signal.emit(text)
        
    def set_thread_user_id(self):
        self.renderthread.user_id = self.user_id
        
    def open_project_window(self):
        self.project_window = CreateProjectWindow(self)
        self.project_window.project_selected.connect(
            self.renderthread.on_project_selected
        )
        self.project_window.show()
        
    def open_video_window(self):
        if self.renderthread.project_set is False:
            QMessageBox.warning(None, "Warning", "当前无项目！")
            return
        self.video_window = VideoWindow(os.path.join(self.renderthread.project_folder, "temp", "video_images"), self)
        self.video_window.finish_signal.connect(self.renderthread.video_frames_got)
        self.video_window.show()
        
    def on_delete_selected_image(self):
        if self.current_page != self.page1:
            return
        row = self.current_list.currentRow()
        if row < 0:
            return
        self.renderthread.remove_image(row)
        
    def on_delete_all_images(self):
        if self.current_page != self.page1:
            return
        self.renderthread.remove_all_images()
        
    def on_delete_selected_label(self):
        if self.current_page != self.page2:
            return
        item = self.current_list.currentItem()
        if item is None:
            return
        index = item.data(Qt.UserRole)
        self.renderthread.hide_label_bbox()
        self._current_label_index = -1
        del self.renderthread.pcd_labels[index]
        self.renderthread.agentthread.set_pcd_labels(self.renderthread.pcd_labels)
        self.renderthread.project.set_pcd_labels(self.renderthread.pcd_labels)
        self.update_current_list()
        
    def on_delete_all_labels(self):
        if self.current_page != self.page2:
            return
        self.renderthread.hide_label_bbox()
        self._current_label_index = -1
        self.renderthread.pcd_labels.clear()
        self.renderthread.agentthread.set_pcd_labels([])
        self.renderthread.project.set_pcd_labels([])
        self.update_current_list()