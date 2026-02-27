from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, Body
from fastapi.responses import StreamingResponse
from io import BytesIO
from PIL import Image
from pydantic import BaseModel
from typing import List
import subprocess 
import time
import numpy as np
import threading
import uuid
import os
from server.GS import train as trainGS, GSrender as renderGS
import torch
from desktop.Colmap.reconstructor import constructor

class CameraParam(BaseModel):
    object_id: str
    K: List[List[float]]   # 3x3
    R: List[List[float]]   # 3x3
    t: List[float]
    H: int
    W: int

app = FastAPI()
BASE_STORAGE = os.path.join(os.path.dirname(__file__), "server_storage")
os.makedirs(BASE_STORAGE, exist_ok=True)
OUTPUT = os.path.join(BASE_STORAGE, "output")
os.makedirs(OUTPUT, exist_ok=True)
    
class SceneObject:
    object_id = None
    folder = None
    gaussians = None
    pp = None
    bg_color = None
    def __init__(self):
        self.train_status = "Not trained"
        self.training_lock = threading.Lock()
        self.render_lock = threading.Lock()
        self.reconstruction_lock = threading.Lock()
        
    def reconstruction(self):
        sfm = constructor(os.path.join(self.folder, "project.db"))
        sfm.add_image_folder(os.path.join(self.folder, "images"))
        sfm.sfm()
        
    def train(self):
        input_folder = self.folder
        output_folder = os.path.join(OUTPUT, self.object_id)
        self.gaussians, self.pp, self.bg_color = trainGS(input_folder, output_folder)
        self.train_status = "Trained"
    
    def render(self, K, R, t, H, W):
        return renderGS(K, R, t, H, W, self.gaussians, self.pp, self.bg_color)
    
scene_objects = {}  # id -> SceneObject
    
@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)
                       ):
    scene_object = SceneObject()
    object_id = str(uuid.uuid4())
    scene_object.object_id = object_id
    obj_folder = os.path.join(BASE_STORAGE, object_id)
    os.makedirs(obj_folder, exist_ok=True)
    scene_object.folder = obj_folder
    
    for f in files:
        file_path = os.path.join(obj_folder, f.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as out_file:
            while content := await f.read(1024*1024):  # 1MB chunks
                out_file.write(content)
            print(f"Uploaded {f.filename} to {file_path}")
    
    scene_objects[object_id] = scene_object
    
    return {"status": "uploaded", "id": object_id}

@app.post("/train")
def train_scene(object_id: str):
    if object_id not in scene_objects:
        return {"error": "ID not found"}
    obj = scene_objects[object_id]
    with obj.training_lock:
        obj.train()
    return {"status": "trained"}

@app.post("/reconstruct")
def reconstruct_scene(object_id: str):
    if object_id not in scene_objects:
        return {"error": "ID not found"}
    obj = scene_objects[object_id]
    with obj.reconstruction_lock:
        obj.reconstruction()
    return {"status": "reconstructed"}

@app.post("/render")
def render_scene(cam: CameraParam = Body(...)):
    obj_id = cam.object_id
    if obj_id not in scene_objects:
        return {"error": "ID not found"}
    obj = scene_objects[obj_id]
    K = np.array(cam.K, dtype=np.float32)
    R = np.array(cam.R, dtype=np.float32)
    t = np.array(cam.t, dtype=np.float32)
    H = cam.H
    W = cam.W
    
    with obj.render_lock:
        img = obj.render(K, R, t, H, W)
    
    if isinstance(img, torch.Tensor):
        img = img.detach().cpu().numpy()
    img = np.ascontiguousarray(img)
    
    return StreamingResponse(
        BytesIO(img.tobytes()),
        media_type="application/octet-stream",
        headers={
            "X-Shape": f"{img.shape[0]},{img.shape[1]},{img.shape[2]}",
            "X-Dtype": str(img.dtype)
        }
    )

@app.post("/destroy")
def destroy_scene(object_id: str):
    pass