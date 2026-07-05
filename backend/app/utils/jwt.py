from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from app.config.settings import settings


def _create_token(
    user_id: str,
    expires_delta: timedelta,
    token_type: str,
) -> str:

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": user_id,
        "type": token_type,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
def create_access_token(user_id: str) -> str:
    return _create_token(
        user_id=user_id,
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        token_type="access",
    )
def create_refresh_token(user_id: str) -> str:
    return _create_token(
        user_id=user_id,
        expires_delta=timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),
        token_type="refresh",
    )
def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise