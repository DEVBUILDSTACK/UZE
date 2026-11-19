// Wallet-bound auth. A principal is a Solana wallet: the base58 string
// IS the ed25519 public key. Sign-in is a signature over a server nonce:
//   client asks for a challenge -> server issues a nonce + message
//   client signs the message with the wallet key -> server verifies
// Verification uses Node's built-in crypto: the raw 32-byte public key is
// wrapped in an SPKI DER envelope (fixed Ed25519 prefix) to build a
// KeyObject. Sessions are bearer tokens bound to the wallet; revoking a
// principal kills all of its sessions at the next call boundary.
import crypto from "node:crypto";
import { base58Decode } from "./base58.mjs";

const SPKI_ED25519_PREFIX = Buffer.from("302a300506032b6570032100", "hex");
const NONCE_TTL_MS = 5 * 60 * 1000;

export function verifyEd25519(pubkeyRaw, message, signature) {
  try {
    const key = crypto.createPublicKey({
      key: Buffer.concat([SPKI_ED25519_PREFIX, Buffer.from(pubkeyRaw)]),
      format: "der",
      type: "spki",
    });
    return crypto.verify(null, Buffer.from(message), key, Buffer.from(signature));
  } catch {
    return false;
  }
}

function decodeSignature(sig) {
  if (Array.isArray(sig)) return Buffer.from(sig);
  if (typeof sig !== "string") return null;
  if (/^[0-9a-fA-F]{128}$/.test(sig)) return Buffer.from(sig, "hex");
  try { const b = Buffer.from(sig, "base64"); if (b.length === 64) return b; } catch { /* fall through */ }
  try { const b = base58Decode(sig); if (b.length === 64) return b; } catch { /* fall through */ }
  return null;
}

export class Auth {
  constructor(chronicle) {
    this.chronicle = chronicle;
    this.nonces = new Map(); // nonce -> {wallet, message, expiresAt}
    this.sessions = new Map(); // token -> {token, wallet, createdAt, revoked}
  }

  challenge(wallet) {
    let pubkey;
    try { pubkey = base58Decode(wallet); } catch { pubkey = null; }
    if (!pubkey || pubkey.length !== 32) {
      this.chronicle.append("auth.refused", { principal: wallet || null, reason: "invalid_wallet" });
      return { error: "invalid_wallet", message: "wallet must be a base58 ed25519 public key (Solana address)" };
    }
    const nonce = crypto.randomBytes(16).toString("hex");
    const message = `UZE Instant MCP — sign-in\nwallet: ${wallet}\nnonce: ${nonce}`;
    this.nonces.set(nonce, { wallet, message, expiresAt: Date.now() + NONCE_TTL_MS });
    this.chronicle.append("auth.challenge", { principal: wallet });
    return { nonce, message, expiresAt: new Date(Date.now() + NONCE_TTL_MS).toISOString() };
  }

  verify(wallet, signature, store) {
    const fail = (reason, message) => {
      this.chronicle.append("auth.refused", { principal: wallet || null, reason });
      return { error: reason, message };
    };
    let entry = null;
    for (const [nonce, e] of this.nonces) if (e.wallet === wallet) { entry = { nonce, ...e }; break; }
    if (!entry) return fail("no_challenge", "request a challenge first (uze/challenge)");
    this.nonces.delete(entry.nonce);
    if (Date.now() > entry.expiresAt) return fail("challenge_expired", "challenge expired; request a new one");
    const principal = store.getPrincipal(wallet);
    if (principal?.revoked) return fail("principal_revoked", "this principal has been revoked");
    const sig = decodeSignature(signature);
    if (!sig) return fail("bad_signature_encoding", "signature must be base64, base58, hex, or a byte array (64 bytes)");
    const pubkey = base58Decode(wallet);
    if (!verifyEd25519(pubkey, entry.message, sig)) return fail("bad_signature", "signature does not verify against the wallet key");
    const token = crypto.randomBytes(32).toString("hex");
    const session = { token, wallet, createdAt: new Date().toISOString(), revoked: false };
    this.sessions.set(token, session);
    this.chronicle.append("auth.verified", { principal: wallet, sessionId: token.slice(0, 8) });
    return { sessionToken: token, principal: wallet, tier: principal?.tier || null };
  }

  // Returns the live session or null. A session is dead if it was killed
  // individually or its principal was revoked (checked by the caller via
  // the store); the dispatcher consults this at every call boundary.
  session(token) {
    if (!token) return null;
    const s = this.sessions.get(token);
    return s && !s.revoked ? s : null;
  }

  // Revoke cascade: kill every session belonging to the wallet, now.
  // Calls already admitted (in-flight) are untouched — they complete.
  revokeSessions(wallet) {
    let killed = 0;
    for (const s of this.sessions.values()) {
      if (s.wallet === wallet && !s.revoked) {
        s.revoked = true;
        killed++;
        this.chronicle.append("session.revoked", { principal: wallet, sessionId: s.token.slice(0, 8) });
      }
    }
    return killed;
  }
}
