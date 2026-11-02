"""Settlement-currency invariant (filed 2026-11-01): USDC only.

USDC on Solana is the sole commerce settlement rail. The Price type is
shared by OfferSnapshot (frozen at quote time) and TripCandidate, and
its generated Pydantic form must REJECT any non-USDC currency at
validation — enforcement at the compose layer on every write, not a
docstring. UZE is measurement/attribution only; UZD is an incentive
token; neither may ever appear in a price.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from offersnapshot_pydantic import Price as SnapshotPrice
from tripcandidate_pydantic import Price as CandidatePrice


@pytest.mark.parametrize("price_cls", [SnapshotPrice, CandidatePrice])
@pytest.mark.parametrize("bad", ["USD", "EUR", "UZE", "UZD", "SOL", "usdc", ""])
def test_non_usdc_currency_rejected(price_cls, bad):
    with pytest.raises(ValidationError):
        price_cls(amount=10.0, currency=bad, taxesIncluded=True)


@pytest.mark.parametrize("price_cls", [SnapshotPrice, CandidatePrice])
def test_usdc_accepted(price_cls):
    price = price_cls(amount=10.0, currency="USDC", taxesIncluded=True)
    assert price.currency.value == "USDC"
