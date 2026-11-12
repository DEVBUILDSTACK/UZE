use near_sdk::{env, near, serde_json};

#[near(contract_state)]
pub struct Contract { /* empty for now */ }

impl Default for Contract { fn default() -> Self { Self {} } }

// Attestation anchors (spec 08 §10) live in raw storage keys,
// NOT in the root contract state: the state struct stays exactly
// as deployed, so adding anchoring needs no state migration and
// cannot disturb the marketplace methods' state. Two key shapes:
//   anchor-rec:{claim_id}:{attestation_hash}   -> juror (bytes)
//   anchor-idx:{claim_id}                      -> JSON [hash, ...]
const ANCHOR_REC_PREFIX: &str = "anchor-rec:";
const ANCHOR_IDX_PREFIX: &str = "anchor-idx:";

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

    /// Anchor one juror attestation hash for a claim (spec 08
    /// §10): the hash is the sha256 of the seat's report as
    /// recorded by compose (canonical JSON). Append-only and
    /// idempotent — re-anchoring the same (claim, hash) records
    /// nothing twice. Returns the anchored hash.
    pub fn anchor_attestation(
        &mut self,
        claim_id: String,
        juror: String,
        attestation_hash: String,
    ) -> String {
        let record_key = format!("{ANCHOR_REC_PREFIX}{claim_id}:{attestation_hash}");
        if !env::storage_has_key(record_key.as_bytes()) {
            env::storage_write(record_key.as_bytes(), juror.as_bytes());
            let index_key = format!("{ANCHOR_IDX_PREFIX}{claim_id}");
            let mut hashes: Vec<String> = env::storage_read(index_key.as_bytes())
                .and_then(|bytes| serde_json::from_slice(&bytes).ok())
                .unwrap_or_default();
            hashes.push(attestation_hash.clone());
            let encoded = serde_json::to_vec(&hashes).expect("hash index serializes");
            env::storage_write(index_key.as_bytes(), &encoded);
        }
        attestation_hash
    }

    /// The anchors recorded for one claim, as a JSON array string
    /// of {"claimId", "juror", "attestationHash"} in anchor order
    /// ("[]" when the claim has none) — the same string-returning
    /// shape as get_matches.
    pub fn get_anchors(&self, claim_id: String) -> String {
        let index_key = format!("{ANCHOR_IDX_PREFIX}{claim_id}");
        let hashes: Vec<String> = env::storage_read(index_key.as_bytes())
            .and_then(|bytes| serde_json::from_slice(&bytes).ok())
            .unwrap_or_default();
        let entries: Vec<serde_json::Value> = hashes
            .iter()
            .map(|hash| {
                let record_key = format!("{ANCHOR_REC_PREFIX}{claim_id}:{hash}");
                let juror = env::storage_read(record_key.as_bytes())
                    .map(|bytes| String::from_utf8_lossy(&bytes).into_owned())
                    .unwrap_or_default();
                serde_json::json!({
                    "claimId": claim_id,
                    "juror": juror,
                    "attestationHash": hash,
                })
            })
            .collect();
        serde_json::to_string(&entries).expect("anchor entries serialize")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Scaffold-stage spec checks: the four stub methods return exactly the
    // values specified in 01-PICKUP-TONIGHT.md. These are replaced when the
    // typed Intent/Bid/Match structs land on Day 2+.
    #[test]
    fn stub_methods_return_specified_values() {
        let mut contract = Contract::default();
        assert_eq!(contract.post_intent("{}".to_string()), "stub_intent_id");
        assert_eq!(
            contract.submit_bid("i1".to_string(), "{}".to_string()),
            "stub_bid_id"
        );
        assert_eq!(
            contract.settle("i1".to_string(), "b1".to_string()),
            "stub_settlement_id"
        );
        assert_eq!(contract.get_matches("i1".to_string()), "[]");
    }

    #[test]
    fn anchors_record_and_read_back() {
        use near_sdk::test_utils::VMContextBuilder;
        use near_sdk::testing_env;
        testing_env!(VMContextBuilder::new().build());

        let mut contract = Contract::default();
        // Nothing anchored yet.
        assert_eq!(contract.get_anchors("claim-1".to_string()), "[]");

        let returned = contract.anchor_attestation(
            "claim-1".to_string(),
            "seat-a".to_string(),
            "aa11".to_string(),
        );
        assert_eq!(returned, "aa11");
        contract.anchor_attestation(
            "claim-1".to_string(),
            "seat-b".to_string(),
            "bb22".to_string(),
        );
        contract.anchor_attestation(
            "claim-2".to_string(),
            "seat-a".to_string(),
            "cc33".to_string(),
        );
        // Idempotent: the same (claim, hash) anchors only once.
        contract.anchor_attestation(
            "claim-1".to_string(),
            "seat-a".to_string(),
            "aa11".to_string(),
        );

        let anchors: Vec<serde_json::Value> =
            serde_json::from_str(&contract.get_anchors("claim-1".to_string()))
                .expect("get_anchors returns a JSON array");
        assert_eq!(anchors.len(), 2);
        assert_eq!(anchors[0]["claimId"], "claim-1");
        assert_eq!(anchors[0]["juror"], "seat-a");
        assert_eq!(anchors[0]["attestationHash"], "aa11");
        assert_eq!(anchors[1]["juror"], "seat-b");
        assert_eq!(anchors[1]["attestationHash"], "bb22");

        let other: Vec<serde_json::Value> =
            serde_json::from_str(&contract.get_anchors("claim-2".to_string()))
                .expect("get_anchors returns a JSON array");
        assert_eq!(other.len(), 1);
        assert_eq!(other[0]["attestationHash"], "cc33");
    }
}
