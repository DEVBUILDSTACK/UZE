"""Paraguay extension fields (DeepSeek directive, 2026-11-08).

countryCode is the dynamic country-extension axis (BR/PY/UY/US —
new markets arrive as enum members, not schema changes), and
macroDistressExit flags the dual-track posture: optimize the
asset (the Hold) while preparing its liquidation route (the
Exit). The routing these fields drive is filed in the HIADR
addenda as spec; the data-science router is Sprint 2 work.
"""

from __future__ import annotations

import copy


def _spec(fixture, **overrides) -> dict:
    body = copy.deepcopy(fixture["spec"])
    body.pop("posterLabel", None)
    body.update(overrides)
    return body


def test_paraguay_dual_track_spec_round_trips(market_client, demo_fixture):
    # A Paraguayan farm polygon (Track A) with its subterranean
    # context, flagged for the dual-track exit strategy.
    r = market_client.post("/api/v1/specs", json=_spec(
        demo_fixture,
        assetSubclass="A",
        targetArea={
            "type": "Polygon",
            "coordinates": [[
                [-57.6, -25.3], [-57.5, -25.3],
                [-57.5, -25.2], [-57.6, -25.3],
            ]],
        },
        subterraneanContext={
            "soil_analysis_depth_meters": 6,
            "resource_types": ["soil", "water"],
            "water_source": "subterranean_aquifer",
            "water_rights_owner": "landowner",
            "jurisdiction": "PY",
        },
        countryCode="PY",
        macroDistressExit=True,
        executionEnvironment="arcium_auction",
    ))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["countryCode"] == "PY"
    assert body["macroDistressExit"] is True
    assert body["subterraneanContext"]["jurisdiction"] == "PY"
    # The exit route is the Arcium pipeline tag (trust-layer pass).
    assert body["executionEnvironment"] == "arcium_auction"


def test_country_defaults_null_and_us_spec_unaffected(
    market_client, demo_fixture
):
    r = market_client.post("/api/v1/specs", json=_spec(demo_fixture))
    assert r.status_code == 201, r.text
    assert r.json()["countryCode"] is None
    assert r.json()["macroDistressExit"] is None

    r = market_client.post(
        "/api/v1/specs", json=_spec(demo_fixture, countryCode="US")
    )
    assert r.status_code == 201, r.text
    assert r.json()["countryCode"] == "US"


def test_unlisted_country_is_422(market_client, demo_fixture):
    r = market_client.post(
        "/api/v1/specs", json=_spec(demo_fixture, countryCode="AR")
    )
    assert r.status_code == 422, r.text
