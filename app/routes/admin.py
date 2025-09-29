from fastapi import APIRouter

router = APIRouter()
@router.get("/{id}")
def get_message(id:str):
    return {"message": f"Hello, World!{id}"}