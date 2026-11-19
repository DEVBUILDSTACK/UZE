#!/usr/bin/env node
/**
 * UZE design gate — pre-ship verification for UZE-branded pages.
 *
 *   node gate.mjs <page-file-or-local-url> [--out <dir>] [--wordmark <css-selector>]
 *
 * Checks (house system: ~/workspace/custom-skills/uze-design-system/SKILL.md):
 *   1. Palette lint   — every hex color in the page source must be a house token.
 *                       For URL targets the page's same-origin stylesheets are
 *                       fetched and linted too (a served app's palette lives in
 *                       its CSS, not its HTML).
 *   2. Renders        — full-page screenshots at 420px and 1280px, saved beside the report.
 *   3. Wordmark check — the wordmark must render on ONE line at 420px. Default
 *                       target is the header h1; --wordmark names the element
 *                       that carries the wordmark on component-built sites
 *                       (e.g. --wordmark ".wordmark"). The check is the same:
 *                       (a) it must carry white-space:nowrap (house rule §2 — the guarantee),
 *                       (b) measured on the live render it must occupy exactly one line
 *                       (rendered height vs line-height) with no horizontal overflow.
 *                       A missing nowrap, a wrap, or a clip is a failure.
 *   4. Axe floor      — axe-core (local npm package, injected from its local file) runs on
 *                       the 420px render; violations are reported by rule id. Report-only
 *                       for now — see README.md ("Axe status").
 *
 * Exit code: 0 = PASS, 1 = FAIL (palette and/or wordmark), 2 = gate could not run.
 * Local targets only: the sandbox Chrome cannot reach the public internet.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import puppeteer from 'puppeteer-core';

const TOKENS = new Set([
  '#1a1a1a', // ink
  '#f5f2ee', // cream
  '#ff6b00', // tangerine
  '#fdeee2', // creamsicle
  '#ddd5c9', // hairline
  '#6b655e', // muted
  '#b8b0a4', // band-muted
  '#ffffff', // white
]);
const WIDTHS = [420, 1280];

// ---------- args ----------
const args = process.argv.slice(2);
const outFlag = args.indexOf('--out');
const outDirArg = outFlag >= 0 ? args[outFlag + 1] : null;
const wmFlag = args.indexOf('--wordmark');
const wordmarkSelector = wmFlag >= 0 ? args[wmFlag + 1] : null;
const flagValues = new Set([outDirArg, wordmarkSelector].filter(Boolean));
const target = args.find((a) => !a.startsWith('--') && !flagValues.has(a));
if (!target) {
  console.error('usage: node gate.mjs <page-file-or-local-url> [--out <dir>] [--wordmark <css-selector>]');
  process.exit(2);
}

const isUrl = /^https?:\/\//i.test(target);
let pageUrl, sourceText, targetLabel;
if (isUrl) {
  const u = new URL(target);
  if (!/^(localhost|127\.0\.0\.1|\[::1\])$/.test(u.hostname)) {
    console.error(`FAIL: gate renders local targets only (got ${u.hostname}). Serve the page locally first.`);
    process.exit(2);
  }
  pageUrl = target;
  targetLabel = target;
  sourceText = await (await fetch(target)).text();
} else {
  const file = path.resolve(target);
  if (!fs.existsSync(file)) {
    console.error(`FAIL: no such file: ${file}`);
    process.exit(2);
  }
  pageUrl = pathToFileURL(file).href;
  targetLabel = file;
  sourceText = fs.readFileSync(file, 'utf8');
}

const outDir = outDirArg
  ? path.resolve(outDirArg)
  : isUrl
    ? path.resolve('design-gate-out')
    : path.join(path.dirname(path.resolve(target)), `${path.basename(target)}.gate`);
fs.mkdirSync(outDir, { recursive: true });

const failures = [];
const lines = [];
const say = (s = '') => { lines.push(s); console.log(s); };

// ---------- 1. palette lint ----------
// For URL targets, a served app's palette lives in its stylesheets, not its
// HTML — fetch every same-origin stylesheet the page links and lint it too.
// Script contents are excluded from the HTML corpus: a served page's inline
// scripts are framework/runtime payloads (Next.js embeds its own default
// error-page CSS — body{color:#000} — in every page's data payload; that is
// framework boilerplate, not authored design). Authored colors still lint:
// they render through stylesheets, <style> elements, and style attributes,
// all of which stay in the corpus. File targets lint whole — a static
// authored page's scripts are the author's own.
let lintText = sourceText;
let cssCount = 0;
if (isUrl) {
  lintText = sourceText.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
  const base = new URL(target);
  const hrefs = new Set();
  for (const m of sourceText.matchAll(/<link[^>]+rel=["']stylesheet["'][^>]*>/gi)) {
    const h = /href=["']([^"']+)["']/i.exec(m[0]);
    if (h) hrefs.add(h[1]);
  }
  for (const h of hrefs) {
    try {
      const u = new URL(h, base);
      if (u.origin !== base.origin) continue;
      const css = await (await fetch(u)).text();
      lintText += `\n${css}`;
      cssCount += 1;
    } catch { /* an unfetchable sheet is a render problem the screenshots will show */ }
  }
}
say(`DESIGN GATE — ${targetLabel}`);
say('');
if (isUrl) say(`[OK]   palette corpus — page HTML + ${cssCount} same-origin stylesheet(s)`);
const hexRe = /#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b/g;
const normalize = (raw) => {
  let h = raw.slice(1).toLowerCase();
  if (h.length === 3 || h.length === 4) h = h.split('').map((c) => c + c).join('');
  if (h.length === 8) h = h.slice(0, 6); // drop alpha
  return `#${h}`;
};
const seen = new Map(); // normalized -> {count, raws:Set}
let transparentCount = 0;
for (const m of lintText.matchAll(hexRe)) {
  // A fully transparent hex (alpha 00 — e.g. #0000, the minified form of
  // `color: transparent` for gradient-clipped text) renders as no color at
  // all; it is not a hue and is counted separately, never a violation.
  // Semi-transparent colors still lint on their RGB: a black scrim must be
  // an ink scrim.
  let h = m[0].slice(1).toLowerCase();
  if (h.length === 3 || h.length === 4) h = h.split('').map((c) => c + c).join('');
  if (h.length === 8 && h.endsWith('00')) { transparentCount += 1; continue; }
  const n = normalize(m[0]);
  const e = seen.get(n) || { count: 0, raws: new Set() };
  e.count += 1; e.raws.add(m[0]);
  seen.set(n, e);
}
if (transparentCount) say(`[OK]   palette lint — ${transparentCount} fully transparent hex(es) ignored (alpha 00 renders as no color)`);
const offenders = [...seen.entries()].filter(([n]) => !TOKENS.has(n));
if (offenders.length === 0) {
  say(`[PASS] palette lint — ${seen.size} distinct hex value(s), all house tokens`);
} else {
  for (const [n, e] of offenders) {
    const msg = `palette violation: ${n} (as ${[...e.raws].join(', ')}) ×${e.count} — not a house token`;
    failures.push(msg);
    say(`[FAIL] ${msg}`);
  }
}

// ---------- chrome discovery ----------
function findChrome() {
  if (process.env.CHROME_PATH && fs.existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  const cache = path.join(os.homedir(), '.cache', 'puppeteer');
  const candidates = [];
  for (const kind of ['chrome', 'chrome-headless-shell']) {
    const base = path.join(cache, kind);
    if (!fs.existsSync(base)) continue;
    for (const ver of fs.readdirSync(base).sort()) {
      for (const sub of fs.readdirSync(path.join(base, ver))) {
        const bin = path.join(base, ver, sub, kind === 'chrome' ? 'chrome' : 'chrome-headless-shell');
        if (fs.existsSync(bin)) candidates.push({ kind, bin });
      }
    }
  }
  const full = candidates.filter((c) => c.kind === 'chrome');
  const pick = (full.length ? full : candidates).at(-1);
  return pick?.bin;
}
const chromePath = findChrome();
if (!chromePath) {
  console.error('FAIL: no Chrome binary found under ~/.cache/puppeteer (set CHROME_PATH).');
  process.exit(2);
}

// ---------- 2–4. renders, wordmark, axe ----------
const browser = await puppeteer.launch({
  executablePath: chromePath,
  args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars'],
});
try {
  for (const width of WIDTHS) {
    const page = await browser.newPage();
    await page.setViewport({ width, height: 900 });
    await page.goto(pageUrl, { waitUntil: 'load', timeout: 30000 });
    await new Promise((r) => setTimeout(r, 600));
    const shot = path.join(outDir, `screenshot-${width}.png`);
    await page.screenshot({ path: shot, fullPage: true });
    say(`[OK]   render — screenshot-${width}.png (${width}px, full page)`);

    if (width === 420) {
      // ----- 3. wordmark one-line check (measured on the live render) -----
      const wm = await page.evaluate((sel) => {
        const el = sel
          ? document.querySelector(sel)
          : document.querySelector('header h1') || document.querySelector('h1');
        if (!el) return null;
        const cs = getComputedStyle(el);
        let lh = parseFloat(cs.lineHeight);
        if (Number.isNaN(lh)) lh = parseFloat(cs.fontSize) * 1.2;
        const rect = el.getBoundingClientRect();
        return {
          text: el.textContent.trim().replace(/\s+/g, ' '),
          heightPx: rect.height,
          lineHeightPx: lh,
          lines: rect.height / lh,
          overflowPx: el.scrollWidth - el.clientWidth,
          whiteSpace: cs.whiteSpace,
          fontSize: cs.fontSize,
        };
      }, wordmarkSelector);
      if (!wm) {
        const msg = wordmarkSelector
          ? `wordmark check: selector "${wordmarkSelector}" matched no element on the page`
          : 'wordmark check: no header h1 found on the page';
        failures.push(msg);
        say(`[FAIL] ${msg}`);
      } else if (wm.whiteSpace !== 'nowrap') {
        // House rule §2: the wordmark must CARRY white-space:nowrap. Rendered fit at one
        // viewport in one engine is luck (font metrics and webview widths vary by device —
        // the 2026-11-18 wrap reached a phone whose render differed from desktop Chromium);
        // the nowrap rule is what makes one line a guarantee instead of a coincidence.
        const msg = `wordmark not wrap-protected at 420px: "${wm.text}" computes white-space: ${wm.whiteSpace} ` +
          `(house rule: white-space: nowrap); rendered lines in this engine: ${wm.lines.toFixed(2)} at ${wm.fontSize} — ` +
          `one line must be guaranteed by the nowrap rule, not by this render's font metrics`;
        failures.push(msg);
        say(`[FAIL] ${msg}`);
      } else if (wm.lines > 1.25) {
        const msg = `wordmark wraps at 420px: "${wm.text}" renders on ${wm.lines.toFixed(2)} lines ` +
          `(height ${wm.heightPx.toFixed(1)}px vs line-height ${wm.lineHeightPx.toFixed(1)}px, font-size ${wm.fontSize})`;
        failures.push(msg);
        say(`[FAIL] ${msg}`);
      } else if (wm.overflowPx > 1) {
        const msg = `wordmark overflows at 420px: "${wm.text}" is ${wm.overflowPx}px wider than its band (clipped, white-space: ${wm.whiteSpace})`;
        failures.push(msg);
        say(`[FAIL] ${msg}`);
      } else {
        say(`[PASS] wordmark one-line at 420px — "${wm.text}" on one line ` +
          `(height ${wm.heightPx.toFixed(1)}px = 1.00 line at ${wm.fontSize}, white-space: ${wm.whiteSpace})`);
      }

      // ----- 4. axe floor (report-only; see README) -----
      const axePath = path.join(process.cwd(), 'node_modules', 'axe-core', 'axe.min.js');
      const localAxe = fs.existsSync(axePath)
        ? axePath
        : path.join(path.dirname(new URL(import.meta.url).pathname), 'node_modules', 'axe-core', 'axe.min.js');
      if (fs.existsSync(localAxe)) {
        await page.addScriptTag({ path: localAxe });
        const results = await page.evaluate(async () => {
          const r = await window.axe.run(document, { resultTypes: ['violations'] });
          return r.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, help: v.help }));
        });
        if (results.length === 0) {
          say('[OK]   axe floor — 0 violations at 420px');
        } else {
          say(`[WARN] axe floor — ${results.length} violation rule(s) at 420px (report-only, see README):`);
          for (const v of results) say(`         - ${v.id} (${v.impact}, ${v.nodes} node(s)) — ${v.help}`);
        }
      } else {
        say('[WARN] axe floor — axe-core not installed locally; skipped (see README)');
      }
    }
    await page.close();
  }
} finally {
  await browser.close();
}

// ---------- verdict + report ----------
say('');
say(failures.length === 0 ? 'GATE: PASS' : `GATE: FAIL — ${failures.length} failure(s)`);
const report = [
  `# Design gate report`,
  ``,
  `- Target: ${targetLabel}`,
  `- When: ${new Date().toISOString()}`,
  `- Chrome: ${chromePath}`,
  `- Verdict: ${failures.length === 0 ? 'PASS' : 'FAIL'}`,
  failures.length ? `- Failures:\n${failures.map((f) => `  - ${f}`).join('\n')}` : `- Failures: none`,
  ``,
  '```',
  ...lines,
  '```',
  ``,
].join('\n');
fs.writeFileSync(path.join(outDir, 'report.md'), report);
say(`report + screenshots in ${outDir}`);
process.exit(failures.length === 0 ? 0 : 1);
