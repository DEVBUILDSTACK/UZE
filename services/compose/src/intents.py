"""Intents router — the Sprint 1.5 CRE marketplace surface (Day 2).

POST /api/v1/specs            post a specification (an Intent) — the
                              compose row is the system of record; the
                              NEAR contract call rides along when the
                              chain gate is open (see near_client.py)
GET  /api/v1/specs/{id}       the spec, with its bid count
GET  /api/v1/specs/{id}/bids  the bids competing on the spec
POST /api/v1/bids             bid on a spec; the first bid moves the
                              intent POSTED -> BIDDING (Diagram 4)

Semantics, stated once here:
  - Field names on the wire are the intent schema's camelCase names —
    the agent surface and the (Day 6) human surface project the same
    fields; a field on one and not the other is a defect (D4).
  - A spec names its micro-region by slug; an unknown slug is a 422
    (the benchmark unit must exist before work is priced against it).
  - budgetMinUsdc must not exceed budgetMaxUsdc (422).
  - Bidding on a missing spec is 404; on an EXPIRED spec, 410.
  - Settlement is NOT here: selection + settle are Day 3. A Match row
    is created only by the settle flow.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

import models
import inference
import near_client
from db import get_session

router = APIRouter(prefix="/api/v1", tags=["intents"])


class AssetContextIn(BaseModel):
    propertyType: models.PropertyType
    doorCount: int
    brandAffiliation: str | None = None
    acquisitionStage: models.AcquisitionStage


class SpecIn(BaseModel):
    kind: models.IntentKind = models.IntentKind.DEMAND
    posterKind: models.PosterKind
    posterAccount: str
    domain: models.IntentDomain
    workProduct: models.WorkProduct
    deliverable: dict[str, Any]
    microRegionId: str
    assetContext: AssetContextIn
    onSiteDays: int | None = None
    remoteDays: int | None = None
    budgetMinUsdc: int
    budgetMaxUsdc: int
    availableFrom: int
    availableUntil: int
    tier: models.IntentTier = models.IntentTier.ANY
    referringPartner: str | None = None
    # Addendum A (HIADR) — optional at the schema level; the track
    # rules are enforced in post_spec when assetSubclass is present.
    assetSubclass: models.AssetSubclass | None = None
    targetArea: dict[str, Any] | None = None
    subterraneanContext: dict[str, Any] | None = None


class BidIn(BaseModel):
    intentId: str
    bidderAccount: str
    bidderKind: models.PosterKind
    amountUsdc: int
    etaHours: int | None = None
    onSiteDays: int | None = None
    remoteDays: int | None = None
    payload: dict[str, Any] = {}


class SpecView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: str
    posterKind: str
    posterAccount: str
    domain: str
    workProduct: str
    deliverable: dict[str, Any]
    microRegionId: str
    assetContext: dict[str, Any]
    assetSubclass: str | None
    targetArea: dict[str, Any] | None
    subterraneanContext: dict[str, Any] | None
    onSiteDays: int | None
    remoteDays: int | None
    budgetMinUsdc: int
    budgetMaxUsdc: int
    availableFrom: int
    availableUntil: int
    tier: str
    referringPartner: str | None
    status: str
    chainIntentRef: str | None
    bidCount: int


class BidView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    intentId: str
    bidderAccount: str
    bidderKind: str
    amountUsdc: int
    etaHours: int | None
    onSiteDays: int | None
    remoteDays: int | None
    payload: dict[str, Any]
    status: str
    chainBidRef: str | None


def _spec_view(intent: models.Intent) -> SpecView:
    return SpecView(
        id=intent.id,
        kind=intent.kind.value,
        posterKind=intent.poster_kind.value,
        posterAccount=intent.poster_account,
        domain=intent.domain.value,
        workProduct=intent.work_product.value,
        deliverable=intent.deliverable,
        microRegionId=intent.micro_region_id,
        assetContext=intent.asset_context,
        assetSubclass=intent.asset_subclass.value if intent.asset_subclass else None,
        targetArea=intent.target_area,
        subterraneanContext=intent.subterranean_context,
        onSiteDays=intent.on_site_days,
        remoteDays=intent.remote_days,
        budgetMinUsdc=intent.budget_min_usdc,
        budgetMaxUsdc=intent.budget_max_usdc,
        availableFrom=intent.available_from,
        availableUntil=intent.available_until,
        tier=intent.tier.value,
        referringPartner=intent.referring_partner,
        status=intent.status.value,
        chainIntentRef=intent.chain_intent_ref,
        bidCount=len(intent.bids),
    )


def _bid_view(bid: models.Bid) -> BidView:
    return BidView(
        id=bid.id,
        intentId=bid.intent_id,
        bidderAccount=bid.bidder_account,
        bidderKind=bid.bidder_kind.value,
        amountUsdc=bid.amount_usdc,
        etaHours=bid.eta_hours,
        onSiteDays=bid.on_site_days,
        remoteDays=bid.remote_days,
        payload=bid.payload,
        status=bid.status.value,
        chainBidRef=bid.chain_bid_ref,
    )


_POLYGON_TRACKS = {
    models.AssetSubclass.A,
    models.AssetSubclass.D,
    models.AssetSubclass.R,
}
_SUBTERRANEAN_TRACKS = {
    models.AssetSubclass.A,
    models.AssetSubclass.D,
    models.AssetSubclass.R,
}


def _validate_hiadr(body: SpecIn) -> None:
    """Addendum A §§2-3, enforced at ingestion. Specs posted without
    an assetSubclass (pre-HIADR shape) pass untouched — additive
    only. A/D/R: GeoJSON polygon required, radius invalid. H/I:
    radius (with epicenter) or polygon. A/D/R: subterraneanContext
    mandatory (§3 as resolved by DeepSeek 2026-11-08: a data-center
    track cannot be underwritten without water and soil/bedrock
    data, so D is in scope alongside A and R)."""
    subclass = body.assetSubclass
    if subclass is None:
        return
    area = body.targetArea
    if subclass in _POLYGON_TRACKS:
        if not area or area.get("type") != "Polygon" or not area.get("coordinates"):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"assetSubclass {subclass.value} requires targetArea as "
                    "a GeoJSON Polygon (radius is invalid for A/D/R tracks)"
                ),
            )
    elif area is not None:
        area_type = area.get("type")
        if area_type == "Radius":
            if area.get("epicenterLat") is None or area.get("epicenterLng") is None:
                raise HTTPException(
                    status_code=422,
                    detail="targetArea Radius requires epicenterLat and epicenterLng",
                )
        elif area_type != "Polygon":
            raise HTTPException(
                status_code=422,
                detail="targetArea must be a Radius or a GeoJSON Polygon",
            )
    if subclass in _SUBTERRANEAN_TRACKS and not body.subterraneanContext:
        raise HTTPException(
            status_code=422,
            detail=(
                f"assetSubclass {subclass.value} requires subterraneanContext "
                "(Addendum A §3)"
            ),
        )


@router.post("/specs", status_code=201)
def post_spec(body: SpecIn, db: Session = Depends(get_session)):
    if body.budgetMinUsdc > body.budgetMaxUsdc:
        raise HTTPException(
            status_code=422,
            detail="budgetMinUsdc must not exceed budgetMaxUsdc",
        )
    _validate_hiadr(body)
    if db.get(models.MicroRegion, body.microRegionId) is None:
        raise HTTPException(
            status_code=422,
            detail=f"unknown microRegionId: {body.microRegionId}",
        )
    intent = models.Intent(
        kind=body.kind,
        poster_kind=body.posterKind,
        poster_account=body.posterAccount,
        domain=body.domain,
        work_product=body.workProduct,
        deliverable=body.deliverable,
        micro_region_id=body.microRegionId,
        asset_context=body.assetContext.model_dump(mode="json"),
        asset_subclass=body.assetSubclass,
        target_area=body.targetArea,
        subterranean_context=body.subterraneanContext,
        on_site_days=body.onSiteDays,
        remote_days=body.remoteDays,
        budget_min_usdc=body.budgetMinUsdc,
        budget_max_usdc=body.budgetMaxUsdc,
        available_from=body.availableFrom,
        available_until=body.availableUntil,
        tier=body.tier,
        referring_partner=body.referringPartner,
    )
    db.add(intent)
    db.commit()
    db.refresh(intent)

    chain = near_client.post_intent(
        {
            "specId": intent.id,
            "microRegionId": intent.micro_region_id,
            "workProduct": intent.work_product.value,
            "budgetMaxUsdc": intent.budget_max_usdc,
        }
    )
    if chain.get("status") == "submitted":
        intent.chain_intent_ref = chain.get("result") or chain.get("txHash")
        db.commit()
        db.refresh(intent)
    return {**_spec_view(intent).model_dump(), "chain": chain}


@router.get("/specs/{spec_id}")
def get_spec(spec_id: str, db: Session = Depends(get_session)):
    intent = db.get(models.Intent, spec_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="spec not found")
    return _spec_view(intent)


@router.get("/specs/{spec_id}/bids")
def list_bids(spec_id: str, db: Session = Depends(get_session)):
    intent = db.get(models.Intent, spec_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="spec not found")
    return [_bid_view(bid) for bid in intent.bids]


@router.post("/bids", status_code=201)
def post_bid(body: BidIn, db: Session = Depends(get_session)):
    intent = db.get(models.Intent, body.intentId)
    if intent is None:
        raise HTTPException(status_code=404, detail="spec not found")
    if intent.status is models.IntentStatus.EXPIRED:
        raise HTTPException(status_code=410, detail="spec is EXPIRED")
    bid = models.Bid(
        intent_id=intent.id,
        bidder_account=body.bidderAccount,
        bidder_kind=body.bidderKind,
        amount_usdc=body.amountUsdc,
        eta_hours=body.etaHours,
        on_site_days=body.onSiteDays,
        remote_days=body.remoteDays,
        payload=body.payload,
    )
    db.add(bid)
    if intent.status is models.IntentStatus.POSTED:
        intent.status = models.IntentStatus.BIDDING
    db.commit()
    db.refresh(bid)

    chain = near_client.submit_bid(
        intent.chain_intent_ref or intent.id,
        {"bidId": bid.id, "amountUsdc": bid.amount_usdc},
    )
    if chain.get("status") == "submitted":
        bid.chain_bid_ref = chain.get("result") or chain.get("txHash")
        db.commit()
        db.refresh(bid)

    # Day 4 (built Day 3 evening): an agent's bid is backed by
    # executed inference — the analysis (or its honest unavailable /
    # error state) attaches to the bid payload. Inference never
    # fails a bid.
    if body.bidderKind is models.PosterKind.AGENT:
        analysis = inference.analyze_property(_spec_view(intent).model_dump())
        bid.payload = {**bid.payload, "inference": analysis}
        db.commit()
        db.refresh(bid)
    return {**_bid_view(bid).model_dump(), "chain": chain}


# --- Day 6: the read-only projections behind the human surface. ---
# D4: one backend, two projections. These endpoints exist so the
# Next.js pages in apps/uze-web render exactly what the agent API
# serves: micro-region detail with its specs, and a talent profile
# aggregated from a bidder's bids. Read-only — nothing here writes.


class MicroRegionView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    label: str
    metro: str
    region: str
    specCount: int
    comparableCount: int


def _micro_region_view(db: Session, row: models.MicroRegion) -> MicroRegionView:
    spec_count = db.query(models.Intent).filter_by(micro_region_id=row.id).count()
    comparable_count = (
        db.query(models.EventLog)
        .filter_by(
            aggregate_type="micro_region",
            aggregate_id=row.id,
            event_type="comparable.recorded",
        )
        .count()
    )
    return MicroRegionView(
        id=row.id,
        label=row.label,
        metro=row.metro,
        region=row.region,
        specCount=spec_count,
        comparableCount=comparable_count,
    )


@router.get("/micro-regions")
def list_micro_regions(db: Session = Depends(get_session)):
    rows = db.query(models.MicroRegion).order_by(models.MicroRegion.id).all()
    return [_micro_region_view(db, row) for row in rows]


@router.get("/micro-regions/{region_id}")
def get_micro_region(region_id: str, db: Session = Depends(get_session)):
    row = db.get(models.MicroRegion, region_id)
    if row is None:
        raise HTTPException(status_code=404, detail="micro-region not found")
    specs = (
        db.query(models.Intent)
        .filter_by(micro_region_id=row.id)
        .order_by(models.Intent.created_at)
        .all()
    )
    return {
        **_micro_region_view(db, row).model_dump(),
        "specs": [_spec_view(spec) for spec in specs],
    }


class TalentView(BaseModel):
    model_config = ConfigDict(frozen=True)

    account: str
    kind: str
    bidCount: int
    totalBidUsdc: int
    bids: list[BidView]


@router.get("/talent/{account}")
def get_talent(account: str, db: Session = Depends(get_session)):
    bids = (
        db.query(models.Bid)
        .filter_by(bidder_account=account)
        .order_by(models.Bid.created_at)
        .all()
    )
    if not bids:
        raise HTTPException(status_code=404, detail="talent not found")
    return TalentView(
        account=account,
        kind=bids[0].bidder_kind.value,
        bidCount=len(bids),
        totalBidUsdc=sum(bid.amount_usdc for bid in bids),
        bids=[_bid_view(bid) for bid in bids],
    )
