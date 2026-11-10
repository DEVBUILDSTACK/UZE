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
- Re-point devpartner / blog / podcast serving from branch-preview
  aliases to Production, with no gap; **re-verify after the merge:**
  blog (Content Desk index + a region page), devpartner (portal, all
  four locales), podcast (editions index), the POD edition URL
  (https://uze-web-uze2.vercel.app/pod/2026-11-07.html), and the nav
  structure.
- File the held SUBMISSION-CHECKLIST edit: preferred track =
  **Unstoppable DeFi** (James, 2026-11-09).
- demo.uzemarkets.com stays pinned to the recording deployment through
  the Nov 14 submission.
