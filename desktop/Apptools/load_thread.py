from PyQt5.QtCore import QThread, pyqtSignal
import os
import json

config_path = "./config.json"
default_config = {
    "url": "http://localhost:8000",
}

class LoaderThread(QThread):
    finished = pyqtSignal(object)
    
    def run(self):
        # reading config file
        try:
            if not os.path.exists(config_path):
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                config = default_config
            else:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
        except Exception as e:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            config = default_config
        
        self.finished.emit(config)