from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.utils.security import hash_password,verify_password
from fastapi import HTTPException, status
from app.utils.jwt import (create_access_token,create_refresh_token,decode_token)
from app.schemas.auth import LoginResponse, TokenResponse
from app.repositories.user_repository import create_user, get_user_by_email, get_user_by_id
from app.serializers.user_serializers import serialize_user
from jose import JWTError




async def register_user(user: UserCreate):      
    existing_user = await get_user_by_email(user.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    hashed_password = hash_password(user.password)

    db_user = User(
    name=user.name,
    email=user.email,
    hashed_password=hashed_password,
)
    result = await create_user(db_user)

    return UserResponse(
        id=str(result["_id"]),
        name=db_user.name,
        email=db_user.email,
        created_at=db_user.created_at,
    )

async def login_user(user: UserLogin):
    db_user = await get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not verify_password(user.password,db_user["hashed_password"],):
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )
    access_token = create_access_token(
    str(db_user["_id"])
)

    refresh_token = create_refresh_token(
        str(db_user["_id"])
    )
    user_response = serialize_user(db_user)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response,
    )

async def refresh_access_token(
    refresh_token: str,
) -> TokenResponse:

    try:
        payload = decode_token(refresh_token)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    db_user = await get_user_by_id(user_id)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(
        str(db_user["_id"])
    )

    return TokenResponse(
        access_token=access_token,
    )