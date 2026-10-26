# Learn2Launch Org — Program Software Stack (DRAFT v0.6)

**INTERNAL — NOT FOR EXTERNAL SHARING.** Draft for James's review. Assembled 2026-10-18.

**Revision v0.2 (2026-10-21):** component 5 added — the standard build
and the Jev Form Router (Python core; NodeJS flavor with Drizzle ORM
instead of Prisma), per James's direction.

**Revision v0.6 (2026-10-26):** component 6 added — Second Brain
Engineering, per James's direction.

The software features of the Learn2Launch Org program stack:

## 1. UZE_KB

Auto-assembling knowledge hub. Monolithic index across the repos;
on-the-fly per-affiliate builds when prompted or clicked.

## 2. Agentic x402

Permissionless, non-custodial micropayments. The company owns and funds
its own accounts; payment clears only if the account holds USDC; the
company sets its own programmatic rules (spend limits, allowlists).

## 3. Altitude + Range

Hierarchical wallet as a service and treasury as a service on
Solana-based wallets — Altitude: workspaces, accounts and balances,
transaction activity, Squads multisig connected as an account connection.
Dashboarding from the treasury layer plus EVM account connectivity,
including EVM wallet use with Safe multisig — Range.

## 4. Animation studio

User-generated, super-intelligence-scaffolded video animation tool for
the content channels. Output visualizes app functionality, brand
positioning (why UZE), differentiation USP, reinforcing CTAs.
Resend-style versioned releases.

## 5. The standard build — Jev Form Router

Every project builds identically to the UZE build: same repository
shape, same deploy path, same gates. The core organization
architecture is Python — FastAPI back end, Pydantic models, Prisma
ORM. The NodeJS flavor is the defined variant: Node.js back end,
Drizzle ORM instead of Prisma, and the Jev x AI SDK Form Router in
its native form. The Python core runs the same router on the official
typesafe-sdk. Intake — leads, contact, issue reports — is routed by
content: Jev decides the destination at the 0.95 confidence policy,
a fallback model decides below it, delivery via Resend with the
decision on record.

## 6. Second Brain Engineering

### Executive overview

Second Brain Engineering is the discipline of running a persistent,
agent-kept knowledge base — a second brain — on a cloud computer that
never closes, so the Org's notes become finished work: a drafted reply
with the right context, a launch plan, a morning page of decisions
waiting for the human lead.

Its place in the stack: UZE_KB (§1) assembles what the Org knows.
Second Brain Engineering is the working layer that keeps that
knowledge alive day to day — controlled intake, summaries traceable to
their sources, drafts produced in the lead's voice, corrections saved
as rules — and feeds finished work back to the other components. Every
program in the Org runs one brain, under the human lead's approval
boundary.

The method in one line: give the brain a job and a starting point;
make every useful fact traceable; finish one workflow by hand, save
it as a skill, then give the skill a schedule. The boundary is the
Desk's own: the brain asks before sending, publishing, purchasing,
deleting, or changing external records. Its memory holds preferences
and summaries — current facts are always rechecked at the source
before use.

### The workspace

One folder shape, the same for every brain:

- `raw/` — original messages, notes, and exports, preserved intact.
- `people/` — working context about collaborators.
- `projects/` — project summaries and decisions.
- `out/` — drafts, plans, and briefs for review.
- `me.md` — confirmed background, goals, collaborators, commitments;
  uncertain details are marked as questions, never filled in.
- `voice.md` — writing guidance: up to ten specific rules, each
  supported by a line the lead actually wrote, linked to its source.
  The starting sample is roughly twenty of the lead's own messages
  across situations — ordinary replies, a project explanation, a
  request, a correction — chosen with account-wide access in mind.
- `attention.md` — current priorities and next actions.
- `rules.md` — approved workflow corrections.
- `INDEX.md` — the file map. `log.md` — the dated record of changes.
- `intake-state.md` — processed source IDs, written only after the
  source and its summary are saved successfully.

### Traceability standard

Every consequential claim carries a source link and a last-checked
date. A summary links to the original behind it; the original stays
intact, and the summary is what gets updated. When two sources
disagree, both references are kept and the conflict is marked for
review. A source that cannot be opened leaves a visible gap in the
answer — "the saved note says Friday; the latest thread could not be
opened" — never a silent guess. Dates, prices, status, and ownership
are rechecked in the current source whenever a task depends on their
current value.

### From notes to finished work

The working loop: read `rules.md` and the relevant project and people
files first; preserve new material in `raw/`; update the linked
summary; produce the finished artifact in `out/`; the human reviews
it and sends it. Review checks, applied to every draft: (1) who said
what is preserved; (2) the draft answers the actual request; (3)
proposed actions are clearly separated from commitments already made;
(4) the approved writing rules are followed. A decision the draft
needs is left as a clearly marked question outside the draft, never
buried in the message text.

### Skills, then routines

A skill stores the method for a task; a routine determines when it
runs. The order is fixed: complete the task, make the process
reliable, save it as a skill, then automate it. Each skill carries its
own acceptance criteria, its required inputs, its source checks, its
output location, and its approval boundary.

Intake is controlled: a Gmail label — Brain — is the deliberate front
door. An intake pass records each message's ID, sender, timestamp,
subject, and source link; skips IDs already processed; files the
original in `raw/`; updates the relevant person or project summary;
and puts ambiguous items on a review list. Running the same pass
twice must produce no duplicates — that check is the regression test
for the whole intake.

Schedules are added only after manual intake and a reviewed draft
both pass: nightly filing of new labelled material; a weekday morning
brief (under 400 words — Facts, each with a source and check time;
Inferences, explicitly labelled; Completed, with paths; Your
decision, the exact choice needed; Questions, what blocks the work —
and quiet when nothing changed); and a weekly review that surfaces
conflicts, stale summaries, repeated corrections, and proposed
merges and removals for the human to decide.

Corrections live in `rules.md`: a correction becomes a proposed rule
with a stated scope and a short example, checked against existing
rules for conflict, shown before saving, then applied to the current
artifact. A one-off format stays attached to its task; only what the
lead intends to reuse enters the rule file.

### Where it runs in the Org

The brain runs on a persistent cloud computer — the pattern of bots on
their own cloud machine, still working while laptops are closed; in
our deployment, the Org's always-on host pattern. Files and signed-in
sessions are shared across the bots on an account, so material is
chosen for the brain with that account-wide access in mind, and no
bot is treated as a security boundary against another.

Worked instances already in the Org: the knowledge hub and UZE_KB
assembly (§1) are the brain's published product; the UZE_MATTY-P
team's KB Archivist and weekly retroactive archive run this pattern
as a team seat; the daily digest briefs are the morning-decisions
pattern in production.
