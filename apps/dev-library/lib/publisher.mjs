// The publisher (P2 §4 — redaction as architecture). This module is
// the publication store's only writer, and it is separated from the
// identity store BY CONSTRUCTION:
//
//   - Its imports are exactly: the document store (for its OWN
//     publications.json), the pinning adapters, and node:crypto.
//   - It imports NOTHING from gate.mjs (the developer/identity
//     records), lifecycle.mjs, engagements.mjs, or assessments.mjs.
//     There is no code path here that can reach a name, an email, or
//     a company name — the publisher never had them.
//   - It accepts a publication CANDIDATE (a plain object built by
//     the system of record) and copies only WHITELISTED fields into
//     the artifact. Anything else in the candidate is dropped here,
//     at the boundary, whatever the caller sent.
//   - As belt-and-braces it scans the finished artifact for an
//     email-shaped string and refuses to publish if one appears.
//
// Triangulation mitigation (all mandatory, P2 §4): coarse bucketing
// (the candidate carries a DAY, never a timestamp; amounts arrive
// banded), aggregate-first publication, engagement-scoped pseudonyms
// (computed by the caller over scope + talent DID), and the
// minimum-anonymity-set threshold — a candidate whose cohort is
// smaller than the threshold does not publish.
import { load, save } from "./store.mjs";
import { activeAdapter } from "./pinning.mjs";

const WHITELIST = ["pseudonym", "vertical", "role", "realm", "gradeBand",
  "validity", "market", "day", "terms", "progress", "cohortKey"];
const EMAIL_SHAPED = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;

export function loadPublications() { return load("publications.json").publications; }
export function findPublication(id) { return loadPublications().find(p => p.id === id) || null; }

// Grade banding: the published copy carries the band, never the raw
// score (coarse bucketing applied to the result itself).
export function bandOf(score) {
  if (score >= 90) return "90-100";
  if (score >= 80) return "80-89";
  if (score >= 70) return "70-79";
  if (score >= 60) return "60-69";
  return "below-60";
}

// Validity is claimed in exactly one form (P2 §2.4): "calibrated
// against reference population X with metric Y" — or the explicit
// gap acknowledgment. Any other shape is refused here, at the
// publication boundary, whatever upstream produced.
export function validityStatement(validity) {
  if (validity && validity.form === "calibrated" && validity.population && validity.metric) {
    return `calibrated against reference population ${validity.population} with metric ${validity.metric}`;
  }
  if (validity && validity.form === "gap" && validity.acknowledgment) {
    return `gap acknowledged: ${validity.acknowledgment}`;
  }
  throw new Error("publication refused: validity must be stated as 'calibrated against reference population X with metric Y' or as an explicit gap acknowledgment");
}

function buildArtifact(candidate) {
  const artifact = {};
  for (const k of WHITELIST) if (candidate[k] !== undefined) artifact[k] = candidate[k];
  artifact.validity = validityStatement(candidate.validity);
  const text = JSON.stringify(artifact);
  if (EMAIL_SHAPED.test(text)) throw new Error("publication refused: the artifact contains an email-shaped string");
  return artifact;
}

const newId = () => `pub_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;

// Publish one outcome. candidate.cohortSize is the size of the
// outcome's cohort in the system of record (same vertical × primary
// Role×Realm pair); below the minimum anonymity set, this refuses.
export async function publishOutcome(candidate, { minAnonymitySet = 5 } = {}) {
  if (!candidate.pseudonym) throw new Error("publication refused: an engagement-scoped pseudonym is required");
  if (!candidate.cohortKey) throw new Error("publication refused: a cohort key is required");
  if (!Number.isFinite(candidate.cohortSize) || candidate.cohortSize < minAnonymitySet) {
    throw new Error(`publication refused: cohort of ${candidate.cohortSize ?? 0} is below the minimum anonymity set (${minAnonymitySet})`);
  }
  const artifact = buildArtifact(candidate);
  const adapter = activeAdapter();
  const { cid, adapter: adapterName } = await adapter.pin(JSON.stringify(artifact, null, 1) + "\n");
  const pub = { id: newId(), cid, adapter: adapterName, pseudonym: candidate.pseudonym,
    cohortKey: candidate.cohortKey, runId: candidate.runId || null,
    publishedAt: new Date().toISOString(), cidHistory: [], artifact };
  const db = load("publications.json");
  db.publications.push(pub); save("publications.json", db);
  return pub;
}

// Progress/activity on an existing publication (the public copy is
// viewable as it proceeds): appends day-bucketed, type-only progress
// entries and re-pins; the prior CID is kept in cidHistory.
export async function appendProgress(publicationId, entries) {
  const db = load("publications.json");
  const pub = db.publications.find(p => p.id === publicationId);
  if (!pub) throw new Error("publication not found: " + publicationId);
  for (const e of entries || []) {
    if (!e.day || !e.event) throw new Error("progress entries carry a day and an event type only");
    pub.artifact.progress = [...(pub.artifact.progress || []), { day: e.day, event: String(e.event) }];
  }
  const text = JSON.stringify(pub.artifact);
  if (EMAIL_SHAPED.test(text)) throw new Error("publication refused: the artifact contains an email-shaped string");
  const adapter = activeAdapter();
  const { cid, adapter: adapterName } = await adapter.pin(JSON.stringify(pub.artifact, null, 1) + "\n");
  pub.cidHistory.push(pub.cid); pub.cid = cid; pub.adapter = adapterName;
  save("publications.json", db);
  return pub;
}

// The public projection — what the public viewer serves. Exactly the
// stored artifact plus its content address; nothing else exists here
// to serve.
export function publicView(pub) {
  return { id: pub.id, cid: pub.cid, adapter: pub.adapter, publishedAt: pub.publishedAt, ...pub.artifact };
}
