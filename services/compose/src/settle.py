"""Settle router — Sprint 1.5 Day 3: selection + real cross-chain
settlement, per the filed flow (02-SPRINT-1.5-PLAN.md Day 3) and the
Diagram 4 lifecycle (docs/diagrams/04-intent-lifecycle.md):

POST /api/v1/settle {intentId, bidId}
  -> the poster's selection is recorded as a Match (bid SELECTED,
     the rest NOT_SELECTED, intent BIDDING -> SELECTED)
  -> contract settle(intent_id, bid_id) records the settlement on
     NEAR (near_client, chain-gated as everywhere)
  -> intent SELECTED -> SETTLING while the payment leg runs
  -> settlement.settle_usdc: the operator's derived Solana address
     pays the winning bid amount in devnet USDC to the winning
     bidder's derived address, MPC-signed (settlement.py)
  -> outcome: SETTLED (+ settlement_event and the micro-region
     comparable written, Diagram 4's SETTLED note) | SETTLE_FAILED
     (resting state; a retry POST resumes from it, the client's
     choice preserved) | still SELECTED when the leg was signed
     but not broadcast for lack of devnet funds — the response
     says exactly which, and nothing claims SETTLED without a
     confirmed Solana transaction.

With the chain gate closed the selection half still runs (it is the
marketplace's own record) and the settlement block reports
"disabled" — the same honesty rule as Day 2's endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

import models
import near_client
import settlement
from db import get_session
from intents import _bid_view, _spec_view

router = APIRouter(prefix="/api/v1", tags=["settle"])


class SettleIn(BaseModel):
    intentId: str
    bidId: str


class MatchView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    intentId: str
    bidId: str
    matchedBy: str
    state: str
    settlementRef: str | None


def _match_view(match: models.Match) -> MatchView:
    return MatchView(
        id=match.id,
        intentId=match.intent_id,
        bidId=match.bid_id,
        matchedBy=match.matched_by,
        state=match.state,
        settlementRef=match.settlement_ref,
    )


def _event(db: Session, aggregate_type: str, aggregate_id: str,
           event_type: str, payload: dict) -> None:
    db.add(
        models.EventLog(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            actor="system",
            payload=payload,
        )
    )


@router.post("/settle")
def post_settle(body: SettleIn, db: Session = Depends(get_session)):
    intent = db.get(models.Intent, body.intentId)
    if intent is None:
        raise HTTPException(status_code=404, detail="spec not found")
    bid = db.get(models.Bid, body.bidId)
    if bid is None:
        raise HTTPException(status_code=404, detail="bid not found")
    if bid.intent_id != intent.id:
        raise HTTPException(
            status_code=422, detail="bid does not belong to this spec"
        )
    if intent.status is models.IntentStatus.EXPIRED:
        raise HTTPException(status_code=410, detail="spec is EXPIRED")
    if intent.status in (
        models.IntentStatus.SETTLED,
        models.IntentStatus.DELIVERED,
    ):
        raise HTTPException(
            status_code=409, detail=f"spec already {intent.status.value}"
        )
    if intent.status not in (
        models.IntentStatus.BIDDING,
        models.IntentStatus.SELECTED,
        models.IntentStatus.SETTLE_FAILED,
    ):
        raise HTTPException(
            status_code=409,
            detail=f"spec is {intent.status.value}; nothing to settle",
        )
    if bid.status is models.BidStatus.WITHDRAWN:
        raise HTTPException(status_code=409, detail="bid is WITHDRAWN")
    if bid.status is models.BidStatus.NOT_SELECTED:
        raise HTTPException(
            status_code=409, detail="bid was not selected for this spec"
        )

    # --- selection: create or reuse the Match -----------------------
    match = next(
        (m for m in intent.matches if m.bid_id == bid.id), None
    )
    if match is None:
        if intent.matches:
            raise HTTPException(
                status_code=409,
                detail="spec already matched to another bid",
            )
        match = models.Match(
            intent_id=intent.id,
            bid_id=bid.id,
            matched_by=intent.poster_account,
            state="SELECTED",
        )
        db.add(match)
        bid.status = models.BidStatus.SELECTED
        for other in intent.bids:
            if other.id != bid.id and other.status is models.BidStatus.SUBMITTED:
                other.status = models.BidStatus.NOT_SELECTED
        intent.status = models.IntentStatus.SELECTED
        db.flush()
        _event(
            db, "intent", intent.id, "match.selected",
            {"matchId": match.id, "bidId": bid.id,
             "matchedBy": intent.poster_account},
        )
        db.commit()
        db.refresh(match)

    result = {
        "spec": _spec_view(intent).model_dump(),
        "bid": _bid_view(bid).model_dump(),
        "match": _match_view(match).model_dump(),
        "settlement": {"status": "disabled"},
    }
    if not near_client.chain_enabled():
        return result

    # --- settlement leg ---------------------------------------------
    intent.status = models.IntentStatus.SETTLING
    match.state = "SETTLING"
    db.commit()

    contract = near_client.settle(
        intent.chain_intent_ref or intent.id, bid.chain_bid_ref or bid.id
    )
    result["settlement"]["contract"] = contract
    if contract.get("status") != "submitted":
        intent.status = models.IntentStatus.SETTLE_FAILED
        match.state = "SELECTED"
        db.commit()
        result["settlement"]["status"] = "failed"
        result["settlement"]["reason"] = (
            f"contract settle not submitted: {contract}"
        )
        result["spec"] = _spec_view(intent).model_dump()
        result["match"] = _match_view(match).model_dump()
        return result

    outcome = settlement.settle_usdc(bid.bidder_account, bid.amount_usdc)
    result["settlement"].update(outcome)

    if outcome["status"] == "settled":
        intent.status = models.IntentStatus.SETTLED
        match.state = "SETTLED"
        match.settlement_ref = outcome["solanaTx"]
        _event(
            db, "intent", intent.id, "settlement.settled",
            {
                "matchId": match.id,
                "bidId": bid.id,
                "amountUsdc": bid.amount_usdc,
                "solanaTx": outcome["solanaTx"],
                "payerAddress": outcome["payerAddress"],
                "payeeAddress": outcome["payeeAddress"],
                "contractRef": contract.get("result"),
            },
        )
        _event(
            db, "micro_region", intent.micro_region_id,
            "comparable.recorded",
            {
                "intentId": intent.id,
                "domain": intent.domain.value,
                "workProduct": intent.work_product.value,
                "assetContext": intent.asset_context,
                "settledAmountUsdc": bid.amount_usdc,
            },
        )
    elif outcome["status"] == "signed":
        # Signed but not broadcast (funds pending): the client's
        # choice stands, ready to fire the moment funds land.
        intent.status = models.IntentStatus.SELECTED
        match.state = "SELECTED"
        _event(
            db, "intent", intent.id, "settlement.signed",
            {"matchId": match.id, "bidId": bid.id,
             "reason": outcome.get("reason")},
        )
    else:  # failed
        intent.status = models.IntentStatus.SETTLE_FAILED
        match.state = "SELECTED"
        _event(
            db, "intent", intent.id, "settlement.failed",
            {"matchId": match.id, "bidId": bid.id,
             "reason": outcome.get("reason")},
        )
    db.commit()
    db.refresh(intent)
    db.refresh(match)
    result["spec"] = _spec_view(intent).model_dump()
    result["match"] = _match_view(match).model_dump()
    return result
