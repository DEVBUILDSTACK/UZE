# Learn2Launch Org — Program Software Stack (DRAFT v0.2)

**INTERNAL — NOT FOR EXTERNAL SHARING.** Draft for James's review. Assembled 2026-10-18.

**Revision v0.2 (2026-10-21):** component 5 added — the standard build
and the Jev Form Router (Python core; NodeJS flavor with Drizzle ORM
instead of Prisma), per James's direction.

The software features of the Learn2Launch Org program stack:

## 1. UZE_KB

Auto-assembling knowledge hub. Monolithic index across the repos;
on-the-fly per-affiliate builds when prompted or clicked.

## 2. Agentic x402

Permissionless, non-custodial micropayments. The company owns and funds
its own accounts; payment clears only if the account holds USDC; the
company sets its own programmatic rules (spend limits, allowlists).

## 3. Altitude + Range

Hierarchical wallet as a service and treasury as a service on
Solana-based wallets — Altitude: workspaces, accounts and balances,
transaction activity, Squads multisig connected as an account connection.
Dashboarding from the treasury layer plus EVM account connectivity,
including EVM wallet use with Safe multisig — Range.

## 4. Animation studio

User-generated, super-intelligence-scaffolded video animation tool for
the content channels. Output visualizes app functionality, brand
positioning (why UZE), differentiation USP, reinforcing CTAs.
Resend-style versioned releases.

## 5. The standard build — Jev Form Router

Every project builds identically to the UZE build: same repository
shape, same deploy path, same gates. The core organization
architecture is Python — FastAPI back end, Pydantic models, Prisma
ORM. The NodeJS flavor is the defined variant: Node.js back end,
Drizzle ORM instead of Prisma, and the Jev x AI SDK Form Router in
its native form. The Python core runs the same router on the official
typesafe-sdk. Intake — leads, contact, issue reports — is routed by
content: Jev decides the destination at the 0.95 confidence policy,
a fallback model decides below it, delivery via Resend with the
decision on record.
