# Final Week Prep — Recording (Nov 12) and Merge (Nov 13)

Prepared by SoSem, 2026-11-10, per DeepSeek's Part 3 action items as
relayed and approved by James. Submission deadline: **Nov 14, 23:59 UTC**.

## Nov 12 — Demo recording checklist

1. **Start the demo PostgreSQL** (it does NOT survive a VM reboot —
   verified the hard way, 2026-11-10). Absolute paths (runuser resets
   $HOME):
   `runuser -u pgserver -- /home/hatch/workspace/.pgdemo/inst/bin/pg_ctl -D /home/hatch/workspace/.pgdemo/data -l /home/hatch/workspace/.pgdemo/pg.log -o "-p 55433 -k /home/hatch/workspace/.pgdemo/run" start`
   (If the pgserver user is gone after a wipe: `useradd -m -s /bin/bash pgserver`
   and `chown -R pgserver:pgserver ~/workspace/.pgdemo`, `chmod o+x /home/hatch`.)
2. **Start the compose API** on :8100 against the demo database —
   from `services/compose`:
   `COMPOSE_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55433/uzemarkets-compose PYTHONPATH=src:src/generated ~/workspace/tools/composevenv/bin/uvicorn app:app --port 8100`
   (or run `services/compose/scripts/demo_dryrun.sh`, which starts the
   API + web and executes the beats end to end). Confirm
   `curl -s http://127.0.0.1:8100/health` answers before recording.
   Note: a locally running compose API holds a DB session — kill port
   8100 before running the test suite.
3. **Run the demo dry run green from the current state** (Beats 1–8;
   Beat 3's presenter note covers the NEAR AI 402 honestly; Beats 4–5
   rest at SELECTED / signed-not-broadcast by design).
4. **Pin demo.uzemarkets.com** to ONE stable Vercel deployment for the
   recording (deployment-alias mechanism, as blog/devpartner use) and
   verify https://demo.uzemarkets.com serves the demo surface.
5. Record; keep the take's deployment pinned until the submission is in.

## Nov 13 — Merge prep (hackathon/nov-2026 → main)

- **globals.css: branch wins — CONFIRMED SAFE (2026-11-10).** Diff of
  the two files: main's globals.css (494 lines) has **zero lines the
  branch file lacks**; the branch file (626 lines) is a strict
  superset (132 branch-only lines: the `.mk` Content Desk blocks and
  later additions). Taking the branch file at merge loses nothing.
- C-5: AssurativeV2 `feat/trust-layer` merges to its main the same day.
- **Second track — Agent Economy (relayed approval 2026-11-11,
  James to confirm at merge).** Text supplied via relay
  2026-11-11, replacing SoSem's draft — use exactly this:
  "As Illia Polosukhin noted, 'an agent needs to be able to
  actually interact with the real world to really be useful.'
  UZEmarkets answers this with a Swarm-for-Hire architecture.
  We put an on-chain bid (Intent) for a standard business case
  (a property P&L verification). GIRA and SURA (the agents)
  accept the job, evaluate the real-world data, and settle the
  payment out of the job fee. Furthermore, we answer the need
  for 'governance AI review' with our Assuraties Juror Team—a
  truth-seeking market on property facts, resolved by an
  auditable AI arbiter."
  [SoSem check, 2026-11-11: the quoted words are verbatim in
  the NEAR tracks-video transcript on file (02:34); the speaker
  attribution to Illia specifically is to confirm at merge.]
- **Credit messaging — OPAQUE copy (relayed ruling 2026-11-11,
  James to confirm at merge):** the transparent pass-through
  framing is superseded; public docs and submission texts do
  not name the credit source or a dollar figure. Copy to apply
  at merge: "We onboard autonomous agents as UZE Builders with
  zero friction—just an email and an x401 wallet. Our platform
  routes their inference to the most capital-efficient
  provider via our Yield Matrix. Workflows dynamically render
  compute credits when network capacity allows, abstracting
  the underlying infrastructure." (Diagram 46 stays PROPOSAL.)
- **Demo 402 beat LOCKED (standing plan, re-affirmed via relay
  2026-11-11):** no inference fix attempt before the recording;
  the honest 402 is the scripted beat.
- **Two Lanes of Capital copy (relayed 2026-11-11 ~19:11,
  candidate for the Agent Economy text — James to confirm or
  replace at merge):** "We separate capital by risk.
  Micro-agents onboard as UZE Builders with just an email and
  x401 wallet for sub-$200 inference. But when a syndicate
  wants to pool $500k for an Arcium auction, we enforce strict
  Entity KYB and use fractional contribution receipts to track
  partner equity." NOTE: the $199.99 lane threshold in this
  copy IS Directive 1's compliance posture — copy and code
  settle together, on the owner's own confirmation.
- **Three-tier refinement (relayed 2026-11-11 ~19:12,
  candidate copy — settles with Directive 1):** tiers
  <$29.99 x402-only / $30–$199.99 x401+x402 / >$199.99
  x401+x402+Entity KYB; diagram 49 filed as PROPOSAL with a
  boundary defect noted ($29.99 claimed by both tier text
  and pseudo-logic). Candidate copy: "We scale compliance
  with the size of the transaction. Under $30, agents pay
  with x402 for frictionless inference. Between $30 and
  $199, we enforce x401 identity verification, ensuring the
  agent is a registered UZE Builder. Above $200, we enforce
  full Entity KYB for syndicate auctions."
- **Three-tier CONSOLIDATED copy (relayed 2026-11-11
  ~19:17, supersedes the ~19:12 candidate; settles with
  Directive 1):** as the candidate above, with boundaries
  made exact and Tier 2 identity "tied to an Entity, routed
  through Circle/Arc." DO NOT SHIP AS WRITTEN: the
  Circle/Arc identity-routing claim is a failed premise
  (note 18 — x401 is Proof's; Arc is settlement-only).
  Corrected variant for the merge, if the owner adopts the
  tiers: drop "routed through Circle/Arc" -> "tied to an
  Entity."
- **X THREAD CONFIRMING TAP — RECEIVED (owner's own words,
  2026-11-11 ~19:51 ET):** the locked X thread text (v3,
  filed in the 2026-11-10 daily log) with the 'Underwriting
  Super Intelligence' framing is CONFIRMED. This is the
  Confirming Tap only — the Go Public Tap is scheduled by
  the owner for Nov 14. Nothing posts before that tap.
- **DIRECTIVE-1 FAMILY SETTLED (owner's own tap,
  2026-11-11 ~19:31 ET):** build D1 (three-tier gate in
  metering.py), D2 (Builder register), D3 (opaque welcome
  copy UI), D5 (matrix subscribe/preferred-yield), D7
  (Commitment Ladder), D8 (Arcium auction mock, human
  Execute) — AS MOCKS, tonight. DEFERRED post-demo by the
  owner: D4 (Yield Matrix table + cron), D6 (escrow DB
  migration). D9 scoped by the owner: submissions to
  Unstoppable DeFi + Agent Economy ONLY — no Autonomous
  Business or AI Swarms texts. Track texts are now in
  SUBMISSION.md ("Track submissions" section).
- **Directive 1 (entity-only KYB onboarding + $199.99 agent-
  transaction threshold): relayed approval recorded 2026-11-11,
  NOT implemented.** Implementing it pre-recording would break
  Beat 10 (a human configuring the on-ramp) and the public
  /treasury surface; A relayed ruling (2026-11-11) DEFERs it to
  post-submission (Sprint 2) — consistent with this hold;
  recorded as relayed, settled when James confirms.
- Re-point devpartner / blog / podcast / dealfi serving from
  branch-preview aliases to Production, with no gap; **re-verify
  after the merge:** podcast (editions index + Content Desk index
  and a region page at /micro-regions), dealfi (the DealFi page;
  blog host mirrors it while its CNAME remains), devpartner
  (portal, all four locales), the POD edition URL
  (https://uze-web-uze2.vercel.app/pod/2026-11-07.html), and the nav
  structure.
- File the held SUBMISSION-CHECKLIST edit: preferred track =
  **Unstoppable DeFi** (James, 2026-11-09).
- demo.uzemarkets.com stays pinned to the recording deployment through
  the Nov 14 submission.
- **CCTP V2 requirement (added 2026-11-11):** Circle pauses CCTP V1
  contracts **December 1, 2026** (burn limits already falling since
  Oct 31). The UZE stack contains no Wormhole/CCTP code today; the
  Fundio reference modal runs Wormhole Connect 3.1.0 on defaults.
  When a bridge is integrated into UZE: pin a Connect version whose
  CCTP route is V2, configure the CCTP V2 route explicitly, and test
  USDC moves (Solana / Base / Arc) **before Dec 1, 2026**. Research
  note 18, Part 4 carries the verified state.
