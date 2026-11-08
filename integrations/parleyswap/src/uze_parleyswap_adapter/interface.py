"""The sealed-bid auction adapter interface (Sprint 2 scaffold).

Mirrors the shape of Nithin's ParleySwap program
(``programs/sealed_bid_auction`` + ``encrypted-ixs`` in
Nithin-Varma/parleySwap): an auction is created with terms, bids
are submitted sealed (encrypted — the adapter never sees a
plaintext bid amount outside the MPC boundary), the winner is
determined inside the encrypted computation, and the auction is
closed out. Settlement is NOT part of this interface: compose
settles USDC on Solana through its own settlement path, keeping
auction execution and settlement as distinct stages (governance
spec 06, §4).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class ParleySwapNotPluggedIn(RuntimeError):
    """Raised by the scaffold adapter: ParleySwap is not plugged
    in yet. Sprint 2 replaces the implementation, not this
    interface."""


@dataclass(frozen=True)
class AuctionTerms:
    """Terms for creating a sealed-bid auction.

    ``asset_ref`` is a plain string reference to the compose-side
    asset/intent (R4: reference, never a foreign key).
    ``authorization_ref`` carries the governance reference that
    allowed the auction adapter to be entered at all (the owner
    instruction behind LISTING_APPROVAL_PENDING →
    AUCTION_ADAPTER).
    """

    asset_ref: str
    reserve_price_usdc: float | None
    bid_window_seconds: int
    authorization_ref: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuctionHandle:
    auction_ref: str  # the auction program's id — a string reference
    adapter_status: str  # e.g. "SCAFFOLD_UNPLUGGED" until Sprint 2


@dataclass(frozen=True)
class SealedBid:
    bidder_ref: str  # bidder identity reference (string, R4)
    encrypted_amount: str  # ciphertext — never a plaintext amount


@dataclass(frozen=True)
class SealedBidReceipt:
    auction_ref: str
    bid_ref: str
    accepted: bool


@dataclass(frozen=True)
class WinnerResult:
    auction_ref: str
    winner_ref: str | None  # None until determined
    determined: bool  # False while the MPC computation has not run


@dataclass(frozen=True)
class AuctionCloseout:
    auction_ref: str
    closed: bool
    settlement_ref: str | None  # compose settlement reference, if any


class ISealedBidAuctionAdapter(Protocol):
    """The only surface compose calls for sealed-bid auctions."""

    def create_auction(self, terms: AuctionTerms) -> AuctionHandle:
        ...

    def submit_sealed_bid(
        self, handle: AuctionHandle, bid: SealedBid
    ) -> SealedBidReceipt:
        ...

    def determine_winner(self, handle: AuctionHandle) -> WinnerResult:
        ...

    def close_auction(self, handle: AuctionHandle) -> AuctionCloseout:
        ...


class ScaffoldSealedBidAuctionAdapter:
    """Scaffold implementation: every method refuses, by name."""

    def _refuse(self, method: str) -> None:
        raise ParleySwapNotPluggedIn(
            f"ParleySwap adapter is a Sprint 2 scaffold; {method} is "
            "not plugged in (Nithin's sealed_bid_auction program + "
            "encrypted-ixs land behind this interface)"
        )

    def create_auction(self, terms: AuctionTerms) -> AuctionHandle:
        self._refuse("create_auction")
        raise AssertionError("unreachable")

    def submit_sealed_bid(
        self, handle: AuctionHandle, bid: SealedBid
    ) -> SealedBidReceipt:
        self._refuse("submit_sealed_bid")
        raise AssertionError("unreachable")

    def determine_winner(self, handle: AuctionHandle) -> WinnerResult:
        self._refuse("determine_winner")
        raise AssertionError("unreachable")

    def close_auction(self, handle: AuctionHandle) -> AuctionCloseout:
        self._refuse("close_auction")
        raise AssertionError("unreachable")
