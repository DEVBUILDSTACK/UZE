"""ICoStarProvider — the CoStar-shaped data adapter (MOCK).

Built 2026-11-11 on the owner's tap, under his standing
correction on the overclaim: WE DO NOT CLAIM a CoStar
integration. CoStar is enterprise-licensed; there is no license
and no live connection. What exists is:

  - The INTERFACE (ICoStarProvider) shaped to the fields the
    underwriting flow consumes: sales comps, STR hospitality
    metrics (occupancy / ADR / RevPAR), and market trends.
  - A MOCK implementation returning SYNTHETIC Baltimore-
    Washington figures, labelled synthetic in every payload
    (synthetic: true, provider: "costar-shaped-mock", and the
    license note verbatim). Synthetic figures are illustrative
    demo data — they are NOT CoStar data and must never be
    presented as CoStar data in any surface or pitch.

The narrative line, per the owner's ruling: "CoStar-shaped
adapter, built to the interface, license pending."

When a real license exists, a live provider implements the
same protocol and the mock is retired; the underwriting flow
does not change.
"""

from __future__ import annotations

from typing import Any, Protocol

from fastapi import APIRouter
from fastapi.responses import JSONResponse

LICENSE_NOTE = (
    "CoStar-shaped adapter, built to the interface, license "
    "pending. Figures are SYNTHETIC demo data — not CoStar data."
)


class ICoStarProvider(Protocol):
    """The comps/metrics surface the underwriting flow reads."""

    def sales_comps(self, micro_region: str) -> dict[str, Any]: ...

    def hospitality_metrics(self, micro_region: str) -> dict[str, Any]: ...

    def market_trends(self, micro_region: str) -> dict[str, Any]: ...


# Synthetic Baltimore-Washington demo data. Plausible magnitudes
# for the market; invented for the demo; labelled as such.
_SYNTHETIC: dict[str, dict[str, Any]] = {
    "baltimore-washington": {
        "sales_comps": [
            {
                "asset": "Select-service hotel, Baltimore Inner Harbor",
                "units": 142,
                "sale_price_usd": 13200000,
                "price_per_unit_usd": 92958,
                "price_per_sqft_usd": 141.20,
                "cap_rate": 0.0575,
                "sold": "2026-06",
            },
            {
                "asset": "Extended-stay hotel, BWI corridor",
                "units": 118,
                "sale_price_usd": 10450000,
                "price_per_unit_usd": 88559,
                "price_per_sqft_usd": 128.40,
                "cap_rate": 0.0590,
                "sold": "2026-03",
            },
            {
                "asset": "Limited-service hotel, Washington DC suburbs (MD)",
                "units": 96,
                "sale_price_usd": 9100000,
                "price_per_unit_usd": 94792,
                "price_per_sqft_usd": 136.75,
                "cap_rate": 0.0560,
                "sold": "2025-11",
            },
        ],
        "hospitality_metrics": {
            "occupancy": 0.684,
            "adr_usd": 158.40,
            "revpar_usd": 108.35,
            "period": "Trailing 12 months",
            "source_label": "STR-shaped (synthetic)",
        },
        "market_trends": {
            "rent_growth_yoy": 0.031,
            "absorption_units_12m": 1840,
            "supply_pipeline_units": 2260,
            "cap_rate_band": [0.0525, 0.0600],
        },
    }
}


def _envelope(micro_region: str, section: str, data: Any) -> dict[str, Any]:
    return {
        "provider": "costar-shaped-mock",
        "synthetic": True,
        "license_note": LICENSE_NOTE,
        "micro_region": micro_region,
        section: data,
    }


class MockCoStarProvider:
    """ICoStarProvider over the synthetic fixture set. Unknown
    regions return the Baltimore-Washington set with the region
    echoed and a fallback flag — never a silent substitution."""

    def _region(self, micro_region: str) -> tuple[str, dict[str, Any], bool]:
        key = (micro_region or "").strip().lower()
        if key in _SYNTHETIC:
            return key, _SYNTHETIC[key], False
        return key, _SYNTHETIC["baltimore-washington"], True

    def sales_comps(self, micro_region: str) -> dict[str, Any]:
        key, region, fallback = self._region(micro_region)
        out = _envelope(key, "sales_comps", region["sales_comps"])
        out["fallback_region"] = fallback
        return out

    def hospitality_metrics(self, micro_region: str) -> dict[str, Any]:
        key, region, fallback = self._region(micro_region)
        out = _envelope(key, "hospitality_metrics", region["hospitality_metrics"])
        out["fallback_region"] = fallback
        return out

    def market_trends(self, micro_region: str) -> dict[str, Any]:
        key, region, fallback = self._region(micro_region)
        out = _envelope(key, "market_trends", region["market_trends"])
        out["fallback_region"] = fallback
        return out


def get_provider() -> ICoStarProvider:
    """The provider the app serves. A live licensed provider
    replaces the mock here, and only here."""
    return MockCoStarProvider()


router = APIRouter(prefix="/api/v1/underwrite", tags=["underwrite-data"])


@router.get("/comps")
async def comps(micro_region: str = "baltimore-washington"):
    provider = get_provider()
    sales = provider.sales_comps(micro_region)
    return JSONResponse(
        content={
            **sales,
            "hospitality_metrics": provider.hospitality_metrics(micro_region)[
                "hospitality_metrics"
            ],
            "market_trends": provider.market_trends(micro_region)["market_trends"],
        }
    )
