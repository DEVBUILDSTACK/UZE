# UZE Architecture — Backend Models

## Two backend models, one approach

| | Reference model | Innovation model |
|---|---|---|
| Repo | `DEVBUILDSTACK/Assurative-V2` (`apps/api`) | `DEVBUILDSTACK/UZE` (`services/api`) |
| Drives | **Fundio.vc** dual client sides | **UZE** backend: UZE consumer + UZED.si secondary |
| Stack | Python/FastAPI, SQLModel, Alembic | Python/FastAPI, Prisma, Neon Postgres, Redis |
| Contract | `APIResponse[T]` envelope, JWT + Privy | Same envelope, same auth pattern |

Assurative-V2 is the **proven backend model** — its router organization, auth
middleware, prestart lifecycle, and Docker patterns are what UZE follows.
UZE's `services/api` is the **innovation backend model**: same architectural DNA,
new domain (events, tickets, resale, auctions), new stack (Neon/Prisma/Redis),
clean ownership in the UZE repo. It does not import or depend on Assurative-V2
code; it follows its approach.

## Dual client sides (per backend)

**Fundio.vc** (on Assurative-V2): dual client-side UI + User Admin Command Console
(one Next.js app, three route-group surfaces — see `repo-scan/FRONTENDS.md`).

**UZE** (on `services/api`): dual client sides with **GIRA agentic guidance**:

| App | Surface | GIRA guidance |
|---|---|---|
| `apps/uze-web` | Consumer: find your next experience | GIRA concierge guidance |
| `apps/uzed-web` | UZED.si resale console (buy/sell/auction) | GIRA listing + bidding guidance |
| `apps/command-center` | C3 operator console (behind sign-in) | GIRA ops guidance for listors/brokers |

## GIRAgents — MVP affiliate creator business

The first affiliate business on the UZE backend, run by the **SoSim** agent,
mirroring the global experimental-music / DJ agency model: opportunity mirroring,
lead gen, gig bookings, revenue share. Backend surface: `/affiliates` (codes,
leaderboard, UZD payouts). See `services/api/src/routers/affiliates.py`.

## Multi-chain ticket commerce (Q4 direction)

UZE advances the innovation backend toward Solana multi-chain + LightLink EVM
NFT ticket commerce:

| Layer | Choice | Rationale |
|---|---|---|
| Primary chain | Solana | USDC x402 micro-transactions, Phantom WaaS (white-label) |
| EVM NFT tickets | **LightLink L2** | Optimism stack + Celestia data layer; gasless **Enterprise Mode**; co-founder/CEO **Roy Hui** explicitly cites ticketing as the gasless use case |
| Enterprise ticketing model | LightLink Enterprise-mode dApps (e.g. **Tickify**) | Built on LightLink's Optimism + Celestia DA stack in Enterprise Mode |
| Wallet | **Stella** (LightLink) | LightLink's chain-abstraction wallet — sign in instantly, move across networks (early-access beta, lightlink.io/wallet) |
| Bridging | **Stargate** (LayerZero) | ETH, USDC, USDT, LL to/from LightLink in minutes |
| Distribution | LightLink enterprise partners | 30+ partnerships incl. Animoca Brands — millions of potential users |

**Enterprise Mode mechanics (LightLink):** enterprises register on-chain in an
Enterprise Smart Contract (name, main account, monthly quota units, wei per unit),
pay fees upfront in stablecoins, and receive reserved block space; whitelisted
enterprise accounts transact at **gas price 0** — users never hold ETH or pay fees.
This is the UZE ticket-commerce model: the platform covers gas, fans just buy.

**Advisor link:** Roy Hui, co-founder/CEO of LightLink (Pellar, MMGN.com), based in
**Melbourne AU** — same city as the 456iP Melbourne blockchain team. Chain config
lives in `services/api/src/chains.py`; onchain ticket records in `/nfts`.
