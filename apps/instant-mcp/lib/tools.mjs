// Tool catalog of record (Scope 3 spec §3, as amended: 9 base + 9
// vertical = 18). M2 ships the 9 base tools: 7 LIVE, and create_escrow /
// release_milestone DARK until M3's settlement substrate (amendment A3).
// The 9 vertical tools are Markets-tier, landing in M3 — they are in the
// catalog so the tier gate can refuse them correctly tonight.
export const TIERS = {
  instance: { name: "UZE Instance", blurb: "Branded NEAR AI Cloud compute + settlement. No vertical access." },
  markets: { name: "UZE Markets Instance", blurb: "UZE Instance + TradeLayer, SigLayer, Arcium and Talent pathways." },
};

// price: per-call meter in micro-USDC. pay_via_x402 meters its amount.
export const CATALOG = {
  // Core — both tiers (5)
  provision_instance: { tier: "base", status: "live", price: 500, description: "Provision a UZE Instance of the given tier and spec. (M2: LOCAL MOCK provisioner — see README.)",
    inputSchema: { type: "object", properties: { tier: { type: "string", enum: ["instance", "markets"] }, spec: { type: "object", properties: { size: { type: "string", enum: ["KVM1", "KVM2", "KVM3"] } } } }, required: ["tier"] } },
  get_credentials: { tier: "base", status: "live", price: 10, description: "Get access credentials for an instance you own. (M2: mock credentials.)",
    inputSchema: { type: "object", properties: { instance_id: { type: "string" } }, required: ["instance_id"] } },
  terminate_instance: { tier: "base", status: "live", price: 25, description: "Terminate an instance you own; final usage is recorded in the chronicle.",
    inputSchema: { type: "object", properties: { instance_id: { type: "string" } }, required: ["instance_id"] } },
  get_status: { tier: "base", status: "live", price: 10, description: "Status and accrued usage of an instance you own.",
    inputSchema: { type: "object", properties: { instance_id: { type: "string" } }, required: ["instance_id"] } },
  list_tiers: { tier: "base", status: "live", price: 0, description: "List the tiers and the tools each tier may call. Settlement tools: available M3.",
    inputSchema: { type: "object", properties: {} } },
  // Settlement — both tiers (4); two ship DARK in M2 per amendment A3
  create_escrow: { tier: "base", status: "dark", price: 100, description: "[Available M3] Create an escrow for an engagement. Registered in M2; every call is refused and recorded until the M3 settlement substrate lands.",
    inputSchema: { type: "object", properties: { engagement: { type: "string" }, amount: { type: "number" }, rail: { type: "string" } }, required: ["engagement", "amount"] } },
  release_milestone: { tier: "base", status: "dark", price: 100, description: "[Available M3] Release an escrow milestone. Registered in M2; every call is refused and recorded until the M3 settlement substrate lands.",
    inputSchema: { type: "object", properties: { escrow: { type: "string" }, milestone: { type: "string" } }, required: ["escrow", "milestone"] } },
  query_balance: { tier: "base", status: "live", price: 10, description: "Query a wallet's balance. (M2: LOCAL MOCK ledger.)",
    inputSchema: { type: "object", properties: { wallet: { type: "string" } }, required: ["wallet"] } },
  pay_via_x402: { tier: "base", status: "live", price: 0, priceFromAmount: true, description: "Make an x402-metered payment. The amount counts against the principal's limits. (M2: recorded in the LOCAL MOCK ledger — no funds move.)",
    inputSchema: { type: "object", properties: { amount: { type: "number" }, currency: { type: "string", default: "USDC" } }, required: ["amount"] } },
  // Vertical — Markets tier only (9), all landing in M3
  sealed_bid_assignment: { tier: "markets", status: "dark", price: 100, description: "[Available M3] Sealed-bid assignment via Arcium MPC (Markets tier).", inputSchema: { type: "object", properties: {} } },
  open_position: { tier: "markets", status: "dark", price: 100, description: "[Available M3] Open a TradeLayer position (Markets tier).", inputSchema: { type: "object", properties: {} } },
  close_position: { tier: "markets", status: "dark", price: 100, description: "[Available M3] Close a TradeLayer position (Markets tier).", inputSchema: { type: "object", properties: {} } },
  sign_attestation: { tier: "markets", status: "dark", price: 100, description: "[Available M3] Sign a SigLayer attestation (Markets tier).", inputSchema: { type: "object", properties: {} } },
  open_dispute: { tier: "markets", status: "dark", price: 100, description: "[Available M3] Open a SigLayer dispute (Markets tier).", inputSchema: { type: "object", properties: {} } },
  publish_redacted: { tier: "markets", status: "dark", price: 100, description: "[Available M3] Publish a redacted engagement record via the publication layer (Markets tier).", inputSchema: { type: "object", properties: {} } },
  submit_assessment: { tier: "markets", status: "live", price: 100, description: "Submit a Talent assessment role configuration to the P2 system of record (Markets tier; LIVE — activated under amendment S2 by the first outcome published under the two gates). The record is created UNGATED: Gate 1 (employer intent) and Gate 2 (approver of record) are human signatures in the console; no tool call can satisfy them.",
    inputSchema: { type: "object", properties: { role_config: { type: "object", description: "employerRef, vertical (HOSPITALITY | CRE_UNDERWRITING), title, seniority, market, skills[], pairs[{role, realm}] keyed to the Role × Realm taxonomy" } }, required: ["role_config"] } },
  score_assessment: { tier: "markets", status: "live", price: 100, description: "Read the scored Talent assessment record for one talent DID (Markets tier; LIVE under amendment S2). Refuses with gates_not_passed unless the assessment's two human gates have passed.",
    inputSchema: { type: "object", properties: { assessment_id: { type: "string" }, talent_did: { type: "string" } }, required: ["assessment_id", "talent_did"] } },
  publish_assessment_outcome: { tier: "markets", status: "live", price: 100, description: "Publish a redacted Talent assessment outcome — publish_redacted wired to the assessment engagement (Markets tier; LIVE under amendment S2). Refuses unless both gates passed and the cohort meets the minimum anonymity set. The artifact carries no name, no email, no company name — ever.",
    inputSchema: { type: "object", properties: { assessment_id: { type: "string" }, run_id: { type: "string" } }, required: ["assessment_id"] } },
};

export const BASE_TOOLS = Object.entries(CATALOG).filter(([, t]) => t.tier === "base").map(([n]) => n);
export const MOCK_START_BALANCE = 1_000_000; // micro-USDC, LOCAL MOCK ledger

export function priceOf(name, args = {}) {
  const t = CATALOG[name];
  if (!t) return 0;
  if (t.priceFromAmount) return Math.max(0, Math.floor(Number(args.amount) || 0));
  return t.price;
}

// Handlers for the LIVE tools (7 base + the 3 Talent tools,
// activated under amendment S2). A handler returns either
// { result } or { refusal: { reason, message } } (ownership failures are
// refusals and are chronicled as such by the dispatcher).
export function makeHandlers({ store, provisioner, chronicle, talent }) {
  const own = (session, instance_id) => {
    const inst = store.getInstance(instance_id);
    if (!inst) return { refusal: { reason: "not_found", message: `no such instance: ${instance_id}` } };
    if (inst.owner !== session.wallet) return { refusal: { reason: "not_owner", message: "instance belongs to a different principal" } };
    return { inst };
  };

  return {
    async list_tiers() {
      const toolsFor = (tier) => Object.entries(CATALOG)
        .filter(([, t]) => t.tier === "base" || (tier === "markets" && t.tier === "markets"))
        .map(([name, t]) => ({ name, status: t.status }));
      return { result: {
        tiers: [
          { id: "instance", ...TIERS.instance, tools: toolsFor("instance") },
          { id: "markets", ...TIERS.markets, tools: toolsFor("markets") },
        ],
        note: "Settlement tools (create_escrow, release_milestone): available M3. Talent vertical tools (submit_assessment, score_assessment, publish_assessment_outcome): LIVE — activated under amendment S2 by the first P2 outcome published under the two human gates; they execute against the P2 system of record and inherit its gates. Other vertical tools: available M3. Provisioning in M2 runs on a LOCAL MOCK — NEAR AI Cloud pending M0-B credits.",
      } };
    },

    async provision_instance(session, args) {
      const size = args?.spec?.size || "KVM1";
      const inst = await provisioner.provision({ owner: session.wallet, tier: args.tier, size });
      chronicle.append("instance.provisioned", { principal: session.wallet, instance: inst.id, detail: { tier: inst.tier, size: inst.size } });
      return { result: { instance_id: inst.id, state: inst.state, tier: inst.tier, size: inst.size, provider: inst.provider } };
    },

    async get_status(session, args) {
      const { inst, refusal } = own(session, args?.instance_id);
      if (refusal) return { refusal };
      return { result: provisioner.status(inst) };
    },

    async get_credentials(session, args) {
      const { inst, refusal } = own(session, args?.instance_id);
      if (refusal) return { refusal };
      if (inst.state !== "active") return { refusal: { reason: "instance_not_active", message: `instance is ${inst.state}` } };
      return { result: provisioner.credentials(inst) };
    },

    async terminate_instance(session, args) {
      const { inst, refusal } = own(session, args?.instance_id);
      if (refusal) return { refusal };
      if (inst.state === "terminated") return { refusal: { reason: "already_terminated", message: "instance is already terminated" } };
      const out = provisioner.terminate(inst);
      chronicle.append("instance.terminated", { principal: session.wallet, instance: inst.id, detail: { finalUsage: out.finalUsage } });
      return { result: out };
    },

    async query_balance(session, args) {
      if (args?.wallet !== session.wallet) return { refusal: { reason: "not_owner", message: "a principal may query only its own wallet balance" } };
      const spent = chronicle.paymentsTotal(session.wallet);
      return { result: { wallet: session.wallet, balance: MOCK_START_BALANCE - spent, currency: "USDC", unit: "micro-USDC", source: "LOCAL MOCK ledger — no real funds" } };
    },

    async pay_via_x402(session, args) {
      const amount = Math.floor(Number(args?.amount) || 0);
      if (amount <= 0) return { refusal: { reason: "bad_amount", message: "amount must be a positive number of micro-USDC" } };
      const currency = args?.currency || "USDC";
      const payment = {
        payment_id: `pay_${chronicle.seq + 1}`,
        amount, currency, unit: "micro-USDC",
        rail: "USDC on Solana (LOCAL MOCK — recorded only, no funds move)",
        status: "recorded",
      };
      return { result: payment, detail: { amount, currency } };
    },

    // --- Talent vertical (P2, Scope 2) — LIVE under amendment S2.
    // The handlers are thin calls into the P2 system of record;
    // the two human gates live there and cannot be satisfied here.
    async submit_assessment(session, args) {
      if (!talent) return { refusal: { reason: "talent_api_unreachable", message: "no Talent client configured" } };
      const out = await talent.submitAssessment(args?.role_config || {});
      if (!out.refusal) chronicle.append("talent.assessment_submitted", { principal: session.wallet, detail: { assessment: out.result.assessment?.id } });
      return out;
    },

    async score_assessment(session, args) {
      if (!talent) return { refusal: { reason: "talent_api_unreachable", message: "no Talent client configured" } };
      return talent.scoreAssessment({ assessment_id: args?.assessment_id, talent_did: args?.talent_did });
    },

    async publish_assessment_outcome(session, args) {
      if (!talent) return { refusal: { reason: "talent_api_unreachable", message: "no Talent client configured" } };
      const out = await talent.publishOutcome({ assessment_id: args?.assessment_id, run_id: args?.run_id });
      if (!out.refusal) chronicle.append("talent.outcome_published", { principal: session.wallet, detail: { cid: out.result.cid } });
      return out;
    },
  };
}
