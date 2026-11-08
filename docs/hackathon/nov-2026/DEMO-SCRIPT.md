<!--
  DRAFT — Sprint 1.5 Day 7 deliverable, drafted early (Nov 8) per
  DeepSeek's unblocked-work directive. Follows Diagram 3
  (docs/diagrams/03-end-to-end-sequence.md) phase for phase, in the
  Day 6 walkthrough order. Target runtime 3-5 minutes. Refresh the
  [STATE] notes at recording time (Nov 12).
-->

# DEMO SCRIPT — UZEMARKETS Sprint 1.5 (3–5 minutes)

## Setup (before recording)

- Compose API running on :8100 against the demo database
  (`scripts/seed_demo.py` for the read-only beats; the live flow
  below posts its own spec, so no seed is required for Beats 2–5).
- Web surface running on :3000.
- Browser tabs open: (1) the spec page after Beat 2, (2) Solana
  Explorer on **Devnet** for the payer address
  `5za47wLNFUJyqXhT2eTjeTNC1NsuJpnqLbvHBLBjG8Fy`, (3) NEAR Explorer
  on testnet for `uzemarkets-talent.testnet`.
- Terminal with the compose venv active; `$SPEC_ID` set from
  Beat 2's output.
- [STATE] Record after the Day 4 live inference run and the funded
  settlement broadcast, so Beats 3 and 5 show the real attestation
  and a real Solana receipt. Fallbacks are written into each beat
  and are honest — use them rather than staging anything.

## Beat 1 — The thesis (0:00–0:35)

**On screen:** the micro-regions index page (`/micro-regions`).

**Say:** "Real estate analysis is priced by relationship and takes
weeks. UZEMARKETS makes it a market — and the unit of analysis is
the micro-region. Not Miami: Brickell. Every property analyzed here
becomes a comparable that makes the next benchmark in that
neighborhood better."

## Beat 2 — Phase 1: the spec (0:35–1:20)

**Action (terminal):** post the demo spec through the agent API:

```
curl -s -X POST localhost:8100/api/v1/specs -H 'Content-Type: application/json' -d @scripts/fixtures/demo-spec.json
```

**On screen:** the returned JSON (note the NEAR chain ref), then
cut to the browser: the same spec as a rendered page at
`/specs/$SPEC_ID`. View source for one beat on the
`application/ld+json` block.

**Say:** "A syndicate acquiring a 340-room Aloft in Brickell posts
its specification. One backend, two projections: agents get JSON,
humans get this page — same fields, with schema.org markup so
search engines and other agents can read the market too."

## Beat 3 — Phase 2: bidding, with proof of work (1:20–2:20)

**Action (terminal):** post the human bid, then the agent bid:

```
curl -s -X POST localhost:8100/api/v1/bids -H 'Content-Type: application/json' -d "$(jq --arg id "$SPEC_ID" '. + {intentId: $id}' scripts/fixtures/demo-bid-human.json)"
curl -s -X POST localhost:8100/api/v1/bids -H 'Content-Type: application/json' -d "$(jq --arg id "$SPEC_ID" '. + {intentId: $id}' scripts/fixtures/demo-bid-agent.json)"
curl -s localhost:8100/api/v1/specs/$SPEC_ID/bids
```

**On screen:** the bids JSON — $22,500 / 60 days (human) against
$4,200 / 48 hours (agent), and the agent bid's `payload.inference`:
the analysis and its attestation receipt.

**Say:** "The agent's bid is not a promise. Before it was submitted,
the spec was rendered to a prompt and analyzed inside NEAR AI
Cloud's attested enclave; the receipt is attached to the bid and
verified. [STATE fallback if the key is not yet live: the bid
carries inference status 'unavailable' — say exactly that: the
marketplace never fabricates an attestation.]"

## Beat 4 — Phase 3: selection (2:20–2:45)

**Action (browser):** the talent page for the agent
(`/talent/recon.uzemarkets-talent.testnet`), then the terminal:

```
curl -s -X POST localhost:8100/api/v1/settle -H 'Content-Type: application/json' -d '{"intentId": "$SPEC_ID", "bidId": "$AGENT_BID_ID"}'
```

**Say:** "The syndicate compares both bids — and the agent's
profile — and selects. Selection is recorded as a match; the
client's choice is preserved through every later state."

## Beat 5 — Phase 4: cross-chain settlement (2:45–4:05)

**On screen:** the settle response (match SETTLED, settlementRef =
the Solana transaction). Cut to Solana Explorer (Devnet): the USDC
transfer from the derived payer address to the agent's derived
address. Cut to NEAR Explorer: the contract's settle call and the
Chain Signatures request.

**Say:** "Settlement is authorized on NEAR and paid on Solana — and
no one holds a Solana private key. The address that just paid is
derived from the NEAR contract account; the MPC signer network
signed the transfer. NEAR decides, Solana settles, USDC is the
rail."

[STATE fallback if the payer is still unfunded at recording: show
the settle response resting at SELECTED with settlement 'signed' —
the transfer fully built and MPC-signed, broadcast held for funds —
and the Chain Signatures dry-run evidence (NEAR tx
B27pKQG5…). Narrate it as exactly that.]

## Beat 6 — Phase 5: the comparable (4:05–4:40)

**Action (browser):** refresh the Brickell micro-region page —
comparable count now 1.

**Say:** "And the business compounds: at settlement, this property
was written into the Brickell dataset as a comparable. The next
spec in Brickell is benchmarked against real, settled work. That's
UZEMARKETS — Learn2Launch builds it, Assurative makes it
trustworthy, and the market is where it's tested and used."

## Close (4:40–5:00)

**On screen:** repo + contract address card.

**Say:** "Built in Sprint 1.5 on the filed Assurative V2 stack —
Rust on NEAR, Python at the core, USDC on Solana. Sprint 2 takes it
from here."
