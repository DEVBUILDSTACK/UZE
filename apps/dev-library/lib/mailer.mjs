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

// Naming rule (James, 2026-11-18): "the reading room" is internal
// language only — it never appears in external copy. External name
// is the UZE Dev Library, full stop. No headline rides the desk
// emails; the copy opens with the greeting.
const HEADLINE = {};
const SANS = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";
const SERIF = "Georgia,'Times New Roman',serif";

// Design system v3 (2026-11-18, built to the Resend/React Email
// research spec in ~/workspace/research_notes/
// resend-email-design-innovation-20261118-2210/report.md):
// table layout (role="presentation"), CSS fully inlined, live text
// only, deliberate preheader per kind (<90 chars), lang/dir set, and
// a dark-mode pack authored for Apple Mail ONLY (color-scheme metas
// + one <style> block whose prefers-color-scheme rules carry
// !important — the documented exception to inlining; Gmail and
// Outlook get the light design, untouched). Total HTML stays far
// under Gmail's ~102KB clip line. Imagery is HOSTED on our own
// domain (never CID): the hero is an animated GIF whose first frame
// is the complete static design — the only motion that survives
// Gmail + Apple Mail. The GIF (assets/hero.gif, 1200x400 shown at
// 600x200, ~353KB) animates one floating card: the card region of
// hero.jpg bobbing ±3px on a 4s sine over the flat-cream wall,
// palette-encoded with transparent delta frames (ffmpeg recipe:
// drawbox-erase + feathered alphamerge patch + overlay eval=frame
// + palettegen reserve_transparent + paletteuse diff_mode=rectangle).
// Standing layout rules (James): CTAs sit directly above the
// signature; the logo sits underneath the signature block; the
// WhatsApp band is the bottom-most element of the card; the OTP
// email stays lean — no hero, no buttons, no banners.
// Lower-half remodel (James, 2026-11-18, Maple Finance design
// language): the top half is locked; from the facts card down, all
// varied colors are removed — black pill buttons (Enter + the CTA
// row), a flat facts list on a hairline, a creamsicle engagement
// banner with a serif headline and ink links, and a black WhatsApp
// band. Tangerine survives only in the wordmark, the facts markers,
// and inline link color — one accent family, disciplined.
const PREHEADER = {
  invitation: "Your seat in the UZE Dev Library is ready — enter with a one-time code.",
  otp: "Your UZE Dev Library sign-in code — it expires in 15 minutes.",
  "source-grant": "Your DEVBUILDSTACK source access is live — details inside.",
  "change-notice": "A change to your Dev Library access — details inside.",
  revocation: "Your Dev Library access has been reset — details inside.",
};
const HERO_URL = "https://dev.uzemarkets.com/hero.gif";
const HERO_ALT = "The UZE Dev Library — design mocks, interface cards and working notes laid out for review";
const STYLE_BLOCK = `<style>
:root{color-scheme:light dark}
@media only screen and (max-width:620px){.em-card{width:100%!important}.em-pad{padding-left:20px!important;padding-right:20px!important}}
@media (prefers-color-scheme:dark){
.em-bg{background-color:#141210!important}
.em-card{background-color:#201c18!important;border-color:#3a352f!important}
.em-text{color:#f2ede6!important}
.em-head{color:#ffffff!important}
.em-muted{color:#b3aa9d!important}
.em-facts{border-top-color:#3a352f!important}
.em-code{background-color:#2a251f!important;border-color:#3a352f!important}
.em-code-num{color:#ffffff!important}
.em-div{border-top-color:#3a352f!important}
}
</style>`;
const LINK = (href, label, color = "#ff6b00") =>
  `<a href="${href}" style="color:${color};font-weight:700;text-decoration:underline">${label}</a>`;

export function renderHtml(entry) {
  const desk = entry.kind !== "otp";
  const greeting = entry.greetingText || GREETING[entry.kind] || "Hello,";
  const preheader = entry.preheader || PREHEADER[entry.kind] || "";
  const code = entry.kind === "otp" && entry.body.match(/is (\d{6})\./)?.[1];
  const pText = (inner) => `<p class="em-text" style="margin:0 0 16px;font-size:16px;line-height:1.65;color:#1a1a1a">${inner}</p>`;
  const paras = esc(entry.body).split(/\n+/).filter(Boolean).map(pText).join("");
  const headline = desk && HEADLINE[entry.kind]
    ? `<h1 class="em-head" style="margin:0 0 18px;font-family:${SERIF};font-size:29px;line-height:1.2;font-weight:700;color:#1a1a1a">${HEADLINE[entry.kind]}</h1>` : "";
  const codeBlock = code ? `<div class="em-code" style="text-align:center;margin:22px 0;padding:20px;background-color:#f5f2ee;border:1px solid #ddd5c9;border-radius:10px"><span class="em-code-num" style="font-size:34px;font-weight:800;letter-spacing:8px;color:#1a1a1a">${code}</span></div>` : "";
  const cta = entry.kind === "invitation"
    ? `<div style="text-align:center;margin:26px 0 8px"><a href="${LIBRARY_URL}" style="display:inline-block;background-color:#1a1a1a;color:#ffffff;text-decoration:none;font-weight:700;font-size:16px;padding:14px 34px;border-radius:999px">Enter the Dev Library</a></div>
    <p class="em-muted" style="text-align:center;margin:0 0 6px;font-size:13px;color:#6b655e">or go straight to ${LINK(LIBRARY_URL, "dev.uzemarkets.com")}</p>` : "";
  const facts = entry.kind === "invitation"
    ? `<div class="em-facts" style="border-top:1px solid #ddd5c9;padding:20px 2px 4px;margin:26px 0 2px">
      <p class="em-text" style="margin:0 0 10px;font-size:14px;line-height:1.6;color:#1a1a1a"><span style="color:#ff6b00;font-weight:800">—</span>&nbsp; The catalogue is organised by <strong>topic, date and repository</strong></p>
      <p class="em-text" style="margin:0 0 10px;font-size:14px;line-height:1.6;color:#1a1a1a"><span style="color:#ff6b00;font-weight:800">—</span>&nbsp; <strong>Comment and suggest</strong> on anything you read, ahead of any source access</p>
      <p class="em-text" style="margin:0;font-size:14px;line-height:1.6;color:#1a1a1a"><span style="color:#ff6b00;font-weight:800">—</span>&nbsp; Sign-in is by an <strong>OTP, one-time code</strong> sent to your email — no password to keep</p>
    </div>` : "";
  // The social-engagement banner (James, 2026-11-18; remodelled the
  // same day in the Maple Finance design language): a creamsicle
  // block, ink text, a serif headline — X and the podcast, with the
  // share ask. A send may carry its own lines (entry.bannerLines,
  // plain text) — outreach copy varies; the desk default is below.
  const bannerLines = entry.bannerLines
    ? entry.bannerLines.map((l, i) => `<p style="margin:${i ? "5px" : "10px"} 0 0;color:#1a1a1a;font-size:14px;line-height:1.55">${esc(l)}</p>`).join("")
    : `<p style="margin:10px 0 0;color:#1a1a1a;font-size:14px;line-height:1.55">${LINK("https://x.com/UZEmarkets_fyi", "Follow us on X", "#1a1a1a")}, like, and post your take.</p>
      <p style="margin:5px 0 0;color:#1a1a1a;font-size:14px;line-height:1.55">Hear the week on ${LINK("https://podcast.uzemarkets.com", "the podcast", "#1a1a1a")} — and share the weekly edition.</p>`;
  const banner = desk
    ? `<div style="margin-top:26px;background-color:#FDEEE2;border-radius:12px;padding:26px 24px;text-align:center">
      <div style="font-family:${SERIF};font-size:21px;line-height:1.25;color:#1a1a1a">Join the conversation</div>${bannerLines}
    </div>` : "";
  // The button row — the house CTAs as unmissable pills, sitting
  // directly above the signature, share line beneath them.
  const pill = (href, label, bg) =>
    `<td bgcolor="${bg}" style="background-color:${bg};border-radius:999px"><a href="${href}" style="display:inline-block;padding:10px 18px;color:#ffffff;font-weight:700;font-size:14px;text-decoration:none;white-space:nowrap">${label}</a></td>`;
  const buttonRow = desk
    ? `<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" style="margin:22px auto 0">
      <tr>${pill("https://x.com/UZEmarkets_fyi", "Follow us on X", "#1a1a1a")}<td width="8"></td>${pill("https://instagram.com/uzemarkets", "Instagram", "#1a1a1a")}<td width="8"></td>${pill("https://podcast.uzemarkets.com", "Listen to the podcast", "#1a1a1a")}</tr>
    </table>
    <p class="em-muted" style="text-align:center;margin:10px 0 0;font-size:13px;color:#6b655e;line-height:1.5">Share the weekly edition, and leave us feedback or a kind word on those channels. Our affiliate WhatsApp group opens soon.</p>` : "";
  const signature = desk
    ? `<div style="margin-top:28px">
      <p class="em-text" style="margin:0 0 2px;color:#1a1a1a">Warm regards,</p>
      <p class="em-text" style="margin:0;font-weight:700;color:#1a1a1a">The UZE Markets Desk</p>
      <p class="em-muted" style="margin:0;color:#6b655e;font-size:13px">Global Support &amp; Contact · ${LINK("mailto:desk@uzemarkets.com", "desk@uzemarkets.com")} · ${LINK(LIBRARY_URL, "dev.uzemarkets.com")}</p>
    </div>
    <div style="margin-top:28px">
      <div style="font-size:22px;font-weight:800;letter-spacing:-0.2px"><span style="color:#ff6b00">UZE</span><span class="em-text" style="color:#1a1a1a">markets</span></div>
      <div class="em-muted" style="font-size:11px;letter-spacing:2.5px;color:#6b655e;margin-top:2px">${esc(entry.footerEyebrow || "THE TALENT DESK · DEV LIBRARY")}</div>
    </div>`
    : `<div class="em-div" style="border-top:1px solid #ddd5c9;margin-top:24px;padding-top:14px">
      <p class="em-muted" style="margin:0;color:#6b655e;font-size:13px">The UZE Markets Desk · ${LINK("mailto:desk@uzemarkets.com", "desk@uzemarkets.com")} · ${LINK(LIBRARY_URL, "dev.uzemarkets.com")}</p>
    </div>`;
  const heroRow = desk
    ? `<tr><td style="padding:0;font-size:0;line-height:0"><img src="${HERO_URL}" width="600" height="200" alt="${HERO_ALT}" style="display:block;width:100%;max-width:600px;height:auto;border:0" /></td></tr>` : "";
  // The WhatsApp band — bottom-most element of the card (James,
  // 2026-11-18), black in the Maple-language remodel (the green is
  // gone). The affiliate group does not exist yet (Meta gate,
  // Dec 2), so the band links to the house site — never an invented
  // group invite.
  const whatsappRow = desk
    ? `<tr><td bgcolor="#1a1a1a" style="background-color:#1a1a1a;border-bottom-left-radius:14px;border-bottom-right-radius:14px;padding:20px 34px;text-align:center">
      <p style="margin:0;font-size:16px;font-weight:800;color:#ffffff">Join us on WhatsApp</p>
      <p style="margin:5px 0 0;font-size:13px;line-height:1.55;color:#ffffff">Our affiliate WhatsApp group opens soon — start at ${LINK("https://uzemarkets.com", "uzemarkets.com", "#ffffff")}</p>
    </td></tr>` : "";
  return `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" dir="ltr">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="color-scheme" content="light dark" />
<meta name="supported-color-schemes" content="light dark" />
<title>${esc(entry.subject || "UZE Dev Library")}</title>
${STYLE_BLOCK}
</head>
<body style="margin:0;padding:0;background-color:#f5f2ee;font-family:${SANS}">
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all">${esc(preheader)}</div>
<table role="presentation" class="em-bg" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f5f2ee" style="background-color:#f5f2ee;font-family:${SANS}">
<tr><td align="center" style="padding:28px 12px">
<table role="presentation" class="em-card" width="600" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="border-collapse:separate;width:600px;max-width:600px;background-color:#ffffff;border:1px solid #ddd5c9;border-radius:14px">
<tr><td bgcolor="#1a1a1a" style="background-color:#1a1a1a;border-top-left-radius:14px;border-top-right-radius:14px;padding:20px 34px">
<div style="font-size:21px;font-weight:800;letter-spacing:-0.2px"><span style="color:#ff6b00">UZE</span><span style="color:#ffffff">markets</span></div>
<div style="font-size:10px;letter-spacing:2.5px;color:#b8b0a4;margin-top:3px">DEV LIBRARY</div>
</td></tr>
${heroRow}
<tr><td class="em-pad" style="padding:28px 34px 24px">
${headline}${pText(esc(greeting))}
${paras}${codeBlock}${cta}${facts}${desk ? `<div class="em-div" style="border-top:1px solid #ddd5c9;margin-top:24px"></div>${banner}${buttonRow}` : ""}${signature}
</td></tr>
${whatsappRow}
</table>
<p style="text-align:center;color:#6b655e;font-size:12px;margin:16px 0 0">© 2026 <a href="https://uzemarkets.com" style="color:#ff6b00;font-weight:700;text-decoration:underline">UZE</a>markets</p>
</td></tr>
</table>
</body>
</html>`;
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
