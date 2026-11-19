// Postgres store for the Dev Library — the talent data layer
// (Vercel Postgres in production; any Postgres via DATABASE_URL).
// Model: the JSON documents remain the app's working set behind the
// exact lib/store.mjs interface; this module (a) hydrates the working
// set from the DB at boot when the DB holds state, and (b) writes
// every save() through to the typed tables in db/schema.sql.
// The DB is the durable record; on an ephemeral filesystem the files
// are re-materialized from it at every boot.
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import pg from "pg";
import { load, save, setPersister } from "./store.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SCHEMA = fs.readFileSync(path.join(HERE, "..", "db", "schema.sql"), "utf8");
const dedupe = (obj) => createHash("md5").update(JSON.stringify(obj)).digest("hex");

let pool = null;
let chain = Promise.resolve();
export function flushPg() { return chain; }

export async function ensurePool() {
  if (!pool) {
    pool = new pg.Pool({ connectionString: process.env.DATABASE_URL || process.env.POSTGRES_URL });
    await pool.query(SCHEMA);
  }
  return pool;
}
// DB-backed one-time codes (serverless-safe; gate.mjs uses these in DB mode).
export async function setOtp(email, hash, expires) {
  const p = await ensurePool();
  await p.query(`INSERT INTO otp_code (email,code_hash,expires_at) VALUES ($1,$2,$3)
                 ON CONFLICT (email) DO UPDATE SET code_hash=EXCLUDED.code_hash, expires_at=EXCLUDED.expires_at`,
    [email, hash, expires]);
}
export async function getOtp(email) {
  const p = await ensurePool();
  const { rows } = await p.query("SELECT code_hash, expires_at FROM otp_code WHERE email=$1", [email]);
  return rows[0] ? { hash: rows[0].code_hash, expires: Number(rows[0].expires_at) } : null;
}
export async function delOtp(email) {
  const p = await ensurePool();
  await p.query("DELETE FROM otp_code WHERE email=$1", [email]);
}
// Eco one-time codes live in eco_otp_code — a distinct namespace so
// Dev Library codes and UZE Buildr Team codes never mix, even for an
// email that holds grants on both surfaces.
export async function setEcoOtp(email, hash, expires) {
  const p = await ensurePool();
  await p.query(`INSERT INTO eco_otp_code (email,code_hash,expires_at) VALUES ($1,$2,$3)
                 ON CONFLICT (email) DO UPDATE SET code_hash=EXCLUDED.code_hash, expires_at=EXCLUDED.expires_at`,
    [email, hash, expires]);
}
export async function getEcoOtp(email) {
  const p = await ensurePool();
  const { rows } = await p.query("SELECT code_hash, expires_at FROM eco_otp_code WHERE email=$1", [email]);
  return rows[0] ? { hash: rows[0].code_hash, expires: Number(rows[0].expires_at) } : null;
}
export async function delEcoOtp(email) {
  const p = await ensurePool();
  await p.query("DELETE FROM eco_otp_code WHERE email=$1", [email]);
}

async function persist(name, obj) {
  const q = (sql, params) => pool.query(sql, params);
  if (name === "developers.json") {
    for (const d of obj.developers) {
      await q(`INSERT INTO developer (email,name,track,stage,session_epoch,roadmap,roadmap_exempt,data)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT (email) DO UPDATE SET name=EXCLUDED.name, track=EXCLUDED.track,
                 stage=EXCLUDED.stage, session_epoch=EXCLUDED.session_epoch,
                 roadmap=EXCLUDED.roadmap, roadmap_exempt=EXCLUDED.roadmap_exempt, data=EXCLUDED.data`,
        [d.email.toLowerCase(), d.name, d.track || "EITHER", d.stage || "prospect",
         d.sessionEpoch || 0, d.roadmap || null, !!d.roadmapExempt, JSON.stringify(d)]);
      await q(`UPDATE developer_status SET gating_status=$2 WHERE email=$1`,
        [d.email.toLowerCase(), d.readingRoom?.active ? "granted" : (d.stage === "revoked" ? "revoked" : "not-granted")]);
      await q(`DELETE FROM developer_expertise WHERE email=$1`, [d.email.toLowerCase()]);
      for (const p of d.pairs || []) {
        await q(`INSERT INTO developer_expertise (email,ordinal,role,realm,rank) VALUES ($1,$2,$3,$4,$5)`,
          [d.email.toLowerCase(), p.ordinal, p.role, p.realm, p.rank]);
      }
    }
  } else if (name === "engagements.json") {
    for (const e of obj.engagements) {
      await q(`INSERT INTO engagement (id,title,client_name,service,deployment,commercial_model,fee_months,
                 developer_email,signed_at,deposit_at,closed_at,cancelled_at,created_at,data)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
               ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, client_name=EXCLUDED.client_name,
                 service=EXCLUDED.service, deployment=EXCLUDED.deployment, commercial_model=EXCLUDED.commercial_model,
                 fee_months=EXCLUDED.fee_months, developer_email=EXCLUDED.developer_email,
                 signed_at=EXCLUDED.signed_at, deposit_at=EXCLUDED.deposit_at, closed_at=EXCLUDED.closed_at,
                 cancelled_at=EXCLUDED.cancelled_at, data=EXCLUDED.data`,
        [e.id, e.title, e.clientName, e.service, e.deployment, e.commercialModel, e.feeMonths,
         e.developerEmail, e.signedAt, e.depositAt, e.closedAt, e.cancelledAt, e.createdAt, JSON.stringify(e)]);
    }
  } else if (name === "mocks.json") {
    for (const m of obj.mocks) {
      await q(`INSERT INTO mock (slug,title,topic,date,repo,track,version,data) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT (slug) DO UPDATE SET title=EXCLUDED.title, topic=EXCLUDED.topic, date=EXCLUDED.date,
                 repo=EXCLUDED.repo, track=EXCLUDED.track, version=EXCLUDED.version, data=EXCLUDED.data`,
        [m.slug, m.title, m.topic || null, m.date || null, m.repo || null, m.track || "BOTH", m.version || 1, JSON.stringify(m)]);
      await q(`DELETE FROM mock_alias WHERE slug=$1`, [m.slug]);
      for (const a of m.aliases || []) await q(`INSERT INTO mock_alias (alias,slug) VALUES ($1,$2) ON CONFLICT (alias) DO UPDATE SET slug=EXCLUDED.slug`, [a, m.slug]);
    }
  } else if (name === "chronicle.json") {
    for (const e of obj.entries) {
      await q(`INSERT INTO chronicle_entry (at,type,dedupe,data) VALUES ($1,$2,$3,$4) ON CONFLICT (dedupe) DO NOTHING`,
        [e.at, e.type, dedupe(e), JSON.stringify(e)]);
    }
  } else if (name === "comms-log.json") {
    for (const s of obj.sends) {
      await q(`INSERT INTO comms_send (at,sender,recipient,kind,subject,status,dedupe,data) VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT (dedupe) DO NOTHING`,
        [s.at, s.from || obj.sender, s.to, s.kind, s.subject || null, s.status || "queued", dedupe(s), JSON.stringify(s)]);
    }
  } else if (name === "comments.json") {
    for (const c of obj.comments) {
      await q(`INSERT INTO comment (slug,by_email,at,text,dedupe) VALUES ($1,$2,$3,$4,$5) ON CONFLICT (dedupe) DO NOTHING`,
        [c.slug, c.by, c.at, c.text, dedupe(c)]);
    }
  } else if (name === "assessments.json") {
    await q(`INSERT INTO assessment_meta (id,data) VALUES (1,$1)
             ON CONFLICT (id) DO UPDATE SET data=EXCLUDED.data`,
      [JSON.stringify({ config: obj.config || {}, approvers: obj.approvers || {}, quotes: obj.quotes || [] })]);
    for (const rc of obj.roleConfigs || []) {
      await q(`INSERT INTO role_config (id,employer_ref,vertical,title,created_at,data) VALUES ($1,$2,$3,$4,$5,$6)
               ON CONFLICT (id) DO UPDATE SET employer_ref=EXCLUDED.employer_ref, vertical=EXCLUDED.vertical,
                 title=EXCLUDED.title, data=EXCLUDED.data`,
        [rc.id, rc.employerRef, rc.vertical, rc.title, rc.createdAt, JSON.stringify(rc)]);
    }
    for (const a of obj.assessments || []) {
      await q(`INSERT INTO assessment (id,role_config_id,template_id,gate1_at,gate2_at,created_at,data)
               VALUES ($1,$2,$3,$4,$5,$6,$7)
               ON CONFLICT (id) DO UPDATE SET role_config_id=EXCLUDED.role_config_id, template_id=EXCLUDED.template_id,
                 gate1_at=EXCLUDED.gate1_at, gate2_at=EXCLUDED.gate2_at, data=EXCLUDED.data`,
        [a.id, a.roleConfigId, a.templateId,
         a.gate1?.decision === "signed" ? a.gate1.at : null,
         a.gate2?.decision === "signed" ? a.gate2.at : null,
         a.createdAt || new Date().toISOString(), JSON.stringify(a)]);
    }
    for (const r of obj.runs || []) {
      await q(`INSERT INTO assessment_run (id,assessment_id,talent_did,score,human_review,taken_at,data)
               VALUES ($1,$2,$3,$4,$5,$6,$7)
               ON CONFLICT (id) DO UPDATE SET assessment_id=EXCLUDED.assessment_id, talent_did=EXCLUDED.talent_did,
                 score=EXCLUDED.score, human_review=EXCLUDED.human_review, taken_at=EXCLUDED.taken_at, data=EXCLUDED.data`,
        [r.id, r.assessmentId, r.talentDid, r.score, r.humanReviewFlag, r.takenAt, JSON.stringify(r)]);
    }
  } else if (name === "advisors.json") {
    // The roster is small and removal is a real operation (there is
    // no tombstone), so the write-through reconciles BY ID: rows
    // whose id left the working set are deleted, the rest upserted.
    // (By id, not email — email is optional on this roster.)
    const list = obj.advisors || [];
    if (list.length) {
      await q(`DELETE FROM advisor WHERE id NOT IN (${list.map((_, i) => `$${i + 1}`).join(",")})`,
        list.map(a => a.id));
    } else {
      await q(`DELETE FROM advisor`);
    }
    for (const a of list) {
      await q(`INSERT INTO advisor (id,name,email,title,org,base,lane,added_at,data)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
               ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, email=EXCLUDED.email,
                 title=EXCLUDED.title, org=EXCLUDED.org, base=EXCLUDED.base, lane=EXCLUDED.lane,
                 added_at=EXCLUDED.added_at, data=EXCLUDED.data`,
        [a.id, a.name, a.email ? a.email.toLowerCase() : null, a.title || null, a.org || null,
         a.base || null, a.lane || null, a.addedAt, JSON.stringify(a)]);
    }
  } else if (name === "orgs.json") {
    // The registry only grows by seed/code updates; upserts suffice
    // (there is no removal operation for organizations).
    for (const o of obj.orgs || []) {
      await q(`INSERT INTO org (key,name,acronym,position,data) VALUES ($1,$2,$3,$4,$5)
               ON CONFLICT (key) DO UPDATE SET name=EXCLUDED.name, acronym=EXCLUDED.acronym,
                 position=EXCLUDED.position, data=EXCLUDED.data`,
        [o.key, o.name, o.acronym || null, o.position || 0, JSON.stringify(o)]);
    }
  } else if (name === "eco-contributors.json") {
    // Same reconcile-by-id discipline as the advisor roster: the
    // roster is small, removal is real, email is optional (key on
    // id, never email). Org grants are rewritten per contributor so
    // the table always mirrors the working set exactly.
    const list = obj.contributors || [];
    if (list.length) {
      await q(`DELETE FROM eco_contributor WHERE id NOT IN (${list.map((_, i) => `$${i + 1}`).join(",")})`,
        list.map(c => c.id));
    } else {
      await q(`DELETE FROM eco_contributor`);
    }
    for (const c of list) {
      await q(`INSERT INTO eco_contributor (id,name,email,role,stage,session_epoch,added_at,data)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, email=EXCLUDED.email,
                 role=EXCLUDED.role, stage=EXCLUDED.stage, session_epoch=EXCLUDED.session_epoch,
                 data=EXCLUDED.data`,
        [c.id, c.name, c.email ? c.email.toLowerCase() : null, c.role || null,
         c.stage || "seeded", c.sessionEpoch || 0, c.addedAt, JSON.stringify(c)]);
      await q(`DELETE FROM eco_contributor_org WHERE contributor_id=$1`, [c.id]);
      for (const orgKey of c.orgs || []) {
        await q(`INSERT INTO eco_contributor_org (contributor_id,org_key) VALUES ($1,$2) ON CONFLICT DO NOTHING`,
          [c.id, orgKey]);
      }
    }
  } else if (name === "eco-flow.json") {
    // Append-only: one row per transition, dedupe on the event id so
    // re-persisting the working set never duplicates a transition.
    for (const e of obj.events || []) {
      await q(`INSERT INTO eco_flow_event (contributor_id,step,at,dedupe,data) VALUES ($1,$2,$3,$4,$5) ON CONFLICT (dedupe) DO NOTHING`,
        [e.contributorId, e.step, e.at, e.id, JSON.stringify(e)]);
    }
  } else if (name === "publications.json") {
    for (const p of obj.publications || []) {
      await q(`INSERT INTO publication (id,cid,pseudonym,cohort_key,published_at,data) VALUES ($1,$2,$3,$4,$5,$6)
               ON CONFLICT (id) DO UPDATE SET cid=EXCLUDED.cid, pseudonym=EXCLUDED.pseudonym,
                 cohort_key=EXCLUDED.cohort_key, data=EXCLUDED.data`,
        [p.id, p.cid, p.pseudonym, p.cohortKey, p.publishedAt, JSON.stringify(p)]);
    }
  }
}

export async function initPgStore() {
  await ensurePool();
  const { rows: devCount } = await pool.query("SELECT count(*)::int AS n FROM developer");
  const { rows: mockCount } = await pool.query("SELECT count(*)::int AS n FROM mock");
  if (devCount[0].n === 0 && mockCount[0].n === 0) {
    // First boot on an empty DB: adopt the working set as the record.
    for (const name of ["developers.json", "mocks.json", "chronicle.json", "comms-log.json", "comments.json", "engagements.json", "assessments.json", "publications.json", "advisors.json", "orgs.json", "eco-contributors.json", "eco-flow.json"]) {
      await persist(name, load(name));
    }
  } else {
    // DB holds state: it wins. Re-materialize the working set from it.
    const devs = await pool.query("SELECT data FROM developer ORDER BY email");
    const cur = load("developers.json");
    save("developers.json", { ...cur, developers: devs.rows.map(r => r.data) });
    const mocks = await pool.query("SELECT data FROM mock ORDER BY slug");
    const curM = load("mocks.json");
    save("mocks.json", { ...curM, mocks: mocks.rows.map(r => r.data) });
    const entries = await pool.query("SELECT data FROM chronicle_entry ORDER BY id");
    save("chronicle.json", { version: 1, entries: entries.rows.map(r => r.data) });
    const sends = await pool.query("SELECT data FROM comms_send ORDER BY id");
    // comms_send holds one row per STATE an entry passes through
    // (persist's dedupe key is the whole entry JSON), so the same
    // entry id appears several times — including stale "queued"
    // snapshots of entries that later sent. Latest snapshot wins
    // (rows arrive in id order, so the last row per id is current);
    // without this, every cold start re-materializes the clogged
    // multi-state log and the drain wastes its budget re-attempting
    // snapshots of mail that already went out.
    const byId = new Map();
    for (const r of sends.rows) byId.set(r.data.id, r.data);
    save("comms-log.json", { version: 1, sender: "desk@uzemarkets.com", sends: [...byId.values()] });
    const comments = await pool.query("SELECT slug, by_email AS by, at, text FROM comment ORDER BY id");
    save("comments.json", { version: 1, comments: comments.rows.map(r => ({ slug: r.slug, by: r.by, at: new Date(r.at).toISOString(), text: r.text })) });
    const engs = await pool.query("SELECT data FROM engagement ORDER BY created_at");
    save("engagements.json", { version: 1, engagements: engs.rows.map(r => r.data) });
    // P2 documents: rebuild only when the DB actually holds P2 state
    // (an existing production DB predates these tables' rows; its
    // working-set seeds then stand until the first P2 write).
    const rcCount = await pool.query("SELECT count(*)::int AS n FROM role_config");
    const pubCount = await pool.query("SELECT count(*)::int AS n FROM publication");
    const metaRows = await pool.query("SELECT data FROM assessment_meta WHERE id=1");
    if (rcCount.rows[0].n || pubCount.rows[0].n || metaRows.rows.length) {
      const meta = metaRows.rows[0]?.data || {};
      const curA = load("assessments.json");
      const rcs = await pool.query("SELECT data FROM role_config ORDER BY created_at");
      const asms = await pool.query("SELECT data FROM assessment ORDER BY created_at");
      const runs = await pool.query("SELECT data FROM assessment_run ORDER BY taken_at");
      save("assessments.json", { version: 1,
        config: meta.config || curA.config || {}, approvers: meta.approvers || {}, quotes: meta.quotes || [],
        roleConfigs: rcs.rows.map(r => r.data), assessments: asms.rows.map(r => r.data), runs: runs.rows.map(r => r.data) });
      const pubs = await pool.query("SELECT data FROM publication ORDER BY published_at");
      save("publications.json", { version: 1, publications: pubs.rows.map(r => r.data) });
    }
    // Organizations (2026-11-19): the registry only grows by seed —
    // upsert the bundled registry first (new keys land), then
    // rebuild the working set from the table.
    await persist("orgs.json", load("orgs.json"));
    const orgRows = await pool.query("SELECT data FROM org ORDER BY position, key");
    if (orgRows.rows.length) save("orgs.json", { version: 1, orgs: orgRows.rows.map(r => r.data) });
    // Advisors (2026-11-19): the DB is the record for what it
    // holds, and bundled seeds the DB does not hold yet are merged
    // in by id (new seeds ship with the code — without the merge, a
    // DB that already holds one seed would hydrate over the rest
    // and they would never land). Desk-added records are never in
    // the bundle, so the merge cannot resurrect a desk removal of
    // anything but a seed record — the same standing-record
    // semantics db/seed.mjs applies to the professionals.
    const advRows = await pool.query("SELECT data FROM advisor ORDER BY added_at, email");
    const fromDb = advRows.rows.map(r => r.data);
    if (!fromDb.length) {
      await persist("advisors.json", load("advisors.json"));
    } else {
      const seedAdv = load("advisors.json").advisors || [];
      const haveIds = new Set(fromDb.map(a => a.id));
      const fresh = seedAdv.filter(a => !haveIds.has(a.id));
      if (fresh.length) {
        const merged = [...fromDb, ...fresh];
        save("advisors.json", { version: 1, advisors: merged });
        await persist("advisors.json", { version: 1, advisors: merged });
      } else {
        save("advisors.json", { version: 1, advisors: fromDb });
      }
    }
    // Eco contributors (2026-11-19): same merge-by-id semantics as
    // the advisor roster — the DB is the record for what it holds,
    // and bundled seeds it does not hold yet merge in by id so the
    // Buildr Team roster lands on an existing production DB.
    const ecoRows = await pool.query("SELECT data FROM eco_contributor ORDER BY added_at, email");
    const ecoFromDb = ecoRows.rows.map(r => r.data);
    if (!ecoFromDb.length) {
      await persist("eco-contributors.json", load("eco-contributors.json"));
    } else {
      const seedEco = load("eco-contributors.json").contributors || [];
      const haveEcoIds = new Set(ecoFromDb.map(c => c.id));
      const freshEco = seedEco.filter(c => !haveEcoIds.has(c.id));
      if (freshEco.length) {
        const mergedEco = [...ecoFromDb, ...freshEco];
        save("eco-contributors.json", { version: 1, contributors: mergedEco });
        await persist("eco-contributors.json", { version: 1, contributors: mergedEco });
      } else {
        save("eco-contributors.json", { version: 1, contributors: ecoFromDb });
      }
    }
    // Eco flow events: rebuild the working set from the append-only
    // table when it holds rows; otherwise the working set stands.
    const ecoFlowRows = await pool.query("SELECT data FROM eco_flow_event ORDER BY id");
    if (ecoFlowRows.rows.length) {
      save("eco-flow.json", { version: 1, events: ecoFlowRows.rows.map(r => r.data) });
    }
  }
  setPersister((name, obj) => { chain = chain.then(() => persist(name, obj)).catch(e => console.error("pg persist failed:", name, e.message)); });
  return pool;
}
export function getPool() { return pool; }
