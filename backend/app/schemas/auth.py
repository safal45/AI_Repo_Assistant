from pydantic import BaseModel

from app.schemas.user import UserResponse


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(Token):
    user: UserResponse

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str