// P2 Assessment — the system of record (Scope 2, separated track;
// Sprint 1 per docs/talent/P2-SCOPE-AND-PHASED-SPRINT-v0.1.md, tapped
// by James 2026-11-18 21:26 ET).
//
// The pipeline: role configuration (P2-1) → generation from the
// curated template library (P2-2, lib/templates.mjs) → the TWO human
// gates (P2-3) → runs + the scoring center (P2-4) → fulfillment hooks
// (P2-5: Path A quotes / Path B engagement attachment, reusing
// lib/engagements.mjs) → publication through lib/publisher.mjs
// (P2-6), whose three-store separation this module respects: the
// publisher receives only a redacted candidate built here, and this
// module is the last place identity data exists.
//
// Invariants (v3.1, carried): status is DERIVED from facts, never
// written; every transition emits a chronicle Event; the gates are
// hard gates — no agent action substitutes for a named human's
// signature, on any surface (the MCP tools inherit them unchanged).
import { createHash } from "node:crypto";
import { load, save, chronicle } from "./store.mjs";
import { validatePairs } from "./taxonomy.mjs";
import { VERTICALS, extractSignals, selectTemplate, fillSlots } from "./templates.mjs";
import { findDeveloper } from "./gate.mjs";
import { findEngagement, engagementState, revealed } from "./engagements.mjs";
import { publishOutcome, bandOf } from "./publisher.mjs";

const now = () => new Date().toISOString();
const newId = (p) => `${p}_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
const dayOf = (iso) => String(iso).slice(0, 10);

// Configuration. humanReviewThreshold is a REQUIRED configuration
// value recorded on every run — the number below is a STARTING
// DEFAULT: no filed source states a threshold (the composite
// requires "a stated threshold"; the value is James's to set, per
// vertical if he chooses). minAnonymitySet starts at the filed
// "e.g. 5" (P2 §4). Retake parameters are the policy of record
// (P2 §2.4): one retake per six months, maximum two total.
export const CONFIG_DEFAULTS = {
  humanReviewThreshold: 70, // STARTING DEFAULT — no source states a number
  borderlineBand: 5,
  minAnonymitySet: 5,
  retakeWindowDays: 182,
  retakeMaxTotal: 2,
};
export function assessmentConfig() {
  return { ...CONFIG_DEFAULTS, ...(load("assessments.json").config || {}) };
}

// Path A markup bands of record (P2 §2.5; James 2026-11-18 —
// starting parameters, adjustable per engagement, never silently
// changed). Markets not listed have no band: James sets them per
// market (ruling 5), and the quote engine refuses rather than invent
// one.
export const MARKUP_BANDS = {
  india: { label: "India", min: 17.5, max: 23.5 },
  "singapore-help-desk": { label: "Singapore — help desk", min: 33.75, max: null },
};
const bandKey = (market) => String(market || "").toLowerCase().replace(/[^a-z]+/g, "-").replace(/^-|-$/g, "")
  .replace("singapore-helpdesk", "singapore-help-desk");

// The talent DID: a stable pseudonymous identifier derived from the
// identity of record. The mapping lives only in the identity store
// (developers.json); everywhere downstream — runs, chronicle,
// publication candidates — the DID is what travels.
export function talentDid(email) {
  return "did:uze:talent_" + createHash("sha256").update(String(email).toLowerCase()).digest("hex").slice(0, 24);
}

const db = () => load("assessments.json");
function mutate(fn) { const d = db(); const out = fn(d); save("assessments.json", d); return out; }
export function loadRoleConfigs() { return db().roleConfigs; }
export function findRoleConfig(id) { return db().roleConfigs.find(r => r.id === id) || null; }
export function loadAssessments() { return db().assessments; }
export function findAssessment(id) { return db().assessments.find(a => a.id === id) || null; }
export function loadRuns() { return db().runs; }
export function findRun(id) { return db().runs.find(r => r.id === id) || null; }
const note = (rec, event, fields = {}) => rec.history.push({ at: now(), event, ...fields });

// ---------- P2-1: role configuration (intake) ----------
// The engaging employer submits and configures the role; the record
// lands keyed to Role × Realm pairs (M1's taxonomy is the key space —
// validatePairs is reused, never forked). Work history is a required
// input on the talent side (its attestation layer is Sprint 2, P2-8).
export function createRoleConfig(input = {}) {
  if (!VERTICALS.includes(input.vertical)) throw new Error("invalid vertical: " + (input.vertical ?? "") + " (seeded verticals: " + VERTICALS.join(", ") + ")");
  if (!input.title || !String(input.title).trim()) throw new Error("role title is required");
  if (!input.employerRef || !String(input.employerRef).trim()) throw new Error("employerRef is required (the configuring employer, internal record only — it never reaches the publisher)");
  const pairs = validatePairs(input.pairs || []);
  if (!pairs.length) throw new Error("a role record is keyed to at least one Role × Realm pair");
  const rc = {
    id: newId("role"), employerRef: String(input.employerRef), vertical: input.vertical,
    title: String(input.title), seniority: input.seniority || "", market: input.market || "",
    engagementMode: input.engagementMode || "", budgetBand: input.budgetBand || "",
    skills: Array.isArray(input.skills) ? input.skills.map(String) : [],
    judgmentDimensions: Array.isArray(input.judgmentDimensions) ? input.judgmentDimensions.map(String) : [],
    pairs, workHistoryRequired: input.workHistoryRequired !== false,
    createdAt: now(), createdBy: input.createdBy || "console", history: [],
  };
  note(rc, "role-config-created", { vertical: rc.vertical, pairs: pairs.map(p => `${p.role}×${p.realm}`) });
  mutate(d => { d.roleConfigs.push(rc); });
  chronicle("role-config-created", { id: rc.id, vertical: rc.vertical, pairs: rc.pairs });
  return rc;
}

// ---------- P2-2: generation (template moat) ----------
export function generateAssessment(roleConfigId, { by = "console" } = {}) {
  const rc = findRoleConfig(roleConfigId);
  if (!rc) throw new Error("role config not found: " + roleConfigId);
  const signals = extractSignals(rc);
  const sel = selectTemplate(signals);
  if (!sel) throw new Error(`no template in the curated library for vertical ${rc.vertical} — generation fills curated templates; it does not author instruments`);
  const instrument = fillSlots(sel.template, rc);
  const a = {
    id: newId("asm"), roleConfigId: rc.id, templateId: sel.template.id,
    templateVersion: sel.template.version, signals,
    selection: { score: sel.score, roleHits: sel.roleHits, realmHits: sel.realmHits, kwHits: sel.kwHits },
    instrument, calibration: sel.template.calibration || null,
    instrumentVersion: 1, gate1: null, gate2: null, createdAt: now(), history: [],
  };
  note(a, "assessment-generated", { templateId: a.templateId, by });
  mutate(d => { d.assessments.push(a); });
  chronicle("assessment-generated", { id: a.id, roleConfigId: rc.id, templateId: a.templateId });
  return a;
}

// Rejection at either gate returns the instrument to generation;
// regeneration re-runs selection + slot-filling on the (possibly
// reconfigured) role and clears the gate facts — the history keeps
// every decision.
export function regenerateAssessment(id, { by = "console" } = {}) {
  const a = findAssessment(id);
  if (!a) throw new Error("assessment not found: " + id);
  const rc = findRoleConfig(a.roleConfigId);
  const signals = extractSignals(rc);
  const sel = selectTemplate(signals);
  if (!sel) throw new Error(`no template in the curated library for vertical ${rc.vertical}`);
  const updated = mutate(d => {
    const x = d.assessments.find(v => v.id === id);
    x.instrument = fillSlots(sel.template, rc);
    x.templateId = sel.template.id; x.templateVersion = sel.template.version;
    x.calibration = sel.template.calibration || null;
    x.instrumentVersion += 1; x.gate1 = null; x.gate2 = null;
    note(x, "assessment-regenerated", { by, instrumentVersion: x.instrumentVersion });
    return x;
  });
  chronicle("assessment-regenerated", { id, instrumentVersion: updated.instrumentVersion });
  return updated;
}

// Derived state (never written): RETURNED if the latest gate
// decision was a return; APPROVED only when both gates stand signed.
export function assessmentState(a) {
  if (a.gate2?.decision === "signed" && a.gate1?.decision === "signed") return "APPROVED";
  if (a.gate1?.decision === "returned" || a.gate2?.decision === "returned") return "RETURNED";
  if (a.gate1?.decision === "signed") return "GATE1_SIGNED";
  return "GENERATED";
}
export function assessmentView(a) { return { ...a, state: assessmentState(a) }; }

// ---------- P2-3: the two gates (console-only, human-signed) ----------
function requireHuman(signer, gateLabel) {
  if (!signer || !signer.name) throw new Error(`${gateLabel}: a named signer is required`);
  if (String(signer.kind || "").toLowerCase() !== "human") {
    throw new Error(`${gateLabel} is human-signed: an agent cannot sign it, on any surface`);
  }
}
export function signGate1(id, { signer, noteText = "" } = {}) {
  requireHuman(signer, "Gate 1");
  const a = mutate(d => {
    const x = d.assessments.find(v => v.id === id);
    if (!x) throw new Error("assessment not found: " + id);
    const st = assessmentState(x);
    if (st === "GATE1_SIGNED" || st === "APPROVED") throw new Error("Gate 1 already signed");
    x.gate1 = { decision: "signed", by: signer.name, kind: "HUMAN", at: now() };
    note(x, "assessment-gate1-signed", { by: signer.name, note: noteText });
    return x;
  });
  chronicle("assessment-gate1-signed", { id, by: signer.name });
  return a;
}
export function returnGate1(id, { signer, noteText = "" } = {}) {
  requireHuman(signer, "Gate 1");
  const a = mutate(d => {
    const x = d.assessments.find(v => v.id === id);
    if (!x) throw new Error("assessment not found: " + id);
    x.gate1 = { decision: "returned", by: signer.name, kind: "HUMAN", at: now() };
    x.gate2 = null; // Gate 2 cannot stand on a returned Gate 1
    note(x, "assessment-gate1-returned", { by: signer.name, note: noteText });
    return x;
  });
  chronicle("assessment-gate1-returned", { id, by: signer.name });
  return a;
}
// The per-vertical approver registry. Ruling 6 (the approver of
// record per vertical) is James's and unsettled — the registry ships
// EMPTY of named rulings. setApprover is the mechanism that records
// the ruling when James makes it; until then Gate 2 refuses, with
// exactly one exception: the master acting explicitly in a
// test/proof context (viaMasterTest), recorded as the basis.
export function setApprover(vertical, names) {
  if (!VERTICALS.includes(vertical)) throw new Error("invalid vertical: " + vertical);
  if (!Array.isArray(names) || names.some(n => !String(n).trim())) throw new Error("approvers must be an array of names");
  mutate(d => { d.approvers = d.approvers || {}; d.approvers[vertical] = names.map(String); });
  chronicle("assessment-approver-set", { vertical, names });
  return loadApprovers();
}
export function loadApprovers() { return db().approvers || {}; }

export function signGate2(id, { signer, viaMasterTest = false, noteText = "" } = {}) {
  requireHuman(signer, "Gate 2");
  const a = findAssessment(id);
  if (!a) throw new Error("assessment not found: " + id);
  if (a.gate1?.decision !== "signed") throw new Error("Gate 2 cannot precede Gate 1: employer intent is not confirmed");
  if (a.gate2?.decision === "signed") throw new Error("Gate 2 already signed");
  const rc = findRoleConfig(a.roleConfigId);
  const registry = (loadApprovers()[rc.vertical] || []).filter(Boolean);
  let basis;
  if (!registry.length) {
    if (!viaMasterTest) throw new Error(`Gate 2 refused: no approver of record is configured for vertical ${rc.vertical} (ruling 6 is James's); only the master acting explicitly in a test/proof context may sign`);
    basis = "master-test";
  } else {
    if (!registry.includes(signer.name)) throw new Error(`Gate 2 refused: ${signer.name} is not the approver of record for ${rc.vertical}`);
    basis = "registry";
  }
  const updated = mutate(d => {
    const x = d.assessments.find(v => v.id === id);
    x.gate2 = { decision: "signed", by: signer.name, kind: "HUMAN", at: now(), basis };
    note(x, "assessment-gate2-signed", { by: signer.name, basis, note: noteText });
    return x;
  });
  chronicle("assessment-gate2-signed", { id, by: signer.name, basis });
  return updated;
}
export function returnGate2(id, { signer, noteText = "" } = {}) {
  requireHuman(signer, "Gate 2");
  const a = mutate(d => {
    const x = d.assessments.find(v => v.id === id);
    if (!x) throw new Error("assessment not found: " + id);
    if (x.gate1?.decision !== "signed") throw new Error("Gate 2 cannot precede Gate 1: employer intent is not confirmed");
    x.gate2 = { decision: "returned", by: signer.name, kind: "HUMAN", at: now() };
    note(x, "assessment-gate2-returned", { by: signer.name, note: noteText });
    return x;
  });
  chronicle("assessment-gate2-returned", { id, by: signer.name });
  return a;
}

// ---------- P2-4: runs + the scoring center ----------
// The scoring engine (v1): a deterministic weighted grade over the
// instrument's dimensions. In production an AI grader produces the
// per-dimension scores from the candidate's evidence; the run
// surface records the grader's output, and THIS function is the
// scoring center it lands in — the grade, the human-review flag at
// the stated threshold, and the validity form are computed here and
// nowhere else.
export function gradeResponses(instrument, responses, config) {
  let total = 0, weight = 0;
  const perDimension = instrument.dimensions.map(dim => {
    const r = responses?.[dim.key];
    if (!r || !Number.isFinite(Number(r.score))) throw new Error(`run responses must carry a numeric score for dimension ${dim.key}`);
    const score = Number(r.score);
    if (score < 0 || score > 100) throw new Error(`dimension ${dim.key} score out of range: ${score}`);
    total += score * dim.weight; weight += dim.weight;
    return { key: dim.key, score, evidence: String(r.evidence || "") };
  });
  const score = Math.round((total / weight) * 100) / 100;
  const threshold = config.humanReviewThreshold;
  const humanReviewFlag = (score - threshold) < config.borderlineBand || perDimension.some(d => d.score < 40);
  return { score, perDimension, humanReviewFlag };
}

export function recordRun({ assessmentId, talentEmail, responses, takenAt = null }) {
  const a = findAssessment(assessmentId);
  if (!a) throw new Error("assessment not found: " + assessmentId);
  if (assessmentState(a) !== "APPROVED") throw new Error("nothing runs before both gates pass, in order (Gate 1 employer intent, Gate 2 approver validity)");
  const dev = findDeveloper(talentEmail);
  if (!dev) throw new Error("talent not found on the Developer List: " + talentEmail);
  if (dev.stage === "revoked") throw new Error("a revoked record cannot be assessed");
  const rc = findRoleConfig(a.roleConfigId);
  const config = assessmentConfig();
  const did = talentDid(dev.email);
  const at = takenAt ? new Date(takenAt).toISOString() : now();
  // Retake policy of record: one retake per six months, maximum two
  // total, logged — refusals are chronicled before they are thrown.
  const prior = loadRuns().filter(r => r.assessmentId === assessmentId && r.talentDid === did)
    .sort((x, y) => x.takenAt.localeCompare(y.takenAt));
  if (prior.length) {
    const retakes = prior.length; // the run after the first is retake #prior.length
    const lastAt = new Date(prior[prior.length - 1].takenAt).getTime();
    const windowMs = config.retakeWindowDays * 86400000;
    if (retakes > config.retakeMaxTotal) {
      chronicle("assessment-retake-refused", { assessmentId, talentDid: did, reason: "maximum two retakes total" });
      throw new Error("retake refused: maximum two retakes total (policy of record, logged)");
    }
    if (new Date(at).getTime() - lastAt < windowMs) {
      chronicle("assessment-retake-refused", { assessmentId, talentDid: did, reason: "one retake per six months" });
      throw new Error("retake refused: one retake per six months (policy of record, logged)");
    }
  }
  const graded = gradeResponses(a.instrument, responses, config);
  const run = {
    id: newId("run"), assessmentId, roleConfigId: rc.id,
    talentEmail: dev.email, talentDid: did,
    pair: rc.pairs[0], // the result is keyed to the PRIMARY Role × Realm pair
    responses: graded.perDimension, score: graded.score, gradeBand: bandOf(graded.score),
    humanReviewFlag: graded.humanReviewFlag, reviewThreshold: config.humanReviewThreshold,
    validity: a.calibration
      ? { form: "calibrated", population: a.calibration.population, metric: a.calibration.metric }
      : { form: "gap", acknowledgment: "no calibration population exists for this instrument yet — the reference populations are built in Sprint 2 (P2-11); this result is not claimed as calibrated" },
    takenAt: at, scoredAt: now(), retakeOf: prior.length ? prior[prior.length - 1].id : null,
    engagementId: null, quoteId: null, publicationId: null, history: [],
  };
  note(run, "assessment-run-scored", { score: run.score, humanReviewFlag: run.humanReviewFlag });
  mutate(d => { d.runs.push(run); });
  chronicle("assessment-run-scored", { id: run.id, assessmentId, talentDid: did, score: run.score, humanReviewFlag: run.humanReviewFlag });
  return run;
}

// The score read for a (talent, assessment) — the score_assessment
// seam. Gates are checked first: a record that has not passed both
// gates has no score to read, whatever surface asks.
export function scoreByTalent({ assessmentId, talentDid: did }) {
  const a = findAssessment(assessmentId);
  if (!a) throw new Error("assessment not found: " + assessmentId);
  if (assessmentState(a) !== "APPROVED") throw new Error("gates not passed: a score exists only for an assessment that passed Gate 1 and Gate 2");
  const runs = loadRuns().filter(r => r.assessmentId === assessmentId && r.talentDid === did)
    .sort((x, y) => x.takenAt.localeCompare(y.takenAt));
  if (!runs.length) throw new Error("no run recorded for this talent on this assessment");
  const r = runs[runs.length - 1];
  return { runId: r.id, assessmentId, talentDid: did, score: r.score, gradeBand: r.gradeBand,
    humanReviewFlag: r.humanReviewFlag, reviewThreshold: r.reviewThreshold, validity: r.validity, pair: r.pair };
}

// ---------- P2-5: fulfillment hooks (Path A / Path B) ----------
// Path B: the assessed outcome attaches to an M1 engagement (the
// machinery is lib/engagements.mjs — reused, never duplicated).
export function attachToEngagement(runId, engagementId) {
  const e = findEngagement(engagementId);
  if (!e) throw new Error("engagement not found: " + engagementId);
  const run = mutate(d => {
    const r = d.runs.find(v => v.id === runId);
    if (!r) throw new Error("run not found: " + runId);
    r.engagementId = engagementId;
    note(r, "assessment-attached-engagement", { engagementId });
    return r;
  });
  chronicle("assessment-attached-engagement", { runId, engagementId, talentDid: run.talentDid });
  return run;
}

// Disclosure (P2 §2.6, stated as design): the client sees the
// outcome under an engagement-scoped pseudonym BEFORE signing; the
// talent's identity is revealed at engagement + deposit — the M1
// machinery's reveal point, reused here unchanged.
export function engagementPseudonym(engagementId, did) {
  return "talent-" + createHash("sha256").update(engagementId + "|" + did).digest("hex").slice(0, 10);
}
export function outcomeForEngagement(engagementId) {
  const e = findEngagement(engagementId);
  if (!e) throw new Error("engagement not found: " + engagementId);
  const isRevealed = revealed(e);
  return loadRuns().filter(r => r.engagementId === engagementId).map(r => {
    const out = { runId: r.id, pseudonym: engagementPseudonym(engagementId, r.talentDid),
      pair: r.pair, gradeBand: r.gradeBand, humanReviewFlag: r.humanReviewFlag,
      validity: r.validity, state: engagementState(e), revealed: isRevealed, talent: null };
    if (isRevealed) {
      const dev = findDeveloper(r.talentEmail);
      if (dev) out.talent = { name: dev.name, email: dev.email };
    }
    return out;
  });
}

// P2-6 (filed numbering): the rate/markup engine. Path A quote
// composition from the bands of record; the composed terms LOCK
// onto the record before work begins.
export function quotePathA(runId, { market, laborRate, markupPct = null } = {}) {
  const run = findRun(runId);
  if (!run) throw new Error("run not found: " + runId);
  const band = MARKUP_BANDS[bandKey(market)];
  if (!band) throw new Error(`no markup band of record for market '${market}' — other markets are set by James per market (ruling 5); the engine refuses rather than invent one`);
  if (!Number.isFinite(Number(laborRate)) || Number(laborRate) <= 0) throw new Error("a positive laborRate is required");
  const pct = markupPct === null || markupPct === undefined ? band.min : Number(markupPct);
  if (!Number.isFinite(pct) || pct < band.min || (band.max !== null && pct > band.max)) {
    throw new Error(`markup ${pct}% is outside the band of record for ${band.label} (${band.min}%${band.max ? "–" + band.max + "%" : " and up"})`);
  }
  const quote = { id: newId("quote"), runId, path: "A", market: band.label,
    laborRate: Number(laborRate), markupPct: pct,
    billedRate: Math.round(Number(laborRate) * (1 + pct / 100) * 100) / 100,
    lockedAt: now() };
  mutate(d => {
    d.quotes = d.quotes || []; d.quotes.push(quote);
    const r = d.runs.find(v => v.id === runId);
    r.quoteId = quote.id; note(r, "assessment-quote-locked", { quoteId: quote.id, market: quote.market, markupPct: pct });
  });
  chronicle("assessment-quote-locked", { runId, quoteId: quote.id, market: quote.market, markupPct: pct, billedRate: quote.billedRate });
  return quote;
}

// ---------- P2-6 (assignment numbering): publication ----------
// Builds the redacted candidate and hands it to the publisher. This
// function is the boundary: employerRef, talent name, and talent
// email exist on this side of it and are never copied across.
export async function publishRunOutcome(runId) {
  const run = findRun(runId);
  if (!run) throw new Error("run not found: " + runId);
  const a = findAssessment(run.assessmentId);
  const rc = findRoleConfig(run.roleConfigId);
  const config = assessmentConfig();
  const scope = run.engagementId || run.assessmentId;
  const pseudonym = "talent-" + createHash("sha256").update(scope + "|" + run.talentDid).digest("hex").slice(0, 10);
  const cohortKey = `${rc.vertical}|${run.pair.role}×${run.pair.realm}`;
  const allRuns = loadRuns();
  const byId = Object.fromEntries(loadAssessments().map(x => [x.id, x]));
  const cohortSize = allRuns.filter(r => {
    const ra = byId[r.assessmentId];
    if (!ra) return false;
    const rrc = findRoleConfig(ra.roleConfigId);
    return rrc && rrc.vertical === rc.vertical && r.pair.role === run.pair.role && r.pair.realm === run.pair.realm;
  }).length;
  const terms = { path: run.engagementId ? "B" : (run.quoteId ? "A" : null) };
  if (run.quoteId) {
    const q = (db().quotes || []).find(v => v.id === run.quoteId);
    if (q) { terms.markupPct = q.markupPct; terms.market = q.market; }
  }
  if (run.engagementId) {
    const e = findEngagement(run.engagementId);
    if (e && e.commercialModel === "PLACEMENT") terms.feeMonths = e.feeMonths;
  }
  const progress = [{ day: dayOf(run.takenAt), event: "assessment-scored" }];
  if (run.engagementId) {
    const e = findEngagement(run.engagementId);
    if (e) for (const h of e.history || []) progress.push({ day: dayOf(h.at), event: h.event });
  }
  const candidate = {
    runId: run.id, pseudonym, cohortKey, cohortSize,
    vertical: rc.vertical, role: run.pair.role, realm: run.pair.realm,
    gradeBand: run.gradeBand, validity: run.validity,
    market: rc.market || "", day: dayOf(run.takenAt), terms, progress,
  };
  const pub = await publishOutcome(candidate, { minAnonymitySet: config.minAnonymitySet });
  mutate(d => {
    const r = d.runs.find(v => v.id === runId);
    r.publicationId = pub.id; note(r, "assessment-outcome-published", { publicationId: pub.id, cid: pub.cid });
  });
  chronicle("assessment-outcome-published", { runId, publicationId: pub.id, cid: pub.cid, pseudonym });
  return pub;
}

// The publish seam for an assessment (the publish_assessment_outcome
// tool calls this): publishes the latest scored run's outcome.
// Gates first — an outcome exists to publish only under both gates.
export async function publishOutcomeForAssessment(assessmentId, { runId = null } = {}) {
  const a = findAssessment(assessmentId);
  if (!a) throw new Error("assessment not found: " + assessmentId);
  if (assessmentState(a) !== "APPROVED") throw new Error("gates not passed: an outcome is published only for an assessment that passed Gate 1 and Gate 2");
  const runs = loadRuns().filter(r => r.assessmentId === assessmentId && (r.score !== null))
    .sort((x, y) => x.takenAt.localeCompare(y.takenAt));
  const run = runId ? runs.find(r => r.id === runId) : runs[runs.length - 1];
  if (!run) throw new Error("no scored run to publish for this assessment");
  return publishRunOutcome(run.id);
}
