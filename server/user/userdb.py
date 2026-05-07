import sqlite3
import os

BASE_STORAGE = os.path.join(os.path.dirname(__file__), "..", "server_storage")
DB_PATH = os.path.join(BASE_STORAGE, "users.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS objects (
        object_id TEXT PRIMARY KEY,
        user_id TEXT,
        object_name TEXT,
        project_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_objects_user_id 
    ON objects(user_id)
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_objects_user_time 
    ON objects(user_id, created_at DESC)
    """)
    
    conn.commit()
    conn.close()