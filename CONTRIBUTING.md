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

## Documentation philosophy (modular, living docs)

This repository follows a modular documentation philosophy. The README is a living index, not a static snapshot and not a dumping ground.

1. **Keep it modular.** When adding a new feature to UZE Underwrite, UZE Assign, or UZE Auction, create a specific markdown file for that feature in the respective `docs/specifications/` subfolder (`underwrite/`, `assign/`, `auction/`) and link it in the Master Index (the root `README.md`). Never append massive blocks of text to the main README.
2. **One component, one folder.** Each major component's specifications live in its own subfolder, with that folder's `README.md` as the component's current spec. New deep-dives are added as sibling files inside the same folder.
3. **Truth in documentation.** Every page states the status of what it describes, using the repository legend: 🟢 VERIFIED BUILT (live, tested, passing) · 🟡 BUILT AS MOCK (structure and endpoints exist and are tested; execution or external integrations are mocked, and payloads say so) · 🔴 PROPOSAL / ROADMAP (design finalized; code held for a future sprint). Never present a 🟡 surface as 🟢; if an integration is an adapter over synthetic data, the page names it as such.
4. **Update the index in the same change.** A new page not linked from the Master Index — and, where partner-facing, from `PARTNER-SHARE.md` — is not finished. The composite archive (`UZE-MASTER-COMPOSITE.md`) is regenerated from the modular files, never edited directly.
5. **Links must resolve.** Before pushing documentation, check that every relative link points at a file that exists in the new structure. Moving a spec means updating every link to it in the same commit.
