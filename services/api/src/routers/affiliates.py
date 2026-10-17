"""Affiliates router — GIRAgents MVP affiliate creator business.
Codes, leaderboard, UZD payouts. Run by the SoSim agent.

Payouts: there is no payout queue until the A4 ApprovalRequest flow exists,
so POST /payout returns 501 (S4; §6.2). It is also operator-gated so a future
implementation cannot be reached by end users (S1; §6.1).
"""
from fastapi import APIRouter, Depends, HTTPException

from src.auth import require_role
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/affiliates", tags=["affiliates"])


@router.get("/", response_model=APIResponse[list])
async def list_affiliates(limit: int = 20):
    # Affiliate entity table is team build work; envelope shape is stable.
    return ok([])


@router.get("/leaderboard", response_model=APIResponse[list])
async def leaderboard(period: str = "weekly"):
    return ok([])


@router.post("/payout", response_model=APIResponse[dict])
async def payout(user_id: str = Depends(require_role("operator"))):
    # No payout queue exists yet; per the L4 rule every monetary action needs
    # per-action human approval (account, amount, asset, timing). Until the
    # A4 ApprovalRequest flow exists, payouts stay unreachable.
    raise HTTPException(
        status_code=501,
        detail="Payouts unavailable until the A4 ApprovalRequest flow exists",
    )
