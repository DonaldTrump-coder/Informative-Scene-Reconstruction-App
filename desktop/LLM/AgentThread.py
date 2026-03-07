from PyQt5.QtCore import QThread, QMutex, QWaitCondition, pyqtSignal
from desktop.LLM.LLMtools import LLM
import numpy as np
from desktop.Colmap.pcd import PCD_label

class AgentThread(QThread):
    
    # thread tools
    mutex = QMutex()
    cond = QWaitCondition()
    paused = False
    
    start_new_signal = pyqtSignal()
    update_text_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.x = None
        self.y = None
        self.z = None
        self.pcd_labels = None
        self.label_coor = None # [[xmin, ymin, zmin, xmax, ymax, zmax],[],...]
        self.status_label = -1
        self.last_label = -1
        
        self.llm = LLM()
        self.llm_using = False
        
        self.running = True
        
        self.name_prompts = "你是一个导览专家，请帮我介绍一下"
        self.description_prompts = "，对应的描述是："
        self.messages = []
        self.last_response = ""
        
    def run(self):
        while self.running:
            if self.llm_using:
                self.mutex.lock()
                pcd_labels = None if self.pcd_labels is None else self.pcd_labels
                label_coor = None if self.label_coor is None else self.label_coor.copy()
                x = self.x
                y = self.y
                z = self.z
                self.mutex.unlock()
                
                if label_coor is None or pcd_labels is None:
                    continue
                if not x or not y or not z:
                    continue
                
                point = np.array([x, y, z])
                mins = label_coor[:, :3]
                maxs = label_coor[:, 3:]
                
                mask = np.all((point >= mins) & (point <= maxs), axis=1)
                if mask.any():
                    self.status_label = np.argmax(mask)
                else:
                    self.status_label = -1
                
                if self.status_label == self.last_label:
                    continue
                else:
                    self.last_label = self.status_label
                    if self.status_label == -1:
                        continue
                    name = pcd_labels[self.status_label].name
                    description = pcd_labels[self.status_label].description
                    
                    self.messages.clear()
                    message = {'role': 'system', 'content': self.name_prompts + name + self.description_prompts + description}
                    self.messages.append(message)
                    self.last_response = ""
                    response = self.llm.send_message(self.messages)
                    self.start_new_signal.emit()
                    for token in response:
                        self.last_response += token
                        self.update_text_signal.emit(token)
                    message = {'role': 'assistant', 'content': self.last_response}
                    self.messages.append(message)
        
    def stop(self):
        self.running = False
        self.wait()
        
    def set_coordinate(self, R: np.ndarray, T: np.ndarray):
        C = -R.T @ T
        self.x, self.y, self.z = C[0], C[1], C[2]
        
    def set_pcd_labels(self, labels: list[PCD_label]):
        self.mutex.lock()
        self.pcd_labels = labels
        self.label_coor = np.array([label.bbox for label in labels], dtype=np.float32)
        self.mutex.unlock()
        
    def send_message(self, text):
        message = {'role': 'user', 'content': text}
        self.messages.append(message)
        self.last_response = ""
        response = self.llm.send_message(self.messages)
        self.start_new_signal.emit()
        for token in response:
            self.last_response += token
            self.update_text_signal.emit(token)
        message = {'role': 'assistant', 'content': self.last_response}
        self.messages.append(message)