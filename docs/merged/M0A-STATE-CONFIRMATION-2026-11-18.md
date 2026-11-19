# M0-A — State Confirmation (Step 1 of M0-A, per amendment C7)

**Date:** 2026-11-18, ~20:17 ET. **Run by:** SoSem, on James's tap of the merged P1+P3 program (with amendments A1–A6).
**Purpose:** M0-A's first act — confirm Scope 1's state claims against the running system before the owner OTP test is treated as meaningful. Claims checked are those stated in the merged scope §2.

## Live surface checks (2026-11-19T01:17:44Z)

| Check | Result | Claim it confirms |
|---|---|---|
| `GET https://dev.uzemarkets.com/` | **200** (8,054 bytes) | The Dev Library is deployed and serving in production |
| `GET https://dev.uzemarkets.com/api/catalog` | **401** | The email-allowlist gate is enforced in production (unauthenticated catalog refused) |
| `GET https://dev.uzemarkets.com/hero.jpg` | **200** (54,655 bytes) | Public asset route serving the filed hero image |
| `GET https://dev.uzemarkets.com/hero.gif` | **200** (360,990 bytes) | Motion hero serving at exactly the filed byte size |

## Filed evidence relied on

- **Production seed counts** — deploy workflow run `44416876207` (2026-11-18, success): the seed step reported `{"developer":6,"developer_status":5,"repo_permission":59}` — the 5 professionals of record plus the owner test persona (uze@uzemarkets.com), 59 repo grants. Neon Postgres attached to the project in the same run; production runs DB-backed.
- **Rehearsal** — the app's test suite stands at **40 passed / 0 failed** as filed (email rendering incl. the "reading room" external-copy guard, gate, lifecycle, mailer/webhook paths).
- **Mailer/webhook code state** — mailer and Svix-verified webhook receiver built and deployed; both inert-by-design until `RESEND_API_KEY` / `RESEND_WEBHOOK_SECRET` land in the environment (the webhook endpoint answers 503 until its secret is set).

## Verdict

The state claims in the merged scope §2 are confirmed at the surface and by the filed run evidence: **built, deployed, DB-backed, gate enforced**. M0-A's remaining steps are unblocked and wait only on the two owner acts:

1. **Resend values placed** (Route 1: GitHub sign-in completed in the live browser session holding the values — that session expires **20:49 ET**; Route 2: placement from James's own sessions — no expiry). On placement: SoSem dispatches the deploy, the workflow syncs both secrets into Vercel Production, and SoSem verifies the mailer is armed.
2. **`LIBRARY_MASTER_TOKEN` value provided by James** — placed the same way; opens the production admin API.

Then: the owner OTP end-to-end test at dev.uzemarkets.com (uze@uzemarkets.com), which closes M0-A.

*Recorded by SoSem, 2026-11-18. Raw outputs above are the actual responses observed; nothing here is a summary of another summary.*
