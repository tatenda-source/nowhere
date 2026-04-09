import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from ..config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    to_encode.update({
        "exp": expire,
        "iss": "nowhere-backend",
        "aud": "nowhere-app",
        "iat": datetime.now(timezone.utc),
    })
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer="nowhere-backend",
            audience="nowhere-app",
        )
    except jwt.PyJWTError:
        return None
