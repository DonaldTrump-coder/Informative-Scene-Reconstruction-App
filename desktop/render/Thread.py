from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
import numpy as np
from desktop.render.rendermode import Rendering_mode, Status_mode
from desktop.render.cameras import get_init_camera
import os
import cv2
from PyQt5.QtWidgets import QFileDialog
from desktop.Colmap.reconstructor import constructor
from desktop.project import rec_project
from desktop.Colmap.pcd import PCD, PCD_label

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
    sparse_folder = None
    pcd = None
    pcd_labels = [] # point cloud labels list
    
    display_mode = Status_mode.FREE
    select_bbox = None # (left, top, right, bottom) in glwidget
    glwidget_width = None
    glwidget_height = None
    scale = None
    gl_x0 = None
    gl_y0 = None
    alpha = 0.45
    display_bbox = True
    left_u = None
    top_v = None
    right_u = None
    bottom_v = None
    
    # thread tools
    mutex = QMutex()
    cond = QWaitCondition()
    paused = False

    def __init__(self):
        super().__init__()
        self.rendering_mode = Rendering_mode.NONE # Initialized Rendering Mode
        self.running=True
        self.fx = 933
        self.fy = 933
        self.cx = 960
        self.cy = 540
        self.K = np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]])
        self.project = rec_project()

        self.project_set = False

    def set_project_path(self):
        # set path from a filedialog
        self.project_folder = QFileDialog.getExistingDirectory(None, "请选择图像文件夹")
        if self.project_folder:
            self.reconstructor = constructor(os.path.join(self.project_folder, "project.db"))
            self.project_set = True
            self.sparse_folder = os.path.join(self.project_folder, "output", "sparse")
            
    def open_project(self):
        self.project_folder = QFileDialog.getExistingDirectory(None, "请选择项目文件夹")
        if self.project_folder:
            self.sparse_folder = os.path.join(self.project_folder, "output", "sparse")

    def set_3DGS_RGB(self):
        self.rendering_mode = Rendering_mode.RENDERING

    def set_image(self):
        self.rendering_mode = Rendering_mode.IMAGE
        
    def set_pcd(self):
        if self.pcd is not None:
            self.rendering_mode = Rendering_mode.PCD
        else:
            self.pcd = PCD(
                os.path.join(self.sparse_folder, "0", "cameras.bin"),
                os.path.join(self.sparse_folder, "0", "images.bin"),
                os.path.join(self.sparse_folder, "0", "points3D.bin")
                )
            self.R, self.T = self.pcd.get_extrinsics_init()
            self.pcd.set_camera(self.R, self.T, self.H, self.W, self.K)
            self.rendering_mode = Rendering_mode.PCD

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
        self.T = -self.R @ (-self.R.T@self.T - step*dir)
        
    def move_left(self, step=0.1):
        dir = self.R[0 , :]
        self.T = -self.R @ (-self.R.T@self.T + step*dir)

    def move_forward(self, step=0.1):
        dir = self.R[2 , :]
        self.T = -self.R @ (-self.R.T@self.T + step*dir)

    def move_back(self, step = 0.1):
        dir = self.R[2 , :]
        self.T = -self.R @ (-self.R.T@self.T - step*dir)
        
    def rotate_in_z_clockwise(self, step = 0.01):
        c, s = np.cos(step), np.sin(-step)
        Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        C = -self.R.T @ self.T
        self.R = Rz @ self.R
        self.T = -self.R @ C
        
    def rotate_in_z_anticlockwise(self, step = 0.01):
        c, s = np.cos(step), np.sin(step)
        Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        C = -self.R.T @ self.T
        self.R = Rz @ self.R
        self.T = -self.R @ C
        
    def rotate(self, dx, dy, sensitivity=0.01):
        yaw   = dx * sensitivity # left-right
        pitch = dy * sensitivity # up-down
        Ry = self.rotation_y(yaw)
        Rx = self.rotation_x(-pitch)
        
        forward = self.R.T @ np.array([0,0,1])
        C = -self.R.T @ self.T
        dist = np.linalg.norm(C - self.pcd.center)
        pivot = C + forward * dist * 0.01
        pivot_c = self.R @ pivot + self.T
        
        self.R = Ry @ Rx @ self.R
        self.T = pivot_c - self.R @ pivot
        
    def rotation_x(self, angle):
        return np.array([
        [1, 0, 0],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle),  np.cos(angle)]
    ])
        
    def rotation_y(self, angle):
        return np.array([
        [ np.cos(angle), 0, np.sin(angle)],
        [0, 1, 0],
        [-np.sin(angle), 0, np.cos(angle)]
    ])

    def run(self):
        self.R, self.T = get_init_camera(self.point_min,self.point_max)
        image = None
        while self.running:
            self.mutex.lock()
            while self.paused:
                self.cond.wait(self.mutex)
            
            select_bbox = None if self.select_bbox is None else tuple(self.select_bbox)
            R = self.R.copy() if self.R is not None else None
            T = self.T.copy() if self.T is not None else None
            K = self.K.copy() if self.K is not None else None
            gl_x0 = self.gl_x0
            gl_y0 = self.gl_y0
            scale = self.scale
            display_bbox = self.display_bbox
            alpha = self.alpha
            H = self.H
            W = self.W
            
            self.mutex.unlock()
            
            # rendering cores:
            if self.rendering_mode is Rendering_mode.NONE or self.rendering_mode is Rendering_mode.IMAGE:
                pass
            if self.rendering_mode is Rendering_mode.PCD:
                self.pcd.set_camera(R, T, H, W, K)
                if select_bbox is not None:
                    left, top, right, bottom = select_bbox
                    left_u = max((left - gl_x0) / scale, 0)
                    top_v = max((top - gl_y0) / scale, 0)
                    right_u = min((right - gl_x0) / scale, W)
                    bottom_v = min((bottom - gl_y0) / scale, H)
                    
                    image = self.pcd.render()
                    
                    if self.display_bbox:
                        overlay = image.copy()
                        roi = overlay[int(top_v):int(bottom_v), int(left_u):int(right_u)].astype(np.float32)
                        roi[..., 0] = roi[..., 0] * (1 - alpha) + 255 * alpha
                        roi[..., 1] = roi[..., 1] * (1 - alpha)
                        roi[..., 2] = roi[..., 2] * (1 - alpha)
                        image[int(top_v):int(bottom_v), int(left_u):int(right_u), :] = roi.astype(np.uint8)
                else:
                    image = self.pcd.render()
                    
                self.frame_ready.emit(image)
        if self.pcd is not None:
            self.pcd.close()
            
    def pause(self):
        self.mutex.lock()
        self.paused = True
        self.mutex.unlock()
        
    def resume(self):
        self.mutex.lock()
        self.paused = False
        self.cond.wakeAll()
        self.mutex.unlock()

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
            
    def add_new_select(self):
        if self.select_bbox is None:
            return
        
        self.pause()
        self.mutex.lock()
        select_bbox = self.select_bbox
        R = self.R.copy() if self.R is not None else None
        T = self.T.copy() if self.T is not None else None
        K = self.K.copy() if self.K is not None else None
        self.mutex.unlock()
        
        left, top, right, bottom = select_bbox
        left_u = max((left - self.gl_x0) / self.scale, 0)
        top_v = max((top - self.gl_y0) / self.scale, 0)
        right_u = min((right - self.gl_x0) / self.scale, self.W)
        bottom_v = min((bottom - self.gl_y0) / self.scale, self.H)
        self.pcd.add_new_select(R, T, self.H, self.W, K, left_u, top_v, right_u, bottom_v)
        
        self.resume()
        
    def add_new_unselect(self):
        if self.select_bbox is None:
            return
        
        self.pause()
        self.mutex.lock()
        select_bbox = self.select_bbox
        R = self.R.copy() if self.R is not None else None
        T = self.T.copy() if self.T is not None else None
        K = self.K.copy() if self.K is not None else None
        self.mutex.unlock()
        
        left, top, right, bottom = select_bbox
        left_u = max((left - self.gl_x0) / self.scale, 0)
        top_v = max((top - self.gl_y0) / self.scale, 0)
        right_u = min((right - self.gl_x0) / self.scale, self.W)
        bottom_v = min((bottom - self.gl_y0) / self.scale, self.H)
        self.pcd.add_new_unselect(R, T, self.H, self.W, K, left_u, top_v, right_u, bottom_v)
        
        self.resume()
        
    def select(self):
        if self.select_bbox is None:
            return
        
        self.pause()
        self.mutex.lock()
        select_bbox = self.select_bbox
        R = self.R.copy() if self.R is not None else None
        T = self.T.copy() if self.T is not None else None
        K = self.K.copy() if self.K is not None else None
        self.select_bbox = None
        self.mutex.unlock()
        
        left, top, right, bottom = select_bbox
        left_u = max((left - self.gl_x0) / self.scale, 0)
        top_v = max((top - self.gl_y0) / self.scale, 0)
        right_u = min((right - self.gl_x0) / self.scale, self.W)
        bottom_v = min((bottom - self.gl_y0) / self.scale, self.H)
        self.pcd.select(R, T, self.H, self.W, K, left_u, top_v, right_u, bottom_v)
        
        self.resume()

    def unselect(self):
        if self.select_bbox is None:
            return
        
        self.pause()
        self.mutex.lock()
        select_bbox = self.select_bbox
        R = self.R.copy() if self.R is not None else None
        T = self.T.copy() if self.T is not None else None
        K = self.K.copy() if self.K is not None else None
        self.select_bbox = None
        self.mutex.unlock()
        
        left, top, right, bottom = select_bbox
        left_u = max((left - self.gl_x0) / self.scale, 0)
        top_v = max((top - self.gl_y0) / self.scale, 0)
        right_u = min((right - self.gl_x0) / self.scale, self.W)
        bottom_v = min((bottom - self.gl_y0) / self.scale, self.H)
        
        self.pcd.unselect(R, T, self.H, self.W, K, left_u, top_v, right_u, bottom_v)
        self.resume()
        
    def unselect_all(self):
        self.pause()
        self.mutex.lock()
        self.mutex.unlock()
        
        self.pcd.unselect_all()
        self.resume()
        
    def add_label(self, name, description):
        xmin, ymin, zmin, xmax, ymax, zmax = self.pcd.get_label_bbox()
        self.pcd_labels.append(PCD_label(name, description, (xmin, ymin, zmin, xmax, ymax, zmax)))