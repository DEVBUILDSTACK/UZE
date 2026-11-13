# Hackathon Submission Checklist — NEAR Hackathon, Sprint 1.5

Deadline: **Nov 14, 2026, 23:59 UTC.** Merge to `main` by Nov 13 EOD Eastern.
Prepared 2026-11-08 (DeepSeek directive) so James can submit without hunting.

## Form fields

- **Project name:** UZEmarkets
- **Short description:** The agentic spatial finance engine for HiCRE,
  Agriculture, Development, and Resource RWAs.
- **Repo link:** https://github.com/DEVBUILDSTACK/UZE (public;
  `hackathon/nov-2026` merges to `main` at the Nov 13 close)
- **Demo video link:** _not yet recorded; recording planned
  Nov 14, ahead of the 23:59 UTC (18:59 ET) deadline_ (script:
  `docs/hackathon/nov-2026/DEMO-SCRIPT.md` — Beat 5 shows the real
  settlement receipt, Solana tx
  `3VXVoKq9pwrMZpQcuNBf6woFKLJm8mfXjNpUByLH9TA5H22j6RC7qFDdmy21KoqbTwdKhrKEyircqgvvj2ihSMJR`)
- **Payout wallet:** `cc26c309ed597488fb7e3b0d7c2d9b916f1fed3484b2c2da7de68f310d4c57bb`
  (native NEAR implicit account, generated 2026-11-09 at James's
  direction per DeepSeek's §11.3 ruling — Path A. Public key
  `ed25519:EjvTBySx4SY5Dk9ZNCrnBEZdGo47Q3wd4ra1UkFZJPqU`; the key file
  is held in SoSem's NEAR credentials store, seed phrase never
  transcribed. Supersedes the EVM address
  `0x1DAF7b5f95a023D441d8817157DD7A8c31426990` (surfsafe.eth), which
  holds NEAR only as an Ethereum ERC-20. Path B follow-up: the named
  account `uzemarkets.near` (verified unregistered 2026-11-09) to be
  created by James's son with a Ledger multisig; any payout can then
  be transferred there.)
- **Team lead email:** uzemarket@uzemarkets.com — supplied by James in his own words 2026-11-11. NOTE: the address cannot receive mail until the iCloud Custom Email Domain setup completes (apple-domain TXT; James expects activation later tonight, Nov 11). It is the published intake address and is correct for the form regardless.
- **Track:** Unstoppable DeFi — James's pick, 2026-11-09 (one
  preferred track of 13 available).
- **Public X demo post:** _James posts_ (@NEARProtocol, #NEARHackathon).

## Evidence the form can point at

- Live settlement on Solana devnet: 20.0 USDC, NEAR-identity-directed,
  Chain Signatures — tx above, verified on-chain (slot 520159103).
- Assurative trust layer: Entity/Affiliate/AgentCredential live-proven
  against compose (merge to Assurative main at the Nov 13 close, C-5).
- Evidence-gated A/D/R governance: Demo Dry Run v2, 14/14.
- Compose suite: 418 passed (local HEAD `b28fa13`). Alembic head `e8048229faab`.
- Live deployment: compose API live on Render at HEAD `e4da173`
  (`/health` ok; MCP `tools/list` returns `UZE_Research_Query`).
- Alpha signup window: opens Nov 15, 2026 (PT), per the live API.
- Pending the push — NOT yet live: the seven-commit local stack
  (desk@ intake, Desk-first llms.txt, SEO/GEO + llms-full.txt,
  D5 comp-set benchmarking, multiyear PDF findings/plan).
- Live attested NEAR AI inference: key provisioned + authenticates;
  fires the moment hackathon credits land on the org
  (HTTP 402 no_limit_configured until then).
