from server.user.userdb import get_conn
import uuid

# User repository
def create_user(username, password_hash):
    conn = get_conn()
    cursor = conn.cursor()
    
    user_id = str(uuid.uuid4()) # generate a unique user id
    
    cursor.execute(
        "INSERT INTO users VALUES (?, ?, ?)",
        (user_id, username, password_hash)
    )
    
    conn.commit()
    conn.close()
    return user_id

def get_user_by_username(username):
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, password_hash FROM users WHERE username=?",
        (username,)
    )
    row = cursor.fetchone()
    conn.close()
    return row

def get_user_by_id(user_id):
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username FROM users WHERE id=?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row

# Object repository
def create_object(user_id, object_name, project_path):
    conn = get_conn()
    cursor = conn.cursor()
    
    object_id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO objects (object_id, user_id, object_name, project_path) VALUES (?, ?, ?, ?)",
        (object_id, user_id, object_name, project_path)
    )
    conn.commit()
    conn.close()
    return object_id

def get_user_objects(user_id):
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT object_id, object_name, project_path FROM objects WHERE user_id=?",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"object_id": r[0], "object_name": r[1], "project_path": r[2]} for r in rows]

def delete_object(user_id, object_ids):
    if not object_ids:
        return False
    conn = get_conn()
    cursor = conn.cursor()
    placeholders = ",".join(
        "?" * len(object_ids)
    )
    sql = f"""
        DELETE FROM objects
        WHERE user_id=?
        AND object_id IN ({placeholders})
    """
    cursor.execute(
        sql,
        [user_id] + object_ids
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted