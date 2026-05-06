from fastapi import APIRouter, HTTPException
from server.user import service

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/register")
def register(username: str, password: str):
    user_id, err = service.register(username, password)
    if err:
        raise HTTPException(400, err)
    return {"user_id": user_id}

@router.post("/login")
def login(username: str, password: str):
    user_id, err = service.login(username, password)
    if err:
        raise HTTPException(400, err)
    return {"user_id": user_id}

@router.get("/objects")
def my_objects(user_id: str):
    return service.list_objects(user_id)