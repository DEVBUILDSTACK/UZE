"""Auth router — operator login issues the Bearer JWT.
Mirrors the analyzed backend's POST /admin/login contract.
End users authenticate via email OTP (no passwords).
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.auth import check_password, create_token
from src.db import prisma
from src.otp import request_otp, verify_otp
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email_address: str
    password: str


class OtpRequestIn(BaseModel):
    email_address: str


class OtpVerifyIn(BaseModel):
    email_address: str
    code: str


@router.post("/login", response_model=APIResponse[dict])
async def login(body: LoginIn):
    user = await prisma.user.find_unique(where={"email_address": body.email_address})
    pw_hash = getattr(user, "passwordHash", None) if user else None
    if not user or not pw_hash or not check_password(body.password, pw_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    role = getattr(user, "role", None) or "user"
    return ok({"access_token": create_token(user.id, role), "token_type": "bearer"})


@router.post("/otp/request", response_model=APIResponse[dict])
async def otp_request(body: OtpRequestIn):
    """Email a 6-digit login code (5-minute expiry, rate-limited)."""
    await request_otp(body.email_address)
    return ok({"sent": True}, message="Login code sent")


@router.post("/otp/verify", response_model=APIResponse[dict])
async def otp_verify(body: OtpVerifyIn, request: Request):
    """Verify the code; auto-create the user (role "user"); return a JWT."""
    ip = request.client.host if request.client else None
    if not await verify_otp(body.email_address, body.code, ip=ip):
        raise HTTPException(status_code=401, detail="Invalid or expired code")
    email = body.email_address.strip().lower()
    user = await prisma.user.find_unique(where={"email_address": email})
    new_user = False
    if user is None:
        # role defaults to "user" at the DB level (schema default); never
        # accepted from the caller.
        user = await prisma.user.create(data={"email_address": email})
        new_user = True
    role = getattr(user, "role", None) or "user"
    return ok(
        {
            "access_token": create_token(user.id, role),
            "token_type": "bearer",
            "new_user": new_user,
        }
    )
