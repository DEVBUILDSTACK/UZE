"""UZEmarkets adapter interface for ParleySwap — Sprint 2 scaffold.

The interface is the plug-in surface for Nithin Mengani's
ParleySwap (Arcium MPC sealed-bid auctions). The scaffold
implementation raises :class:`ParleySwapNotPluggedIn` from every
method: nothing here talks to Arcium, Anchor, or Solana.
"""
from __future__ import annotations

from .interface import (
    AuctionCloseout,
    AuctionHandle,
    AuctionTerms,
    ISealedBidAuctionAdapter,
    ParleySwapNotPluggedIn,
    ScaffoldSealedBidAuctionAdapter,
    SealedBid,
    SealedBidReceipt,
    WinnerResult,
)

__all__ = [
    "AuctionCloseout",
    "AuctionHandle",
    "AuctionTerms",
    "ISealedBidAuctionAdapter",
    "ParleySwapNotPluggedIn",
    "ScaffoldSealedBidAuctionAdapter",
    "SealedBid",
    "SealedBidReceipt",
    "WinnerResult",
]
