"""Single-step workflow guard for evidence-gated AgReferrals.

Every state change in the A/D/R ladder goes through
``transition_ag_referral``. The transition table is the governance
spec's state machine; a caller cannot jump from intake to service
authorization, financing, or an auction adapter.

Execution-side transitions additionally require an explicit
authorization reference supplied at the moment of transition:
- SERVICE_AUTHORIZED: farmer/entity consent reference;
- FINANCING_REVIEW: explicit financing-request reference;
- SALE_ELIGIBILITY_REVIEW / LISTING_APPROVAL_PENDING /
  AUCTION_ADAPTER: explicit owner-instruction reference.

Adapter calls are evidence-producing steps, not authorization.
The mock spatial provider leaves an assessment pending. Only a
separate completion step carrying spatial evidence can complete
it. A mock provider proposal is stored as evidence and moves the
referral to FARMER_APPROVAL_PENDING — never to SERVICE_AUTHORIZED.
"""
from __future__ import annotations

import time
from typing import Any

import models
from agtech_adapters import (
    IAgTechProvider,
    ISpatialProvider,
    MockAgroDigitalSpatialProvider,
    MockEffathaAgTechProvider,
)

State = models.AgReferralState

ALLOWED_TRANSITIONS: dict[State, frozenset[State]] = {
    State.INTENT_RECEIVED: frozenset({State.INPUT_VALIDATED}),
    State.INPUT_VALIDATED: frozenset({State.SPATIAL_ASSESSMENT_PENDING}),
    State.SPATIAL_ASSESSMENT_PENDING: frozenset(
        {State.SPATIAL_ASSESSMENT_COMPLETED}
    ),
    State.SPATIAL_ASSESSMENT_COMPLETED: frozenset(
        {State.PROVIDER_ELIGIBILITY_PENDING}
    ),
    State.PROVIDER_ELIGIBILITY_PENDING: frozenset(
        {State.PROVIDER_PROPOSAL_RECEIVED}
    ),
    State.PROVIDER_PROPOSAL_RECEIVED: frozenset(
        {State.FARMER_APPROVAL_PENDING}
    ),
    State.FARMER_APPROVAL_PENDING: frozenset({State.SERVICE_AUTHORIZED}),
    State.SERVICE_AUTHORIZED: frozenset({State.SERVICE_REPORTED_ACTIVE}),
    State.SERVICE_REPORTED_ACTIVE: frozenset({State.OBSERVATIONS_COLLECTED}),
    State.OBSERVATIONS_COLLECTED: frozenset({State.OUTCOME_ASSESSED}),
    State.OUTCOME_ASSESSED: frozenset(
        {State.FINANCING_REVIEW, State.SALE_ELIGIBILITY_REVIEW}
    ),
    State.FINANCING_REVIEW: frozenset(),
    State.SALE_ELIGIBILITY_REVIEW: frozenset(
        {State.LISTING_APPROVAL_PENDING}
    ),
    State.LISTING_APPROVAL_PENDING: frozenset({State.AUCTION_ADAPTER}),
    State.AUCTION_ADAPTER: frozenset(),
}

AUTHORIZATION_REQUIRED = frozenset(
    {
        State.SERVICE_AUTHORIZED,
        State.FINANCING_REVIEW,
        State.SALE_ELIGIBILITY_REVIEW,
        State.LISTING_APPROVAL_PENDING,
        State.AUCTION_ADAPTER,
    }
)


class InvalidAgReferralTransition(ValueError):
    """Raised when a caller attempts to skip a gated state."""


class AuthorizationRequired(ValueError):
    """Raised when an execution-side transition lacks an explicit
    consent/request/owner-instruction reference."""


def transition_ag_referral(
    db,
    referral: models.AgReferral,
    target: State,
    *,
    actor: str,
    authorization_reference: str | None = None,
    evidence: dict[str, Any] | None = None,
) -> models.AgReferral:
    """Move a referral exactly one lawful step, or fail.

    The caller owns the surrounding transaction; this function
    flushes and writes the append-only EventLog row but does not
    commit.
    """
    allowed = ALLOWED_TRANSITIONS.get(referral.state, frozenset())
    if target not in allowed:
        raise InvalidAgReferralTransition(
            f"{referral.state.value} -> {target.value} is not an allowed "
            "single-step evidence-gated transition"
        )
    if target in AUTHORIZATION_REQUIRED and not authorization_reference:
        raise AuthorizationRequired(
            f"{target.value} requires an explicit authorization reference"
        )

    previous = referral.state
    referral.state = target
    db.add(
        models.EventLog(
            aggregate_type="ag_referral",
            aggregate_id=referral.id,
            event_type="ag_referral.transition",
            actor=actor,
            payload={
                "fromState": previous.value,
                "toState": target.value,
                "authorizationReferencePresent": bool(authorization_reference),
                "evidence": evidence or {},
            },
        )
    )
    db.flush()
    return referral


def request_spatial_assessment(
    db,
    referral: models.AgReferral,
    *,
    provider: ISpatialProvider | None = None,
    actor: str = "system:agtech-workflow",
) -> models.SpatialAssessment:
    """Open a spatial assessment and store the adapter result as
    evidence. The mock result remains pending; this function does
    not complete the assessment."""
    provider = provider or MockAgroDigitalSpatialProvider()
    transition_ag_referral(
        db,
        referral,
        State.SPATIAL_ASSESSMENT_PENDING,
        actor=actor,
    )
    polygon = referral.payload.get("polygon") or {}
    result = provider.assess_polygon(
        polygon,
        country_code=referral.country_code.value if referral.country_code else None,
    )
    assessment = models.SpatialAssessment(
        referral_id=referral.id,
        provider=result.provider,
        status=result.status,
        geometry=result.geometry,
        registry_matches=result.registry_matches,
        confidence_score=result.confidence_score,
        ownership_established=False,
        created_at=int(time.time()),
    )
    db.add(assessment)
    db.flush()
    return assessment


def complete_spatial_assessment(
    db,
    referral: models.AgReferral,
    assessment: models.SpatialAssessment,
    *,
    registry_matches: list[dict[str, Any]],
    confidence_score: float,
    actor: str,
) -> models.SpatialAssessment:
    """Complete a pending assessment using separately supplied
    evidence. Even a registry match does not establish ownership."""
    if assessment.referral_id != referral.id:
        raise ValueError("spatial assessment belongs to another referral")
    if referral.state is not State.SPATIAL_ASSESSMENT_PENDING:
        raise InvalidAgReferralTransition(
            "spatial assessment can only complete from "
            "SPATIAL_ASSESSMENT_PENDING"
        )
    assessment.status = State.SPATIAL_ASSESSMENT_COMPLETED.value.upper()
    assessment.registry_matches = registry_matches
    assessment.confidence_score = confidence_score
    assessment.ownership_established = False
    transition_ag_referral(
        db,
        referral,
        State.SPATIAL_ASSESSMENT_COMPLETED,
        actor=actor,
        evidence={"spatialAssessmentId": assessment.id},
    )
    return assessment


def check_provider_eligibility(
    db,
    referral: models.AgReferral,
    *,
    provider: IAgTechProvider | None = None,
    actor: str = "system:agtech-workflow",
):
    """Move to PROVIDER_ELIGIBILITY_PENDING and ask the adapter.
    The mock's pending answer is not an eligibility finding."""
    provider = provider or MockEffathaAgTechProvider()
    transition_ag_referral(
        db,
        referral,
        State.PROVIDER_ELIGIBILITY_PENDING,
        actor=actor,
    )
    return provider.check_eligibility(referral.payload)


def request_provider_proposal(
    db,
    referral: models.AgReferral,
    *,
    provider: IAgTechProvider | None = None,
    actor: str = "system:agtech-workflow",
) -> models.ProviderProposal:
    """Store a provider proposal as evidence and advance only to
    FARMER_APPROVAL_PENDING. This never authorizes a service."""
    provider = provider or MockEffathaAgTechProvider()
    if referral.state is not State.PROVIDER_ELIGIBILITY_PENDING:
        raise InvalidAgReferralTransition(
            "a provider proposal requires PROVIDER_ELIGIBILITY_PENDING"
        )
    result = provider.request_proposal(referral.payload)
    if result.execution_authorized:
        raise ValueError("an unverified adapter cannot authorize execution")
    if result.status != State.PROVIDER_PROPOSAL_RECEIVED.value.upper():
        raise ValueError(f"unexpected proposal status: {result.status}")

    proposal = models.ProviderProposal(
        referral_id=referral.id,
        provider=result.provider,
        status=result.status,
        proposal=result.proposal,
        execution_authorized=False,
        created_at=int(time.time()),
    )
    db.add(proposal)
    db.flush()
    transition_ag_referral(
        db,
        referral,
        State.PROVIDER_PROPOSAL_RECEIVED,
        actor=actor,
        evidence={"providerProposalId": proposal.id},
    )
    transition_ag_referral(
        db,
        referral,
        State.FARMER_APPROVAL_PENDING,
        actor=actor,
        evidence={"providerProposalId": proposal.id},
    )
    return proposal


def authorize_service(
    db,
    referral: models.AgReferral,
    *,
    actor: str,
    consent_record_id: str,
) -> models.AgReferral:
    """Authorize a service only from FARMER_APPROVAL_PENDING and
    only with an explicit consent reference."""
    return transition_ag_referral(
        db,
        referral,
        State.SERVICE_AUTHORIZED,
        actor=actor,
        authorization_reference=consent_record_id,
    )


def record_ai_assessment(
    db,
    referral: models.AgReferral,
    *,
    model_version: str,
    input_evidence_refs: list[str],
    calculation: dict[str, Any],
    estimated_difference_value: float | None = None,
    estimated_difference_unit: str | None = None,
    signed: bool = False,
) -> models.AIAssessment:
    """Persist an AI calculation without certifying it.

    The record always starts as PENDING_REVIEW with
    scientifically_verified=False — including when signed=True.
    Scientific verification is a separate review outcome, never a
    side effect of a signature.
    """
    assessment = models.AIAssessment(
        referral_id=referral.id,
        model_version=model_version,
        input_evidence_refs=input_evidence_refs,
        calculation=calculation,
        estimated_difference_value=estimated_difference_value,
        estimated_difference_unit=estimated_difference_unit,
        signed=signed,
        scientifically_verified=False,
        review_status="PENDING_REVIEW",
        created_at=int(time.time()),
    )
    db.add(assessment)
    db.flush()
    return assessment
