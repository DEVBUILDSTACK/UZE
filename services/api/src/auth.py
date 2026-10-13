"""JWT auth — backend-issued Bearer tokens (analyzed backend pattern).
Admins/operators: bcrypt password -> /auth/login -> JWT.
Routers protect routes with `Depends(require_auth)`.
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from src.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)


def create_token(subject: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": subject, "exp": exp},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return str(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_auth(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return verify_token(creds.credentials)


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def check_password(pw: str, hashed: str) -> bool:
    return pwd_ctx.verify(pw, hashed)
