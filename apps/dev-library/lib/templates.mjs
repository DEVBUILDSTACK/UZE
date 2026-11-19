// The curated assessment template library (P2 §2.2 — the template
// moat). Generation FILLS SLOTS in these curated templates; it does
// not author instruments. Four stages, in order: role-signal
// extraction → template selection → slot-filling → calibration. The
// first three live here as pure functions (no store, no identity
// data — this module is safe to import anywhere); the calibration
// record rides on the template and lands on the generated instrument.
//
// Sprint 1 seeds the two verticals of record: HOSPITALITY and
// CRE_UNDERWRITING (the H&I CRE financial-underwriting worked example
// of the attestation addendum, DealFi screens included). Further
// verticals are Sprint 2 (P2-10) — each arrives as curated data here,
// with its own calibration record and per-vertical approver.
//
// Calibration: every seed template carries calibration: null. The
// reference populations are built in Sprint 2 (P2-11); until one
// exists, generated instruments carry the explicit gap acknowledgment
// — no surface may call an assessment "valid" without a named
// population and metric (P2 §2.4).

export const VERTICALS = ["HOSPITALITY", "CRE_UNDERWRITING"];

export const TEMPLATES = [
  {
    id: "tpl_hospitality_front_desk_v1",
    vertical: "HOSPITALITY",
    title: "Guest Operations — Front Desk & Service Recovery",
    version: 1,
    roleSignals: {
      roles: ["TALENT_HR_SPECIALIST", "OTHER_ROLE"],
      realms: ["OTHER_REALM"],
      keywords: ["guest", "front desk", "front-desk", "check-in", "check-out", "reservations", "concierge", "service recovery", "pms"],
    },
    dimensions: [
      { key: "guest_communication", label: "Guest communication", weight: 30,
        prompt: "As a {seniority} {title} in {market}, handle a guest who is disputing a charge at check-out: acknowledge, explain the folio, and offer the recovery path. Focus skills: {skills}.",
        evidence: "Clarity, tone, and ownership of the interaction, judged against the property's service standard." },
      { key: "service_recovery_judgment", label: "Service-recovery judgment", weight: 30,
        prompt: "A service failure has reached the guest (room not ready at the promised time). Decide the recovery: what is offered, what is comped, what is escalated — and why. Focus skills: {skills}.",
        evidence: "Judgment proportional to the failure; the recovery protects the guest relationship without giving away the rate." },
      { key: "pms_workflow", label: "PMS workflow accuracy", weight: 20,
        prompt: "Walk the exact property-management-system workflow for a same-day reservation change with a rate override, end to end, naming each check. Focus skills: {skills}.",
        evidence: "Sequence is complete and in order; overrides are flagged for audit, never buried." },
      { key: "rate_integrity_upsell", label: "Rate integrity & upsell", weight: 20,
        prompt: "Offer the paid upgrade at check-in without discounting below the rate floor. Script the offer and the response to a guest who counters. Focus skills: {skills}.",
        evidence: "The offer is made, the floor holds, and the guest hears value rather than pressure." },
    ],
    screens: [],
    calibration: null,
  },
  {
    id: "tpl_hospitality_supervision_v1",
    vertical: "HOSPITALITY",
    title: "Hospitality Supervision — Shift Leadership & Team Coordination",
    version: 1,
    roleSignals: {
      roles: ["TALENT_HR_SPECIALIST", "OTHER_ROLE"],
      realms: ["OTHER_REALM"],
      keywords: ["supervisor", "supervision", "shift", "housekeeping", "scheduling", "team lead", "duty manager"],
    },
    dimensions: [
      { key: "shift_handover", label: "Shift handover discipline", weight: 25,
        prompt: "Write the handover note for the incoming shift of a {seniority} {title} in {market}: open guest issues, room status exceptions, and the one item that must not be missed. Focus skills: {skills}.",
        evidence: "Complete, prioritized, and unambiguous — the incoming shift can act without a follow-up call." },
      { key: "team_coordination", label: "Team coordination under load", weight: 25,
        prompt: "Two call-outs on a full-occupancy day. Re-plan the team's assignments and state what slips, what is covered, and what the guest never sees. Focus skills: {skills}.",
        evidence: "Coverage protects the guest-facing line first; the plan is realistic about the hours available." },
      { key: "quality_inspection", label: "Quality inspection", weight: 25,
        prompt: "Inspect a turned room against the brand checklist and record the defects you would bounce back, in the order you would check them. Focus skills: {skills}.",
        evidence: "Defects are found in checklist order and described so housekeeping can act on them directly." },
      { key: "incident_judgment", label: "Incident judgment", weight: 25,
        prompt: "A guest reports a safety concern in a public area. Sequence your first ten minutes: secure, document, escalate, communicate. Focus skills: {skills}.",
        evidence: "Safety before property, documentation before discussion, escalation at the right moment." },
    ],
    screens: [],
    calibration: null,
  },
  {
    id: "tpl_cre_underwriting_analyst_v1",
    vertical: "CRE_UNDERWRITING",
    title: "H&I CRE Financial Underwriting — Statement Analysis, Valuation & DealFi Screens",
    version: 1,
    roleSignals: {
      roles: ["DATA_SCIENTIST", "OTHER_ROLE", "FULL_STACK_DEV"],
      realms: ["OTHER_REALM"],
      keywords: ["underwriting", "underwriter", "noi", "valuation", "financial statement", "acquisition", "ebitda", "proforma", "private equity", "cre", "hospitality"],
    },
    dimensions: [
      { key: "financial_statement_analysis", label: "Financial statement analysis", weight: 30,
        prompt: "Given the T-12 of a hospitality asset, analyze the financial statements for a {seniority} {title} engagement in {market}: separate Revenue, Operating Expenses, Taxes, Insurance(s), Interest, Miscellaneous Net, and Profit into the seven buckets of record — Operating Expenses never absorb Taxes, Insurance, or Interest. Focus skills: {skills}.",
        evidence: "Every line lands in exactly one bucket; NOI is unlevered (pre-interest) and a separate post-interest levered cash flow is shown." },
      { key: "valuation", label: "Corporate & asset valuation", weight: 25,
        prompt: "Build the valuation view for the asset: cap-rate on in-place NOI, the adjustment set you would defend, and the sensitivity that moves the answer most. Focus skills: {skills}.",
        evidence: "The valuation ties to the statement analysis; assumptions are named, not smuggled." },
      { key: "dealfi_acquisition_screens", label: "DealFi-style acquisition screens", weight: 25,
        prompt: "Run the DealFi acquisition screens of record against the candidate deal and report pass/fail per screen with the figure behind each. Focus skills: {skills}.",
        evidence: "Each screen is answered with its own figure; a failed screen is reported as failed, not averaged away." },
      { key: "market_comp_judgment", label: "Market & comp judgment", weight: 20,
        prompt: "Judge the asset against same-micro-region benchmarks only: which comp set, which lines deviate, and what the deviation is worth per year. Focus skills: {skills}.",
        evidence: "Comps are same-micro-region and tier-matched; deviations are dollar-ranked with their evidence." },
    ],
    // The DealFi screens of record (attestation addendum §1).
    screens: [
      { key: "annual_revenue_threshold", label: "Annual revenues over the deal threshold" },
      { key: "quarterly_ebitda", label: "Accumulated EBITDA for a quarter" },
      { key: "run_rate_per_annum", label: "Run-rate per annum (startup basis)" },
      { key: "property_noi_vs_comps", label: "Single property's NOI against market comps" },
    ],
    calibration: null,
  },
  {
    id: "tpl_cre_acquisition_screening_v1",
    vertical: "CRE_UNDERWRITING",
    title: "CRE Acquisition Screening — DealFi Screen Battery",
    version: 1,
    roleSignals: {
      roles: ["DATA_SCIENTIST", "OTHER_ROLE"],
      realms: ["OTHER_REALM"],
      keywords: ["screening", "screen", "dealfi", "acquisition screen", "pipeline", "sourcing"],
    },
    dimensions: [
      { key: "screen_application", label: "Screen application", weight: 40,
        prompt: "Apply the full DealFi screen battery to three candidate deals for a {seniority} {title} in {market} and rank the survivors with the failing figure named for each rejection. Focus skills: {skills}.",
        evidence: "Screens are applied uniformly; rejections name the figure that failed." },
      { key: "noi_analysis", label: "NOI analysis", weight: 30,
        prompt: "For the surviving deal, derive NOI from the statement lines and reconcile it against the seller's figure, line by line. Focus skills: {skills}.",
        evidence: "The reconciliation finds the seller's absorbed lines (Taxes, Insurance, Interest) and restates NOI unlevered." },
      { key: "comp_selection", label: "Comp selection", weight: 30,
        prompt: "Select the comp set for the surviving deal's micro-region and defend each inclusion and exclusion. Focus skills: {skills}.",
        evidence: "Same micro-region, tier-matched; no comp is included for convenience." },
    ],
    screens: [
      { key: "annual_revenue_threshold", label: "Annual revenues over the deal threshold" },
      { key: "quarterly_ebitda", label: "Accumulated EBITDA for a quarter" },
      { key: "run_rate_per_annum", label: "Run-rate per annum (startup basis)" },
      { key: "property_noi_vs_comps", label: "Single property's NOI against market comps" },
    ],
    calibration: null,
  },
];

// Stage 1 — role-signal extraction: the configured role reduced to
// the signals that select and parameterize an instrument.
export function extractSignals(roleConfig) {
  const text = [roleConfig.title, roleConfig.seniority, ...(roleConfig.skills || []),
    ...(roleConfig.judgmentDimensions || [])].join(" ").toLowerCase();
  return {
    vertical: roleConfig.vertical,
    roles: (roleConfig.pairs || []).map(p => p.role),
    realms: (roleConfig.pairs || []).map(p => p.realm),
    keywords: text.split(/[^a-z0-9-]+/).filter(w => w.length > 2),
    seniority: roleConfig.seniority || "",
    market: roleConfig.market || "",
  };
}

// Stage 2 — template selection: vertical is a hard filter (a
// hospitality role is assessed as hospitality); within the vertical,
// Role × Realm overlap and keyword hits score the candidates.
export function selectTemplate(signals) {
  const pool = TEMPLATES.filter(t => t.vertical === signals.vertical);
  if (!pool.length) return null;
  const scored = pool.map(t => {
    const roleHits = t.roleSignals.roles.filter(r => signals.roles.includes(r)).length;
    const realmHits = t.roleSignals.realms.filter(r => signals.realms.includes(r)).length;
    const kwHits = t.roleSignals.keywords.filter(k => signals.keywords.some(w => w.includes(k) || k.includes(w))).length;
    return { template: t, score: roleHits * 3 + realmHits * 2 + kwHits, roleHits, realmHits, kwHits };
  }).sort((a, b) => b.score - a.score);
  return scored[0];
}

// Stage 3 — slot-filling: the template's dimension prompts are
// parameterized by the configured role. Content per vertical fills
// the slots; the instrument's structure is the template's, unchanged.
export function fillSlots(template, roleConfig) {
  const fill = (s) => String(s || "")
    .replaceAll("{title}", roleConfig.title || "role")
    .replaceAll("{seniority}", roleConfig.seniority || "mid-level")
    .replaceAll("{market}", roleConfig.market || "the market")
    .replaceAll("{skills}", (roleConfig.skills || []).join(", ") || "the configured skills");
  return {
    templateId: template.id,
    templateVersion: template.version,
    title: template.title,
    dimensions: template.dimensions.map(d => ({ ...d, prompt: fill(d.prompt) })),
    screens: (template.screens || []).map(s => ({ ...s })),
  };
}
