"""Users router — end-user identity.

Mass assignment is closed: create/update take typed models with explicit
fields only. Role is never accepted from the caller (DB default "user").
User creation and the user list are operator-only; lookups are self-or-operator.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.auth import require_auth, require_role, require_role_claims
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateIn(BaseModel):
    email_address: str = Field(min_length=3, max_length=320)
    name: str | None = Field(default=None, max_length=120)


class UserUpdateIn(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=160)
    avatarUrl: str | None = Field(default=None, max_length=500)
    interests: list[str] | None = None


@router.post("/create", response_model=APIResponse[dict])
async def create_user(
    body: UserCreateIn, user_id: str = Depends(require_role("operator"))
):
    email = body.email_address.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Invalid email address")
    user = await prisma.user.create(data={"email_address": email, "name": body.name})
    return ok(user, message="User created")


@router.get("/get-one", response_model=APIResponse[dict])
async def get_one(
    email_address: str, claims: dict = Depends(require_role_claims("user"))
):
    """Look up a user by email: own record, or any record as operator/admin."""
    if claims["role"] not in ("operator", "admin"):
        me = await prisma.user.find_unique(where={"id": claims["sub"]})
        if me is None or me.email_address != email_address.strip().lower():
            raise HTTPException(
                status_code=403, detail="You can only look up your own record"
            )
    user = await prisma.user.find_unique(
        where={"email_address": email_address.strip().lower()}
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return ok(user)


@router.get("/", response_model=APIResponse[list])
async def list_users(
    limit: int = 20, user_id: str = Depends(require_role("operator"))
):
    users = await prisma.user.find_many(take=min(limit, 100))
    return ok(users)


@router.post("/update", response_model=APIResponse[dict])
async def update_user(
    body: UserUpdateIn, user_id: str = Depends(require_auth)
):
    """Self-service profile update. Only safe fields; role/passwordHash are
    never writable here."""
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if "interests" in data:
        data["interests"] = [i.strip()[:40] for i in data["interests"][:10] if i.strip()]
    user = await prisma.user.update(where={"id": user_id}, data=data)
    return ok(user, message="User updated")
