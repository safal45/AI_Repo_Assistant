from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth_service import login_user, refresh_access_token, register_user
from app.schemas.auth import LoginResponse, RefreshTokenRequest, TokenResponse
from app.dependencies.auth import get_current_user
from app.serializers.user_serializers import serialize_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED,)
async def register(user: UserCreate):
    return await register_user(user)

@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = UserLogin(
        email=form_data.username,
        password=form_data.password,
    )

    return await login_user(user)

@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(current_user = Depends(get_current_user),):
    return serialize_user(current_user)

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    request: RefreshTokenRequest,
):
    return await refresh_access_token(
        request.refresh_token
    )