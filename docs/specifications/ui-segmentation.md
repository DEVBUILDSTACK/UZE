# /underwrite — UI Segmentation (Specification)

**Status: SPECIFICATION (owner tap, 2026-11-12).** Specifies
the three-tab segmentation of the underwrite surface. The
current /underwrite page (landing + upload + the Talent
Placement CTA added 2026-11-12) is the pre-segmentation
surface; this spec is the target layout, not a description
of what is deployed today.

## The three tabs

1. **Standard Reports** — the SKU grid (UZ-W-001…010 from
   `underwrite-sku-menu.md`). Each card: what the report
   computes, its build status, and a Generate action. The
   price shown on a card is fetched live from the
   UZEguidance priced market (published via `llms.txt`) —
   **no static price is ever rendered**.
2. **Custom Analysis** — one question field, a metrics
   picker, and the citation guarantee stated on the tab:
   every figure cites its source lines, or the answer is
   INSUFFICIENT_DATA naming what's missing.
3. **Valuation** — the UZE Evaluate form (verified NOI,
   cap rate, comps source) with the single output panel:
   implied value, price per unit, price per square foot,
   comps labelled synthetic.

Each tab carries its own pricing display (live-fetched) and
its own rate limit, and plan gating is enforced at the API,
not by hiding tabs. The Talent Placement CTA remains on the
results view in all three tabs — the underwrite names the
roles, the CTA routes to the desk that fills them.
