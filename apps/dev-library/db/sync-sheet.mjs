// Regenerate the Google Sheet from the talent data layer — the sheet
// is an output of the DB, never hand-edited (addendum §4).
// Usage: DATABASE_URL=postgres://… node db/sync-sheet.mjs [--dry-run]
// Env: SHEET_ID overrides the default ledger spreadsheet.
import { execFileSync } from "node:child_process";
import pg from "pg";

const SHEET_ID = process.env.SHEET_ID || "1n-D2eCYFYTLiTvExkstjXBljQYD9tSxBCqbAAXS6hRM";
const CLI = "/opt/hatch/bin/hatch_gws_cli";
const dry = process.argv.includes("--dry-run");

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const perms = (await pool.query(
  `SELECT org, repo_url, developer_name, developer_email, to_char(date_recorded,'YYYY-MM-DD') AS recorded,
          permission, to_char(date_modified,'YYYY-MM-DD') AS modified,
          to_char(date_removed,'YYYY-MM-DD') AS removed, status
   FROM repo_permission WHERE status='active'
   ORDER BY lower(repo) ASC, developer_name ASC, date_recorded DESC`)).rows;
const removed = (await pool.query(
  `SELECT org, repo_url, developer_name, developer_email, to_char(date_recorded,'YYYY-MM-DD') AS recorded,
          permission, to_char(date_modified,'YYYY-MM-DD') AS modified,
          to_char(date_removed,'YYYY-MM-DD') AS removed, status
   FROM repo_permission WHERE status='removed'
   ORDER BY lower(repo) ASC, developer_name ASC, date_recorded DESC`)).rows;
const status = (await pool.query(
  `SELECT name, email, github_username, dev_class, access_summary, gating_status, expertise_summary, notes
   FROM developer_status ORDER BY name`)).rows;
await pool.end();

const row = (r) => [r.org, r.repo_url, r.developer_name, r.developer_email, r.recorded, r.permission,
  "", r.modified || "", "", r.removed || "", r.status === "removed" ? "removed" : ""];
const ledger = [["Org", "Repo URL", "Name", "Email", "Date recorded", "Permission", "", "Date modified", "", "Date removed", "Removed"],
  ...perms.map(row), ...removed.map(row)];
const classLabel = { PRIOR_TEAM: "Prior team dev", PEER_PROSPECT: "Peer prospect dev", COLD_RECRUIT: "Cold peer dev recruit" };
const gatingLabel = { "not-granted": "Not seeded yet", granted: "Dev Library access granted", revoked: "Revoked — reset to zero" };
const statusRows = [["Name", "Email", "GitHub", "Class", "Repos with access", "Dev Library gating status", "Notes"],
  ...status.map(s => [s.name, s.email, s.github_username || "", classLabel[s.dev_class] || s.dev_class,
    s.access_summary || "0", gatingLabel[s.gating_status] || s.gating_status,
    [s.expertise_summary, s.notes].filter(Boolean).join(" ")])];

console.log(`ledger rows: ${ledger.length - 1} (active ${perms.length}, removed ${removed.length}); status rows: ${statusRows.length - 1}`);
if (dry) { console.log("dry run — sheet not written"); process.exit(0); }

function update(range, values) {
  execFileSync(CLI, ["sheets", "spreadsheets", "values", "update", "--params",
    JSON.stringify({ spreadsheetId: SHEET_ID, range, valueInputOption: "USER_ENTERED" }),
    "--json", JSON.stringify({ values })], { stdio: "pipe" });
}
update("Permissions Ledger!A1", ledger);
update("Developer Status!A1", statusRows);
console.log("sheet regenerated from DB:", SHEET_ID);
