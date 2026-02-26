import os
import requests
import numpy as np

SERVER = "http://IP:8000"

def upload(local_folder):
    files_to_upload = []
    for root, dirs, files in os.walk(local_folder):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, local_folder) # use relative path for upload
            files_to_upload.append(
            ("files", (rel_path.replace("\\","/"), open(full_path, "rb")))
            )
    
    r = requests.post(f"{SERVER}/upload", files=files_to_upload)
    scene_id = r.json()["id"] # the scene object creadted on the server
    
def render(scene_id, K, R, t, H, W):
    payload = {
        "object_id": scene_id,
        "K": K.tolist(),
        "R": R.tolist(),
        "t": t.tolist(),
        "H": H,
        "W": W
    }
    r = requests.post(f"{SERVER}/render", json=payload)
    shape = tuple(map(int, r.headers["X-Shape"].split(",")))
    dtype = np.dtype(r.headers["X-Dtype"])
    img = np.frombuffer(r.content, dtype=dtype).reshape(shape)