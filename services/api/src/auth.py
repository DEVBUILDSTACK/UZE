"""JWT auth — backend-issued Bearer tokens (analyzed backend pattern).
Roles: user | operator | agent | admin (spec §6.1). The JWT carries a `role`
claim; `require_role(...)` gates operator routes. Admins pass every role gate.
Legacy sub-only tokens still verify and are treated as role "user".
Routers protect routes with `Depends(require_auth)` (any valid token) or
`Depends(require_role("operator"))` (operator+admin).
"""
from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from src.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

ROLES = ("user", "operator", "agent", "admin")


def create_token(subject: str, role: str = "user") -> str:
    if role not in ROLES:
        role = "user"
    exp = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": subject, "role": role, "exp": exp},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")
    role = payload.get("role") or "user"
    if role not in ROLES:
        role = "user"
    return {"sub": str(payload["sub"]), "role": role}


async def require_auth(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    """Any valid token passes. Returns the caller's user id."""
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return verify_token(creds.credentials)["sub"]


def require_role_claims(*roles: str) -> Callable:
    """Dependency factory: caller must hold one of `roles`; admins always
    pass. Returns the verified claims dict ({"sub", "role"})."""
    allowed = {r for r in roles if r in ROLES}

    async def _gate(
        creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> dict:
        if creds is None or not creds.credentials:
            raise HTTPException(status_code=401, detail="Missing bearer token")
        claims = verify_token(creds.credentials)
        if claims["role"] != "admin" and claims["role"] not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return claims

    return _gate


def require_role(*roles: str) -> Callable:
    """Dependency factory: like require_role_claims, but returns the user id."""
    claims_dep = require_role_claims(*roles)

    async def _uid(claims: dict = Depends(claims_dep)) -> str:
        return claims["sub"]

    return _uid


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def check_password(pw: str, hashed: str) -> bool:
    return pwd_ctx.verify(pw, hashed)
