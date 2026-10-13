"""Users router — Privy-backed end-user identity."""
from fastapi import APIRouter, Depends, HTTPException

from src.auth import require_auth
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/create", response_model=APIResponse[dict])
async def create_user(payload: dict):
    user = await prisma.user.create(data=payload)
    return ok(user, message="User created")


@router.get("/get-one", response_model=APIResponse[dict],
            dependencies=[Depends(require_auth)])
async def get_one(email_address: str):
    user = await prisma.user.find_unique(
        where={"email_address": email_address}
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return ok(user)


@router.get("/", response_model=APIResponse[list],
            dependencies=[Depends(require_auth)])
async def list_users(limit: int = 20):
    users = await prisma.user.find_many(take=min(limit, 100))
    return ok(users)


@router.post("/update", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def update_user(payload: dict):
    user_id = payload.pop("id", None)
    if not user_id:
        raise HTTPException(status_code=422, detail="id required")
    user = await prisma.user.update(where={"id": user_id}, data=payload)
    return ok(user, message="User updated")
