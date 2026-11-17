# SURA v1 — Agentic Guidance over the Talent Marketplace

**Status: 🔨 SPEC + BUILD (2026-11-17).** Owner directive
(James, 2026-11-17 16:24 ET): reverse-engineer Saral AI's
public behaviour clean-room, rename and rebuild it as our
own product — **SURA, agentic guidance** — over the Talent
marketplace that landed today
(`talent-extension-headsin-v1.md`, commit `572a96f`).

**The name (owner naming fact, 2026-11-17 16:28 ET):**
**SURA** is spelled **S-U-R-A** and is an acronym built
from the **Assurative word family** — Assurative /
Assuraties / Assuratized, the platform's trust vocabulary.
SURA is **built from the Assurative V2 repo**: its
implementation home is the **Assurative V2 core**, in this
monorepo, consistent with **Scope Tenet 01** (one
Assurative V2 Python/FastAPI core; front ends integrate
with it). SURA is a core capability of that platform, not
an affiliate surface and not an external product — like
Talent itself (extension spec §1 governance), it stays
internal to UZEmarkets permanently.

**Naming supersession, stated plainly:** the talent
extension spec §8 recorded the standing confinement of the
GIRA/SURA names to real-estate surfaces. The owner's
direct naming of this Talent-marketplace layer as SURA
(2026-11-17 16:24–16:28 ET) extends SURA's remit to this
surface. The confinement otherwise stands; this spec is
the record of the exception and its reason.

**Clean-room rule (absolute, owner ruling 2026-11-17):**
Saral AI is reverse-engineered from **publicly observable
behaviour only** — its public marketing, pricing, about,
and FAQ pages, read 2026-11-17. No contact with the
company, no account, no login, nothing obtained or reused
from its code, copy, or scoring internals. §1 records
*behaviour*; everything from §2 onward is our own design,
our own copy, and our own deterministic scoring. Saral
remains a separate product of HeadsIn Connect LLP with
its own pricing; nothing public says the HeadsIn
agreement covers it, and no step here depends on it.

---

## 1. Reverse build — Saral AI's public behaviour

Verified against the live public pages on 2026-11-17
(saralhire.ai homepage, /pricing, /about), extending and
correcting §3 + component 8 of the HeadsIn reverse-build
memo (filed 2026-11-17, research notes). Source tags:
**[SITE]** the company's own public pages; **[SEARCH]**
third-party public sources (as carried in the memo).

### 1.1 What the product is

- An **outbound sourcing** product: it finds **passive
  candidates** — people who never applied — rather than
  processing inbound applications. Its homepage headline
  is "Your next hire never applied. We find them anyway."
  [SITE — homepage]
- The employer states a need in **natural language**
  ("Describe who you need, in English or Hinglish") and
  receives a **ranked shortlist**. [SITE — homepage]
- Claimed corpus: **150M+ candidate profiles**. [SITE —
  homepage, /pricing]
- It is **not technical-only**: it also sources sales,
  marketing, operations, and finance roles. [SITE —
  homepage FAQ]
- The founders' stated philosophy: AI does the searching
  and sorting; **"the decision to hire… should stay
  human."** [SITE — /about] (Consistent with the memo's
  §7 note from their privacy policy — confirmed here on a
  second public surface.)

### 1.2 The signal model

- Saral reads **public professional activity**: code
  commits, projects, career history, and engagement on
  **GitHub, LinkedIn, X, and Stack Overflow**. [SITE —
  homepage FAQ]
- The behavioural signals it names: **commit
  consistency, repo quality, career trajectory, and
  switch-likelihood**. [SITE — homepage FAQ]
- Multi-source enrichment (GitHub, Behance, email, phone)
  is claimed in a customer testimonial. [SITE — homepage
  testimonial — weaker source, labelled as such]
- Switch-intent signals are presented **alongside salary
  bands** in the same testimonial account. [SITE —
  homepage testimonial]

### 1.3 The Fit Score

- The **Saral Fit Score** is defined publicly as "a
  relevance score assigned to every candidate based on
  **role fit, career trajectory, behavioural signals, and
  switch-likelihood**" — one composite that ranks the
  shortlist. [SITE — homepage FAQ]
- A second named, metered element: **Saral Insights** —
  a per-candidate insight generation, charged at 1 credit
  for the first generation; re-opening is free. [SITE —
  /pricing]

### 1.4 The credit economy (their monetization — context, not copied)

- Searching and opening a profile cost **0 credits**;
  value is metered at reveal/action: Insights 1, email
  unlock 1, phone unlock 2, export 1, AI outreach message
  1 per person. [SITE — /pricing]
- Plans (INR, monthly): **Sprint ₹2,000** (unlimited
  searches; 180 contact + 180 export credits; 100 outreach
  projects; 250 Insights unlocks); **Starter ₹8,000**
  (500/500 credits; 550 outreach projects + AI templates;
  400 Insights); **Growth ₹18,000** (1500/1500; 1500
  outreach projects; 1200 Insights); **Enterprise**
  custom (CRM/ATS integration, SSO, DPDP-compliant DPA).
  Annual billing 10% off; prices exclude 18% GST. [SITE —
  /pricing]
- **SURA takes no part of this economy.** Our settlement
  is the standing matrix (USDC Solana / USDC Base / USDG
  Robinhood Chain) and the engagement-class money flows
  of the extension spec §4. The credit table is recorded
  only because it is part of the behaviour being
  reverse-built: their insight is that *search is free
  and judgement is the product* — §2.3 adopts that shape
  in our own terms.

### 1.5 Corrections and extensions vs the memo

1. **Signal sources.** The memo §3 listed "GitHub,
   LinkedIn, X and the web." The live FAQ names
   **Stack Overflow** explicitly as a fourth source.
   Corrected here. [SITE — homepage FAQ]
2. **The "83% email accuracy" figure** carried in memo
   §3 (attributed there to their llms.txt/terms) was
   **not re-found** on the homepage, /pricing, or /about
   pages in this pass. It stands downgraded: claimed in
   their machine-readable file per the memo, **not
   re-verified** on the public HTML surfaces.
3. **Saral Insights, the credit table, and outreach
   projects/AI templates** as metered elements (§1.3,
   §1.4) were not in the memo; the live /pricing page
   carries all three. [Extension]
4. **Pricing detail refined:** the memo's tier summary
   is confirmed; per-tier credit and unlock counts are
   now exact (§1.4). [Confirmed + refined]
5. **HeadsIn's six-month numbers** (5,000 candidates,
   200 companies, 45+ closings) reconfirmed on Saral's
   own /about page. [SITE — /about]
6. A homepage "days to first hire" statistic rendered
   unclearly in text extraction and is **not relied on**
   anywhere in this spec.

---

## 2. SURA — the two-sided guidance model

SURA is the **agentic guidance layer** over the Talent
marketplace. Saral's shape — one engine serving the
employer who states a need — becomes, on our dual-plane
marketplace, guidance for **both** sides, over the same
live objects:

### 2.1 Demand side — guidance to the employer

The audience: the **human or agentic employer** — a
person hiring, or an agent posting a hiring job or an
**agentic-market skill listing** (an employer expressing a
skill need as a listing). For a role requirement (a need,
the same object the matcher and the solver consume), SURA
returns a **demand guidance object**:

- the category route for the need (native vs labelled
  affiliate-expert route — extension spec §3, unchanged);
- a **pool summary**: how much supply answers this need,
  split **applied vs sourced**, with the fit-score
  distribution across the pool (§3);
- the **ranked candidates**, each with fit score, fit
  explanation, switch-likelihood (sourced candidates), and
  **provenance where the candidate is sourced**;
- **sourcing recommendations** — deterministic guidance
  derived from the pool's actual state: a thin pool says
  so and names the widening moves (skills, geo); a pool
  with no sourced supply says the feed is the gap; a pool
  whose fit is concentrated in the early-career segment
  against a placement-focus need says the intents
  marketplace serves it (§4).

### 2.2 Supply side — guidance to the candidate

The audience: the **human candidate seeking job roles**.
Roles are defined by **skill** and by **geo-requirement —
remote, hybrid, or onsite** (the need's `geo_requirement`,
one of `REMOTE | HYBRID | ON_SITE`). For a candidate
profile and a set of open role listings, SURA returns a
**supply guidance object**:

- the roles the candidate **geo-qualifies** for (their
  declared availability against each role's
  geo-requirement — §3.3), ranked by fit score;
- per role, a **fit explanation**: which required skills
  are covered and which are missing, the geo basis, the
  experience basis — the candidate sees *why*, in the same
  arithmetic the demand side sees;
- **guidance notes** derived from the profile's own
  state: no pre-assessment on file (the assessment is fit
  evidence the candidate can add); geo availability that
  excludes open roles is named, with the count.

### 2.3 The shape adopted from the reverse build

Saral's one transferable insight, re-expressed as ours:
**search is free; judgement is the product.** SURA does
not meter looking — profiles and listings are open on
both planes. What SURA produces is the judgement layer:
fit with an explanation, likelihood with its basis, and a
recommendation that follows from the pool's real state.
No credit economy, no unlocks.

---

## 3. The signal-sourcing model as data

### 3.1 The feed is the surface — provenance is required

SURA v1 ingests sourced profiles through an **explicit
feed surface** (§5). A feed record is:

```json
{
  "profile":     { …a TalentProfile, validated as always… },
  "provenance": {
    "source":     "github | linkedin | x | stack_overflow
                   | behance | web | partner_feed | manual",
    "source_ref": "string — where the profile was observed",
    "feed":       "string — the feed / operator supplying it",
    "sourced_at": "string — ISO-8601 timestamp",
    "basis":      "string — the public signal that
                   justified inclusion"
  },
  "signals": {
    "last_activity_days":   "number ≥ 0, optional",
    "activity_events_90d":  "number ≥ 0, optional",
    "career_moves_5y":      "number ≥ 0, optional",
    "years_in_current_role":"number ≥ 0, optional",
    "open_to_work":         "boolean, optional"
  },
  "geo_availability": ["REMOTE | HYBRID | ON_SITE", "…"]
}
```

- **Provenance is required.** A feed record without a
  complete provenance object is refused, naming the
  fields (the platform's INSUFFICIENT_DATA discipline).
  There is no anonymous sourced supply.
- **Signals are supplied, never fetched.** Every signal
  is a value the feed asserts about public activity; SURA
  computes over asserted values only (§6 honesty).
- `geo_availability` is the candidate's declared
  acceptance of work modes — the supply-side counterpart
  of a role's geo-requirement. (The core TalentProfile
  schema is untouched: availability rides on the feed
  record, and on the stored profile as an annotation,
  like provenance.)

### 3.2 Storage and the solver pool

- Feed records persist to an append-only JSONL store
  (env `TALENT_SOURCED_PATH`) — the feed's audit record:
  feed, receipt time, provenance, signals, scores.
- The sourced **profile** (validated TalentProfile +
  provenance + signals + geo_availability annotations +
  computed switch-likelihood) enters the **same solver
  pool** as applied profiles: the solve endpoint's pool is
  applied ∪ sourced. Inside the solver, sourced
  candidates are treated **identically** to applied ones
  (memo component 8) — same matcher, same scorecard, same
  segment routing — and their **provenance is visible** in
  every offer that carries them.

### 3.3 Geo-requirement semantics

- A need may declare `geo_requirement` ∈
  `REMOTE | HYBRID | ON_SITE` (the platform work-mode
  enum). The natural spelling `ONSITE` is accepted at the
  SURA boundary and normalized to the canonical `ON_SITE`;
  storage is always canonical.
- A candidate's availability: their `geo_availability`
  when declared; else their employee `work_mode` as a
  singleton; else undeclared (unconstrained).
- **Geo-qualified**: the requirement is in the
  availability, or either side is undeclared. Supply
  guidance lists only geo-qualified roles; demand fit
  scores the geo component only when both sides declare.

### 3.4 Fit score — our deterministic heuristic v1

One composite, 0–100, computed per (need, profile) from
**declared fields only**. Components (earned / available):

| Component | Max | Rule |
|---|---|---|
| Skill coverage | 50 | Need declares `skills`: 50 × (required skills the profile covers ÷ required skills). Profile skills and assessment-proven skills both count as coverage. |
| Role match | 20 | 20 when the profile matches the need under the existing matcher (`match_profiles` on the single profile); else 10 when the role family agrees; else 0. |
| Geo fit | 20 | Both sides declare (§3.3): 20 when geo-qualified, 0 when not. |
| Experience fit | 10 | Need declares `min_experience_years`: 10 × min(profile years ÷ required, 1). Profile declares none of the basis → excluded like any undeclared component. |
| Assessment evidence | 10 | The profile's pre-assessment score ÷ 10, when an assessment is on file. |

Fit = round(100 × earned ÷ available) over the
components whose basis is declared; 0 when no component
has a basis. Deterministic: same inputs, same score,
always. **Labelled heuristic v1** — it is arithmetic over
declared fields, published here in full; it is not a
learned model and no surface may call it one.

### 3.5 Switch-likelihood — our deterministic heuristic v1

Per profile, 0–100, from **supplied signals only**
(§3.1). Missing signals contribute 0 and are named in the
breakdown — the score never invents a signal.

| Component | Max | Bands |
|---|---|---|
| Tenure pressure (`years_in_current_role`) | 30 | <1 yr → 10 · 1–2 → 22 · 2–4 → 30 · 4–6 → 18 · >6 → 8 |
| Mobility history (`career_moves_5y`) | 25 | 0 moves → 5 · 1 → 15 · 2 → 25 · ≥3 → 15 |
| Public activity (`activity_events_90d`) | 25 | ≥40 → 25 · ≥15 → 18 · ≥5 → 10 · ≥1 → 5 · 0 → 0 |
| Activity recency (`last_activity_days`) | 20 | ≤14 days → 20 · ≤45 → 12 · ≤120 → 6 · else → 0 |
| Declared openness (`open_to_work` true) | +10 | Added, total capped at 100 |

Deterministic and bounded by construction. **Labelled
heuristic v1**, same honesty rule as §3.4: the bands are
published, the basis is always returned with the score,
and a profile with no signals scores from its declared
openness alone (or 0).

---

## 4. SURA over the intents solver

The white-collar knowledge-worker market is matched
through the **NEAR AI Intents solver** (extension spec
§5): role requirements are intents; human and agentic
supply responds as solvers; settlement of a match is the
placement record. SURA sits **over** that marketplace —
needs versus supply — in both directions:

- **Guidance feeds intents.** A demand guidance object is
  computed over the same pool the solver answers from, so
  the employer's guidance and the solver's offers can
  never disagree about what supply exists. An employer
  who accepts the guidance posts the intent; the solver
  returns the same candidates, scorecard-ranked.
- **Sourced supply enters the solver pool** (§3.2) with
  provenance — a sourced candidate is a solver response
  like any other, marked as sourced wherever it appears.
- **Supply guidance reads the same intents.** The roles a
  candidate is guided toward are need objects of exactly
  the solver's shape; a candidate who acts on guidance
  enters the lifecycle (§2.6 of the extension spec) at
  RECOMMENDED against that role.
- The **honesty label stands**: the solver behind the
  interface is the deterministic matcher; NEAR AI attested
  inference is credit-blocked (HTTP 402, $0 balance) and
  is labelled unavailable in every solver response. SURA
  adds no inference claim of its own — its scores are
  §3.4/§3.5 arithmetic, labelled heuristic v1.

---

## 5. Headless surface added by this spec

All under the existing `/api/v1/talent` prefix, in the
existing INSUFFICIENT_DATA discipline (422 naming fields):

| Endpoint | Behaviour |
|---|---|
| `POST /api/v1/talent/sura/sourced` | Ingest one feed record (§3.1). Provenance required; the profile validates as a TalentProfile; the record persists to the feed store and the profile enters the solver pool with provenance + computed switch-likelihood. |
| `GET /api/v1/talent/sura/sourced` | The sourced supply: every sourced profile with provenance, signals, and switch-likelihood. |
| `POST /api/v1/talent/sura/guidance/demand` | Demand guidance (§2.1) for one need, over the applied ∪ sourced pool. |
| `POST /api/v1/talent/sura/guidance/supply` | Supply guidance (§2.2): a candidate (by `profile_name` from either pool, or a profile object) against a list of role listings (need objects). Geo-filtered, fit-ranked, explained. |

The solve endpoint (`POST /api/v1/talent/intents/solve`)
is unchanged in shape; its pool now includes sourced
supply (§3.2).

---

## 6. Honesty constraints (standing)

- **No live signal scraping is claimed.** SURA v1 does
  not crawl GitHub, LinkedIn, X, Stack Overflow, or any
  other source, and no surface may say or imply that it
  does. Sourced profiles arrive through the explicit feed
  surface (§3.1), carrying the provenance of whoever
  supplied them. A real signal connector is future work
  and will be labelled when it exists.
- **Scores are heuristics, labelled v1**, with their full
  arithmetic published in §3.4–§3.5 and their basis
  returned in every response that carries them.
- **Provenance is never stripped.** A sourced candidate
  is marked sourced — source, feed, basis — in solver
  offers, in guidance, and on the human plane.
- **No "AI match" language.** SURA is agentic *guidance*:
  deterministic scoring and recommendation over declared
  fields and supplied signals. The NEAR AI inference
  state rides in band, unchanged (extension spec §5).

---

## 7. What stays unchanged

- The TalentProfile schema and validation, the
  deterministic matcher, the scorecard, category and
  segment routing, the ATS lifecycle — all as built in
  the extension. SURA reads those objects; it does not
  alter their behaviour.
- The extension spec's governance: Talent — and SURA
  with it — is internal to UZEmarkets, permanently,
  never an affiliate.
- Storage discipline: append-only JSONL v1 stores
  (env-overridable paths); a database migration is later
  work, stated as plainly here as in the modules it joins.

---

## 8. As built (2026-11-17)

- `services/compose/src/sura.py` (new): feed-record
  validation (provenance required), the sourced JSONL
  store + pool loader, fit score (§3.4) and
  switch-likelihood (§3.5) with full component breakdowns,
  and the demand/supply guidance generators.
- `services/compose/src/talent_sura.py` (new): the §5
  endpoints, wired beside `talent_applications` in
  `app.py`; the solve endpoint's pool is applied ∪
  sourced.
- Guidance events (§9.2): every guidance call records an
  episode-ready event (JSONL, env
  `TALENT_GUIDANCE_EVENTS_PATH`); ATS application
  creation and transitions settle the linked events'
  outcome fields (matched / placed / accepted /
  rejected). Training and promotion stay in uze-rl; no
  trained policy exists yet, and the talent pages'
  disclosure (§9.3) says so.
- Web: `/talent/placement` gains the SURA section —
  two-sided guidance (employer side / candidate side),
  the fit and switch scores with their heuristic-v1
  labels, and the honest v1 feed note.
- Tests: `tests/test_talent_sura.py` — provenance
  required at ingestion; deterministic + bounded scoring;
  sourced candidates in solver results with provenance;
  guidance for both sides; geo-requirement filtering.

---

## 9. Designated follow-on layers (recorded requirements — NOT built in v1)

Two standing requirements attach to Talent/SURA by owner
direction (James, 2026-11-17 16:30 ET). They are recorded
here so the architecture carries them from the start;
neither expands the v1 build.

### 9.1 RAG connection — the Talent knowledge base

All agentic builds connect to our internal RAG solutions,
one by one. For Talent the requirement is specific:
**Talent is to be a knowledge base that is EXTERNALLY
FACING** — readable by agents on both the supply and
demand sides, and by humans (the employer, the
contractor, the future employee candidate).

- The **internal home** is the Knowledge Hub / shared RAG
  of Scope Tenet 01 (shared FastAPI + RAG knowledge bases
  across the platform's front ends). The **Talent KB is
  its external face**: the same knowledge, published for
  outside readers — profiles, role listings, taxonomy,
  guidance — in the dual-plane discipline (human-readable
  pages; agent-readable JSON) that every Talent surface
  already follows.
- Design consequence for v1, already honoured: SURA's
  objects (feed records, guidance, scores with published
  arithmetic) are plain JSON over declared fields — the
  shape a knowledge base ingests without transformation.
- The KB build itself — indexing, retrieval, the external
  read surface — is a follow-on workstream, sequenced
  with the other agentic builds' RAG connections.

### 9.2 RL implantation — SURA's guidance is an RL workload of the talent environment

**SURA's agentic guidance incorporates its RL plane**
(owner requirement, 2026-11-17 16:33 ET). The RL
framework (**uze-rl**, built 2026-11-17) runs **five
environments — underwrite / assign / auction / talent /
whb** — and SURA's guidance is an **RL workload of the
talent environment**: fit scoring, switch-likelihood,
and the sourcing/guidance recommendations are the
guidance policy that environment learns over.

- **How it improves:** from marketplace outcomes only —
  matches made, placements settled, applications accepted
  or rejected — through the framework's **gated promotion
  discipline**. A candidate guidance policy must **beat
  the incumbent on held-out outcomes** before it is
  promoted. **No silent self-modification; no ad-hoc
  weight tuning.** The heuristic v1 bands of §3.4–§3.5
  are the incumbent until a policy clears the gate.
- **What the monorepo builds (v1, this spec): the honest
  event feed.** Every SURA guidance call records a
  **guidance event** in episode-ready form (append-only
  JSONL, env `TALENT_GUIDANCE_EVENTS_PATH`): the guidance
  given (side, subject, recommendations, scores), the
  context (role/candidate, required skills,
  geo-requirement), and **outcome fields the ATS
  lifecycle fills as outcomes settle** — matched / placed
  / accepted / rejected, linked to the application by the
  candidate-and-role reference. This record is the feed
  the RL talent environment reads to build episodes.
- **What the monorepo does NOT build:** training,
  benchmarking, and promotion live in **uze-rl**, never
  in this repo. The monorepo side is the event feed, plus
  **consuming the currently-served policy where a policy
  exists. None does yet** — the talent environment has no
  promoted policy — and every surface that mentions the
  RL plane labels that state plainly (§9.3).
- Until a policy clears the gate, the labelled heuristic
  v1 arithmetic (§3.4–§3.5) is the whole of SURA's
  scoring, and every surface keeps saying so.

### 9.3 Disclosure — the RL plane is a value proposition, stated truthfully

The RL plane is **disclosed** on the external-facing
talent surfaces (owner requirement, 2026-11-17 16:33
ET) — it is part of what the platform offers, not an
internal secret. The disclosure, on the talent pages and
in any external knowledge-base rendering, covers:

- **The mechanism:** SURA's guidance incorporates its RL
  plane (the RL framework's talent environment); the
  solution continually learns from interacting with the
  marketplace — every match, placement, and outcome makes
  the guidance better for the next employer and the next
  candidate.
- **The value, both sides:** demand side (employers) —
  matching and guidance improve with use; supply side
  (candidates and contractors) — guidance and fit improve
  with use. **Engaging with the platform is what trains
  it.**
- **The discipline:** learning happens through gated
  promotion on held-out outcomes — no silent
  self-modification.
- **The current state, stated plainly alongside the
  mechanism (standing honesty rule, never softened):**
  v1 guidance is heuristic; the RL feed is recording
  outcomes now; trained policies are promoted only when
  the evidence clears the gate. **The disclosure sells
  the loop truthfully — it must not claim a trained
  policy exists today, because none does.**

*End of spec v1.*
