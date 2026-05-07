from server.user import repo
from argon2 import PasswordHasher
ph = PasswordHasher()

def hash_password(password: str):
    return ph.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        ph.verify(hashed_password, password)
        return True
    except:
        return False

def register(username, password): # original password
    exist = repo.get_user_by_username(username)
    if exist:
        return None, "user exists"
    user_id = repo.create_user(username, hash_password(password))
    return user_id, None

def login(username, password): # original password
    user = repo.get_user_by_username(username)
    
    if not user:
        return None, "user not found"
    if not verify_password(password, user[2]):
        return None, "wrong password"
    return user[0], None # return user id

def create_object(user_id, object_name, project_path):
    return repo.create_object(user_id, object_name, project_path)

def list_objects(user_id):
    return repo.get_user_objects(user_id)