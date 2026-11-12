# UZE Underwrite — Technical Specification

**Status: BUILT.** Implemented in `services/compose/src/` (`agents.py`, `chart_of_accounts.py`, `email_gateway.py`, `costar.py`, `juror.py`) and covered by the compose test suite.

## 1. Agents

- **SURA** — the Hospitality & Income (HiCRE) underwriting agent. Routes built, income-producing assets: hospitality (hotel, resort, motel, trailer park) and non-hospitality income (residential rental, residential condo).
- **GIRA** — the Agriculture, Natural Resources & Development (ANRD) agent. Routes land tracks: Agriculture Surface, Natural Resources (Water, Mineral, Rare Earth, Oil/Carbon), and Development Raw Land.
- Routing is by asset track at claim/judging time. (The HICRE | ANRD claim-model restructure is ratified and lands Nov 15, 2026; the HIADR addenda it restructures are filed at `docs/hackathon/nov-2026/07-HIADR-TAXONOMY-ADDENDA.md`.)

## 2. The seven-bucket P&L taxonomy

Every financial-performance claim is normalized into **exactly one** of seven buckets (`chart_of_accounts.py`):

1. Revenue
2. Operating Expenses
3. Taxes (local / state / federal)
4. Insurance(s)
5. Interest Expense / Income
6. Miscellaneous Net Expenses / Income
7. Profit (Net Income)

**Hard rule:** Operating Expenses never absorb Taxes, Insurance, or Interest. Raw, inconsistent T-12 line-item labels from operator financials are mapped into this taxonomy before any metric is computed; unmapped labels surface as review items rather than being silently absorbed.

## 3. Ingestion

- **Email gateway** (`email_gateway.py`): a T-12 sent to the published intake address is parsed into the fixture shape the underwriter consumes — units, square footage, revenue and expense lines — and normalized through §2. Worked fixture on record: $9,400,000 price · 128 units · 96,400 sqft · NOI $504,100 · cap rate 5.5% · price per unit $73,437.50.
- **Valuation metrics:** cap rate, NOI, cost per unit, and price per square foot, computed against sales comps for the asset's micro-region — never against a whole-metro average. Micro-region is the analytical unit throughout ("Brickell, not 'Miami'").

## 4. Market data — the CoStar-shaped adapter

**The standing line: "CoStar-shaped adapter, built to the interface, license pending."**

`costar.py` defines `ICoStarProvider` — the interface the underwriting flow consumes (sales comps; STR hospitality metrics: occupancy / ADR / RevPAR; market trends) — and a mock implementation returning **synthetic** Mid-Atlantic figures. Every payload is labelled `synthetic: true`, `provider: "costar-shaped-mock"`, with the license note attached.

UZEmarkets does **not** claim a CoStar integration. CoStar is enterprise-licensed; there is no license and no live connection. Synthetic figures are illustrative demo data and must never be presented as CoStar data. When a real license exists, a live provider implements the same protocol and the mock is retired; the underwriting flow does not change.

## 5. Judging

Normalized claims are judged by the Juror Team against **same-micro-region benchmarks only** — taxes are the largest driver of micro-market variability, which is why the taxonomy isolates them. Claims that pass resolution are the reliance-grade outputs financing partners consume via the Reliance API (see `docs/specifications/07-ASSURATIES-CLAIM-RESOLUTION-EXTENSION.md`).
