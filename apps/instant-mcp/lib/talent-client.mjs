// The Talent client — instant-mcp's seam into the P2 system of
// record (apps/dev-library, Scope 2). HTTP on purpose: the
// dev-library owns the assessment state, the two human gates, and
// the publisher; this server holds no copy of any of it, and no
// code path here can satisfy a gate — the gates sign in the
// console, by named humans, or not at all.
//
// Configuration (read lazily, at call time, so tests and deploys
// can set it after import):
//   TALENT_API_URL           default http://127.0.0.1:8734
//   TALENT_API_MASTER_TOKEN  the dev-library console credential
//
// Dev-library refusals map to dispatcher refusals: a record whose
// gates have not passed answers "gates_not_passed"; a cohort below
// the minimum anonymity set answers "below_minimum_anonymity_set".

export function createTalentClient() {
  const base = () => (process.env.TALENT_API_URL || "http://127.0.0.1:8734").replace(/\/$/, "");

  async function call(path, body) {
    let res;
    try {
      res = await fetch(base() + path, { method: "POST",
        headers: { "content-type": "application/json",
          "x-master-token": process.env.TALENT_API_MASTER_TOKEN || "" },
        body: JSON.stringify(body || {}) });
    } catch {
      return { refusal: { reason: "talent_api_unreachable", message: "the P2 assessment API did not answer" } };
    }
    const data = await res.json().catch(() => ({}));
    if (res.status !== 200 || data.ok === false) {
      const msg = data.error || `HTTP ${res.status}`;
      const reason = /gates not passed|nothing runs before both gates|cannot precede Gate 1/i.test(msg) ? "gates_not_passed"
        : /anonymity/i.test(msg) ? "below_minimum_anonymity_set"
        : "talent_api_error";
      return { refusal: { reason, message: msg } };
    }
    return { result: data };
  }

  return {
    // submit_assessment: configure a role + generate the
    // instrument from the template library. The record created is
    // UNGATED by design — Gate 1 and Gate 2 are human acts in the
    // console; an agent submission can never carry them.
    async submitAssessment(roleConfig) {
      const rc = await call("/api/admin/role-configs", roleConfig || {});
      if (rc.refusal) return rc;
      const gen = await call(`/api/admin/role-configs/${rc.result.roleConfig.id}/generate`, { by: "instant-mcp" });
      if (gen.refusal) return gen;
      return { result: { role_config_id: rc.result.roleConfig.id, assessment: gen.result.assessment,
        note: "submitted UNGATED: Gate 1 (employer intent) and Gate 2 (approver of record) sign in the console before any run, score, or publication" } };
    },
    // score_assessment: the scored record for one talent DID —
    // the dev-library refuses unless both gates have passed.
    async scoreAssessment({ assessment_id, talent_did }) {
      const r = await call(`/api/admin/assessments/${assessment_id}/score-by-talent`, { talentDid: talent_did });
      if (r.refusal) return r;
      return { result: r.result.score };
    },
    // publish_assessment_outcome: publish_redacted wired to the
    // assessment outcome — redacted, pseudonymous, minimum-
    // anonymity-set enforced in the publisher.
    async publishOutcome({ assessment_id, run_id }) {
      const r = await call(`/api/admin/assessments/${assessment_id}/publish-outcome`, { runId: run_id || null });
      if (r.refusal) return r;
      return { result: r.result.publication };
    },
  };
}
