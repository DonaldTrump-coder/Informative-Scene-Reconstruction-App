from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from render.rendermode import Rendering_mode
from pathlib import Path
from render.parsingckpt import CKPT_Parser
from render.cameras import get_init_camera
import torch
from internal.cameras.cameras import Cameras,Camera
from internal.renderers.sep_depth_trim_2dgs_renderer import SepDepthTrim2DGSRenderer

class RenderThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    parser = None
    camera = None
    R = None # [3x3]
    T = None # [3x1]
    K = None # [3x3]
    point_min = None
    point_max = None
    W = 1920
    H = 1080

    def __init__(self, filename):
        super().__init__()
        self.rendering_mode = Rendering_mode.NONE # Initialized Rendering Mode
        self.file=filename
        self.running=True
        self.fx = 1659
        self.fy = 933
        self.cx = 960
        self.cy = 540

    def parsing_file(self):
        # parsing file:
        file_path = Path(self.file)
        if file_path.suffix.lower() == ".ckpt": # parsing ckpt file
            self.parser = CKPT_Parser(self.file)
            self.model = self.parser.get_model()
            self.model.active_sh_degree = 0
            self.data = self.parser.get_points()
            self.params = self.parser.get_params()
            self.point_min, self.point_max = self.parser.get_boundary()
            self.Rs=torch.zeros(1,3,3,device=torch.device("cuda"))
            self.Ts=torch.zeros(1,3,device=torch.device("cuda"))
            self.fxs=torch.full((1,),self.fx,device=torch.device("cuda"))
            self.fys=torch.full((1,),self.fy,device=torch.device("cuda"))
            self.cxs=torch.full((1,),self.cx,device=torch.device("cuda"))
            self.cys=torch.full((1,),self.cy,device=torch.device("cuda"))
            self.width=torch.full((1,),self.W,device=torch.device("cuda"))
            self.height=torch.full((1,),self.H,device=torch.device("cuda"))
            self.appearance_id=torch.full((1,),0,device=torch.device("cuda"))
            self.normalized_appearance_id=torch.full((1,),0,device=torch.device("cuda"))
            self.camera_type=torch.full((1,),0,device=torch.device("cuda"))
            self.bg_color = torch.zeros((3,), dtype=torch.float, device=torch.device("cuda"))#背景颜色
            self.renderer = SepDepthTrim2DGSRenderer()

    def set_2DGS_RGB(self,checked):
        if checked:
            self.rendering_mode = Rendering_mode.CKPT_RGB
        else:
            self.rendering_mode = Rendering_mode.NONE

    def set_2DGS_Disp(self,checked):
        if checked:
            self.rendering_mode = Rendering_mode.CKPT_GS
        else:
            self.rendering_mode = Rendering_mode.NONE

    def set_2DGS_Depth(self,checked):
        if checked:
            self.rendering_mode = Rendering_mode.CKPT_DEPTH
        else:
            self.rendering_mode = Rendering_mode.NONE

    def set_mesh_RGB(self,checked):
        if checked:
            self.rendering_mode = Rendering_mode.MESH
        else:
            self.rendering_mode = Rendering_mode.NONE

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
        self.parsing_file() # parsing the file first
        self.R, self.T = get_init_camera(self.point_min,self.point_max)
        while self.running:
            # rendering cores:
            if self.rendering_mode is Rendering_mode.NONE:
                pass
            if self.rendering_mode in (Rendering_mode.CKPT_RGB, Rendering_mode.CKPT_DEPTH):
                self.Rs[0] = torch.tensor(self.R,device=torch.device("cuda"))
                self.Ts[0] = torch.tensor(self.T,device=torch.device("cuda"))
                camera=Cameras(
                    R=self.Rs,
                    T=self.Ts,
                    fx=self.fxs,
                    fy=self.fys,
                    cx=self.cxs,
                    cy=self.cys,
                    width=self.width,
                    height=self.height,
                    appearance_id=self.appearance_id,
                    normalized_appearance_id=self.normalized_appearance_id,
                    distortion_params=None,
                    camera_type=self.camera_type
                    )
                camera = [camera[0]]
                camera[0].idx.to(torch.device("cuda"))
                camera[0].to_device(torch.device("cuda"))
                render_pkg = self.renderer(camera[0], self.model, self.bg_color)
                rgb = render_pkg['render']
                self.frame_ready.emit(rgb.detach().cpu().numpy()*255)

    def stop(self):
        self.running=False
        self.wait()