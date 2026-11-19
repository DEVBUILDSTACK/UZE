// JSON data store. Data dir defaults to ../data, overridable with
// LIBRARY_DATA (tests run against a temp copy — the real chronicle
// is never touched by a test run).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DATA = process.env.LIBRARY_DATA || path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "data");
export function load(name) { return JSON.parse(fs.readFileSync(path.join(DATA, name), "utf8")); }
// Write-through persistence (lib/store-pg.mjs registers here in DB
// mode): the JSON documents are the working set; Postgres is the
// durable record. In JSON mode no persister is registered.
let persister = null;
export function setPersister(fn) { persister = fn; }
export function save(name, obj) {
  fs.writeFileSync(path.join(DATA, name), JSON.stringify(obj, null, 1) + "\n");
  if (persister) persister(name, obj);
}
export function chronicle(type, fields) {
  const c = load("chronicle.json");
  c.entries.push({ at: new Date().toISOString(), type, ...fields });
  save("chronicle.json", c);
}
export function commsSend(to, kind, subject, body, extra = {}) {
  const log = load("comms-log.json");
  const entry = { id: `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`,
    at: new Date().toISOString(), from: log.sender, to, kind, subject, body, status: "queued", ...extra };
  log.sends.push(entry); save("comms-log.json", log);
  chronicle("comms-send", { to, kind, subject });
  return entry;
}
