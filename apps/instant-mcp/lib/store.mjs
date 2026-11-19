// Store — principals (pre-authorizations) and instances, persisted as
// JSON in the app data dir. Sessions and auth nonces are memory-only.
// The chronicle (lib/chronicle.mjs) is the audit record; this file is
// the working state the gate reads.
import fs from "node:fs";
import path from "node:path";

export class Store {
  constructor(file) {
    this.file = file;
    this.principals = new Map(); // wallet -> {wallet, tier, limits, revoked, createdAt, updatedAt}
    this.instances = new Map(); // id -> instance record
    fs.mkdirSync(path.dirname(file), { recursive: true });
    if (fs.existsSync(file)) {
      const raw = JSON.parse(fs.readFileSync(file, "utf8"));
      for (const p of raw.principals || []) this.principals.set(p.wallet, p);
      for (const i of raw.instances || []) this.instances.set(i.id, i);
    }
  }

  save() {
    const raw = { principals: [...this.principals.values()], instances: [...this.instances.values()] };
    fs.writeFileSync(this.file, JSON.stringify(raw, null, 2));
  }

  getPrincipal(wallet) {
    return this.principals.get(wallet) || null;
  }

  upsertPrincipal(p) {
    const prev = this.principals.get(p.wallet);
    const rec = { ...prev, ...p, wallet: p.wallet, updatedAt: new Date().toISOString(), createdAt: prev?.createdAt || new Date().toISOString() };
    this.principals.set(p.wallet, rec);
    this.save();
    return rec;
  }

  getInstance(id) {
    return this.instances.get(id) || null;
  }

  putInstance(inst) {
    this.instances.set(inst.id, inst);
    this.save();
    return inst;
  }

  instancesOf(wallet) {
    return [...this.instances.values()].filter((i) => i.owner === wallet);
  }
}
