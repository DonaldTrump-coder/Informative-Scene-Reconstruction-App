from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition, QObject, QTimer, pyqtSlot
import numpy as np
from desktop.render.rendermode import Rendering_mode, Status_mode
from desktop.render.cameras import get_init_camera
import os
import cv2
from PyQt5.QtWidgets import QFileDialog
from desktop.Colmap.reconstructor import constructor
from desktop.project import rec_project
from desktop.Colmap.pcd import PCD, PCD_label
import requests
from desktop.Colmap.folder import temp_sparse
import math
import websocket
import struct
import json
from desktop.LLM.AgentThread import AgentThread
from server.webtools import is_server_running
from desktop.render.WSthread import WSThread
from PyQt5.QtWidgets import QMessageBox
import time
import av
import shutil

class RenderThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    add_image_list = pyqtSignal(list)
    clear_image_list = pyqtSignal()
    start_new_signal = pyqtSignal()
    update_text_signal = pyqtSignal(str)
    sfm_progress = pyqtSignal(int)
    sfm_finished = pyqtSignal()
    sfm_canceled = pyqtSignal()
    upload_progress = pyqtSignal(int)
    upload_finished = pyqtSignal()
    upload_canceled = pyqtSignal()
    uploaded = pyqtSignal() # Uploaded to server but not finished
    train_progress = pyqtSignal(int)
    train_finished = pyqtSignal()
    train_canceled = pyqtSignal()
    pcd_loading_started = pyqtSignal()
    pcd_loading_finished = pyqtSignal()
    request_project_path = pyqtSignal()
    objects_ready = pyqtSignal(list)
    update_list = pyqtSignal()
    parser = None
    camera = None
    R = None # [3x3]
    T = None # [3x1]
    K = None # [3x3]
    point_min = None
    point_max = None
    W = 960
    H = 540

    image_folder = None
    images = [] # images path list
    current_image = None # current image path
    sparse_folder = None
    pcd = None
    pcd_labels = [] # point cloud labels list
    project_folder = None
    
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
    
    local2server_url = ""
    rendering_url = ""
    server_scene_id = None
    server_running = True
    user_id = None
    
    # thread tools
    mutex = QMutex()
    cond = QWaitCondition()
    paused = False
    
    # progress tools
    sparse = False
    gs = False

    def __init__(self):
        super().__init__()
        self.rendering_mode = Rendering_mode.NONE # Initialized Rendering Mode
        self.running=True
        self.fx = 933
        self.fy = 933
        self.cx = self.W / 2
        self.cy = self.H / 2
        self.K = np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]])

        self.project_set = False
        self.agentthread = AgentThread()
        self.agentthread.start_new_signal.connect(self.start_new_response)
        self.agentthread.update_text_signal.connect(self.update_message)
        self.agentthread.start()

    def set_project_path(self):
        self.request_project_path.emit()
    
    def on_project_selected(self, project_folder, project_name):
        # set path from a filedialog
        # create a scene in server
        if project_folder:
            self.project_folder = project_folder
            create_url = self.local2server_url + "/user/create_object"
            params = {
                "user_id": self.user_id,
                "object_name": project_name,
                "project_path": project_folder
            }
            r = requests.post(create_url, params=params)
            self.server_scene_id = r.json()["object_id"] # object id of the created scene
        
            self.reconstructor = constructor(os.path.join(self.project_folder, "reconstructor.db"))
            self.project_set = True
            self.sparse_folder = os.path.join(self.project_folder, "output", "sparse")
            
            self.project = rec_project()
            self.project.set_path(self.project_folder, self.server_scene_id)
            
    def open_project(self):
        self.project_folder = QFileDialog.getExistingDirectory(None, "请选择项目文件夹")
        if self.project_folder:
            self.project = rec_project()
            self.project.read_from_path(self.project_folder)
            self.server_scene_id = self.project.object_id
            self.reconstructor = constructor(os.path.join(self.project_folder, "reconstructor.db"))
            self.sparse_folder = os.path.join(self.project_folder, "output", "sparse")
            self.project_set = True
            
            self.images = []
            self.clear_image_list.emit()
            self.image_folder = os.path.join(self.project_folder, "temp", "images")
            if os.path.isdir(self.image_folder):
                self.get_images()
            self.get_project_labels()
            self.update_list.emit()
                
    def open_project_from_path(self, project_folder):
        if project_folder:
            self.project_folder = project_folder
            self.project = rec_project()
            self.project.read_from_path(self.project_folder)
            self.server_scene_id = self.project.object_id
            self.reconstructor = constructor(os.path.join(self.project_folder, "reconstructor.db"))
            self.sparse_folder = os.path.join(self.project_folder, "output", "sparse")
            self.project_set = True
            
            self.images = []
            self.clear_image_list.emit()
            self.image_folder = os.path.join(self.project_folder, "temp", "images")
            if os.path.isdir(self.image_folder):
                self.get_images()
            self.get_project_labels()
            self.update_list.emit()
            
    def video_frames_got(self, video_name: str):
        self.image_folder = os.path.join(self.project_folder, "temp", "video_images", video_name)
        self.get_images()

    def set_3DGS_RGB(self):
        if self.project_set is False:
            QMessageBox.warning(None, "Warning", "当前未设置项目！")
            return
        if self.project.gs is False:
            QMessageBox.warning(None, "Warning", "还未进行实景生成！")
            return
        self.rendering_mode = Rendering_mode.RENDERING

    def set_image(self):
        self.rendering_mode = Rendering_mode.IMAGE
        
    def set_pcd(self): # Setting pointcloud mode when tab is changed
        if self.pcd is not None:
            self.rendering_mode = Rendering_mode.PCD
        else:
            if self.project_set is False:
                QMessageBox.warning(None, "Warning", "当前未设置项目！")
                return
            if self.project.sparse is False:
                QMessageBox.warning(None, "Warning", "还未进行稀疏重建！")
                return
            self.pcd_loading_started.emit()
            self.pcd_loading_thread = QThread()
            self.pcd_loader = PCD_Loader(self.sparse_folder, self.H, self.W, self.K)
            self.pcd_loader.moveToThread(self.pcd_loading_thread)
            self.pcd_loading_thread.started.connect(self.pcd_loader.run)
            self.pcd_loader.finished.connect(self.on_pcd_loaded)
            self.pcd_loader.finished.connect(self.pcd_loading_thread.quit)
            self.pcd_loading_thread.start()
    
    def on_pcd_loaded(self, pcd, R, T):
        self.pcd = pcd
        self.R = R
        self.T = T
        self.rendering_mode = Rendering_mode.PCD
        self.pcd_loading_finished.emit()

    def get_images(self):
        supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.ppm']
        for filename in os.listdir(self.image_folder):
            file_path = os.path.join(self.image_folder,filename)
            if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in supported_extensions):
                self.images.append(file_path)
        if not self.images:
            return
        self.current_image = self.images[0]
        self.set_simple_image()
        self.add_image_list.emit(self.images)

    def set_current_image(self, image):
        self.current_image = image
        self.set_simple_image()

    def move_right(self, step=0.1):
        if self.rendering_mode is Rendering_mode.RENDERING:
            step = step * 0.2
        if self.R is None:
            return
        dir = self.R[0 , :]
        if self.rendering_mode is Rendering_mode.PCD:
            self.T = -self.R @ (-self.R.T@self.T - step*dir)
        else:
            self.T = -self.R @ (-self.R.T@self.T + step*dir)
        
    def move_left(self, step=0.1):
        if self.rendering_mode is Rendering_mode.RENDERING:
            step = step * 0.2
        if self.R is None:
            return
        dir = self.R[0 , :]
        if self.rendering_mode is Rendering_mode.PCD:
            self.T = -self.R @ (-self.R.T@self.T + step*dir)
        else:
            self.T = -self.R @ (-self.R.T@self.T - step*dir)

    def move_forward(self, step=0.1):
        if self.rendering_mode is Rendering_mode.RENDERING:
            step = step * 0.2
        if self.R is None:
            return
        dir = self.R[2 , :]
        self.T = -self.R @ (-self.R.T@self.T + step*dir)

    def move_back(self, step = 0.1):
        if self.rendering_mode is Rendering_mode.RENDERING:
            step = step * 0.2
        if self.R is None:
            return
        dir = self.R[2 , :]
        self.T = -self.R @ (-self.R.T@self.T - step*dir)
        
    def rotate_in_dir(self, _2D_dir, step=math.pi/180):
        if self.R is None:
            return
        _2D_dir = _2D_dir / np.linalg.norm(_2D_dir)
        step1 = step * np.sign(_2D_dir[0])
        step2 = -step * np.sign(_2D_dir[1])
        
        c1, s1 = np.cos(step1), np.sin(step1)
        c2, s2 = np.cos(step2), np.sin(step2)
        
        R1 = np.array([
            [c1, 0, -s1],
            [0, 1, 0],
            [s1, 0, c1]
        ])
        R2 = np.array([
            [1, 0, 0],
            [0, c2, s2],
            [0, -s2, c2]
        ])
        
        R_ = R2 @ R1
        
        R = self.R
        self.R = R_ @ R
        self.T = self.R @ (R.T @ self.T)
        
    def rotate_in_z_clockwise(self, step = 0.01):
        if self.R is None:
            return
        c, s = np.cos(step), np.sin(-step)
        Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        C = -self.R.T @ self.T
        self.R = Rz @ self.R
        self.T = -self.R @ C
        
    def rotate_in_z_anticlockwise(self, step = 0.01):
        if self.R is None:
            return
        c, s = np.cos(step), np.sin(step)
        Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        C = -self.R.T @ self.T
        self.R = Rz @ self.R
        self.T = -self.R @ C
        
    def rotate(self, dx, dy, sensitivity=0.01):
        if self.R is None:
            return
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
        if is_server_running(self.local2server_url):
            self.ws = WSThread(self.rendering_url.replace("http", "ws"))
        else:
            self.server_running = False
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
            if R is None or T is None or K is None:
                continue
            
            # rendering cores:
            if self.rendering_mode is Rendering_mode.NONE or self.rendering_mode is Rendering_mode.IMAGE:
                continue
            if self.rendering_mode is Rendering_mode.PCD:
                if self.project.sparse is False:
                    continue
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
                    
            elif self.rendering_mode is Rendering_mode.RENDERING:
                self.agentthread.set_coordinate(None, None)
                if not self.server_running:
                    continue
                if self.project.gs is False:
                    continue
                self.agentthread.set_coordinate(R, T)
                payload = {
                    "user_id": self.user_id,
                    "object_id": self.server_scene_id,
                    "K": K.tolist(),
                    "R": R.tolist(),
                    "t": T.tolist(),
                    "H": H,
                    "W": W
                }
                self.ws.send_payload(payload)
                data = self.ws.get_result()
                if data is not None:
                    img = cv2.imdecode(
                        np.frombuffer(data, np.uint8),
                        cv2.IMREAD_COLOR
                    )
                    self.frame_ready.emit(img)
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
        if self.rendering_mode is not Rendering_mode.IMAGE and self.rendering_mode is not Rendering_mode.NONE:
            return
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
        self.agentthread.stop()
        self.running=False
        self.wait()
        
    # SFM control
    def start_sfm(self):
        # sfm reconstruction with images
        if self.project_set:
            self.sfm_thread = QThread()
            self.sfm_worker = SFMWorker(self.reconstructor, self.images, self.project_folder, self.sparse_folder)
            self.sfm_worker.moveToThread(self.sfm_thread)
            
            self.sfm_worker.progress.connect(self.sfm_progress.emit)
            self.sfm_worker.finished.connect(self._on_sfm_finished)
            self.sfm_worker.canceled.connect(self._on_sfm_canceled)
            self.sfm_thread.started.connect(self.sfm_worker.run)
            self.sfm_worker.finished.connect(self.sfm_thread.quit)
            self.sfm_worker.finished.connect(self.sfm_worker.deleteLater)
            self.sfm_thread.finished.connect(self.sfm_thread.deleteLater)
            
            self.sfm_thread.start()
            
    def sfm_stop(self):
        time.sleep(0.5)
        if self.sfm_worker:
            self.sfm_worker.stop()
        
        if self.sfm_thread and self.sfm_thread.isRunning():
            self.sfm_thread.quit()
    
    def _on_sfm_finished(self):
        if self.project_set is True:
            self.project.set_sparse()
        self.sfm_finished.emit()
        
    def _on_sfm_canceled(self):
        self.sfm_canceled.emit()
    
    # PCD Selection
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
        self.agentthread.set_pcd_labels(self.pcd_labels)
        self.project.set_pcd_labels(self.pcd_labels)
        
    def get_project_labels(self):
        self.pcd_labels = self.project.pcd_labels.copy()
        self.agentthread.set_pcd_labels(self.pcd_labels)
        
    def upload_folder(self):
        self.upload_thread = QThread()
        self.upload_worker = UploadWorker(
            self.user_id,
            self.server_scene_id,
            self.project_folder,
            self.local2server_url
        )
        self.upload_worker.moveToThread(self.upload_thread)
        self.upload_thread.started.connect(self.upload_worker.run)
        self.upload_worker.progress.connect(self.upload_progress.emit)
        self.upload_worker.finished.connect(self._upload_finished)
        self.upload_worker.canceled.connect(self._upload_canceled)
        self.upload_worker.uploaded.connect(self.uploaded.emit)
        self.upload_thread.start()
        
    def _upload_canceled(self):
        self.upload_canceled.emit()
        self.upload_thread.quit()
    
    def upload_cancel(self):
        self.upload_worker.stop()
    
    def _upload_finished(self, status):
        if status == "uploaded":
            if self.project_set is True:
                self.project.set_uploaded()
        self.upload_finished.emit()
        self.upload_thread.quit()
        
    def scene_train(self):
        def check_ws_and_train():
            if self.ws.ws is not None:
                self.train_timer.stop()
            else:
                return
            url = self.local2server_url + "/train"
            params = {
                "user_id": self.user_id,
                "object_id": self.server_scene_id
            }
            self.train_monitor_thread = QThread()
            self.train_monitor = TrainMonitorWorker(self.local2server_url, params)
            self.train_monitor.moveToThread(self.train_monitor_thread)
            self.train_monitor_thread.started.connect(self.train_monitor.run)
            self.train_monitor.progress.connect(self.train_progress.emit)
            self.train_monitor.finished.connect(self._train_finished)
            self.train_monitor.canceled.connect(self._train_canceled)
            self.train_monitor_thread.start()
            requests.post(url, params=params) # send training signal

        self.train_timer = QTimer()
        self.train_timer.setInterval(500)
        self.train_timer.timeout.connect(check_ws_and_train)
        self.train_timer.start()
        
    def _train_canceled(self):
        self.train_canceled.emit()
        self.train_monitor_thread.quit()
        
    def _train_finished(self):
        if self.project_set is True:
            self.project.set_gs()
        self.train_finished.emit()
        self.train_monitor_thread.quit()
        
    def train_cancel(self):
        self.train_monitor.stop()
        
    def start_new_response(self):
        self.start_new_signal.emit()
        
    def update_message(self, token):
        self.update_text_signal.emit(token)
        
    @pyqtSlot()
    def get_server_objects(self): # find all objects of the user on server
        if self.user_id is not None:
            try:
                params = {"user_id": self.user_id}
                url = self.local2server_url + "/user/objects"
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    self.objects_ready.emit(data)
            except Exception as _:
                return
    
    @pyqtSlot(list)
    def delete_server_object(self, object_id_list):
        if self.user_id is not None:
            try:
                params = [
                    ("user_id", self.user_id)
                ]
                for oid in object_id_list:
                    params.append(
                        ("object_ids", oid)
                    )
                
                url = self.local2server_url + "/user/delete_object"
                response = requests.delete(
                    url,
                    params=params
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.get_server_objects()
            except Exception as _:
                return
            
    def set_scene(self, scene_data):
        project_folder = scene_data["project_path"]
        object_id = scene_data["object_id"]
        if os.path.exists(os.path.join(project_folder, "project.db")):
            self.open_project_from_path(project_folder)
            self.server_scene_id = object_id
        
class SFMWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    canceled = pyqtSignal()
    
    def __init__(self, reconstructor, images, project_folder, sparse_folder):
        super().__init__()
        self.reconstructor = reconstructor
        self.reconstructor.running = True
        self.images = images
        self.project_folder = project_folder
        self.sparse_folder = sparse_folder
        self._is_running = True
        
    def run(self):
        def progress_callback(step, total):
            if not self._is_running:
                raise Exception("Canceled")
            percent = int(step / total * 100)
            self.progress.emit(percent)
            
        if self._is_running:
            self.reconstructor.add_images(self.images)
        else:
            self.canceled.emit()
            return
        
        if self._is_running:
            self.reconstructor.sfm(progress_callback)
        else:
            self.canceled.emit()
            return
        
        if self._is_running:
            temp_sparse(os.path.join(self.project_folder, "temp"), self.sparse_folder)
        else:
            self.canceled.emit()
            return
        
        self.finished.emit()
        
    def stop(self):
        self._is_running = False
        self.reconstructor.running = False
        
class UploadWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    canceled = pyqtSignal()
    uploaded = pyqtSignal()
    
    def __init__(self, user_id, object_id, project_folder, url):
        super().__init__()
        self.user_id = user_id
        self.object_id = object_id
        self.project_folder = project_folder
        self.url = url
        self._running = True
    
    def run(self):
        temp_folder = os.path.join(self.project_folder, "temp")
        file_list = []
        for root, _, files in os.walk(temp_folder):
            for file in files:
                full = os.path.join(root, file)
                file_list.append(full)
        total = len(file_list)
        files_to_upload = []
        for i, full_path in enumerate(file_list):
            if not self._running:
                self.canceled.emit()
                return
            rel = os.path.relpath(full_path, temp_folder)
            files_to_upload.append(
                ("files", (rel.replace("\\","/"), open(full_path,"rb")))
            )
            percent = int((i+1)/total*100)
            self.progress.emit(percent)
        self.uploaded.emit()
        r = requests.post(self.url + "/upload",
                          files=files_to_upload,
                          data={
                              "user_id": self.user_id,
                              "object_id": self.object_id
                          })
        status = r.json()["status"]
        self.progress.emit(100)
        self.finished.emit(status)
    
    def stop(self):
        self._running = False
        
class TrainMonitorWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    canceled = pyqtSignal()
    
    def __init__(self, url, params):
        super().__init__()
        self.url = url
        self.params = params
        self._running = True
        
    def run(self):
        while 1:
            if not self._running:
                self.canceled.emit()
                return
            r = requests.get(self.url + "/steps", params=self.params)
            data = r.json()
            step = data["step"]
            total = 30000
            progress = int(step / total * 100)
            self.progress.emit(progress)
            if step >= total:
                self.finished.emit()
                break
            time.sleep(1)
        
    def stop(self):
        r = requests.post(self.url + "/stop", params=self.params)
        self._running = False
        
class PCD_Loader(QObject):
    finished = pyqtSignal(object, object, object)  # pcd, R, T
    
    def __init__(self, sparse_folder, H, W, K):
        super().__init__()
        self.sparse_folder = sparse_folder
        self.H = H
        self.W = W
        self.K = K
        
    def run(self):
        pcd = PCD(
                    os.path.join(self.sparse_folder, "0", "cameras.bin"),
                    os.path.join(self.sparse_folder, "0", "images.bin"),
                    os.path.join(self.sparse_folder, "0", "points3D.bin")
                )
        R, T = pcd.get_extrinsics_init()
        pcd.set_camera(R, T, self.H, self.W, self.K)
        self.finished.emit(pcd, R, T)
        
class VideoFrameExtractThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal()
    
    def __init__(self, video_path, output_dir, interval=30):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.interval = interval
        self._running = True
        self.video_name = os.path.splitext(
            os.path.basename(self.video_path)
        )[0]
        
    def run(self):
        try:
            if not os.path.exists(self.video_path):
                self.error_signal.emit()
                return
            container = av.open(self.video_path)
            stream = container.streams.video[0]
            if stream.frames:
                total_frames = stream.frames
            elif stream.duration and stream.average_rate:
                total_frames = int(stream.duration * float(stream.average_rate) * stream.time_base)
            else:
                total_frames = 0
            frame_idx = 0
            saved_count = 0
            save_dir = os.path.join(self.output_dir, self.video_name)
            if os.path.exists(save_dir):
                shutil.rmtree(save_dir)
            os.makedirs(save_dir, exist_ok=True)
            for frame in container.decode(video=0):
                if not self._running:
                    break
                if frame_idx % self.interval == 0:
                    img = frame.to_image()
                    save_path = os.path.join(
                        self.output_dir,
                        self.video_name,
                        f"frame_{saved_count:06d}.jpg"
                    )
                    img.save(save_path)
                    saved_count += 1
                if total_frames > 0:
                    progress = int(frame_idx / total_frames * 100)
                    self.progress_signal.emit(progress)
                frame_idx += 1
            container.close()
            if self._running:
                self.finished_signal.emit(self.video_name)
        except Exception as e:
            self.error_signal.emit()
            
    def stop(self):
        self._running = False