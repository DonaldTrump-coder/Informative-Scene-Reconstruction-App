from fastapi import APIRouter, HTTPException
from server.user import service
from typing import List
from fastapi import Query

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

@router.post("/create_object")
def create_object(user_id: str, object_name: str, project_path: str):
    object_id = service.create_object(
        user_id,
        object_name,
        project_path
    )
    return {"object_id": object_id}

@router.delete("/delete_object")
def delete_object(user_id: str, object_ids: List[str] = Query(...)):
    success = service.delete_object(user_id, object_ids)
    if success:
        return {
            "success": True,
            "message": "Deleted"
        }
    return {
        "success": False,
        "message": "Failed"
    }