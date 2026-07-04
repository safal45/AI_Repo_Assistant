from fastapi import APIRouter, status

from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import register_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED,)
async def register(user: UserCreate):
    return await register_user(user)