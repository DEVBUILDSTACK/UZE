"""Affiliates router — GIRAgents MVP affiliate creator business.
Codes, leaderboard, UZD payouts. Run by the SoSim agent.
"""
from fastapi import APIRouter, Depends

from src.auth import require_auth
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/affiliates", tags=["affiliates"])


@router.get("/", response_model=APIResponse[list])
async def list_affiliates(limit: int = 20):
    # Affiliate entity table is team build work; envelope shape is stable.
    return ok([])


@router.get("/leaderboard", response_model=APIResponse[list])
async def leaderboard(period: str = "weekly"):
    return ok([])


@router.post("/payout", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def payout(payload: dict):
    # UZD payout settlement is team build work.
    return ok(payload, message="Payout queued")
