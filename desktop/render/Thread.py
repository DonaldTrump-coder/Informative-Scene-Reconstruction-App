from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from desktop.render.rendermode import Rendering_mode
from desktop.render.cameras import get_init_camera
import os
import cv2
from PyQt5.QtWidgets import QFileDialog
from desktop.Colmap.reconstructor import constructor
from desktop.project import rec_project

class RenderThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    add_image_list = pyqtSignal(list)
    parser = None
    camera = None
    R = None # [3x3]
    T = None # [3x1]
    K = None # [3x3]
    point_min = None
    point_max = None
    W = 1920
    H = 1080

    image_folder = None
    images = [] # images path list
    current_image = None # current image path

    def __init__(self):
        super().__init__()
        self.rendering_mode = Rendering_mode.NONE # Initialized Rendering Mode
        self.running=True
        self.fx = 1659
        self.fy = 933
        self.cx = 960
        self.cy = 540
        self.project = rec_project()

        self.project_set = False

    def set_project_path(self):
        # set path from a filedialog
        self.project_folder = QFileDialog.getExistingDirectory(None, "请选择图像文件夹")
        if self.project_folder:
            self.reconstructor = constructor(os.path.join(self.project_folder, "project.db"))
            self.project_set = True

    def set_3DGS_RGB(self):
        self.rendering_mode = Rendering_mode.RENDERING

    def set_image(self):
        self.rendering_mode = Rendering_mode.IMAGE

    def get_images(self):
        supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.ppm']
        for filename in os.listdir(self.image_folder):
            file_path = os.path.join(self.image_folder,filename)
            if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in supported_extensions):
                self.images.append(file_path)
        self.current_image = self.images[0]
        self.set_simple_image()
        self.add_image_list.emit(self.images)

    def set_current_image(self, image):
        self.current_image = image
        self.set_simple_image()

    def move_right(self, step=0.1):
        dir = self.R[0 , :]
        self.T = -self.R @ (-self.R.T@self.T + step*dir)
    def move_left(self, step=0.1):
        dir = self.R[0 , :]
        self.T = -self.R @ (-self.R.T@self.T - step*dir)

    def move_forward(self, step=0.1):
        dir = self.R[2 , :]
        self.T = -self.R @ (-self.R.T@self.T + step*dir)

    def move_back(self, step = 0.1):
        dir = self.R[2 , :]
        self.T = -self.R @ (-self.R.T@self.T - step*dir)

    def run(self):
        self.R, self.T = get_init_camera(self.point_min,self.point_max)
        while self.running:
            # rendering cores:
            if self.rendering_mode is Rendering_mode.NONE or self.rendering_mode is Rendering_mode.IMAGE:
                pass

    def set_simple_image(self):
        data = np.fromfile(self.current_image, dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # downsample to height-500
        
        """target_height = 400
        h, w = image.shape[:2]
        if h>target_height:
            scale = target_height / h
            new_w = int(w * scale)
            new_h = target_height
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_NEAREST)"""

        self.frame_ready.emit(image)

    def stop(self):
        self.running=False
        self.wait()

    def start_sfm(self):
        # sfm reconstruction with images
        if self.project_set:
            self.reconstructor.add_images(self.images)
            self.reconstructor.sfm()