# Contributing to the UZE monorepo

## Naming discipline (strict — do not drift)
- Outward-facing name is **GIRA**. Never write **SURA** in product, copy, or code identifiers. The in-app agent and agent guidance are called **GIRA**; the Assurative.ai experience is the **GIRAx Layer**.
- Marketplace copy reads **"UZED.si resale by UZE"** — never write `UZE.fi` in user-facing copy. `UZE.fi` is the product brand and deploy domain only.
- Consumer-facing copy stays free of tokens, chains, and "super-intelligence" until those capabilities are built and approved.

## Dual theme system
- **UZE primary** (uze-web, command-center): Solana ombre theme — blue → light blue → green accents on logo and buttons; purple boxes as the web3 degen card color; bright winter-white text on black glass. No neon "UZ" badge in nav.
- **Auction / UZED.si secondary / Preowned** (uzed-web) and **Knowledge Base / dev docs**: Maple.finance-inspired editorial language — serif headlines, institutional dark sections, **tangerine/coral** accent. Tangerine-on-purple is banned.
- **GIRA icon** keeps Solana ombre coloring everywhere. **UZED icon** is distinct (never Solana-colored): Maple/cream + tangerine ombre, winter white on black glass.

## Branch model
- `main` — protected; what deploys. `dev` — integration. `feat/<scope>` — feature branches, PR into `dev`.
- Melbourne / Surat / USA: coordinate in `dev`; rebase before PR.

## Commits
Conventional commits: `feat(uze-web): …`, `fix(uzed-web): …`, `docs: …`, `chore: …`.
