from app.database.database import db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.utils.security import hash_password
from fastapi import HTTPException, status

async def register_user(user: UserCreate):
    existing_user = await db.users.find_one(
        {"email": user.email}
    )

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
    result = await db.users.insert_one(
    db_user.model_dump()
)
    

    return UserResponse(
    id=str(result.inserted_id),
    name=db_user.name,
    email=db_user.email,
    created_at=db_user.created_at,
)