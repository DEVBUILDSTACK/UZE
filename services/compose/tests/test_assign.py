"""UZE Assign (mock) — category vocabulary, listing + bid flow."""
import pytest


def test_categories_are_the_directive2_set(client):
    resp = client.get("/api/v1/assign/categories")
    assert resp.status_code == 200
    cats = resp.json()["categories"]
    assert cats == [
        "REAL_ESTATE_CONTRACT",
        "OPERATING_BUSINESS",
        "DEFUNCT_BUSINESS",
        "BANKRUPTCY_ESTATE",
        "COLLECTIBLE_CARDS",
        "FINE_ART",
        "VEHICLES",
        "ON_CHAIN_NFT",
        "SECONDARY_TICKETS",
    ]


@pytest.mark.parametrize(
    "category",
    [
        "REAL_ESTATE_CONTRACT",
        "OPERATING_BUSINESS",
        "DEFUNCT_BUSINESS",
        "BANKRUPTCY_ESTATE",
        "COLLECTIBLE_CARDS",
        "FINE_ART",
        "VEHICLES",
        "ON_CHAIN_NFT",
        "SECONDARY_TICKETS",
    ],
)
def test_every_category_can_be_listed(client, category):
    resp = client.post(
        "/api/v1/assign/listings",
        json={"category": category, "title": f"Demo {category}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["category"] == category
    assert resp.json()["mock"] is True


def test_unknown_category_refused(client):
    resp = client.post(
        "/api/v1/assign/listings",
        json={"category": "SPACESHIPS", "title": "Nope"},
    )
    assert resp.status_code == 422
    assert "closed" in resp.json()["detail"]


def test_listing_then_bid_flow(client):
    listing = client.post(
        "/api/v1/assign/listings",
        json={
            "category": "BANKRUPTCY_ESTATE",
            "title": "Estate lot 12 — warehouse contract",
            "reserve_price_usdc": 45000,
        },
    ).json()
    bid = client.post(
        f"/api/v1/assign/listings/{listing['listing_id']}/bids",
        json={"bidder": "agent-sura", "amount_usdc": 46000},
    )
    assert bid.status_code == 200
    assert bid.json()["bid_count"] == 1
    listed = client.get(
        "/api/v1/assign/listings", params={"category": "BANKRUPTCY_ESTATE"}
    ).json()
    assert listed["count"] >= 1
