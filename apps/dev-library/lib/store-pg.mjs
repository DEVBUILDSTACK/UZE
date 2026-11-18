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
  }
}

export async function initPgStore() {
  await ensurePool();
  const { rows: devCount } = await pool.query("SELECT count(*)::int AS n FROM developer");
  const { rows: mockCount } = await pool.query("SELECT count(*)::int AS n FROM mock");
  if (devCount[0].n === 0 && mockCount[0].n === 0) {
    // First boot on an empty DB: adopt the working set as the record.
    for (const name of ["developers.json", "mocks.json", "chronicle.json", "comms-log.json", "comments.json"]) {
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
    save("comms-log.json", { version: 1, sender: "desk@uzemarkets.com", sends: sends.rows.map(r => r.data) });
    const comments = await pool.query("SELECT slug, by_email AS by, at, text FROM comment ORDER BY id");
    save("comments.json", { version: 1, comments: comments.rows.map(r => ({ slug: r.slug, by: r.by, at: new Date(r.at).toISOString(), text: r.text })) });
  }
  setPersister((name, obj) => { chain = chain.then(() => persist(name, obj)).catch(e => console.error("pg persist failed:", name, e.message)); });
  return pool;
}
export function getPool() { return pool; }
