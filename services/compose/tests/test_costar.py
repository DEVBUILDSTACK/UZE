"""ICoStarProvider mock — synthetic labelling is the contract."""
import costar


def test_mock_payload_is_labelled_synthetic_everywhere():
    provider = costar.get_provider()
    for payload in (
        provider.sales_comps("baltimore-washington"),
        provider.hospitality_metrics("baltimore-washington"),
        provider.market_trends("baltimore-washington"),
    ):
        assert payload["synthetic"] is True
        assert payload["provider"] == "costar-shaped-mock"
        assert "license pending" in payload["license_note"]
        assert "not CoStar data" in payload["license_note"]


def test_sales_comps_carry_the_institutional_fields():
    comps = costar.get_provider().sales_comps("baltimore-washington")
    assert len(comps["sales_comps"]) >= 3
    for comp in comps["sales_comps"]:
        for field in ("units", "sale_price_usd", "price_per_unit_usd",
                      "price_per_sqft_usd", "cap_rate"):
            assert field in comp


def test_str_metrics_present():
    metrics = costar.get_provider().hospitality_metrics("baltimore-washington")
    h = metrics["hospitality_metrics"]
    assert 0 < h["occupancy"] < 1
    assert h["adr_usd"] > 0 and h["revpar_usd"] > 0
    # RevPAR is occupancy x ADR by definition — the synthetic
    # figures must at least obey their own arithmetic.
    assert abs(h["revpar_usd"] - round(h["occupancy"] * h["adr_usd"], 2)) < 0.05


def test_unknown_region_falls_back_with_flag(client):
    resp = client.get("/api/v1/underwrite/comps", params={"micro_region": "nowhere"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["fallback_region"] is True
    assert body["synthetic"] is True
