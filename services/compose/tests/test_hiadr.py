"""Addendum A (HIADR) — the taxonomy rules at ingestion, and the
Content Desk pulse payload.

Rules under test (Addendum A §§2-3, as filed):
  - A/D/R require a GeoJSON Polygon targetArea; radius is invalid.
  - H/I accept a Radius (with epicenter) or a Polygon.
  - subterraneanContext is mandatory for A, D and R (Addendum A
    §3 as resolved by DeepSeek 2026-11-08 — Track D included:
    data centers need water rights and soil/bedrock data).
  - Specs without an assetSubclass (pre-HIADR shape) still post —
    the extension is additive.
The pulse tests pin the honesty contract: measured variables are
computed from real records, and pulse_data is null until the data
pipeline populates it — never fabricated.
"""

from __future__ import annotations

import copy

import models
from db import session as db_session

POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [[-80.20, 25.75], [-80.18, 25.75], [-80.18, 25.77],
         [-80.20, 25.77], [-80.20, 25.75]]
    ],
}
RADIUS = {
    "type": "Radius",
    "epicenterLat": 25.7587,
    "epicenterLng": -80.1912,
    "radiusMiles": 37.5,
}
SUBTERRANEAN = {
    "soil_analysis_depth_meters": 6,
    "resource_types": ["soil", "water"],
    "water_source": "subterranean_aquifer",
    "water_rights_owner": "landowner",
    "jurisdiction": "BR",
}


def _spec(fixture, **overrides) -> dict:
    body = copy.deepcopy(fixture["spec"])
    body.pop("posterLabel", None)
    # Start from the pre-HIADR shape; each case adds exactly what it tests.
    body.pop("assetSubclass", None)
    body.pop("targetArea", None)
    body.update(overrides)
    return body


def _post(client, body):
    return client.post("/api/v1/specs", json=body)


def test_h_track_accepts_radius_and_polygon(market_client, demo_fixture):
    r = _post(market_client, _spec(
        demo_fixture, assetSubclass="H", targetArea=RADIUS))
    assert r.status_code == 201, r.text
    assert r.json()["assetSubclass"] == "H"
    assert r.json()["targetArea"]["type"] == "Radius"

    r = _post(market_client, _spec(
        demo_fixture, assetSubclass="I", targetArea=POLYGON))
    assert r.status_code == 201, r.text
    assert r.json()["targetArea"]["type"] == "Polygon"


def test_h_track_radius_needs_epicenter(market_client, demo_fixture):
    r = _post(market_client, _spec(
        demo_fixture, assetSubclass="H",
        targetArea={"type": "Radius", "radiusMiles": 10}))
    assert r.status_code == 422, r.text
    assert "epicenterLat" in r.json()["detail"]


def test_polygon_tracks_reject_radius(market_client, demo_fixture):
    for subclass in ("A", "D", "R"):
        r = _post(market_client, _spec(
            demo_fixture, assetSubclass=subclass, targetArea=RADIUS,
            subterraneanContext=SUBTERRANEAN))
        assert r.status_code == 422, (subclass, r.text)
        assert "Polygon" in r.json()["detail"]


def test_subterranean_mandatory_for_a_d_and_r(market_client, demo_fixture):
    for subclass in ("A", "D", "R"):
        r = _post(market_client, _spec(
            demo_fixture, assetSubclass=subclass, targetArea=POLYGON))
        assert r.status_code == 422, (subclass, r.text)
        assert "subterraneanContext" in r.json()["detail"]

        r = _post(market_client, _spec(
            demo_fixture, assetSubclass=subclass, targetArea=POLYGON,
            subterraneanContext=SUBTERRANEAN))
        assert r.status_code == 201, (subclass, r.text)
        assert r.json()["subterraneanContext"]["jurisdiction"] == "BR"


def test_pre_hiadr_spec_still_posts(market_client, demo_fixture):
    r = _post(market_client, _spec(demo_fixture))
    assert r.status_code == 201, r.text
    assert r.json()["assetSubclass"] is None
    assert r.json()["targetArea"] is None


def test_pulse_shape_and_honest_zeros(market_client, demo_fixture):
    r = market_client.get("/api/v1/micro-regions/miami-brickell/pulse")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["@type"] == "Dataset"
    assert body["name"] == "Miami — Brickell Pulse"
    assert body["variableMeasured"] == {
        "spec_count": 0,
        "comparable_count": 0,
        "settled_volume_usdc": 0,
    }
    assert body["pulse_data"] is None
    assert body["agent_action"] == "POST /api/v1/specs to initiate underwriting"

    _post(market_client, _spec(
        demo_fixture, assetSubclass="H", targetArea=RADIUS))
    body = market_client.get("/api/v1/micro-regions/miami-brickell/pulse").json()
    assert body["variableMeasured"]["spec_count"] == 1
    assert body["temporalCoverage"] is not None


def test_pulse_data_passthrough_when_populated(market_client):
    pulse = {
        "prior_period_30d": {"volume": 1200000},
        "prior_period_90d": {"volume": 3900000},
        "lookback_18m": {"comps": 41},
        "lookback_36m": {"comps": 87},
    }
    with db_session() as s:
        region = s.get(models.MicroRegion, "tampa-fl")
        region.pulse_data = pulse
        s.commit()
    body = market_client.get("/api/v1/micro-regions/tampa-fl/pulse").json()
    assert body["pulse_data"] == pulse


def test_pulse_missing_region_is_404(market_client):
    r = market_client.get("/api/v1/micro-regions/nope/pulse")
    assert r.status_code == 404, r.text
