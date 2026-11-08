"""ParleySwap adapter scaffold pins (Sprint 2 scaffolding).

Run standalone (not part of the compose suite):
    PYTHONPATH=src python -m pytest tests/ -q

The scaffold's contract: the interface exists, the governance
fields are mandatory, and every operation refuses by name until
Nithin's program plugs in.
"""

from __future__ import annotations

import pytest

from uze_parleyswap_adapter import (
    AuctionHandle,
    AuctionTerms,
    ParleySwapNotPluggedIn,
    ScaffoldSealedBidAuctionAdapter,
    SealedBid,
)


def _terms(**overrides):
    base = dict(
        asset_ref="ag_referral:demo-1",
        reserve_price_usdc=1000.0,
        bid_window_seconds=3600,
        authorization_ref="owner-instruction:demo-1",
    )
    base.update(overrides)
    return AuctionTerms(**base)


def test_auction_terms_require_an_authorization_ref():
    with pytest.raises(TypeError):
        AuctionTerms(
            asset_ref="ag_referral:demo-1",
            reserve_price_usdc=1000.0,
            bid_window_seconds=3600,
        )


def test_scaffold_adapter_refuses_every_method():
    adapter = ScaffoldSealedBidAuctionAdapter()
    handle = AuctionHandle(
        auction_ref="scaffold", adapter_status="SCAFFOLD_UNPLUGGED"
    )
    with pytest.raises(ParleySwapNotPluggedIn):
        adapter.create_auction(_terms())
    with pytest.raises(ParleySwapNotPluggedIn):
        adapter.submit_sealed_bid(
            handle, SealedBid(bidder_ref="bidder:1", encrypted_amount="cipher")
        )
    with pytest.raises(ParleySwapNotPluggedIn):
        adapter.determine_winner(handle)
    with pytest.raises(ParleySwapNotPluggedIn):
        adapter.close_auction(handle)
