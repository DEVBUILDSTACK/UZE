// Pinning adapters for the publication layer (P2 §5 seam point 3).
// One publication layer serves both programs; the pinning home is an
// adapter behind this interface, never a label: a local store is
// never called IPFS, and a bucket is never labeled IPFS.
//
// Operating home of record: Filebase/Pinata (diagnosis outcome,
// 2026-11-18); UZE-IPFS on NEAR Cloud is the conditional target,
// gated on the four-point P0 verification + NEAR credits. Tonight
// neither home is credentialed, so the Filebase/Pinata adapter is
// coded to its API shape but INERT — it refuses before any network
// call until credentials exist — and the LOCAL adapter (a
// content-addressed store, address = the sha256 of the content) is
// the proof adapter in force.
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DATA = process.env.LIBRARY_DATA || path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "data");

// Local content-addressed store. The address is the sha256 of the
// exact content pinned — retrieval is verifiable byte-for-byte
// (retrieved content's hash = the address it was retrieved by).
export const localAdapter = {
  name: "local-sha256",
  async pin(content) {
    const cid = "sha256:" + createHash("sha256").update(content).digest("hex");
    const dir = path.join(DATA, "pins");
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, cid.slice("sha256:".length) + ".txt"), content);
    return { cid, adapter: this.name };
  },
  async fetch(cid) {
    const file = path.join(DATA, "pins", String(cid).replace(/^sha256:/, "") + ".txt");
    return fs.existsSync(file) ? fs.readFileSync(file, "utf8") : null;
  },
};

// Filebase/Pinata — the operating home of record, INERT tonight.
// Coded to the Pinata pinning API shape (Filebase exposes a
// compatible pinning service); refuses before any network call while
// no credential is configured. Do not create accounts or credentials
// to wake this adapter — credentialing the operating home is a
// separate, gated step.
export const filebasePinataAdapter = {
  name: "filebase-pinata",
  async pin(content) {
    const credential = process.env.PINATA_JWT || process.env.FILEBASE_API_KEY || "";
    if (!credential) {
      throw new Error("pinning adapter 'filebase-pinata' is INERT: no PINATA_JWT / FILEBASE_API_KEY configured — the operating home is not yet credentialed; the local adapter remains in force");
    }
    // API shape only — unreachable until a credential exists.
    const res = await fetch("https://api.pinata.cloud/pinning/pinJSONToIPFS", {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${credential}` },
      body: JSON.stringify({ pinataContent: JSON.parse(content) }),
    });
    if (!res.ok) throw new Error(`filebase-pinata pin failed: HTTP ${res.status}`);
    const out = await res.json();
    return { cid: out.IpfsHash, adapter: this.name };
  },
  async fetch(cid) {
    const gateway = process.env.PINATA_GATEWAY || "https://gateway.pinata.cloud";
    const res = await fetch(`${gateway}/ipfs/${cid}`);
    return res.ok ? res.text() : null;
  },
};

// The adapter in force: Filebase/Pinata only when explicitly
// selected AND credentialed; otherwise the local proof adapter.
export function activeAdapter() {
  if (process.env.PUBLISH_PINNER === "filebase-pinata") return filebasePinataAdapter;
  return localAdapter;
}
