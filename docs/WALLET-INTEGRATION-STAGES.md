# Wallet Integration — Business-through-Technical Implementation

**INTERNAL.** Written for the Web3 developer who represents us to enterprise clients: enough business framing to sell it, enough technical detail to build it.

## Why these five wallets

| Wallet | Business coverage | Technical path |
|---|---|---|
| **Phantom** | Solana retail + mobile; aligns with our Solana-native / Seeker positioning | Solana wallet-adapter; also speaks EVM |
| **Coinbase Wallet** | 100M+ Coinbase retail users; smart-wallet gasless UX | `@coinbase/wallet-sdk` (already in Fundio @ 4.4.0); CDP embedded wallets server-side |
| **Robinhood Wallet** | Mainstream brokerage-crossover users | WalletConnect universal provider (no standalone web SDK — integrate via WC) |
| **MetaMask** | Largest EVM installed base; DeFi natives | EIP-6963 discovery + wagmi injected connector |
| **Safe** | Enterprise/DAO treasuries — the multisig story clients pay for | `@safe-global/protocol-kit` (already in Fundio @ 6.1.2) |

EVM side runs on **wagmi 2.x + viem 2.x** (proven in Fundio). Solana side runs on the Solana wallet-adapter + `@solana/spl-token`. Privy covers embedded/auth abstraction where the client wants email login instead of a seed phrase.

## The stack that's already proven
Fundio carries the working wallet surface today: wagmi, viem, Safe protocol-kit, Coinbase wallet-sdk + CDP, Privy, solana web3. UZE's apps (`uze-web`, `uzed-web`) have **no wallet deps yet** — this doc is the blueprint for adding them.

## Stage 1 — Connect (read)
**Business:** the user links a wallet in seconds; the dapp knows who they are and what they hold.
**Build:**
- One connect modal listing all five (EIP-6963 auto-discovery for MetaMask/Coinbase/Robinhood-via-WC; Solana adapter for Phantom).
- Connect → address → balances (SOL/SPL on Solana; ETH/ERC-20 on EVM) → session persisted.
- No private keys ever touch our servers. Non-custodial, always.
**Mockup visualizes:** wallet picker, connected address chip, portfolio balances.

## Stage 2 — Transact (write)
**Business:** the user does things — signs, pays, mints, lists.
**Build:**
- Sign messages (auth, attestations) and send transactions per chain.
- Token transfers: `@solana/spl-token` (Solana), ERC-20 via wagmi/viem (EVM).
- x402 payment flows ride on the connected wallet's signing.
- Per-wallet signing UX is respected, not fought (Phantom's mobile deeplinks, Coinbase smart-wallet passkeys, MetaMask's confirmation screens).
**Mockup visualizes:** checkout signing flow, listing confirmation, payment status states.

## Swap & bridging rails — primary/secondary decided by MVP → production data
Users need to swap tokens and move Bitcoin in and out. We integrate the rails the wallets already trust instead of building our own.

**Matcha / 0x — swap aggregation (primary candidate, EVM + Solana)**
- The trading API for every chain: 150+ liquidity sources across EVM, Solana, Tron, HyperCore — one integration.
- Swap API: firm quotes (`/swap/allowance-holder/quote`), gas estimates, tx data; API key via the 0x dashboard (`0x-api-key`, `0x-version: v2` headers).
- Gasless API: gasless approvals via ERC-7597 permits — pairs with Coinbase smart-wallet UX.
- Cross-Chain API: 15+ chains, 12+ bridge providers, price-or-speed routing, streamed routes with fallbacks.
- Monetization built in: `tradeSurplusRecipient` routes trade surplus to our wallet; affiliate options on top.
- Provenance: $400B+ volume, 500+ teams; already powers swaps inside Coinbase, Robinhood, Phantom, and MetaMask.
- Docs: https://docs.0x.org/docs/introduction/welcome

**Garden — native Bitcoin bridging (primary candidate, BTC)**
- Intent-based orderbook: users submit swap intents, solvers compete, settlement is atomic via HTLCs — no wrapped assets, no liquidity pools, no custody given up.
- Chains: Bitcoin, Ethereum, Arbitrum, Base, Solana, Starknet, Sui, Tron, Litecoin.
- API: quote → create order → track lifecycle; key from the Integrator Portal (`garden-app-id` header); SDKs `@gardenfi/core`, `@gardenfi/orderbook`, `@gardenfi/react-hooks`.
- One-Click Swaps: a preimage manager redeems on the destination chain — the user doesn't stay online (matters for mobile and slow Bitcoin finality).
- Affiliate fees on every swap through our integration = a revenue line.
- Provenance: $2B+ volume, 32 integrators — including Coinbase, MetaMask, Phantom, and Robinhood Wallet. Starknet support aligns with the UZD rail evaluation.
- Docs: https://garden.finance/docs/developers/api/overview · full index: https://docs.garden.finance/docs/llms.txt

**The call we make with data:** MVP ships Matcha as the primary swap rail and Garden as the primary BTC rail. Primary/secondary is NOT locked — we compare fill rates, latency, and all-in fees from MVP telemetry through production launch, then commit. Both sit behind our own swap abstraction so switching costs stay near zero.

## Stage 3 — Enterprise (multisig + treasury)
**Business:** the client enterprise doesn't sign with one key — it governs with many. This is the finish line that wins contracts.
**Build:**
- Deploy Safe (EVM) via protocol-kit; configure owners + threshold (M-of-N).
- Propose → collect signatures → execute: the full multisig lifecycle in the dapp.
- Spending policies and role-scoped permissions on top.
- Treasury views tie into the entity treasury spec (balances, flows, attestations).
**Mockup visualizes:** Safe dashboard, pending-signature queue, threshold progress, treasury overview.

## What the dev rep tells enterprise clients
- **Custody stays with you.** We never hold keys; Safe gives you M-of-N governance over every treasury move.
- **One integration, five wallets.** Your users bring the wallet they already trust; your treasury runs on Safe.
- **Audit trail built in.** Every action is provenance-recorded (TREE) — who proposed, who signed, what executed.
- **Phased rollout.** Stage 1 → 2 → 3 ships in order; each stage is demoable on its own.
- **Test mode until Nov 10.** No mainnet, no production funds until the decision gate.

## Gates & open items
- Test/testnet only until the 2026-11-10 decision gate.
- Robinhood Wallet path needs a WalletConnect project ID (Cloud) — obtain before Stage 1 build.
- Safe transaction-service URL per chain (mainnet vs testnet) — confirm at Stage 3 kickoff.
- Decide: Privy embedded wallets as the fallback for users with no wallet (recommended yes for conversion).
- Swap rails: obtain a 0x API key (dashboard) and a Garden Integrator Portal key (`garden-app-id`); lock primary/secondary on MVP telemetry (fill rate, latency, all-in fees), not before.
