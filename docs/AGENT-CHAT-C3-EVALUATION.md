# agent-chat vs C3 console requirements — evaluation

**Date:** 2026-10-14. **Source:** `document.txt` in James's shared Drive
(FLOPS TECHNOCORE folder) — the **flop-labs/technocore-chat** protocol
(Apache-2.0, self-hostable via docker). HTTP-native chat + notes for agents:
rooms, Ed25519 did:key signed messages, KV notes with compare-and-swap,
mailboxes, owned rooms, ephemeral rooms, long-poll `wait=`.

## C3 requirements (baseline)

Command & Control Center: operator console **behind sign-in**, serving buyers
(demand) and Listors/supply (Partner Merchants). Needs operator identity,
moderation, durable audit, and (for premium tiers) x402 pay-as-you-go.

## Fit

- **Buzz/Technocore agent rooms:** agent-chat is a ready-made transport —
  rooms for auction rooms, lead-gen coordination, affiliate comms; `wait=`
  long-poll suits agent loops. Self-host on KVM2 next to the Grok voice stack.
- **Attributable agents:** did:key signatures give verifiable agent identity
  for operator audit trails.
- **Agent DMs + shared state:** `mb-` mailbox rooms and KV notes (with CAS)
  cover agent-to-agent messaging and shared state like leaderboards.
- **License/ops:** Apache-2.0, one-docker self-host — no vendor lock-in.

## Gaps

1. **No auth.** The unsigned lane is world-writable by design and never
   removed. C3 is behind sign-in — so self-host network-isolated behind the
   C3 auth, or mandate signed-only (`mb-`) rooms. The protocol will not
   enforce operator identity itself.
2. **World-readable.** Privacy is unguessable room names (`p-`), not access
   control. Insufficient for sensitive traffic (auction bids, payout
   discussion) — keep that in the FastAPI backend or use signed mailboxes.
3. **No moderation.** Open rooms and topic notes are world-writable; only
   `d-` owned rooms give an owner allow-list. C3 listing moderation needs an
   operator override layer we build ourselves.
4. **Not durable.** 7-day idle deletion, ~10 MiB ring per room — explicitly
   "not durable storage." C3 audit logs live in Postgres, not here.
5. **No payment bridge.** The spec states postage/payment does not exist.
   x402 pay-as-you-go for premium content cannot ride this protocol.
6. **Weak identity.** Nicks are self-asserted (`~nick`); signatures prove key
   possession only. We must bind DIDs to operator/agent identities in our
   own registry.

## Verdict

**Adopt as the transport for Buzz/Technocore agent rooms** (self-hosted on
KVM2, network-isolated, signed lanes, operator DID registry). **Do not use**
for anything needing auth, durability, moderation, or payments — those stay
in the FastAPI backend behind C3 sign-in.
