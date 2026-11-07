# PICKUP TONIGHT — November 7, 2026

**From:** James and DeepSeek
**To:** SoSem
**Window:** Tonight (Nov 7) through tomorrow morning
**Purpose:** Establish Day 1 foundation. Chain Signatures go/no-go. Nothing else.

---

## Tonight's three deliverables

### Deliverable 1 — Rust contract scaffold

Create `contracts/near/uzemarkets-talent/` with:

```bash
cargo near new uzemarkets-talent
cd uzemarkets-talent
```

Four methods in src/lib.rs, empty bodies, that compile and deploy:

```rust
#[near(contract_state)]
pub struct Contract { /* empty for now */ }

impl Default for Contract { fn default() -> Self { Self {} } }

#[near]
impl Contract {
    pub fn post_intent(&mut self, intent_json: String) -> String {
        "stub_intent_id".to_string()
    }

    pub fn submit_bid(&mut self, intent_id: String, bid_json: String) -> String {
        "stub_bid_id".to_string()
    }

    pub fn settle(&mut self, intent_id: String, bid_id: String) -> String {
        "stub_settlement_id".to_string()
    }

    pub fn get_matches(&self, intent_id: String) -> String {
        "[]".to_string()
    }
}
```

Critical serialization rule (from the NEAR docs): contract state uses Borsh, function inputs/outputs use JSON. u64/u128 must be U64/U128 from near_sdk::json_types. Not doing this costs half a day. We are using String for JSON payloads at the scaffold stage to avoid this entirely — the real typed structs come in Day 2+.

Build and deploy:

```bash
cargo test
cargo near build non-reproducible-wasm
near create-account uzemarkets-talent.testnet --useFaucet
near deploy uzemarkets-talent.testnet ./target/near/uzemarkets_talent.wasm
near call uzemarkets-talent.testnet post_intent '{"intent_json":"{}"}' --useAccount uzemarkets-talent.testnet
```

Success criterion: the four empty methods return success on-chain.

Deliverable 2 — Two named accounts

```bash
near create-account treasury.sarah.testnet --useFaucet
near create-account recon.agent.testnet --useFaucet
```

Note the .testnet suffix. Named accounts carry identity. Both are real testnet accounts with real keys.

Deliverable 3 — Chain Signatures dry-run (THE GO/NO-GO)

This is the single most important test tonight. If it works, the entire demo is real cross-chain settlement. If it doesn't, we retry through Nov 9, then fall back to mocked settlement.

Use near-omni-client (Python):

```python
from near_omni_client import ChainSignatures

cs = ChainSignatures(network="testnet")
solana_address = cs.derive_address(
    near_account="uzemarkets-talent.testnet",
    chain="solana"
)
print(f"Derived Solana address: {solana_address}")

signed_tx = cs.sign_transaction(
    near_account="uzemarkets-talent.testnet",
    chain="solana",
    tx_payload={ /* Solana devnet transfer payload */ }
)
print(f"Signed: {signed_tx}")
```

Success criterion: a Solana address is derived from the NEAR account, and a Solana devnet transaction is signed.

If this succeeds: the settlement rail is proven. Proceed to Day 2 with confidence.

If this fails tonight: identify the specific failure point (derivation, signing, submission) and report it. Do not attempt the full settlement flow yet. Retry Nov 8.

If this fails Nov 9 EOD: the demo uses mocked settlement with honest framing: "NEAR flow complete, Solana primitive proven separately, full integration in Sprint 2."

---

Also tonight — the intent schema

Draft docs/hackathon/nov-2026/intent-schema.md with this shape:

```rust
Intent {
  kind: "availability" | "demand",
  poster_kind: "human" | "agent" | "internal_agent" | "partner",
  poster_account: AccountId,
  domain: "cre_expense_analysis" | "cre_property_management" | 
          "cre_market_survey" | "cre_income_analysis",
  work_product: "operating_budget" | "pm_spec" | "cost_model" | 
                "benchmark_analysis" | "placement",
  deliverable: JSON,
  micro_region_id: String,
  asset_context: {
    property_type: "branded_hotel" | "residential_rental" | 
                   "residential_condo" | "hospitality" | "medical_recovery",
    door_count: Int,
    brand_affiliation: String?,
    acquisition_stage: "underwriting" | "post_close" | "operating"
  },
  on_site_days: Int?,
  remote_days: Int?,
  budget_min_usdc: U64,
  budget_max_usdc: U64,
  available_from: U64,
  available_until: U64,
  tier: "A" | "B" | "C" | "D" | "E" | "ANY",
  referring_partner: String?
}
```

---

What not to do tonight

· Do not touch Sprint 1's compose code. Slices 1 and 2 remain as filed. This is a new branch, not a replacement.
· Do not create a new repo. Work in DevBuildStack/UZEMARKETS.
· Do not attempt the full settlement flow. Tonight is scaffold + primitive proof. Full settlement is Day 3.
· Do not integrate NEAR AI inference. That is Day 4.
· Do not build the Next.js pages. That is Day 6.

---

What to report back tonight

One message, three items:

1. Contract deployed — testnet address, WASM hash, four methods callable
2. Two accounts created — confirm both .testnet accounts exist
3. Chain Signatures status — success or specific failure mode with detail

Report by end of your working session tonight.
