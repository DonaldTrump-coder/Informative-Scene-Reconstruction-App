from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, Body, WebSocket, WebSocketDisconnect
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
from server.GS import train as trainGS, GSrender as renderGS, import_gs as import_GS
import torch
import struct
import cv2
from server.user.router import router as user_router
from server.user.userdb import init_db

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

app.include_router(user_router)
    
class SceneObject:
    object_id = None
    folder = None
    gaussians = None
    pp = None
    def __init__(self):
        self.train_status = "Not trained"
        self.training_lock = threading.Lock()
        self.render_lock = threading.Lock()
        self.bg_color = torch.tensor([1,1,1], dtype=torch.float32, device="cuda")
        self.current_step = 0
        self.training = True
        
    def train(self):
        def step_update(step):
            self.current_step = step
            return self.training # True: training; False: stop training
        input_folder = self.folder
        output_folder = os.path.join(OUTPUT, self.object_id)
        os.makedirs(output_folder, exist_ok=True)
        self.gaussians, self.pp, self.bg_color = trainGS(input_folder, output_folder, step_callback=step_update)
        self.current_step = 30000
        self.train_status = "Trained"
    
    def render(self, K, R, t, H, W):
        return renderGS(K, R, t, H, W, self.gaussians, self.pp, self.bg_color)
    
    def import_gs(self, GS_folder):
        self.gaussians, self.pp = import_GS(GS_folder)
    
scene_objects = {}  # id -> SceneObject
    
@app.on_event("startup")
def on_startup():
    init_db() # automatically start up the database

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

@app.get("/steps")
async def get_current_step(object_id: str):
    if object_id not in scene_objects:
        return {"error": "ID not found"}
    obj = scene_objects[object_id]
    return {"step": obj.current_step}

@app.post("/train")
async def train_scene(object_id: str, background_tasks: BackgroundTasks):
    if object_id not in scene_objects:
        return {"error": "ID not found"}
    obj = scene_objects[object_id]
    background_tasks.add_task(run_training, obj)
    return {"status": "training started"}

def run_training(obj: SceneObject):
    with obj.training_lock:
        obj.train()
    
@app.websocket("/ws/render")
async def render_scene_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            obj_id = data["object_id"]
            if obj_id not in scene_objects:
                scene_object = SceneObject()
                scene_object.object_id = obj_id
                scene_object.folder = os.path.join(BASE_STORAGE, obj_id)
                scene_objects[obj_id] = scene_object
            
            obj = scene_objects[obj_id]
            if obj.gaussians is None:
                obj.import_gs(os.path.join(OUTPUT, obj.object_id))
            K = np.array(data["K"], dtype=np.float32)
            R = np.array(data["R"], dtype=np.float32)
            t = np.array(data["t"], dtype=np.float32)
            H = data["H"]
            W = data["W"]
            
            with obj.render_lock:
                img = obj.render(K, R, t, H, W)
            
            if isinstance(img, torch.Tensor):
                img = img.permute(1, 2, 0).detach().cpu().numpy()
            img = np.ascontiguousarray(img)
            img = (img * 255).astype(np.uint8)
            _, img_bytes = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            await websocket.send_bytes(img_bytes.tobytes())
    except WebSocketDisconnect:
        print("client disconnected")
    except Exception as e:
        print("render websocket error:", e)

@app.post("/destroy")
async def destroy_scene(object_id: str):
    pass

@app.post("/stop")
async def stop_training(object_id: str):
    obj_id = object_id
    if obj_id not in scene_objects:
        return {"error": "ID not found"}
    obj = scene_objects[obj_id]
    obj.training = False
    return {"status": "stopped"}