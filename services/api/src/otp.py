"""Email OTP — low-friction end-user auth for the UZE SocialFi onboarding.

Flow:
  POST /auth/otp/request {email_address} -> 6-digit code sent via Resend,
      stored in Redis with a 5-minute TTL, rate-limited per email.
  POST /auth/otp/verify {email_address, code} -> JWT (user auto-created).

No passwords for end users. Operator accounts keep bcrypt + /auth/login.
"""
import secrets

import resend
from fastapi import HTTPException

from src.config import settings
from src.db import redis_client

OTP_TTL_SECONDS = 300
OTP_REQUEST_LIMIT_PER_HOUR = 5


def _otp_key(email: str) -> str:
    return f"otp:{email.strip().lower()}"


def _rate_key(email: str) -> str:
    return f"otp:rate:{email.strip().lower()}"


async def request_otp(email_address: str) -> None:
    """Generate a code, store it in Redis, and email it via Resend."""
    if redis_client is None:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    email = email_address.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Invalid email address")

    count = await redis_client.incr(_rate_key(email))
    if count == 1:
        await redis_client.expire(_rate_key(email), 3600)
    if count > OTP_REQUEST_LIMIT_PER_HOUR:
        raise HTTPException(
            status_code=429, detail="Too many code requests — try again later"
        )

    code = f"{secrets.randbelow(900_000) + 100_000:06d}"
    await redis_client.set(_otp_key(email), code, ex=OTP_TTL_SECONDS)

    if not settings.RESEND_API_KEY or not settings.RESEND_SENDER_EMAIL:
        raise HTTPException(status_code=503, detail="Email sending not configured")

    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send(
        {
            "from": f"{settings.RESEND_SENDER_NAME} <{settings.RESEND_SENDER_EMAIL}>",
            "to": [email],
            "subject": f"Your UZE login code: {code}",
            "html": (
                "<p>Your UZE login code is <strong>"
                f"{code}</strong>. It expires in 5 minutes.</p>"
                "<p>If you didn't request this, you can ignore this email.</p>"
            ),
            "text": (
                f"Your UZE login code is {code}. It expires in 5 minutes. "
                "If you didn't request this, you can ignore this email."
            ),
        }
    )


async def verify_otp(email_address: str, code: str) -> bool:
    """Check a code. Single-use: deleted on success."""
    if redis_client is None:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    email = email_address.strip().lower()
    stored = await redis_client.get(_otp_key(email))
    if stored is None:
        return False
    if not secrets.compare_digest(stored, code.strip()):
        return False
    await redis_client.delete(_otp_key(email))
    return True
