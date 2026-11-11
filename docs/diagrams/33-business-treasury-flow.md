# Diagram 33 — Business Treasury Flow (Fiat & Treasury)

Filed 2026-11-11 with the Autonomous Treasury build (owner's
override). Sourcing annotations per research note 18:

- **Fiat on-ramp session:** the integration pattern is Fundio's
  CDP onramp session route (`src/app/api/session/route.ts` —
  JWT-minted session token, third-party provider, funds land
  directly in the user's self-custodial wallet; UZEmarkets
  never touches fiat).
- **Swaps / x402 payments:** CDP is the target integration
  (AgentKit = Sprint 2 build item; Fundio contains no AgentKit
  and no swap module — verified 2026-11-11). Hackathon state:
  mock CDP router in compose (`treasury.py` / `treasury_router.py`).
- **Cross-chain USDC:** production moves ride Circle CCTP —
  **V2 only; V1 contracts pause December 1, 2026** (note 18,
  Part 4). No CCTP code exists in the UZE stack today.
- **x401 identity:** Proof's open protocol (draft 0.2.0);
  verification is issuer-key verification over HTTP. Arc is a
  supported network on the settlement side of the x401/x402
  flow. Real x401 verification is pending research/build —
  see diagram 34 and note 18.

```mermaid
flowchart TD
    subgraph FIAT["Fiat On-Ramp (Third-Party)"]
        BANK["Debit Card / ACH / Wire"]
        PROVIDER["Fiat Provider<br/>(No UZE MSB License)"]
        BANK --> PROVIDER
    end

    subgraph TREASURY["UZEmarkets Self-Custodial Treasury"]
        WALLET["User Wallet<br/>(Squads, Safe, Phantom, etc.)"]

        subgraph ASSETS["Supported Assets"]
            SOL["Solana USDC (Default)"]
            BAS["Base / Ink / Arc / Robinhood"]
            NEAR["Native NEAR"]
        end
    end

    subgraph UTILITY["Platform Utility"]
        INF["NEAR AI Inference<br/>(Requires NEAR)"]
        AUCTION["Arcium Auctions<br/>(Requires USDC)"]
    end

    PROVIDER -->|"Routes Fiat to Crypto"| WALLET
    WALLET --> ASSETS

    ASSETS -->|"Swaps/Sends"| INF
    ASSETS -->|"Swaps/Sends"| AUCTION

    style FIAT fill:#fff3e0
    style TREASURY fill:#e3f2fd
    style UTILITY fill:#e8f5e9
```
