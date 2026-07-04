from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    name: str
    email: EmailStr
    hashed_password: str

    is_verified: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)