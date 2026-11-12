# UZE Master Audit — The Ecosystem

**HiCRE underwriting · Inference Treasury · Information
Markets · Tier Pricing.** One document for the analyst and
the lead engineer. Filed 2026-11-12 · suite **327 passed** ·
documentation only.

**Status legend:** 🟢 VERIFIED BUILT · 🟡 BUILT AS MOCK ·
🔴 PROPOSAL — not built.

**The headline correction, stated once and plainly:** the
commissioning brief for this document asserts a dynamic
tier-pricing mechanism whose price "is frozen for a 24-hour
cycle, resetting at exactly 10:29:59 UTC", and asks for the
code snippet and line numbers where that freeze is
calculated. **No such logic exists.** A full-text search for
`10:29`, "pricing freeze" and "dynamic pricing" across the
UZE repository, the venue-ticketing repository and the
internal architecture KB returns zero hits. There is no
snippet to quote, and none is fabricated here. The mechanism
is documented in Part 4 as what it is: a 🔴 PROPOSAL. Every
other part separates built state from vision the same way.

---

# Part 1 — The HiCRE Underwriting Engine 🟢/🟡

Covered definitively in `docs/UZE-MASTER-AUDIT-HICRE.md`;
the summary and proof:

The **Universal Parser** (`proforma.py`) ingests .xlsx,
.xlsm, legacy .xls, CSV, and link-shared Google Sheets through
one grid extractor — identical file, identical math, any
container (`test_all_formats_produce_identical_math`).
**SURA** standardizes historicals into the seven-bucket
taxonomy (Revenue · Operating Expenses · Taxes · Insurance(s)
· Interest Expense/Income · Miscellaneous Net · Profit),
keeps Taxes and Insurance out of OpEx, and derives **unlevered
NOI** (interest appears only in the separately named levered
cash flow).

**Proof — Graham Hill** (152 units, Mechanicsburg PA; the
workbook's own cached values as the standard): GPR 3,340,080
→ EGI **3,288,199.76** → NOI **$1,947,713.77** in Year 1, and
2,030,527.85 / 2,084,983.68 / 2,141,301.19 / 2,199,536.23 in
Years 2–5 (3% rent and expense growth, reserve escalating
$200→$400/unit), every year matching the file to the cent.
Valuation: Year 1 NOI at the labelled 5.5% parameter rate →
$35,412,977.66; $232,980.12 per unit. 🟡 labels that ride
along: email-surface extraction is a mock; comps are a
synthetic CoStar-shaped adapter, license pending.

# Part 2 — The Inference Treasury for Agents 🟡

**What exists** (`treasury.py`, `treasury_router.py`,
`inference.py`):

- An agent treasury surface with **structurally real,
  explicitly mocked execution**: a tiered onramp ladder
  ($5–100 in $5 steps, $101–250 in $10, $251–1,750 in $50,
  everything else refused), self-custodial Send & Receive,
  default settlement in Solana USDC. No real funds move; no
  private keys exist in the service.
- **Swap quotes are genuinely live**: `_oneclick_quote` calls
  the NEAR Intents 1Click API and returns wet quotes (verified
  in production testing — e.g. 0.01 Base ETH → ≈5.636 wNEAR).
  Chains absent from the 1Click registry are refused (Ink
  returns 422). Quotes are real; execution is not wired.
- **Inference is wired and honestly blocked**: the NEAR AI
  presenter calls the live API with the owner's key; both
  orgs currently hold $0.00 balance, so the endpoint returns
  the provider's 402 — the demo's locked "402 beat". The code
  fires live the moment a balance exists.

**What does not exist** (🔴 PROPOSAL): agents autonomously
holding/staking NEAR or USDC to *fund their own inference* —
the "Strategic Treasury" loop — is a design direction, not a
running system; no staking, no balance-driven routing, no
self-funding agent exists in the code. The **"Opaque Credit
Engine"** is a name that arrived in a relayed directive
package (2026-11-12) and was never ratified or built; dynamic
compute-credit provisioning without exposed infrastructure
cost is, at most, a label for the mocked-execution posture
above. This audit records both as proposals so nobody quotes
them as product.

# Part 3 — Prediction & Information Markets 🟡/🔴

**What exists** (`ticketing.py`, the venue demo): holders of
a **primary** ticket for an event submit scalar price calls
for the settled secondary price of a focus sector/ring
(secondary holders and prize winners are refused — you must
own the asset to price its secondary market). Calls are
transformed into **threshold binary markets**: quartile
thresholds rounded to round levels, initial Yes = the share
of calls above the threshold (at-threshold counts one half) —
the empirical seed for an LMSR maker. Markets return as
`mock_proposed`; the partner demo ranks calls and mints
pair/single prizes **in its front-end**, against a mock
settled price.

**What does not exist** (🔴 PROPOSAL): there is **no Gensyn
settlement oracle** connected to anything, and **no feedback
loop from market results into any pricing engine**. The
production design — markets resolving on the actual NEAR
solver clearing price, with a settlement connector — is
specified in `docs/GENSYN-BRIDGE-SPEC.md` as the grant-funded
build. Delphi and Gensyn are internal plumbing names; the
public product is the **UZE Event Market**.

# Part 4 — Tier Pricing: x401/x402, the Word Graph, and the 10:29:59 Proposal

## What is published and built 🟢/🟡

The **Word Graph** tiers, as published (the page is the
product — a headless agentic publication brands private-label;
the 2026-10-31 edition is the filed sample):

| Tier | For | What you get | How it meters |
|---|---|---|---|
| **Plug In** | Aligned SMEs with their own stack and agents to feed | Free trial plug-in, then the Word Graph data + publishing, white-labelled | Free trial, then **x402 Pay-As-You-Go** — founding rates locked for early affiliates |
| **Advisory** | Teams designing their content operation now | A free advisory call: an agent-guided stack, or an autonomous curated stack modeled on ours | **Free** |
| **Managed Desk** | Teams who want the desk run for them | A custom Content Desk application — provisioned, operated, iterated as a managed service | Provisioning engagement — scoped on the call |

The metering machinery behind the tiers (`metering.py`,
`builders.py`): x402 payment requirements with a **mock**
authorization verifier (labelled as such in code —
`build_mock_authorization` / `validate_mock_authorization`),
an x401 identity-verification endpoint, and amount bands that
escalate requirements — under $29.99: x402 only · $30–199.99:
x402 + x401 credential carrying an entityId · over $199.99:
plus entity KYB. Builder onboarding matches: email + x401
wallet, `entity_id` stays NULL until a transaction over
$199.99 or a syndicate join triggers KYB.

**The one dynamic-pricing mechanism that actually exists**
is adjacent: **UZEguidance priced markets** on /guidance —
the participation levels (UZEBuilder · UZEaffiliate ·
UZEaffiliate actively onramped uzing TradeLayer or SigLayer)
carry no posted prices; the market bids them, and UZEmarkets
honors the results prospectively for KYB entities and KYC
partner agents signing up Nov 15, 2026 – Jan 12, 2027
(`/alpha` intake is live). Dynamic pricing in this ecosystem
is real — for participation levels, on that window, by that
mechanism.

## The 10:29:59 UTC daily freeze — 🔴 PROPOSAL, NOT BUILT

The proposed extension: entity-verified agents (x401 identity
+ x402 rails) would *determine tier pricing dynamically* —
bids from verified agents setting the Plug In / Advisory /
Managed Desk rates on a daily cycle, the price **frozen for
24 hours at a daily reset of 10:29:59 UTC**. Recorded here as
a proposal at the owner's direction, with its status
unambiguous:

- **No code implements it.** No pricing job, no freeze
  timestamp, no tier-price market exists in any repository
  (search evidence in the header note).
- **No test covers it**; the 327-test suite contains no
  pricing-freeze test, and Part 5 does not invent one.
- **Open design questions** a build would have to answer:
  the bidding instrument (an extension of the UZEguidance
  priced-markets pattern is the obvious candidate), the
  weighting of verified-agent bids, manipulation resistance
  for thin markets, the fallback price when no bids clear,
  and why 10:29:59 UTC — a reset time no filed document
  currently justifies.

When and if the owner ratifies it, this section gets
rewritten with the snippet. Until then, anyone quoting a
10:29:59 freeze as product is quoting this proposal page
without its label.

# Part 5 — The Code Stack (for the lead engineer)

| Area | Modules (`services/compose/src/`) |
|---|---|
| Universal Parser + pro forma | `proforma.py` (grids: openpyxl / xlrd / csv; guarded Sheets fetch; one extractor) |
| Taxonomy + historical math | `chart_of_accounts.py`, `email_gateway.py` (`analyze_multiyear`), `underwrite_engine.py` (Tiers 1–5) |
| Treasury | `treasury.py` (onramp ladder, send/receive, `_oneclick_quote`, `/swap`), `treasury_router.py`, `chain_sig.py`, `settle.py` / `settlement.py` (testnet settlement of record) |
| Inference | `inference.py` (NEAR AI presenter; honest 402 while org balance is $0) |
| Ticketing + Delphi bridge | `ticketing.py` (mint/list/transfer/verify, holder-gated calls, `derive_markets`) |
| Metering + identity | `metering.py` (x402 requirements + mock verifier, x401 identity), `builders.py` (registry), `trust.py` (AssurativeV2 trust layer), `alpha.py` (priced-market intake) |
| Auctions + assign | `auctions.py` (Commitment Ladder), `assign.py`, `contributions.py` |

**The 10:29:59 UTC logic:** there is none to cite. The
verification performed for this audit: full-text search of
DEVBUILDSTACK/UZE (all files), DEVBUILDSTACK/uze-venue-ticketing,
and the internal architecture KB for `10:29`, `pricing freeze`,
`dynamic pricing` — **zero matches**. The honest entry in a
code audit is this paragraph.

**The test suite:** 327 passed at filing. Highlights by area:
pro forma & formats (`test_proforma.py`, 15 — Graham Hill
five-year match, identical-math across formats, Sheets guards,
blind hardening, gateway routing) · taxonomy & NOI
(`test_chart_of_accounts.py`, `test_email_gateway.py`,
`test_underwrite_metrics.py`) · tiers & verification
(`test_underwrite_engine.py`) · ticketing & Delphi
(`test_ticketing.py`) · alpha intake (`test_alpha.py`).
No pricing-freeze test exists, because no pricing freeze
exists.
