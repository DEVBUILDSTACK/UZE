// The comms desk's sending arm. Every comms entry is first written
// to the log as "queued" (lib/store.mjs commsSend — the per-developer
// record). When RESEND_API_KEY is present, sends fire at the moment
// of the event that created them, by two paths:
//   (1) OTP codes send SYNCHRONOUSLY — sendEntryNow() is awaited
//       inside the request-code handler, so the attempt and its
//       outcome are persisted before the response returns; the
//       general queue can never starve a sign-in code.
//   (2) Everything else goes through drainComms() (the server drains
//       after every POST): the log is deduped first (the DB
//       write-through stores one row per state an entry passes
//       through, so hydration can load stale "queued" snapshots of
//       entries that later sent — latest state wins), OTP entries
//       go first, then oldest-first, and ATTEMPTS are capped per
//       drain so a run of failures cannot burn the whole function
//       budget the way the old successes-only cap allowed (the
//       2026-11-18/19 production starvation: stale snapshots × the
//       8s fetch timeout vs the 30s function limit, the invocation
//       killed mid-drain before save(), OTPs at the tail of the
//       queue never attempted).
// Without the key the queue simply holds — nothing is ever silently
// dropped, and the log always shows what actually went out. Every
// failure records the mail API's HTTP status and a truncated
// response body (or a distinctly-worded timeout) in lastError.
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
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load, save } from "./store.mjs";
import { HUMAN_SURFACE_PNG_B64, AGENTIC_SURFACE_PNG_B64 } from "./diagram-images.mjs";
import { DIAGRAMS_JONATHAN_MD, DIAGRAMS_OWNERS_MD, DIAGRAMS_FULL_MD } from "./eco-content.mjs";

const APP_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");

const API_URL = () => process.env.RESEND_API_URL || "https://api.resend.com/emails";
const FROM = () => process.env.LIBRARY_FROM || "UZE Dev Library <desk@uzemarkets.com>";
// UZE Buildr Team sends (entries with app "eco") carry the Buildr
// Team sender name on the same desk@ address, the same key, and the
// same sending discipline — only the name and the home link differ.
const ECO_FROM = () => process.env.ECO_FROM || "UZE Buildr Team <desk@uzemarkets.com>";
const LIBRARY_URL = "https://dev.uzemarkets.com";
const ECO_URL = "https://buildr-eco.uzemarkets.com";
export const mailConfigured = () => Boolean(process.env.RESEND_API_KEY);

const GREETING = { otp: "Hello,", invitation: "Dear Development Partner,",
  "source-grant": "Dear Development Partner,", "change-notice": "Dear Development Partner,",
  revocation: "Dear Development Partner,",
  "eco-otp": "Hello,", "eco-invitation": "Hello,", invitation_dual: "Hello," };
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
  // The greeting resolution is the SAME as renderHtml's — an
  // entry's greetingText (Hello "First Name", or an explicit
  // greeting) governs both parts. (The dashboard caught the text
  // part greeting bare "Hello," on the Bruno proof, 2026-11-19.)
  // A personal sign-off name (James, 2026-11-19 — e.g. "James Sr."
  // on principal/owner letters) sits below the body and above the
  // desk signature.
  const signoff = entry.signoffName ? `${entry.signoffName}\n\n` : "";
  return `${entry.greetingText || GREETING[entry.kind] || "Hello,"}\n\n${entry.body}\n\n${CTA_TEXT}\n\n${signoff}${SIGN_OFF}\n${entry.siteUrl || LIBRARY_URL}\n\nUZEmarkets`;
}

// Naming rule (James, 2026-11-18; completed 2026-11-19): the term
// "reading room" is RETIRED from all writing and email, ecosystem-
// wide — the surface is the UZE Dev Library, full stop. It survives
// only as a code identifier (the readingRoom field, the grant
// route), never in copy. No headline rides the desk emails; the
// copy opens with the greeting.
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
  "eco-otp": "Your UZE Buildr Team sign-in code — it expires in 15 minutes.",
  "eco-invitation": "Your access to the UZE Buildr Team is ready — enter with a one-time code.",
  invitation_dual: "Start with the ecosystem — then step into the UZE Dev Partner Library.",
};
const HERO_URL = "https://dev.uzemarkets.com/hero.gif";
const HERO_ALT = "The UZE Dev Library — design mocks, interface cards and working notes laid out for review";
const STYLE_BLOCK = `<style>
:root{color-scheme:light dark}
@media only screen and (max-width:620px){.em-card{width:100%!important}.em-pad{padding-left:20px!important;padding-right:20px!important}}
.em-brow a{color:#6b655e;text-decoration:none}
.em-brow a:hover{color:#1a1a1a;text-decoration:underline}
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
.em-brow a{color:#b3aa9d}
}
</style>`;
const LINK = (href, label, color = "#ff6b00") =>
  `<a href="${href}" style="color:${color};font-weight:700;text-decoration:underline">${label}</a>`;

export function renderHtml(entry) {
  const desk = entry.kind !== "otp" && entry.kind !== "eco-otp";
  const SITE = entry.siteUrl || LIBRARY_URL;
  const SITEL = entry.siteLabel || "dev.uzemarkets.com";
  const greeting = entry.greetingText || GREETING[entry.kind] || "Hello,";
  const preheader = entry.preheader || PREHEADER[entry.kind] || "";
  const code = (entry.kind === "otp" || entry.kind === "eco-otp") && entry.body.match(/is (\d{6})\./)?.[1];
  const pText = (inner) => `<p class="em-text" style="margin:0 0 16px;font-size:16px;line-height:1.65;color:#1a1a1a">${inner}</p>`;
  // Bare URLs in a body render as house links (letters carry links
  // in prose — an advisor's mock-up link above all). Escape first,
  // then linkify; the plain-text part keeps the raw URL.
  const linkify = (s) => s.replace(/(https:\/\/[^\s<]+)/g,
    (u) => `<a href="${u}" style="color:#ff6b00;font-weight:700;text-decoration:underline">${u}</a>`);
  const paras = esc(entry.body).split(/\n+/).filter(Boolean).map((p) => pText(linkify(p))).join("");
  const headline = desk && HEADLINE[entry.kind]
    ? `<h1 class="em-head" style="margin:0 0 18px;font-family:${SERIF};font-size:29px;line-height:1.2;font-weight:700;color:#1a1a1a">${HEADLINE[entry.kind]}</h1>` : "";
  const codeBlock = code ? `<div class="em-code" style="text-align:center;margin:22px 0;padding:20px;background-color:#f5f2ee;border:1px solid #ddd5c9;border-radius:10px"><span class="em-code-num" style="font-size:34px;font-weight:800;letter-spacing:8px;color:#1a1a1a">${code}</span></div>` : "";
  const pillCta = (href, label, sub) =>
    `<div style="text-align:center;margin:26px 0 8px"><a href="${href}" style="display:inline-block;background-color:#1a1a1a;color:#ffffff;text-decoration:none;font-weight:700;font-size:16px;padding:14px 34px;border-radius:999px">${label}</a></div>
    <p class="em-muted" style="text-align:center;margin:0 0 6px;font-size:13px;color:#6b655e">${sub}</p>`;
  const factLine = (inner) =>
    `<p class="em-text" style="margin:0 0 10px;font-size:14px;line-height:1.6;color:#1a1a1a"><span style="color:#ff6b00;font-weight:800">—</span>&nbsp; ${inner}</p>`;
  const factsWrap = (lines) =>
    `<div class="em-facts" style="border-top:1px solid #ddd5c9;padding:20px 2px 4px;margin:26px 0 2px">${lines}</div>`;
  const cta = entry.kind === "invitation"
    ? pillCta(LIBRARY_URL, "Enter the Dev Library", `or go straight to ${LINK(LIBRARY_URL, "dev.uzemarkets.com")}`)
    : entry.kind === "eco-invitation"
    ? pillCta(ECO_URL, "Enter the Buildr Team", `or go straight to ${LINK(ECO_URL, "buildr-eco.uzemarkets.com")}`)
    : entry.kind === "invitation_dual"
    ? pillCta(ECO_URL, "Start with the ecosystem", `start at ${LINK(ECO_URL, "buildr-eco.uzemarkets.com")} — then step into ${LINK(LIBRARY_URL, "dev.uzemarkets.com")}`)
    : "";
  const facts = entry.kind === "invitation"
    ? factsWrap(
      factLine(`The catalogue is organised by <strong>topic, date and repository</strong>`) +
      factLine(`<strong>Comment and suggest</strong> on anything you read, ahead of any source access`) +
      `<p class="em-text" style="margin:0;font-size:14px;line-height:1.6;color:#1a1a1a"><span style="color:#ff6b00;font-weight:800">—</span>&nbsp; Sign-in is by an <strong>OTP, one-time code</strong> sent to your email — no password to keep</p>`)
    : entry.kind === "eco-invitation"
    ? factsWrap(
      factLine(`The <strong>whole ecosystem</strong> is here: both design surfaces, the pillars, the architecture`) +
      factLine(`You see the <strong>sections your role carries</strong> — the Ecosystem level is open to every contributor`) +
      `<p class="em-text" style="margin:0;font-size:14px;line-height:1.6;color:#1a1a1a"><span style="color:#ff6b00;font-weight:800">—</span>&nbsp; Sign-in is by an <strong>OTP, one-time code</strong> sent to your email — no password to keep, no GitHub account needed</p>`)
    : entry.kind === "invitation_dual"
    ? factsWrap(
      factLine(`<strong>1 — UZE Buildr Team:</strong> start here. The whole ecosystem, both design surfaces, the pillars — ${LINK(ECO_URL, "buildr-eco.uzemarkets.com")}`) +
      `<p class="em-text" style="margin:0;font-size:14px;line-height:1.6;color:#1a1a1a"><span style="color:#ff6b00;font-weight:800">—</span>&nbsp; <strong>2 — UZE Dev Partner Library:</strong> then step into the library, where the work itself lives — ${LINK(LIBRARY_URL, "dev.uzemarkets.com")}</p>`)
    : "";
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
      ${entry.signoffName ? `<p class="em-text" style="margin:0 0 14px;color:#1a1a1a">${esc(entry.signoffName)}</p>` : ""}
      <p class="em-text" style="margin:0 0 2px;color:#1a1a1a">Warm regards,</p>
      <p class="em-text" style="margin:0;font-weight:700;color:#1a1a1a">The UZE Markets Desk</p>
      <p class="em-muted" style="margin:0;color:#6b655e;font-size:13px">Global Support &amp; Contact · ${LINK("mailto:desk@uzemarkets.com", "desk@uzemarkets.com")}</p>
    </div>
    <div style="margin-top:28px">
      <div style="font-size:22px;font-weight:800;letter-spacing:-0.2px"><span style="color:#ff6b00">UZE</span><span class="em-text" style="color:#1a1a1a">markets</span></div>
      <div class="em-muted em-brow" style="font-size:10px;letter-spacing:1px;color:#6b655e;margin-top:2px;white-space:nowrap">${entry.footerEyebrowHtml ? entry.footerEyebrowHtml : entry.footerEyebrow ? esc(entry.footerEyebrow) : `<a href="https://uzemarkets.com" style="color:#6b655e;text-decoration:none">THE TALENT DESK</a> · <a href="https://dev.uzemarkets.com" style="color:#6b655e;text-decoration:none">DEV LIBRARY</a> · <a href="https://buildr-eco.uzemarkets.com" style="color:#6b655e;text-decoration:none">BUILDER COLLABORATOR</a>`}</div>
    </div>`
    : `<div class="em-div" style="border-top:1px solid #ddd5c9;margin-top:24px;padding-top:14px">
      <p class="em-muted" style="margin:0;color:#6b655e;font-size:13px">The UZE Markets Desk · ${LINK("mailto:desk@uzemarkets.com", "desk@uzemarkets.com")}</p>
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
<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
<td style="padding-right:14px;vertical-align:middle"><img src="https://dev.uzemarkets.com/swoop.png" width="29" height="34" alt="UZEmarkets Tri-Swoop" style="display:block;border:0" /></td>
<td style="vertical-align:middle">
<div style="font-size:21px;font-weight:800;letter-spacing:-0.2px"><span style="color:#ff6b00">UZE</span><span style="color:#ffffff">markets</span></div>
<div style="font-size:10px;letter-spacing:2.5px;color:#b8b0a4;margin-top:3px">${esc(entry.bandLabel || "DEV LIBRARY")}</div>
</td>
</tr></table>
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

export const SEND_TIMEOUT_MS = 8000;
const truncate = (s, n = 300) => { s = String(s ?? ""); return s.length > n ? s.slice(0, n) + "…" : s; };

// The recorded text of a failed send. A timeout/abort is recorded
// distinctly — a bare "the operation was aborted" is not evidence:
// the next reader must be able to tell a slow API from a refused one.
function sendErrorText(e) {
  if (e && (e.name === "TimeoutError" || e.name === "AbortError"))
    return `timeout: no response from the mail API within ${SEND_TIMEOUT_MS}ms (fetch aborted)`;
  return String((e && e.message) || e);
}

export async function sendMail(entry) {
  // Copy rule (James, 2026-11-19): every send copies the house —
  // and a LIVE send to an external individual copies the shared
  // agent mailbox giraxnautilo@gmail.com instead of the founder's
  // Gmail, so the proof of sending is readable by both the founder
  // and the desk. entry.live marks a live external send.
  // Sender rule (James, 2026-11-19): mail to a PRINCIPAL or an
  // OWNER is sent from uze@uzemarkets.com and its replies return
  // to uze@ — an entry carries fromEmail/fromName/replyTo to say
  // so; the desk signature block still shows the desk contact.
  const from = entry.fromEmail ? (entry.fromName ? `${entry.fromName} <${entry.fromEmail}>` : entry.fromEmail)
    : entry.app === "eco" ? ECO_FROM() : FROM();
  const payload = { from, to: [entry.to], bcc: [entry.live ? "giraxnautilo@gmail.com" : "jsondealzapp@gmail.com"], subject: entry.subject,
    text: renderText(entry), html: renderHtml(entry),
    tags: [{ name: "app", value: entry.app === "eco" ? "eco" : "dev-library" }, { name: "kind", value: entry.kind }] };
  if (entry.replyTo) payload.reply_to = entry.replyTo;
  // Attachments (James, 2026-11-19): an entry may carry attachment
  // descriptors ({ filename, file } — file is app-relative; the
  // content ships with the app). The mailer resolves them at send
  // time and sends base64 content per the Resend API. A missing
  // file fails the send loudly (recorded in lastError) — an
  // invitation never goes out silently missing its diagrams.
  if (entry.attachments?.length) {
    payload.attachments = entry.attachments.map(a => ({
      filename: a.filename,
      // A "diagram:" token names one of the design-surface
      // pictures carried as data in lib/diagram-images.mjs (they
      // are never loose files — see that module); anything else
      // is an app-relative file read at send time.
      content: a.file === "diagram:human" ? HUMAN_SURFACE_PNG_B64.replace(/\s/g, "")
        : a.file === "diagram:agentic" ? AGENTIC_SURFACE_PNG_B64.replace(/\s/g, "")
        : a.file === "diagram-md:jonathan" ? Buffer.from(DIAGRAMS_JONATHAN_MD, "utf8").toString("base64")
        : a.file === "diagram-md:owners" ? Buffer.from(DIAGRAMS_OWNERS_MD, "utf8").toString("base64")
        : a.file === "diagram-md:full" ? Buffer.from(DIAGRAMS_FULL_MD, "utf8").toString("base64")
        : fs.readFileSync(path.join(APP_ROOT, a.file)).toString("base64"),
    }));
  }
  const r = await fetch(API_URL(), {
    method: "POST",
    // Resend dev-docs findings (deep dive 2026-11-18): a raw-API call
    // MUST set User-Agent or the API returns 403 (error 1010) despite a
    // valid key; Idempotency-Key (24h) makes serverless retries safe;
    // tags are the metadata channel (echoed back in webhooks).
    headers: { authorization: `Bearer ${process.env.RESEND_API_KEY}`, "content-type": "application/json",
      "user-agent": "uze-dev-library/1.0", "idempotency-key": `comms/${entry.id}` },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(SEND_TIMEOUT_MS),
  });
  const raw = await r.text().catch(() => "");
  let data = {}; try { data = JSON.parse(raw); } catch { /* body kept raw for the error text */ }
  // Diagnosability: a refusal carries the HTTP status AND the body —
  // the status alone (or worse, "timeout") is not acceptable evidence.
  if (!r.ok) throw new Error(`mail API ${r.status}: ${truncate(data.message || data.name || raw || "send failed")}`);
  return data.id || null;
}

// Attempt one entry's send, mutating the entry with the outcome.
// Returns true when the entry was sent. The caller persists.
async function attemptSend(entry) {
  try {
    entry.providerId = await sendMail(entry);
    entry.status = "sent";
    entry.sentAt = new Date().toISOString();
    delete entry.lastError;
    return true;
  } catch (e) {
    entry.attempts = (entry.attempts || 0) + 1;
    entry.lastAttemptAt = new Date().toISOString();
    entry.lastError = sendErrorText(e);
    return false;
  }
}

// The log can hold the same entry more than once: the DB
// write-through (lib/store-pg.mjs) stores one comms_send row per
// state an entry passes through — its dedupe key is the whole entry
// JSON — and hydration loads every snapshot back. Latest state
// wins: the last row for an id is the entry's current truth, and a
// stale "queued" snapshot of an entry that later sent must never
// be sent again. Result is in creation order.
export function dedupeSends(sends) {
  const byId = new Map();
  for (const s of sends) byId.set(s.id, s);
  return [...byId.values()].sort((a, b) => String(a.at).localeCompare(String(b.at)));
}

// Send one queued entry NOW, by id, persisting the outcome before
// returning. The OTP path uses this (server.mjs awaits it inside
// the request-code handler): a sign-in code is attempted inside the
// request that created it, so the general queue can never starve
// it. Returns the entry, or null when unconfigured/unknown.
export async function sendEntryNow(id) {
  if (!mailConfigured()) return null;
  const log = load("comms-log.json");
  const deduped = dedupeSends(log.sends);
  const healed = deduped.length !== log.sends.length;
  log.sends = deduped;
  const entry = log.sends.find((s) => s.id === id);
  if (!entry) { if (healed) save("comms-log.json", log); return null; }
  if (entry.status === "queued") { await attemptSend(entry); save("comms-log.json", log); }
  else if (healed) save("comms-log.json", log);
  return entry;
}

// Drain the queue: dedupe first (latest state wins), then attempt
// at most `maxAttempts` sends — OTP entries first (a sign-in code
// is worthless in 15 minutes), the rest oldest-first. ATTEMPTS are
// capped, not successes: the old successes-only cap let a clogged
// queue of failing stale entries burn the entire invocation budget
// (8s per timeout against a 30s function limit) and the invocation
// died before save(), losing even the attempt bookkeeping. The log
// is therefore also persisted after EVERY attempt: if the platform
// kills an invocation mid-drain, the attempts already made are on
// record and the next drain resumes where this one stopped. A
// failed send stays queued with the attempt recorded — the next
// drain retries it. `excludeIds` skips entries already attempted
// inside the current request (the synchronous OTP send).
export async function drainComms({ maxAttempts = 10, excludeIds = new Set() } = {}) {
  if (!mailConfigured()) return { configured: false, sent: 0, attempted: 0 };
  const log = load("comms-log.json");
  const deduped = dedupeSends(log.sends);
  const healed = deduped.length !== log.sends.length;
  log.sends = deduped;
  if (healed) save("comms-log.json", log); // the heal persists even if nothing is attempted
  const otpFirst = (e) => (e.kind === "otp" || e.kind === "eco-otp") ? 0 : 1;
  const queued = log.sends
    .filter((e) => e.status === "queued" && !excludeIds.has(e.id))
    .sort((a, b) => otpFirst(a) - otpFirst(b)
      || String(a.at).localeCompare(String(b.at)));
  let sent = 0, attempted = 0;
  for (const entry of queued) {
    if (attempted >= maxAttempts) break;
    attempted++;
    if (await attemptSend(entry)) sent++;
    save("comms-log.json", log);
  }
  return { configured: true, sent, attempted };
}
