"""StandardChartOfAccounts — line-item normalization into the
ratified seven-bucket P&L taxonomy.

Built 2026-11-11 on the owner's tap ("Build the SURA/CoStar
mock"), under his standing corrections:

  - The mapping target is the FULL P&L TAXONOMY ratified
    2026-11-10 (Spec 07 §2.2): exactly seven buckets — Revenue;
    Operating Expenses; Taxes (local/state/federal);
    Insurance(s); Interest Expense/Income; Miscellaneous Net
    Expenses/Income; Profit (Net Income). Every normalized
    figure lands in exactly one bucket.
  - Operating Expenses NEVER absorb Taxes, Insurance, or
    Interest. The variant table below routes every known tax,
    insurance, and interest label to its own bucket, and the
    test suite pins that no variant of those three families
    can land in Operating Expenses.
  - Multi-year T-12s arrive with inconsistent labels across
    years and firms ("Repairs & Maintenance" one year, "R&M"
    the next, "Maintenance Expense" the third). Normalization
    is label-based: case/punctuation-insensitive exact match
    against the variant table. A label with no variant is NOT
    guessed — it is returned in `unmapped` for human review.
    Silently mis-bucketing a tax line as an expense is exactly
    the failure this layer exists to prevent.

This module is deterministic and side-effect free: raw
{label: amount} in, bucketed totals + unmapped labels out.
"""

from __future__ import annotations

import re
from typing import Any

# The seven ratified buckets (Spec 07 §2.2), in filing order.
BUCKETS: tuple[str, ...] = (
    "Revenue",
    "Operating Expenses",
    "Taxes",
    "Insurance(s)",
    "Interest Expense/Income",
    "Miscellaneous Net Expenses/Income",
    "Profit (Net Income)",
)

# label-variant -> bucket. Keys are stored pre-normalized
# (lowercase, punctuation collapsed) — see _key().
_VARIANTS: dict[str, str] = {
    # Revenue
    "room revenue": "Revenue",
    "rooms revenue": "Revenue",
    "rental income": "Revenue",
    "rent income": "Revenue",
    "gross potential rent": "Revenue",
    # Contra-revenue (owner tap, 2026-11-12): vacancy and credit
    # losses are revenue deductions, filed as negative amounts or
    # deduction lines — sign is the caller's convention and is
    # preserved, so they net against Revenue rather than inflating
    # an expense bucket or surfacing as unmapped.
    "vacancy loss": "Revenue",
    "vacancy losses": "Revenue",
    "vacancy credit loss": "Revenue",
    "vacancy and credit loss": "Revenue",
    "credit loss": "Revenue",
    "credit losses": "Revenue",
    "credit loss bad debt": "Revenue",
    "vacancy loss credit loss": "Revenue",
    "bad debt": "Revenue",
    "bad debt expense": "Revenue",
    "other income": "Revenue",
    "total revenue": "Revenue",
    "total income": "Revenue",
    "revenue": "Revenue",
    # Operating Expenses (never taxes / insurance / interest)
    "repairs maintenance": "Operating Expenses",
    "rm": "Operating Expenses",
    "maintenance expense": "Operating Expenses",
    "maintenance": "Operating Expenses",
    "payroll": "Operating Expenses",
    "salaries wages": "Operating Expenses",
    "utilities": "Operating Expenses",
    "management fee": "Operating Expenses",
    "management fees": "Operating Expenses",
    "marketing": "Operating Expenses",
    "general administrative": "Operating Expenses",
    "ga": "Operating Expenses",
    "operating expenses": "Operating Expenses",
    "total operating expenses": "Operating Expenses",
    # Taxes — its own bucket, always
    "real estate taxes": "Taxes",
    "property tax": "Taxes",
    "property taxes": "Taxes",
    "taxes": "Taxes",
    "state taxes": "Taxes",
    "local taxes": "Taxes",
    "federal taxes": "Taxes",
    # Insurance — its own bucket, always
    "insurance": "Insurance(s)",
    "hazard insurance": "Insurance(s)",
    "property insurance": "Insurance(s)",
    "liability insurance": "Insurance(s)",
    "crop insurance": "Insurance(s)",
    # Interest — its own bucket, always
    "interest expense": "Interest Expense/Income",
    "mortgage interest": "Interest Expense/Income",
    "interest income": "Interest Expense/Income",
    "interest": "Interest Expense/Income",
    # Miscellaneous net
    "miscellaneous": "Miscellaneous Net Expenses/Income",
    "misc net": "Miscellaneous Net Expenses/Income",
    "other expenses net": "Miscellaneous Net Expenses/Income",
    # Profit
    "net income": "Profit (Net Income)",
    "net operating income": "Profit (Net Income)",
    "noi": "Profit (Net Income)",
    "profit": "Profit (Net Income)",
}


def _key(label: str) -> str:
    """Normalize a raw line-item label for variant matching:
    lowercase, '&' -> ' and ' collapsed away, punctuation and
    repeated whitespace removed."""
    k = label.lower().replace("&", " ")
    k = re.sub(r"[^a-z0-9 ]+", " ", k)
    return re.sub(r"\s+", " ", k).strip()


def bucket_for(label: str) -> str | None:
    """The ratified bucket for one raw label, or None when the
    label has no filed variant (never guessed)."""
    key = _key(label)
    # Try the spaced form, then the squashed form ("R&M" -> "rm").
    return _VARIANTS.get(key) or _VARIANTS.get(key.replace(" ", ""))


def normalize_line_items(items: dict[str, float]) -> dict[str, Any]:
    """Bucket one period's raw line items.

    Returns {buckets: {bucket: total for all seven, in filing
    order}, unmapped: [{label, amount}] for labels with no
    filed variant}. Amounts are summed per bucket; sign is the
    caller's convention and is preserved."""
    totals: dict[str, float] = {b: 0.0 for b in BUCKETS}
    unmapped: list[dict[str, Any]] = []
    for label, amount in items.items():
        bucket = bucket_for(label)
        if bucket is None:
            unmapped.append({"label": label, "amount": amount})
        else:
            totals[bucket] += float(amount)
    return {"buckets": totals, "unmapped": unmapped}
