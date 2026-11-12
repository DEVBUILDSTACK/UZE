# UZE Auction — Technical Specification

**Status: BUILT AS MOCK — no live MPC.** Implemented in `services/compose/src/auctions.py` and `services/compose/src/commitments.py` (2026-11-11, Directives 7 + 8 of the owner's scoped set). No Arcium MPC is integrated; the execute step is a mock reveal of the highest sealed bid. All state is in-memory (the persistent EntityPool schema is a deferred post-demo directive).

## 1. Sealed bids

Bid amounts are stored server-side and never appear in any response until a human-confirmed execution reveals the winner.

## 2. The Commitment Ladder

A syndicate auction's capital discipline: partners lock against their target bid on a schedule derived from the close time —

| Checkpoint | Lock required |
|---|---|
| T-7 days | 30% of target bid |
| T-72 hours | 90% of target bid |
| T-12 hours | 100% of target bid |

A partner under the due percentage at a checkpoint falls off the whitelist. Evaluation takes an explicit `now`, so the schedule is deterministic and testable.

## 3. The Temporal Trigger

When the pricing (Delphi) market closes, the trigger:

1. **Locks** the escrow state,
2. **Finalizes** the whitelist, and
3. Raises a **READY_TO_EXECUTE** alert.

The trigger does **not** start any auction execution. Execution requires `POST /execute` with `human_confirmed: true`; without it, the request is refused (422). This human gate is a design invariant, not a placeholder: confidential execution machinery does not remove it.

## 4. Confidential execution (design)

The production design executes the sealed-bid reveal inside Arcium's MPC network, so bid values are computed over without being exposed to any single party, including the operator. That integration is **design only** in the current build; §1–§3 describe what is implemented and tested today.
