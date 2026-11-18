// The comms desk's sending arm. Every comms entry is first written
// to the log as "queued" (lib/store.mjs commsSend — the per-developer
// record). When RESEND_API_KEY is present, drainComms() sends each
// queued entry at the moment of the event that created it (the server
// drains after every POST) and marks it "sent" with the provider id.
// Without the key the queue simply holds — nothing is ever silently
// dropped, and the log always shows what actually went out.
//
// Sender identity is desk@uzemarkets.com (James, 2026-11-18: the
// mailbox is live and operational on his iCloud+ domain; the app
// sends as desk@ through the Resend service verified on the domain).
// Trigger definition (SoSem, per James's direction 2026-11-18): a
// send fires at the event — (1) sign-in code requested -> the code,
// (2) reading-room grant -> invitation, (3) access change /
// reset-to-zero -> notice, (4) GitHub source grant -> notice.
import { load, save } from "./store.mjs";

const API_URL = () => process.env.RESEND_API_URL || "https://api.resend.com/emails";
const FROM = () => process.env.LIBRARY_FROM || "UZE Dev Library <desk@uzemarkets.com>";
export const mailConfigured = () => Boolean(process.env.RESEND_API_KEY);

export async function sendMail({ to, subject, body }) {
  const r = await fetch(API_URL(), {
    method: "POST",
    headers: { authorization: `Bearer ${process.env.RESEND_API_KEY}`, "content-type": "application/json" },
    body: JSON.stringify({ from: FROM(), to: [to], subject, text: body }),
    signal: AbortSignal.timeout(8000),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`mail API ${r.status}: ${data.message || data.name || "send failed"}`);
  return data.id || null;
}

// Send every queued comms entry, oldest first. A failed send stays
// queued with the attempt recorded — the next drain retries it.
export async function drainComms(max = 20) {
  if (!mailConfigured()) return { configured: false, sent: 0 };
  const log = load("comms-log.json");
  let sent = 0, changed = false;
  for (const entry of log.sends) {
    if (sent >= max) break;
    if (entry.status !== "queued") continue;
    try {
      entry.providerId = await sendMail(entry);
      entry.status = "sent";
      entry.sentAt = new Date().toISOString();
      sent++;
    } catch (e) {
      entry.attempts = (entry.attempts || 0) + 1;
      entry.lastError = String(e.message || e);
    }
    changed = true;
  }
  if (changed) save("comms-log.json", log);
  return { configured: true, sent };
}
