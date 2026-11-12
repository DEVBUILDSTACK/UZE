"""Evidence-gated workflow and mock-adapter tests.

These tests pin the governance boundary, not just the happy path:
- mock adapters do not fabricate live results or authorize work;
- states move only one lawful step at a time;
- a proposal reaches FARMER_APPROVAL_PENDING and stops there;
- service authorization requires an explicit consent reference;
- the sale branch requires its own owner-instruction references;
- a signed AI assessment is not scientifically verified.
"""

from __future__ import annotations

import time

import pytest

import db as db_module
import models
from agtech_adapters import (
    MockAgroDigitalSpatialProvider,
    MockEffathaAgTechProvider,
)
from agtech_workflow import (
    AuthorizationRequired,
    InvalidAgReferralTransition,
    authorize_service,
    check_provider_eligibility,
    complete_spatial_assessment,
    record_ai_assessment,
    request_provider_proposal,
    request_spatial_assessment,
    transition_ag_referral,
)

State = models.AgReferralState
POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [-57.6, -25.3], [-57.5, -25.3],
        [-57.5, -25.2], [-57.6, -25.3],
    ]],
}


def _make_referral(session, *, key="gov-1", state=State.INPUT_VALIDATED):
    referral = models.AgReferral(
        idempotency_key=key,
        state=state,
        payload={
            "schema_version": "1.0",
            "track": "A",
            "transaction_type": "agtech_referral",
            "crop_type": "CORN",
            "production_purpose": "SILAGE",
            "provider_preference": "EFFATHA",
            "provider_status": "UNVERIFIED",
            "polygon": POLYGON,
        },
        country_code=models.CountryCode.PY,
        macro_distress_exit=True,
        created_at=int(time.time()),
    )
    session.add(referral)
    session.commit()
    session.refresh(referral)
    return referral


def test_mock_adapters_return_pending_or_proposal_never_authorization():
    spatial = MockAgroDigitalSpatialProvider().assess_polygon(
        POLYGON, country_code="PY"
    )
    assert spatial.status == "SPATIAL_ASSESSMENT_PENDING"
    assert spatial.completed is False
    assert spatial.confidence_score is None
    assert spatial.registry_matches == []
    assert spatial.ownership_established is False
    assert spatial.adapter_status == "MOCK_UNVERIFIED"

    provider = MockEffathaAgTechProvider()
    eligibility = provider.check_eligibility({"crop_type": "CORN"})
    assert eligibility.status == "PROVIDER_ELIGIBILITY_PENDING"
    assert eligibility.eligible is None
    assert eligibility.execution_authorized is False

    proposal = provider.request_proposal(
        {"crop_type": "CORN", "production_purpose": "SILAGE"}
    )
    assert proposal.status == "PROVIDER_PROPOSAL_RECEIVED"
    assert proposal.approval_required is True
    assert proposal.execution_authorized is False
    assert proposal.proposal["adapter"] == "MOCK_UNVERIFIED"
    assert proposal.proposal["treatmentOrdered"] is False
    assert proposal.proposal["commercialTerms"] is None


def test_transition_guard_rejects_skips_from_intake(market_client):
    session = db_module.session()
    try:
        referral = _make_referral(session)
        for target in (
            State.SERVICE_AUTHORIZED,
            State.FINANCING_REVIEW,
            State.SALE_ELIGIBILITY_REVIEW,
            State.AUCTION_ADAPTER,
        ):
            with pytest.raises(InvalidAgReferralTransition):
                transition_ag_referral(
                    session,
                    referral,
                    target,
                    actor="test:guard",
                    authorization_reference="explicit-reference",
                )
        session.rollback()
        session.refresh(referral)
        assert referral.state is State.INPUT_VALIDATED
    finally:
        session.close()


def test_full_agtech_path_stops_at_farmer_gate_then_needs_consent(
    market_client,
):
    session = db_module.session()
    try:
        referral = _make_referral(session)

        assessment = request_spatial_assessment(session, referral)
        session.commit()
        assert referral.state is State.SPATIAL_ASSESSMENT_PENDING
        assert assessment.status == "SPATIAL_ASSESSMENT_PENDING"
        assert assessment.ownership_established is False

        # Eligibility cannot be checked before spatial evidence is
        # separately completed.
        with pytest.raises(InvalidAgReferralTransition):
            check_provider_eligibility(session, referral)
        session.rollback()
        session.refresh(referral)
        assert referral.state is State.SPATIAL_ASSESSMENT_PENDING

        complete_spatial_assessment(
            session,
            referral,
            assessment,
            registry_matches=[{"registry": "CAR", "matchId": "mock-car-1"}],
            confidence_score=0.81,
            actor="test:spatial-reviewer",
        )
        session.commit()
        assert referral.state is State.SPATIAL_ASSESSMENT_COMPLETED
        assert assessment.registry_matches[0]["matchId"] == "mock-car-1"
        # Even with a registry match and confidence score, the
        # assessment does not establish ownership.
        assert assessment.ownership_established is False

        eligibility = check_provider_eligibility(session, referral)
        session.commit()
        assert eligibility.status == "PROVIDER_ELIGIBILITY_PENDING"
        assert referral.state is State.PROVIDER_ELIGIBILITY_PENDING

        proposal = request_provider_proposal(session, referral)
        session.commit()
        assert proposal.status == "PROVIDER_PROPOSAL_RECEIVED"
        assert proposal.execution_authorized is False
        assert referral.state is State.FARMER_APPROVAL_PENDING

        with pytest.raises(AuthorizationRequired):
            authorize_service(
                session,
                referral,
                actor="test:farmer",
                consent_record_id="",
            )
        session.rollback()
        session.refresh(referral)
        assert referral.state is State.FARMER_APPROVAL_PENDING

        authorize_service(
            session,
            referral,
            actor="test:farmer",
            consent_record_id="consent-record-explicit-1",
        )
        session.commit()
        assert referral.state is State.SERVICE_AUTHORIZED
    finally:
        session.close()


def test_sale_branch_is_separately_authorized_and_cannot_skip_listing_gate(
    market_client,
):
    session = db_module.session()
    try:
        referral = _make_referral(
            session, key="gov-sale", state=State.OUTCOME_ASSESSED
        )

        with pytest.raises(AuthorizationRequired):
            transition_ag_referral(
                session,
                referral,
                State.SALE_ELIGIBILITY_REVIEW,
                actor="test:owner",
            )
        session.rollback()

        transition_ag_referral(
            session,
            referral,
            State.SALE_ELIGIBILITY_REVIEW,
            actor="test:owner",
            authorization_reference="owner-instruction-1",
        )
        session.commit()
        with pytest.raises(InvalidAgReferralTransition):
            transition_ag_referral(
                session,
                referral,
                State.AUCTION_ADAPTER,
                actor="test:owner",
                authorization_reference="owner-instruction-2",
            )
        session.rollback()
        session.refresh(referral)
        assert referral.state is State.SALE_ELIGIBILITY_REVIEW

        transition_ag_referral(
            session,
            referral,
            State.LISTING_APPROVAL_PENDING,
            actor="test:owner",
            authorization_reference="owner-instruction-2",
        )
        transition_ag_referral(
            session,
            referral,
            State.AUCTION_ADAPTER,
            actor="test:owner",
            authorization_reference="owner-instruction-3",
        )
        session.commit()
        assert referral.state is State.AUCTION_ADAPTER
    finally:
        session.close()


def test_signed_ai_assessment_is_not_scientifically_verified(market_client):
    columns = models.AIAssessment.__table__.columns
    assert {
        "calculation",
        "signed",
        "scientificallyVerified",
        "reviewStatus",
    } <= set(columns.keys())

    session = db_module.session()
    try:
        referral = _make_referral(session, key="gov-ai")
        assessment = record_ai_assessment(
            session,
            referral,
            model_version="near-ai-mock/1.0",
            input_evidence_refs=["spatial-assessment:1", "observation:1"],
            calculation={
                "baselineYield": 8.1,
                "estimatedYield": 8.7,
                "estimatedDifferencePct": 7.4,
            },
            estimated_difference_value=7.4,
            estimated_difference_unit="percent",
            signed=True,
        )
        session.commit()
        session.refresh(assessment)

        assert assessment.signed is True
        assert assessment.scientifically_verified is False
        assert assessment.review_status == "PENDING_REVIEW"
        assert assessment.calculation["estimatedDifferencePct"] == 7.4
        assert assessment.input_evidence_refs == [
            "spatial-assessment:1",
            "observation:1",
        ]
        # Recording a calculation does not assess the outcome or
        # move the referral anywhere.
        session.refresh(referral)
        assert referral.state is State.INPUT_VALIDATED
    finally:
        session.close()
