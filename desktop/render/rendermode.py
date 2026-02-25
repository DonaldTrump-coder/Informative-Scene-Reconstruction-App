from enum import Enum

class Rendering_mode(Enum):
    NONE = 0 # Initialized mode
    RENDERING = 1 # 3DGS rendering
    IMAGE = 2 # image displaying mode
    PCD = 3 # point cloud displaying mode
    
class Status_mode(Enum):
    FREE = 0
    SELECT = 1
    UNSELECT = 2