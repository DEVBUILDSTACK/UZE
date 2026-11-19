# Vendored — pinned copy of the design gate

This directory is a **pinned copy** of the canonical UZE design gate,
vendored 2026-11-19 for the HUMAN ECOSYSTEM DESIGN Stage 1 wiring, so the
car wash can run in this repo's CI (the canonical gate lives outside any
repo, in SoSem's workspace).

- **Canonical source:** `~/workspace/tools/design-gate/` (SoSem workspace).
- **Pinned files:** `gate.mjs` (md5 `01f70d18fa1e1670c52f57be80a255b5` —
  gate v0.2, re-vendored 2026-11-19: `--wordmark` selector, stylesheet
  palette lint for URL targets, alpha-00 hexes counted not failed;
  first vendored 2026-11-19 at md5 `b6cfa8a6235b32b510d66291f959d4a2`),
  `package.json`, `package-lock.json`, `README.md` — copied byte-for-byte. `node_modules` is never vendored; CI installs from the
  lockfile (`npm install --no-workspaces --prefix tools/design-gate`).
- **Sync rule:** the gate is one implementation for the whole ecosystem.
  Never edit this copy to change gate behavior — amend the canonical gate,
  then re-vendor and note the new hash here. A repo-local gate fork is a
  design-system change and needs James's ratification like any other.
- **Note:** the README's axe paragraph describes the Dev Library page's
  pre-2026-11-19 findings; those two findings were fixed on 2026-11-19 and
  the page runs at zero axe violations. Promoting critical/serious axe
  findings to hard gate failures is the documented next step.
