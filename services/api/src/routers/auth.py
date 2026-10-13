"""Auth router — operator login issues the Bearer JWT.
Mirrors the analyzed backend's POST /admin/login contract.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.auth import check_password, create_token
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email_address: str
    password: str


@router.post("/login", response_model=APIResponse[dict])
async def login(body: LoginIn):
    user = await prisma.user.find_unique(where={"email_address": body.email_address})
    pw_hash = getattr(user, "passwordHash", None) if user else None
    if not user or not pw_hash or not check_password(body.password, pw_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return ok({"access_token": create_token(user.id), "token_type": "bearer"})
