// Seed the talent data layer with the known professionals and their
// verified DEVBUILDSTACK access (db/professionals.mjs — live scan of
// 2026-11-18). Idempotent: safe to re-run. Records access exactly as
// found; changes nothing on GitHub.
// Usage: DATABASE_URL=postgres://… node db/seed.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pg from "pg";
import { PROFESSIONALS, SCAN_DATE } from "./professionals.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
await pool.query(fs.readFileSync(path.join(HERE, "schema.sql"), "utf8"));

for (const p of PROFESSIONALS) {
  await pool.query(
    `INSERT INTO developer_status (email,name,dev_class,github_username,whatsapp,telegram,linkedin,x_handle,
       expertise_summary,repos_with_access,access_summary,gating_status,status_recorded_on,notes)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,'not-granted',$12,$13)
     ON CONFLICT (email) DO UPDATE SET name=EXCLUDED.name, dev_class=EXCLUDED.dev_class,
       github_username=EXCLUDED.github_username, whatsapp=EXCLUDED.whatsapp, telegram=EXCLUDED.telegram,
       linkedin=EXCLUDED.linkedin, x_handle=EXCLUDED.x_handle, expertise_summary=EXCLUDED.expertise_summary,
       repos_with_access=EXCLUDED.repos_with_access, access_summary=EXCLUDED.access_summary,
       status_recorded_on=EXCLUDED.status_recorded_on, notes=EXCLUDED.notes`,
    [p.email, p.name, p.devClass, p.github, p.whatsapp, p.telegram, p.linkedin, p.x,
     p.expertiseSummary, p.grants.length, p.accessSummary, SCAN_DATE, p.notes]);

  // The Developer List record itself. source[] carries the pre-system
  // grants with their origin marked — grantedAt is null because these
  // grants predate the desk; the ledger (repo_permission) dates them
  // by the scan that verified them.
  const record = {
    name: p.name, email: p.email, expertise: p.expertise, roadmapExempt: false, track: p.track,
    contact: { email: { done: false, at: null }, whatsapp: { done: false, at: null } },
    readingRoom: { active: false, grantedAt: null, revokedAt: null },
    source: p.grants.map(([repo]) => ({ repo: "DEVBUILDSTACK/" + repo, grantedAt: null, revokedAt: null, origin: `pre-system (verified ${SCAN_DATE} scan)` })),
    sessionEpoch: 0, roadmap: null, stage: p.stage,
    stageHistory: [{ stage: p.stage, at: new Date().toISOString(), note: `seeded ${SCAN_DATE} with verified status (James's tap)` }],
  };
  await pool.query(
    `INSERT INTO developer (email,name,dev_class,track,stage,session_epoch,roadmap,roadmap_exempt,data)
     VALUES ($1,$2,$3,$4,$5,0,NULL,false,$6)
     ON CONFLICT (email) DO UPDATE SET name=EXCLUDED.name, dev_class=EXCLUDED.dev_class,
       track=EXCLUDED.track, stage=EXCLUDED.stage, data=EXCLUDED.data`,
    [p.email, p.name, p.devClass, p.track, p.stage, JSON.stringify(record)]);

  for (const [repo, permission] of p.grants) {
    await pool.query(
      `INSERT INTO repo_permission (org,repo,repo_url,developer_email,developer_name,permission,date_recorded,origin)
       VALUES ('DEVBUILDSTACK',$1,$2,$3,$4,$5,$6,'verified-scan-2026-11-18') ON CONFLICT DO NOTHING`,
      [repo, "https://github.com/DEVBUILDSTACK/" + repo, p.email, p.name, permission, SCAN_DATE]);
  }
}
const counts = {};
for (const t of ["developer", "developer_status", "repo_permission"]) {
  counts[t] = (await pool.query(`SELECT count(*)::int AS n FROM ${t}`)).rows[0].n;
}
console.log("seeded:", JSON.stringify(counts));
await pool.end();
