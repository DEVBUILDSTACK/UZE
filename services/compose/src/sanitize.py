"""Untrusted-input sanitization for the juror path (spec 08 §8).

Claim statements and claimed values are untrusted input: they
are written by claimants (human or agent) and later rendered
into the juror's prompt, and into precedent blocks for OTHER
claims' judgments. The classic smuggling channel for prompt
injection is invisible Unicode — characters that steer a
model (or a human reviewer) without appearing in any rendered
view of the text:

  - zero-width characters (U+200B–U+200D) and the BOM /
    zero-width no-break space (U+FEFF): word-boundary and
    tokenization games, hidden markers;
  - bidi controls (U+202A–U+202E embeddings/overrides,
    U+2066–U+2069 isolates): rendered order diverges from
    logical order — text that reads one way to a human and
    another way to a model;
  - Unicode tag characters (U+E0000–U+E007F): an entire hidden
    ASCII channel, invisible in every renderer;
  - the soft hyphen (U+00AD): invisible unless line-broken.

This module strips exactly those classes. It does not attempt
to detect or remove visible instruction-like text — that is
the juror's evidence standard and the challenge mechanism's
job. What it guarantees is narrower and total: the text the
juror sees is the text a human reviewer sees.

This is the juror-path slice of the UZEmarkets sanitization
pipeline (spec 08 §8). The full pipeline — Grok/Hermes desk
output included — is Sprint 2 scope.
"""

from __future__ import annotations

import re
from typing import Any

_INVISIBLE_RE = re.compile(
    "["
    "\u200b-\u200d"  # zero-width space, non-joiner, joiner
    "\ufeff"  # BOM / zero-width no-break space
    "\u202a-\u202e"  # bidi embeddings and overrides
    "\u2066-\u2069"  # bidi isolates
    "\U000e0000-\U000e007f"  # Unicode tag characters
    "\u00ad"  # soft hyphen
    "]"
)


def strip_invisible(text: str) -> str:
    """Remove every invisible-Unicode character of the classes
    above from a free-text string. Visible text is untouched,
    including ordinary whitespace and punctuation."""
    if not isinstance(text, str):
        return text
    return _INVISIBLE_RE.sub("", text)


def sanitize_value(value: Any) -> Any:
    """Recursively strip invisibles from the string LEAVES of a
    JSON-shaped value (dicts and lists are walked; scalars pass
    through). Dict keys are structure, not leaves, and are left
    as written."""
    if isinstance(value, str):
        return strip_invisible(value)
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_value(item) for key, item in value.items()}
    return value
