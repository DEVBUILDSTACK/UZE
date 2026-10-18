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
