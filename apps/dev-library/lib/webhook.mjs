// Resend delivery webhooks (Svix-signed). Resend reports the real
// fate of every send — delivered, bounced, complained, suppressed —
// and this records it against the comms entry it belongs to, joined
// on the provider id the send returned. So the per-developer comms
// log shows not just "sent" but what actually happened.
// Verification is the Standard Webhooks scheme: HMAC-SHA256 over
// "{id}.{timestamp}.{raw body}" with the base64-decoded whsec_
// secret, checked against the RAW body before any JSON parsing
// (Resend dev-docs deep dive, 2026-11-18). Svix retries reuse the
// same id — duplicates are acked and ignored.
import crypto from "node:crypto";
import { load, save } from "./store.mjs";

const STATUS = { "email.sent": "sent", "email.delivered": "delivered",
  "email.delivery_delayed": "delayed", "email.bounced": "bounced",
  "email.complained": "complained", "email.failed": "failed",
  "email.suppressed": "suppressed" };
export const webhookConfigured = () => Boolean(process.env.RESEND_WEBHOOK_SECRET);

export function verifySignature(raw, headers) {
  const secret = process.env.RESEND_WEBHOOK_SECRET || "";
  const key = Buffer.from(secret.replace(/^whsec_/, ""), "base64");
  const id = headers["svix-id"], ts = headers["svix-timestamp"], sigHeader = headers["svix-signature"];
  if (!id || !ts || !sigHeader) return false;
  if (Math.abs(Date.now() / 1000 - Number(ts)) > 300) return false; // 5-minute tolerance
  const expected = crypto.createHmac("sha256", key).update(`${id}.${ts}.${raw}`).digest("base64");
  return String(sigHeader).split(" ").some((part) => {
    const [version, sig] = part.split(",");
    if (version !== "v1" || !sig) return false;
    const a = Buffer.from(sig), b = Buffer.from(expected);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  });
}

export function applyWebhook(raw, headers) {
  if (!verifySignature(raw, headers)) return { ok: false, reason: "bad signature" };
  let event; try { event = JSON.parse(raw); } catch { return { ok: false, reason: "bad json" }; }
  const log = load("comms-log.json");
  log.webhookSeen = log.webhookSeen || [];
  const svixId = headers["svix-id"];
  if (log.webhookSeen.includes(svixId)) return { ok: true, deduped: true };
  log.webhookSeen = [...log.webhookSeen.slice(-499), svixId];
  const status = STATUS[event.type];
  const entry = event.data?.email_id && log.sends.find((s) => s.providerId === event.data.email_id);
  if (entry && status) {
    entry.delivery = entry.delivery || { status: "sent", events: [] };
    entry.delivery.status = status;
    entry.delivery.updatedAt = event.created_at || new Date().toISOString();
    entry.delivery.events.push({ type: event.type, at: event.created_at || new Date().toISOString() });
    if (event.type === "email.bounced" && event.data?.bounce) entry.delivery.bounce = event.data.bounce;
  }
  save("comms-log.json", log);
  return { ok: true, applied: Boolean(entry && status) };
}
