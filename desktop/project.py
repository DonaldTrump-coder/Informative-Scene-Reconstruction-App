import os
import sqlite3
import json
from desktop.Colmap.pcd import PCD_label

class rec_project:
    def __init__(self):
        self.db_path = None
        self.object_id = None
        self.sparse = False
        self.uploaded = False
        self.gs = False
        self.pcd_labels = []

    def set_path(self, project_folder, object_id):
        self.db_path = os.path.join(project_folder, "project.db")
        self.object_id = object_id
        os.makedirs(os.path.join(project_folder, "temp", "images"), exist_ok=True)
        os.makedirs(os.path.join(project_folder, "temp", "video_images"), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO kv_store (key, value)
            VALUES (?, ?)
        """, ("object_id", object_id))
        cursor.execute("""
            INSERT OR REPLACE INTO kv_store (key, value)
            VALUES (?, ?)
        """, ("sparse", "False")) # whether sparse reconstruction is finished
        cursor.execute("""
            INSERT OR REPLACE INTO kv_store (key, value)
            VALUES (?, ?)
        """, ("uploaded", "False")) # whether the data is uploaded to the server
        cursor.execute("""
            INSERT OR REPLACE INTO kv_store (key, value)
            VALUES (?, ?)
        """, ("gs", "False")) # whether gaussian splatting is finished
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pcd_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                bbox TEXT
            )
        """)
        conn.commit()
        conn.close()
        
    def set_sparse(self):
        self.sparse = True
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO kv_store (key, value)
            VALUES (?, ?)
        """, ("sparse", "True"))

        conn.commit()
        conn.close()
        
    def set_uploaded(self):
        self.uploaded = True
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO kv_store (key, value)
            VALUES (?, ?)
        """, ("uploaded", "True"))

        conn.commit()
        conn.close()
        
    def set_gs(self):
        self.gs = True
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO kv_store (key, value)
            VALUES (?, ?)
        """, ("gs", "True"))

        conn.commit()
        conn.close()
        
    def set_pcd_labels(self, pcd_labels: list[PCD_label]):
        self.pcd_labels = pcd_labels
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pcd_labels")
        for label in pcd_labels:
            cursor.execute("""
                INSERT INTO pcd_labels (name, description, bbox)
                VALUES (?, ?, ?)
            """, (
                label.name,
                label.description,
                json.dumps(label.bbox)
            ))
        conn.commit()
        conn.close()
        
    def read_from_path(self, project_folder):
        self.db_path = os.path.join(project_folder, "project.db")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor.execute("""
            SELECT key, value FROM kv_store
        """)
        rows = cursor.fetchall()
        result = {k: v for k, v in rows}
        self.object_id = result.get("object_id", None)
        self.sparse = result.get("sparse", "False") == "True"
        self.uploaded = result.get("uploaded", "False") == "True"
        self.gs = result.get("gs", "False") == "True"
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pcd_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                bbox TEXT
            )
        """)
        cursor.execute("""
            SELECT name, description, bbox
            FROM pcd_labels
        """)
        rows = cursor.fetchall()
        self.pcd_labels = []
        for name, description, bbox_json in rows:
            bbox = tuple(json.loads(bbox_json))
            self.pcd_labels.append(
                PCD_label(
                    name,
                    description,
                    bbox
                )
            )
        
        conn.close()
        #self.disp_db()
        
    def disp_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
        """)
        tables = cursor.fetchall()
        for (table_name,) in tables:
            print(f"\n--- TABLE: {table_name} ---")
            try:
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]
                print("COLUMNS:", col_names)
                #for row in rows:
                    #print(row)
            except Exception as e:
                print(f"ERROR reading {table_name}:", e)
        conn.close()