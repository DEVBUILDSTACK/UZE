use near_sdk::near;

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
}
