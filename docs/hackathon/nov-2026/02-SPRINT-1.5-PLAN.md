# SPRINT 1.5 — Seven-Day Hackathon Plan

**Sprint window:** November 7–13, 2026 (build), November 14 (submit)
**Branch:** `hackathon/nov-2026`
**Merge to main:** November 13, end of day Eastern
**Submission deadline:** November 14, 11:29 UTC

---

## The encapsulated relationship to Sprint 2

Sprint 2 (filed) is unchanged. Sprint 1.5 is Sprint 2's dress rehearsal. What Sprint 1.5 produces becomes Sprint 2's starting point:

| Sprint 1.5 artifact | Sprint 2 destination |
|---|---|
| Rust contract scaffold | Foundation for NEAR pairing contracts |
| Intent schema (additive migration) | Becomes the Sprint 2 intent contract |
| Intent API endpoints | Become the Intent Gateway's public surface |
| Chain Signatures settlement flow | Extends to ticket purchases |
| NEAR AI inference integration | Becomes the standard agent-executor pattern |
| Read-only Next.js pages | Become the human UI's first content |
| Micro-region reference table | Seeds the benchmark dataset structure |
| Four diagrams in docs/ | Living reference for the architecture |

**What is thrown away:** demo fixtures, recording, submission narrative, mocked settlement if Chain Signatures fails.
**What is kept:** every structural decision, every schema, every integration pattern.

---

## Day 1 — November 7 (tonight)

**See `01-PICKUP-TONIGHT.md` for full detail.**

Deliverables:
- Rust contract scaffold deployed to testnet
- Two named accounts created (treasury.sarah.testnet, recon.agent.testnet)
- **Chain Signatures dry-run — GO/NO-GO**
- Intent schema drafted

---

## Day 2 — November 8

**Focus:** Python orchestration layer connects to contract.

### Deliverables

**Additive compose migration** (`services/compose/migrations/versions/`):
- `MicroRegion` reference table
- `Intent` model with fields from `intent-schema.md`
- `Bid` model
- `Match` model
- From-empty replay verified

**API endpoints in `services/compose/api/intents.py`:**
```python
POST /api/v1/specs
GET  /api/v1/specs/{id}
GET  /api/v1/specs/{id}/bids
POST /api/v1/bids
```

py-near integration (services/compose/near_client.py):

· Connect to testnet
· Call post_intent, submit_bid on the deployed contract
· Read get_matches

Demo fixture data:

· One syndicate (conceptual — no account needed for the fixture)
· One human bid: treasury.sarah.testnet — $22,500, 60 days
· One agent bid: recon.agent.testnet — $4,200, 48 hours
· One spec: 340-room Aloft, Miami-Brickell

---

Day 3 — November 9

Focus: Real cross-chain settlement.

Deliverables

Chain Signatures settlement in services/compose/api/settle.py:

```python
POST /api/v1/settle
  → call contract settle(intent_id, bid_id)
  → contract requests signature from v1.signer
  → derived Solana address sends USDC
  → signature receipt returns to contract
  → settlement_event emitted
```

End-to-end flow:

1. POST /api/v1/specs
2. POST /api/v1/bids × 2
3. GET /api/v1/specs/{id}/bids
4. POST /api/v1/settle
5. Solana devnet transaction confirms
6. Receipt returns to contract

Two full dry runs.

---

Day 4 — November 10

Focus: NEAR AI inference integration.

Pre-flight check (do this first)

Verify Python 3.12+ on Assurative V2. The nearai-inference-sdk requires Python 3.12 or later. If V2 is on 3.10 or 3.11, that upgrade is blocking for this day. Report immediately if upgrade is needed.

Deliverables

services/compose/inference.py:

```python
from nearai_inference_sdk import NearAIClient

client = NearAIClient(api_key=os.environ["NEARAI_API_KEY"])

def analyze_property(spec: Intent) -> dict:
    completion = client.chat.completions.create(
        model="glm-5.3-flash",
        messages=[
            {"role": "system", "content": "You are a CRE operating cost analyst."},
            {"role": "user", "content": render_spec_as_prompt(spec)}
        ],
        e2ee=False
    )
    client.verify_response(completion.id)
    return parse_analysis(completion)
```

Agent bid now backed by executed inference:

· When agent bid posted, call analyze_property(spec)
· Capture completion.id, attestation receipt, verification result
· Attach to bid payload

---

Day 5 — November 11

Focus: x402/x401 mock flow (stretch) + diagnostic retry buffer.

If Chain Signatures is working

x402 mock in services/compose/metering.py:

· Inference endpoint returns HTTP 402 with payment requirements
· Agent signs mock authorization
· Call proceeds, mock transfer logged

x401 mock:

· Identity verification stub for tier C+ engagements
· Returns verified credential shape

If Chain Signatures is NOT working

· Mocked settlement for settle step
· Demo explicitly framed as "NEAR flow complete, Solana primitive proven separately, full integration in Sprint 2"

This is the flex day.

---

Day 6 — November 12

Focus: Read-only HTML surface + demo recording.

Read-only Next.js pages (4 hours)

app/specs/[id]/page.tsx — spec detail page with JSON-LD:

```tsx
export default async function SpecPage({ params }) {
  const spec = await fetchSpec(params.id);
  return (
    <>
      <script type="application/ld+json" 
        dangerouslySetInnerHTML={{__html: JSON.stringify(buildJsonLd(spec))}} />
      <article>
        <h1>{spec.title}</h1>
        <p>{spec.description}</p>
        <dl>
          <dt>Micro-region</dt><dd>{spec.micro_region.label}</dd>
          <dt>Budget</dt><dd>{spec.budget_min_usdc}–{spec.budget_max_usdc} USDC</dd>
        </dl>
      </article>
    </>
  );
}
```

app/talent/[handle]/page.tsx — human and agent profiles
app/micro-regions/[id]/page.tsx — micro-region page
Crawler files: app/sitemap.ts, public/robots.txt, public/llms.txt

Demo recording (afternoon/evening)

3–5 minutes, walkthrough:

1. Open spec page in browser — shows rendered HTML + JSON-LD source
2. curl the same spec as JSON
3. Show agent bid with attestation receipt
4. Show settlement: NEAR authorizes, Solana USDC transfers
5. Close on the micro-region benchmark story

---

Day 7 — November 13

Focus: Submission + buffer.

Deliverables

docs/hackathon/nov-2026/SUBMISSION.md:

· Product narrative (three asset classes, two service lines)
· Technical architecture (NEAR/Solana split, attested inference)
· Micro-region benchmark thesis
· Roadmap
· All links

docs/hackathon/nov-2026/DEMO-SCRIPT.md:

· Timestamped walkthrough

Merge to main:

```bash
git checkout main
git merge hackathon/nov-2026
git push origin main
```

---

November 14 — Submission

Submit before 11:29 UTC (06:29 Eastern).

---

Non-negotiable rules

· Additive migrations only
· From-empty replay before filing each revision
· Statement-identical proof for behavior-neutral edits
· Bidirectional tests for ledger-class bindings
· No tautological tests
· Kitchen Standard: evidence from running system
· Frozen migrations never import live application source
· USDC-only settlement invariant maintained
· No LLM in classify()
· Schema supports both surfaces; hackathon launches agent fully, human read-only

If any rule appears to block progress, surface it. Do not work around it.
