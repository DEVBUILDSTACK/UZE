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
//
// Branding (James, 2026-11-18): every send is a branded UZEmarkets
// email — tangerine/cream/ink, a proper greeting ("Dear Development
// Partner," for desk correspondence; "Hello," for the code), the
// library link, and the desk's signature (Global Support & Contact).
// Founders WCD and D5 get their own signature blocks, titled
// "Founder", when they join the domain — the desk signature below is
// the standing default until then.
import { load, save } from "./store.mjs";

const API_URL = () => process.env.RESEND_API_URL || "https://api.resend.com/emails";
const FROM = () => process.env.LIBRARY_FROM || "UZE Dev Library <desk@uzemarkets.com>";
const LIBRARY_URL = "https://dev.uzemarkets.com";
export const mailConfigured = () => Boolean(process.env.RESEND_API_KEY);

const GREETING = { otp: "Hello,", invitation: "Dear Development Partner,",
  "source-grant": "Dear Development Partner,", "change-notice": "Dear Development Partner,",
  revocation: "Dear Development Partner," };
const SIGN_OFF = "Warm regards,\nThe UZE Markets Desk\nGlobal Support & Contact · desk@uzemarkets.com";
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// The house calls to action — the site's current links (James,
// 2026-11-18): they sit succinctly right above the signature on every
// branded send, and the logo goes underneath them. The affiliate
// WhatsApp group joins this block once it exists (Meta gate, Dec 2).
const CTA_LINKS = [
  ["Follow us on X", "https://x.com/UZEmarkets_fyi"],
  ["Instagram", "https://instagram.com/uzemarkets"],
  ["Listen to the podcast", "https://podcast.uzemarkets.com"],
];
const CTA_TEXT = `Stay close — ${CTA_LINKS.map(([label, url]) => `${label}: ${url}`).join(" · ")}
Share the weekly edition, and leave us feedback or a kind word on those channels. Our affiliate WhatsApp group opens soon.`;

export function renderText(entry) {
  return `${GREETING[entry.kind] || "Hello,"}\n\n${entry.body}\n\n${CTA_TEXT}\n\n${SIGN_OFF}\n${LIBRARY_URL}\n\nUZEmarkets`;
}

export function renderHtml(entry) {
  const greeting = GREETING[entry.kind] || "Hello,";
  const code = entry.kind === "otp" && entry.body.match(/is (\d{6})\./)?.[1];
  const paras = esc(entry.body).split(/\n+/).filter(Boolean)
    .map((p) => `<p style="margin:0 0 14px;line-height:1.55;color:#1a1a1a">${p}</p>`).join("");
  const codeBlock = code ? `<div style="text-align:center;margin:22px 0;padding:18px;background:#f5f2ee;border:1px solid #ddd5c9;border-radius:10px"><span style="font-size:32px;font-weight:800;letter-spacing:8px;color:#1a1a1a">${code}</span></div>` : "";
  const cta = entry.kind === "invitation"
    ? `<div style="text-align:center;margin:22px 0"><a href="${LIBRARY_URL}" style="display:inline-block;background:#ff6b00;color:#ffffff;text-decoration:none;font-weight:700;padding:12px 26px;border-radius:999px">Enter the Dev Library</a></div>` : "";
  const ctaLinks = CTA_LINKS.map(([label, url]) => `<a href="${url}" style="color:#ff6b00;text-decoration:none;font-weight:600">${label}</a>`).join(" &nbsp;·&nbsp; ");
  return `<div style="background:#f5f2ee;padding:28px 12px;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #ddd5c9;border-radius:14px;padding:30px 30px 22px">
    <p style="margin:0 0 14px;line-height:1.55;color:#1a1a1a">${esc(greeting)}</p>
    ${paras}${codeBlock}${cta}
    <div style="border-top:1px solid #ddd5c9;margin-top:24px;padding-top:14px">
      <p style="margin:0 0 4px;font-size:13px;color:#1a1a1a">${ctaLinks}</p>
      <p style="margin:0;font-size:13px;color:#6b655e;line-height:1.5">Share the weekly edition, and leave us feedback or a kind word on those channels. Our affiliate WhatsApp group opens soon.</p>
    </div>
    <div style="margin-top:18px">
      <p style="margin:0 0 2px;color:#1a1a1a">Warm regards,</p>
      <p style="margin:0;font-weight:700;color:#1a1a1a">The UZE Markets Desk</p>
      <p style="margin:0;color:#6b655e;font-size:13px">Global Support &amp; Contact · <a href="mailto:desk@uzemarkets.com" style="color:#ff6b00;text-decoration:none">desk@uzemarkets.com</a> · <a href="${LIBRARY_URL}" style="color:#ff6b00;text-decoration:none">dev.uzemarkets.com</a></p>
    </div>
    <div style="margin-top:22px">
      <div style="font-size:22px;font-weight:800;letter-spacing:-0.2px"><span style="color:#ff6b00">UZE</span><span style="color:#1a1a1a">markets</span></div>
      <div style="font-size:11px;letter-spacing:2.5px;color:#6b655e;margin-top:2px">DEV LIBRARY · THE READING ROOM</div>
    </div>
  </div>
  <p style="text-align:center;color:#6b655e;font-size:12px;margin:16px 0 0">© 2026 <a href="https://uzemarkets.com" style="color:#ff6b00;text-decoration:none">UZE</a>markets</p>
</div>`;
}

export async function sendMail(entry) {
  const r = await fetch(API_URL(), {
    method: "POST",
    // Resend dev-docs findings (deep dive 2026-11-18): a raw-API call
    // MUST set User-Agent or the API returns 403 (error 1010) despite a
    // valid key; Idempotency-Key (24h) makes serverless retries safe;
    // tags are the metadata channel (echoed back in webhooks).
    headers: { authorization: `Bearer ${process.env.RESEND_API_KEY}`, "content-type": "application/json",
      "user-agent": "uze-dev-library/1.0", "idempotency-key": `comms/${entry.id}` },
    body: JSON.stringify({ from: FROM(), to: [entry.to], subject: entry.subject,
      text: renderText(entry), html: renderHtml(entry),
      tags: [{ name: "app", value: "dev-library" }, { name: "kind", value: entry.kind }] }),
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
