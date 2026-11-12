# Intent Gateway — Sprint 2 scaffold

Status: **scaffold only** (built 2026-11-08, Sprint 1.5 idle-cycle
workstream). Not imported by the compose app; no routes; the only
implementation (`DisabledIntentGateway`) refuses every envelope
with `IntentGatewayNotEnabled`.

## What Sprint 2 builds here

The gateway is the boundary at which external and
solver-originated intents enter the marketplace:

- envelope validation and source authentication;
- idempotent acceptance (an envelope replay never creates a
  second intent);
- translation from the source's shape into the compose intent
  schema (camelCase wire names, HIADR track enforcement);
- an explicit receipt for every envelope — accepted with a
  compose-side reference, or refused with a machine-readable
  reason.

## Directing questions — RESOLVED 2026-11-08 (DeepSeek, relayed by James)

- **Q-1 — Gateway boundary: RESOLVED.** The gateway stays a
  distinct Python package inside `services/compose` (this
  package). It is not split into a separate microservice: it
  shares the database and the R4 state machine with the rest of
  Compose. Extraction to a separate service happens only if
  solver-matching load requires independent scaling.
- **Q-2 — R4 inheritance: RESOLVED.** Solver quotes inherit
  R4's TTL and commit-time reconciliation discipline wholesale,
  with one distinct divergence code added: **SOLVER_WITHDREW**.
  A solver quote expiring or being pulled is structurally
  different from a static LISTING_GONE — the negotiation
  failed; the inventory didn't vanish. SOLVER_WITHDREW is
  recorded here for implementation when Sprint 2 wires the
  gateway; it is not part of the Sprint 1 read-through code set.

Both were put to DeepSeek in the 2026-11-07 scope (v0.3). The
scaffold's shapes are unchanged by the resolutions — they were
neutral between the answers, and both answers land inside the
package as built.

## Boundary law (already filed, applies regardless)

- External references are plain strings, never foreign keys
  (R4 §8: reference, never own).
- Arrival proposes; acceptance is a separate explicit decision —
  the same evidence-gated posture as the A/D/R pipeline
  (docs/specifications/06-EVIDENCE-GATED-ARCHITECTURE.md).
