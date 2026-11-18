# P2 — Assessment: Scope and Specification v0.1

**Status: FOR JAMES'S TAP — no build begins before the tap.**
**Filed:** 2026-11-18, from James's specification dictation of the same
day. **Parent scope:** `CONSOLIDATED-SCOPE-v3.1.md` (P2 = the
ASSESSMENT layer, DAL) and `BUILD-SCOPE-AND-PHASED-SPRINT-v1.0.md`.
**Companion:** `ADDENDUM-TALENT-COMMERCIAL-MODELS-2026-11-18.md`
(the two money models and the confidentiality doctrine).

---

## 1. What P2 is

An **agentially built skills assessment**, generated from the role
the engaging employer configures. The market submits and configures
the role; agents build the assessment to that role; a **human in the
loop approves** that the role and its assessment fit before anything
runs. The human gate is mandatory — no assessment goes live, and no
fulfillment starts, without it.

## 2. The flow

1. **Role configuration** — the engaging employer submits and
   configures the role (skills, level, market, engagement mode).
2. **Assessment generation** — agents build the skills assessment
   from the configured role.
3. **Human gate** — a human approves the role's fit and the
   assessment's fit. Rejection returns the role for reconfiguration;
   nothing is assessed against an unapproved role.
4. **Assessment** — talent is assessed against the approved role.
5. **Fulfillment** — one of the two paths in §3, per the engagement's
   terms.

## 3. The two fulfillment paths

**Path A — Agentic skills fulfillment (the autonomous market).**
The talent is a **UZE Markets paid employee**. The client is billed
the labor rate **plus a markup**, set per labor market. Initial
parameters (James, 2026-11-18 — starting figures, adjustable per
engagement, never silently changed):

| Labor market | Markup on the labor rate |
|---|---|
| India | **17.5% – 23.5%** |
| Singapore — help desk | **from 33.75%** |
| Other markets | Set by James per market |

**Path B — Pre-gated client engagements.** For a client who has
already gone through the gate — the engagement is **accepted** and
an **advance is held on account** — fulfillment runs under the
commercial-models addendum: **outstaffing** (UZE pays the talent,
bills the client) or **placement** (fee of at least 30 days' salary;
the client pays the individual directly). The advance on account is
the deposit leg of the confidentiality doctrine: no talent identity
or contact information is exposed before a signed engagement and
that advance are both in hand.

## 4. The transparency layer — IPFS engagement copy

Every engagement carries a **published copy on IPFS-based cloud**
(NEAR AI Cloud is the reference home James named):

- the engagement's terms of record, and
- its **progress and activity**, viewable as it proceeds,

with a hard redaction rule: **no talent names, no talent or agent
email addresses, no company names** — ever. The public copy proves
the engagement exists and is progressing; it identifies nobody.
This is the confidentiality doctrine (§3, and the addendum) carried
into the transparency layer: visibility of work, invisibility of
people.

## 5. Invariants carried from v3.1

- The human gate is a hard gate, in the same class as v3.1's
  human-`promotedBy` ladder rule: no agent action substitutes for it.
- Status is derived, never written; every transition emits an Event.
- Markup parameters are engagement terms — recorded on the
  engagement before work begins, visible in the engagement's IPFS
  copy only as the redaction rule allows (figures yes, identities
  no).

## 6. Build decomposition (sprint sketch, on the tap)

1. Role-configuration intake (employer-submitted role → structured
   Role record, Role × Realm taxonomy of record).
2. Assessment generator (agents build the assessment from the role).
3. Gate console (human approve / return, with the decision and the
   approver recorded as an Event).
4. Rate + markup engine (labor-market parameter table; Path A
   billing terms generated from it).
5. IPFS publisher + public engagement view (redacted by
   construction — the publisher never receives identity fields).

## 7. Open items for James

1. Markup bands for labor markets beyond India and Singapore help
   desk.
2. The human approver of record for the gate (the desk, or James
   personally, per engagement class).
3. IPFS pinning home: NEAR AI Cloud as named, or another IPFS cloud
   — the publisher is built against the redaction rule either way.

---

*End of P2 scope and specification v0.1 — prepared for James's tap.*
