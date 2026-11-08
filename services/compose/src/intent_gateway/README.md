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

## Open directing questions (do not decide in code)

- **Q-1 — Gateway boundary:** which intent kinds cross the
  gateway, and in which direction (inbound only, or also
  outbound solver quotes)?
- **Q-2 — R4 inheritance:** do solver quotes inherit the R4
  read-through contract wholesale, or a gateway-specific subset?

Both were put to DeepSeek in the 2026-11-07 scope (v0.3) and
remain directing-agent calls. The scaffold's shapes are neutral
between the answers.

## Boundary law (already filed, applies regardless)

- External references are plain strings, never foreign keys
  (R4 §8: reference, never own).
- Arrival proposes; acceptance is a separate explicit decision —
  the same evidence-gated posture as the A/D/R pipeline
  (docs/specifications/06-EVIDENCE-GATED-ARCHITECTURE.md).
