"""Unverified partner adapters for the evidence-gated A/D/R pipeline.

The interfaces are the boundary. Until commercial agreements and
technical documentation are signed and reviewed, Agro Digital and
Effatha are represented only by local mock adapters:

- no network calls;
- no assumed live API;
- no treatment ordering or execution;
- no ownership conclusion from a spatial match;
- no eligibility conclusion from an eligibility request.

The mock proposal is explicitly labelled MOCK / UNVERIFIED. It can
be stored as a ProviderProposal evidence record and can move a
referral only to FARMER_APPROVAL_PENDING through the workflow's
single-step transition guard.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class SpatialAssessmentResult:
    provider: str
    status: str
    completed: bool
    geometry: dict[str, Any]
    registry_matches: list[dict[str, Any]] = field(default_factory=list)
    confidence_score: float | None = None
    ownership_established: bool = False
    adapter_status: str = "MOCK_UNVERIFIED"


@dataclass(frozen=True)
class ProviderEligibilityResult:
    provider: str
    status: str
    eligible: bool | None
    execution_authorized: bool = False
    adapter_status: str = "MOCK_UNVERIFIED"


@dataclass(frozen=True)
class ProviderProposalResult:
    provider: str
    status: str
    proposal: dict[str, Any]
    execution_authorized: bool = False
    approval_required: bool = True
    adapter_status: str = "MOCK_UNVERIFIED"


class ISpatialProvider(Protocol):
    """Spatial-data provider boundary (Agro Digital in the plan)."""

    def assess_polygon(
        self,
        polygon: dict[str, Any],
        *,
        country_code: str | None = None,
    ) -> SpatialAssessmentResult:
        """Request a spatial assessment without treating its return
        as proof of ownership or as a completed live integration."""
        ...


class IAgTechProvider(Protocol):
    """AgTech provider boundary (Effatha in the plan)."""

    def check_eligibility(
        self,
        referral_payload: dict[str, Any],
    ) -> ProviderEligibilityResult:
        """Ask whether eligibility can be assessed. A pending result
        is not an eligibility finding."""
        ...

    def request_proposal(
        self,
        referral_payload: dict[str, Any],
    ) -> ProviderProposalResult:
        """Request a proposal for human/entity review. A proposal is
        not authorization to execute the proposed service."""
        ...


class MockAgroDigitalSpatialProvider:
    """Local Agro Digital stand-in used until a real agreement/API
    is signed and reviewed."""

    provider_name = "AGRO_DIGITAL"

    def assess_polygon(
        self,
        polygon: dict[str, Any],
        *,
        country_code: str | None = None,
    ) -> SpatialAssessmentResult:
        # Deliberately pending: the mock does not fabricate a CAR
        # match, a confidence score, or an ownership conclusion.
        return SpatialAssessmentResult(
            provider=self.provider_name,
            status="SPATIAL_ASSESSMENT_PENDING",
            completed=False,
            geometry=polygon,
            registry_matches=[],
            confidence_score=None,
            ownership_established=False,
        )


class MockEffathaAgTechProvider:
    """Local Effatha stand-in: referral/eligibility only."""

    provider_name = "EFFATHA"

    def check_eligibility(
        self,
        referral_payload: dict[str, Any],
    ) -> ProviderEligibilityResult:
        return ProviderEligibilityResult(
            provider=self.provider_name,
            status="PROVIDER_ELIGIBILITY_PENDING",
            eligible=None,
        )

    def request_proposal(
        self,
        referral_payload: dict[str, Any],
    ) -> ProviderProposalResult:
        proposal = {
            "adapter": "MOCK_UNVERIFIED",
            "service": "AGTECH_REFERRAL_ELIGIBILITY_REVIEW",
            "cropType": referral_payload.get("crop_type"),
            "productionPurpose": referral_payload.get("production_purpose"),
            "commercialTerms": None,
            "treatmentOrdered": False,
            "notes": (
                "Mock proposal for workflow verification only. No live "
                "Effatha API, treatment, price, or yield claim is assumed."
            ),
        }
        return ProviderProposalResult(
            provider=self.provider_name,
            status="PROVIDER_PROPOSAL_RECEIVED",
            proposal=proposal,
        )
