// The organization registry: organizations are first-class and
// contacts attach to them. Advisor records carry an org key; this
// module is the read path for the registry (seeded from
// db/orgs.mjs into data/orgs.json, mirrored to the org table in
// DB mode by lib/store-pg.mjs).
import { load } from "./store.mjs";

export function loadOrgs() {
  return load("orgs.json").orgs || [];
}
export function findOrg(key) {
  return loadOrgs().find(o => o.key === key) || null;
}
