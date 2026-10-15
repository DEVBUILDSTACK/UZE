"""Public social profiles — the 20-second SocialFi onboarding identity.

One profile per user. Creating it mints the affiliate identity:
handle -> {handle}.uze.fi (provisioned by the blog builder) + UZE referral
code + referred_by attribution for UZD payouts.

Public reads never leak email_address.
"""
import re
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth import require_auth
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/profiles", tags=["profiles"])

HANDLE_RE = re.compile(r"^[a-z0-9_]{3,30}$")
MAX_INTERESTS = 10


def _new_referral_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "UZE-" + "".join(secrets.choice(alphabet) for _ in range(6))


class ProfileCreateIn(BaseModel):
    handle: str
    bio: str | None = None
    avatarUrl: str | None = None
    interests: list[str] = []
    referredBy: str | None = None  # referrer's referral code (QR scan / link)


@router.get("/check/{handle}", response_model=APIResponse[dict])
async def check_handle(handle: str):
    """Handle availability for the onboarding flow (public)."""
    h = handle.strip().lower()
    if not HANDLE_RE.match(h):
        return ok(
            {
                "available": False,
                "reason": "3-30 chars: lowercase letters, numbers, underscore",
            }
        )
    existing = await prisma.user.find_unique(where={"handle": h})
    return ok({"available": existing is None})


@router.post("/", response_model=APIResponse[dict])
async def create_profile(
    body: ProfileCreateIn, user_id: str = Depends(require_auth)
):
    """Create the 20-second profile. One per user; mints the referral code."""
    handle = body.handle.strip().lower()
    if not HANDLE_RE.match(handle):
        raise HTTPException(status_code=422, detail="Invalid handle")

    me = await prisma.user.find_unique(where={"id": user_id})
    if me is None:
        raise HTTPException(status_code=404, detail="User not found")
    if me.handle:
        raise HTTPException(status_code=409, detail="Profile already created")

    if await prisma.user.find_unique(where={"handle": handle}):
        raise HTTPException(status_code=409, detail="Handle taken")

    # Mint a unique referral code (retry on the vanishingly rare collision)
    referral_code = _new_referral_code()
    for _ in range(3):
        if not await prisma.user.find_unique(where={"referralCode": referral_code}):
            break
        referral_code = _new_referral_code()
    else:
        raise HTTPException(status_code=500, detail="Could not mint referral code")

    user = await prisma.user.update(
        where={"id": user_id},
        data={
            "handle": handle,
            "bio": (body.bio or "")[:120],
            "avatarUrl": body.avatarUrl,
            "interests": [i.strip()[:40] for i in body.interests[:MAX_INTERESTS] if i.strip()],
            "referralCode": referral_code,
            "referredBy": (body.referredBy or "").strip() or None,
        },
    )
    return ok(
        {"handle": user.handle, "referralCode": user.referralCode},
        message="Profile created",
    )


@router.get("/{handle}", response_model=APIResponse[dict])
async def get_profile(handle: str):
    """Public profile card (feed identity). No email_address leaked."""
    user = await prisma.user.find_unique(where={"handle": handle.strip().lower()})
    if user is None or not user.handle:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ok(
        {
            "handle": user.handle,
            "bio": user.bio,
            "avatarUrl": user.avatarUrl,
            "interests": user.interests,
            "createdAt": user.createdAt,
        }
    )
