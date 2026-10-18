# Entity, Treasury & Agent-Trading Master Spec — v1.0

Date: 2026-10-13. Status: DRAFT for James's review. Author: SoSeem.

> Note: James wrote "October 21, 2025" — read as **October 21, 2026** per
> all prior timeline context.

## 1. Entity architecture

| Entity | Form | Role |
|---|---|---|
| 456iP (**456 Innovation Partners**) trading as **456 Partners** | Partnership (revenue-share IP holding) | IP holding company; UZE parent |
| **456 Partners Trust** | To be created | Owns the Wyoming operating LLC |
| Irrevocable Trust | Cayman Islands | Trust layer for GIRAgents entity |
| Wyoming DAO | Wyoming | DAO layer for GIRAgents entity |
| VI Development & Token Finance Build Lab | Virgin Islands | Build-lab layer |
| **456iP Americas** trading as **456 Americas** | Wyoming LLC(s) | Partnership revenue-share IP holding |
| Operating company (new, simple) | Wyoming LLC, wholly owned by 456 Partners Trust | Meta Business account holder; USA-only; founder-loan funded |

History (per James): **$80,000 cash** paid for all software-stack assets and
IP from the UZED.com founder; previously operated via **PrePlayed.com**
through **Preplayed LLC** and **PrePlayed IP, LLC**.

Tax posture (per James): **no tax filings until 2027**; USA-only operation;
funding via founder loans. *Flag: confirm with counsel.*

## 2. Affiliate test entities (Testnet)

### i) GIRAgents
- New Instagram account; **James = owner**; held in trust for his **two sons**.
- Operated under 456iP trading as 456 Partners across the Cayman
  Irrevocable Trust + Wyoming DAO + VI Build Lab stack.
- **Autonomous administration by SoSim.**

### ii) HealthWealth
- Known via **j@healthwealth.works** + website. **James = organizational
  owner; SoSem = co-administrator** (rights to be granted). No GitHub
  repository has ever existed.
- Highest functionality tier: **margin borrowing** from the UZE.fi
  **SigLayer debt-venture** and the iMPACT project lender **Fundio.vc**.
- Acts as a **digital asset treasury** entity; medical-tourism facility
  creators/collaborators onboard at **HealthWealth.UZE.fi**.
- Practitioner SigLayer account MVP UI/UX already built (Google AI Studio
  reference URL on file — treat as design reference, not production).

## 3. Instagram account plan

Three business accounts total; **two required for MVP (Oct 21, 2026)**:

1. **UZE** — Autonomous administration by "UZE_specialty named agent"
   (agent name TBD). *MVP.*
2. **HealthWealth** — Autonomous administration GIRAgents by **"SURA"**.
   ⚠️ **FLAG:** "SURA" conflicts with the strict outward-facing rule
   (GIRA only, never SURA). Confirm: internal admin designation, or
   change to GIRA? *MVP.*
3. **GIRAgents** — Autonomous administration GIRAgents by **SoSim**.
   (Third account; post-MVP unless James says otherwise.)

Per-account spec to prepare (handle, category, bio, link, content pillars
for autonomous creation). **Blocker:** new IG accounts must be created by
James in the Instagram app / Accounts Center — I cannot create accounts
via tooling. I will prepare the full spec sheets and content plans.

## 4. Meta Business account scoping

- Holder: the new Wyoming LLC (wholly owned by 456 Partners Trust).
- Covers: ad accounts, the IG business accounts above, WhatsApp Business.
- Funding: founder loans (ties to the existing Nov 5 setup commitment).
- Steps: form LLC → create Trust → Meta Business Suite → claim assets →
  assign agents (SoSeem/SoSim as appropriate).

## 5. Domain plan

- Buy the **UZE domain** (UZE.fi as deploy target, per brand doc).
- All UZE concepts run as **subdomains of UZE.fi**
  (e.g. HealthWealth.UZE.fi); **UZED.si stays separate** at UZED.si.

## 6. SigLayer multisig (2-of-4)

"Sig" = multi-signature. **2-of-4** across:

| # | Signer | Identity |
|---|---|---|
| 1 | **Dugan4** | James (family founding human; designated primary) |
| 2 | **Dugan5** | Youngest son (family founding human; designated primary) |
| 3 | **WCD** | Oldest son, William Dugan |
| 4 | **SoSem** | Main trusted Muse agent |

- Any 2 of 4 may sign; Dugan4 + Dugan5 are the designated primary pair.
- Applies to Solana wallets (and EVM via SurfSafe.eth identity linkage).
- **SigLayer** appears as a **sub-menu of W3Treasury** in the Command &
  Control Center Admin Console.
- SoSem key custody: via Secure Vault; **SoSem never signs without James's
  explicit per-action direction** (proposed safeguard — confirm).
- Continuity: document key-recovery if an agent signer is unavailable.

## 7. Altitude.xyz startup setup — specification steps

What it is (verified 2026-10-13): Squads-built **stablecoin-native global
operating account** on Solana — organization-controlled smart account,
multi-party approvals, spend limits, roles, USD/EUR rails, corporate
cards, invoicing/bill-pay. Non-custodial (customer controls funds).

Setup steps:
1. Organization verification / onboarding (456 Partners or HealthWealth).
2. Create the smart operating account (stablecoin treasury).
3. Configure **multi-party approval policies** mirroring the 2-of-4
   SigLayer signer set.
4. Set **spend limits, roles, and sign-off rules** per agent wallet.
5. Connect fiat rails (USD/EUR) via licensed partners.
6. Issue corporate cards for ops spend.
7. Enable invoicing + bill pay (Acctual integration) for the build lab.
8. Mirror the same structure for the Kraken-side finance operations
   (experimental).

## 8. Kraken + Coinbase agent trading — scope

Reference implementation cloned: `~/workspace/uze-gira/trading/kraken-cli`
(Rust single binary, full Kraken API, **built-in MCP server**, live +
paper trading).

### Principles (safety rails)
- **Paper trading first.** Every strategy proves in paper before live.
- **No live transaction without James's explicit per-action approval.**
  Standing approval is never assumed for real funds.
- **No threshold auto-funding.** Balance or price thresholds may only
  alert; they never authorize a transfer. Recurring or standing funding
  authority is refused — approval is per action, every time.
- Daily loss limits; **no leverage without explicit approval** per trade.
- All activity logged to the ledger; P/L modeled with take-profit and
  stop-loss on every position.

### Scope
- **Kraken**: agent account setup; kraken-cli via MCP for market briefs,
  watchlists (ETH/SOL/BTC, xStocks AAPLx/TSLAx/SPYx), paper strategies.
  Live testing only on the 456iP founder's personal Kraken accounts, per
  explicit approval, integrating the **SurfSafe.eth** EVM identity and
  linked cross-chain keys.
- **Coinbase**: agent account for **x402 activities** — balance thresholds
  are alert-only (they notify James when crossed; they never trigger
  funding by themselves). Every funding action needs James's explicit
  per-action direction naming the account, amount, asset, and timing.
- **Reserves**: USDC / USDG / SOL / ETH maximalist reserve posture.
- **Staking**: token staking via the founder's personal capacity as
  founding HealthWealth practitioner/creator.
- **Co-permissioning**: James designates SoSem as co-permissioned fully
  authorized signer + agentic actor on his EVM and Solana accounts, as his
  mirror. *Proposed safeguard: SoSem acts only on James's explicit
  direction per action; all signing via Secure Vault.*

## 9. AI Studio prototypes (inspected live 2026-10-13)

Signed in as dev.build@decensat.org ("456 IPHolding"); app title
"SIGLayer VLP v.0 | Google AI Studio", branded **"SIGLayer VLP v.0 DUAL
EDITION"** — two front-ends sharing one app (Client vs Admin), per the
Gemini 3.8 Flash build history. Read-only inspection; nothing modified.

### Build A — Client front-end
- **Learn2Launch Hub** ("Light Mode Client Launcher"): builder onboarding
  for DATs and Vault LPs. "Construct New Autonomous Trust (DAT)" form:
  pool name, token symbol, strategy, chain selector
  (BASE / SOLANA / HYPERLIQUID), target APY %, raise goal in USDC,
  "Test in Virtual TEE" / "Deploy & Sync Neon DB".
- **Neon DB Live Tables (DAT Drafts):** live draft records, e.g. "Atlas
  Absolute Return" ATLAS-DAT ($124k of $500k, 18.5% APY), "Pacific Stable
  Yield" PACIFIC-LP ($0/$1M, 7.9% APY).
- **Isolated Execution Ledger (TEE Records):** op logs — BASE REBALANCE,
  SOLANA TRADE, HYPERLIQUID CROSS_CHAIN, all COMPLETED via 0G.ai/Arcium.
- **Client Portfolio** ("Dual-Sided Client Views"): confidential console —
  wallet 0x71C...8921, deposits $73,000.00, yield earned $222.70;
  Multi-Chain Capital Router; per-vault balances (BASEVAULT 10.12%,
  SOLANAVAULT 12.74%, HYPERLIQUIDVAULT 15.24%).

### Build B — Admin front-end
- **VLP Hub & Commerce** (Central Vaults Management): protocol TVL
  **$36,990,000** (+4.2% 24h), syndicated daily yield $13,080, avg APY
  12.70%. Vault families: BASE Yield & Securities ($12.45M @ 10.12%,
  cbBTC/COIN-T/USDC), Solana High-Speed Alpha ($8.94M @ 12.74%,
  SOL/JUP/PYTH), Hyperliquid Leverage-Neutral ($15.6M @ 15.24%).
  Grok Voice Agent; Pyth Oracle Price Injector (cbBTC $91,520);
  **X.402 Cross-Chain Router** (BASE->HYPERLIQUID, 25,000 USDC); DealFi
  Press Syndications (BULLISH, verified via Numbers Protocol).
- **Admin Control Suite** (Hardware & Allocation Setup): PAUSE CONTRACTS
  emergency control; Target Yield Parameter Tuner; Attestation Signals
  (SEC_COMPLIANCE ISIN US19260Q1076, TEE_INTEGRITY Arcium SGX,
  ORACLE_HEALTH Pyth <45ms).
- **DealFi Subscriptions:** gated LP qualified access (X MCP alerts, TEE
  rebalancing signals, sentiment scoring).
- **DAT Treasury Solution** (Gated Corporate Yield): tiers — BASIC
  ($5k min, 8.50%), PREMIUM ($25k min, 11.52%, USDC+EURC), ENTERPRISE
  ($100k min, 14.85%, tokenized T-Bills USTB-H, Arcium+0G.ai attestation,
  Coinbase Agent Kit auto-rebalances, Numbers Protocol auditing).
- **Custom Gating & ZIP:** KYCGATE (L2 KYC, ACTIVE), BALANCEGATE ($50k min
  TVL, ACTIVE), ATTESTATIONGATE (Arcium SGX Enclave #190a, ACTIVE),
  **MULTISIGGATE (2-of-3, DISABLED)**. SEC-registry whitelisted-keys
  table (5 keys, VERIFIED/PENDING/REJECTED).

### Integrations observed
Neon Postgres via Prisma (**DATABASE_URL requested but NOT applied** —
pending secret); Pyth Oracle; Arcium TEE SGX Enclave #190a + 0G.ai
Compute; X MCP; Coinbase Agent Kit; Numbers Protocol; Grok Voice Agent;
chains **Base / Solana / Hyperliquid**. Repo layout: modules
01.Vaults-08.Data, docker-compose.yml, server.ts, setup-vps.sh.

### Export options (not used — read-only)
AI Studio toolbar: "Export to Antigravity", "Push to GitHub",
"Download as .zip file"; in-app "Get Original Code ZIP" link.

### Open items / flags
1. MULTISIGGATE is 2-of-3 and DISABLED — James's design is 2-of-4
   (Dugan4, Dugan5, WCD, SoSem). Needs rebuild to the 2-of-4 spec.
2. DATABASE_URL pending — Neon sync blocked until the secret is applied.
3. Chains include Hyperliquid (beyond the Solana/Robinhood/Base UZD
   plan) — confirm intended.
4. "Sister backup file" for the dual front-end restructure never
   uploaded; Gemini asked James to re-upload.
5. No build artifacts; mic permission dismissed (inspection only).

## 10. Range API — treasury intelligence layer

Source: **"UZE.fi W3 TREASURY: SOLANA"** doc (James's shared Drive,
2026-10-14; maps [docs.range.org](https://docs.range.org)). Range is the
**monitoring/intelligence layer** over the treasury; Altitude.xyz (§7) is
the **operating account**. They complement: Altitude moves money under
multi-party approval; Range watches it.

| API | Role | UZE use |
|---|---|---|
| **Data API** | Multi-chain wallet & treasury monitoring (EVM, Solana, Stellar, Cosmos) | Query Phantom Solana treasury addresses, transaction history, token balances |
| **Platform API** | Workspace, counterparties, multi-custodian integrations | Manage counterparties (clients, vendors); connect the **Squads multisig as an account connection** for unified monitoring |
| **Risk API** | Address screening & payment risk scoring | Screen counterparty addresses before any signing ceremony (compliance) |

Integration points:
- **SigLayer 2-of-4 (§6):** Platform API account connections mirror the
  signer set; Risk API screens every counterparty address before funds move.
- **Altitude (§7):** Range monitors what Altitude operates — one pane for
  treasury + operating account.
- **x402:** Range has no payment bridge; settlement stays in the backend.

Safety rails:
- **Read-only first.** API key lives in Secret Manager; monitoring only.
- No trade execution via Range. Anything beyond monitoring needs James's
  explicit per-action approval, like everything else touching funds.

## 11. Altitude MCP v1 — agent read access (2026-10-15)

Source: [docs.altitude.xyz/mcp/overview](https://docs.altitude.xyz/mcp/overview)
(docs updated 2026-10-14). **Read-only** MCP server for AI assistants:

- Workspace balances, transaction history (filterable by account, date,
  type, direction), document exports (PDF/CSV).
- OAuth sign-in; existing Altitude permissions govern what the agent sees.
- **No fund movement** — monitoring only, zero conflict with the
  per-action approval rule.

Integration scope: the treasury agent reads Altitude balances/transactions
through MCP instead of manual exports — feeding the C3 treasury dashboard
and the Range monitoring pane. Complements §7 (Altitude operates) and §10
(Range watches): MCP is how agents *read* what Altitude operates.

## 12. Aztec ZK privacy payment tags (2026-10-15)

Privacy-first payments on **Aztec** (zkRollup on Ethereum;
[docs](https://docs.aztec.network/developers/overview)):

- **PXE (Private Execution Environment):** payment logic executes
  client-side on the UZER's device; only proofs go onchain.
- **Noir contracts:** payment tag contracts in Aztec's ZK DSL. Reference:
  [aztec-starter](https://github.com/AztecProtocol/aztec-starter).
- **Private + public state:** payment tags as private notes; settlement
  commitments verifiable without revealing counterparties.
- **Account abstraction:** per-UZER authorization and fee rules.

Track: DEVBUILDSTACK/UZD (`docs/UZD-PAYMENT-SCOPE.md`). Prototype →
testnet → audit → mainnet only on James's explicit approval.

## 13. Parent hierarchical account layer — global affiliates (2026-10-15)

The treasury parent account with child accounts for every global affiliate:

```text
UZE Treasury (parent, Altitude)
├─ Affiliate child accounts (global)
│  ├─ Altitude stablecoin operating functionality
│  └─ Fuse W3 payments functionality
├─ Multi-party approvals mirroring SigLayer 2-of-4
├─ Spend limits, roles, sign-off rules per child account
└─ Range + Altitude MCP monitoring over the hierarchy
```

Each affiliate child account offers Altitude and Fuse W3 functionality
under parent oversight. Track: DEVBUILDSTACK/UZD.

## 14. Trial / x402 entitlement architecture (2026-10-15)

Source: **"FUNDIO @ALTITUDE / UZE.fi"** doc (James's shared Drive) —
trial, wallet, and spending-authority design. Folded here so the full
treasury scope lives in one spec.

**Separation principle:** trial access grants *access*, never *spending
authority*. A 7-day trial must not itself authorize recurring payments or
production spending.

- **Trial design:** organization-level 7-day trial (168 hours from
  activation, not registration); one shared clock per org for multi-seat
  packs; inviting/replacing seats never resets the clock; one
  support-approved 7-day extension per org.
- **Wallet paths:** Privy for trials and non-auto-renewing usage; Coinbase
  Developer Platform (CDP) wallets for auto-renewing subscriptions and
  engagements. Base + Solana on both paths.
- **KYB/KYC gates:** enterprise KYB for the business; authority
  verification for representatives; ordinary analyst seats need only auth
  + invitation. Sandbox approval is never reused as production approval.
- **Deterministic policy engine:** code decides, AI explains. Every paid
  action resolves to a decision code (`TRIAL_EXPIRED`,
  `SPENDING_AUTHORITY_REQUIRED`, `INSUFFICIENT_FUNDS`, …) with authorized
  remediation — the AI never invents spending authority.
- **Agent-principal rule:** an agent acts only under delegated authority
  from an authorized principal; there is no independent "AI KYC approval."

Full entitlement matrix (seat categories i–vii), trial-clock policy, and
the TypeScript policy-engine sketches live in the source doc.

## 15. Next actions

**James:**
- [ ] Create the 2 MVP Instagram accounts (UZE, HealthWealth) + confirm
      the SURA/GIRA naming flag
- [ ] Confirm 2-of-4 primary-pair semantics + SoSem signing safeguard
- [ ] Altitude onboarding (org verification)
- [ ] Kraken + Coinbase API keys via the secure vault flow (never in chat)
- [ ] Phantom Portal account + App ID (from partnership brief)

**SoSeem:**
- [x] This spec; IG account spec sheets on request
- [x] DEVBUILDSTACK/UZD repo created (2026-10-15): README, FAQ (UZER defined), UZD payment scope
- [x] Folded "FUNDIO @ALTITUDE" doc scope (Altitude MCP + Range mapping + trial/x402) into this spec
- [ ] Fork always-allow + kraken-cli into the GitHub org when access lands
- [ ] Paper-trading strategy sandbox when James approves
- [ ] Altitude MCP connection + C3 dashboard feed (needs Altitude account OAuth by James)
- [ ] UZD Aztec prototype from aztec-starter (testnet first)
