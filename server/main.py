from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import subprocess 
import time

app = FastAPI()

class TaskCmd(BaseModel):
    cmd: str # Command to execute
    
def run_task(cmd: str):
    print(f"[SERVER] 开始执行任务: {cmd}")
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    print("[STDOUT]", stdout.decode())
    print("[STDERR]", stderr.decode())
    
@app.post("/run")
def run_command(task: TaskCmd, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_task, task.cmd)
    return {"status": "task submitted"}