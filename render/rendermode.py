from enum import Enum

class Rendering_mode(Enum):
    NONE = 0 # Initialized mode
    CKPT_RGB = 1 # 2DGS Rendering mode
    CKPT_GS = 2 # 2DGS displaying mode
    CKPT_DEPTH = 3 # 2DGS depth Rendering mode
    MESH = 4 # mesh Rendering mode