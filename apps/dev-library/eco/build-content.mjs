// Build the UZE Buildr Team content fragments from the internal
// reference set (James's direction, 2026-11-19: the four documents
// are served to the principals through this gated site).
//   node eco/build-content.mjs
// Sources live OUTSIDE the repo (~/workspace/your_files/) and are
// never edited by this script. The converter is deliberately
// minimal and safe: escape everything first, then apply inline
// formatting; Mermaid fences become <pre class="mermaid"> blocks
// (rendered client-side when the CDN loads) AND a collapsible
// "diagram code" block — the code is the machine-readable seed for
// the later JSON/agent access layer. Palette safety: any hex color
// that is not one of the eight house tokens is replaced with ink —
// the source documents DISCUSS off-palette colors (they document
// wash failures); the served fragments must never carry them.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC_DIR = process.env.ECO_CONTENT_SRC || path.join(HERE, "..", "..", "..", "..", "..", "your_files");
const OUT_DIR = path.join(HERE, "content");

const DOCS = [
  ["HUMAN-DESIGN-SURFACE-FOR-UZE-ECOSYSTEM-2026-11-19.md", "human.html"],
  ["AGENTIC-DESIGN-SURFACE-FOR-UZE-ECOSYSTEM-2026-11-19.md", "agentic.html"],
  ["UZE-ECOSYSTEM-MAPPING-DIAGRAMS-2026-11-19.md", "diagrams.html"],
  ["UZE-ECOSYSTEM-VERBAL-OVERVIEW-2026-11-19.md", "overview.html"],
];

const TOKENS = new Set(["#1a1a1a", "#f5f2ee", "#ff6b00", "#fdeee2", "#ddd5c9", "#6b655e", "#b8b0a4", "#ffffff"]);
function sanitizePalette(html) {
  return html.replace(/#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b/g, (m) => {
    let hex = m.slice(1).toLowerCase();
    if (hex.length === 3) hex = hex.split("").map(c => c + c).join("");
    if (hex.length === 4) hex = hex.slice(0, 3).split("").map(c => c + c).join("");
    if (hex.length === 8) hex = hex.slice(0, 6);
    return TOKENS.has("#" + hex) ? m : "#1a1a1a";
  });
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
function inline(raw) {
  let s = esc(raw);
  const spans = [];
  s = s.replace(/`([^`]+)`/g, (_, code) => { spans.push(code); return `\u0001${spans.length - 1}\u0002`; });
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, text, url) => `<a href="${url}">${text}</a>`);
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  s = s.replace(/\u0001(\d+)\u0002/g, (_, i) => `<code>${spans[Number(i)]}</code>`);
  return s;
}

function renderList(items) {
  // items: [{ indent, ordered, text }] → nested <ul>/<ol> by indent.
  let html = "";
  const stack = []; // [{ indent, tag }]
  const closeTo = (indent) => {
    while (stack.length && stack[stack.length - 1].indent >= indent) { html += `</li></${stack.pop().tag}>`; }
  };
  for (const it of items) {
    const tag = it.ordered ? "ol" : "ul";
    if (!stack.length || it.indent > stack[stack.length - 1].indent) {
      html += `<${tag}><li>`; stack.push({ indent: it.indent, tag });
    } else if (it.indent === stack[stack.length - 1].indent && stack[stack.length - 1].tag !== tag) {
      closeTo(it.indent); html += `<${tag}><li>`; stack.push({ indent: it.indent, tag });
    } else {
      closeTo(it.indent + 1); html += "</li><li>";
    }
    html += inline(it.text);
  }
  while (stack.length) { html += `</li></${stack.pop().tag}>`; }
  return html;
}

export function mdToHtml(md) {
  const lines = md.split("\n");
  const out = [];
  let i = 0;
  const isBlockStart = (l) => /^#{1,6}\s/.test(l) || /^```/.test(l) || /^\s*(?:[-*]|\d+\.)\s+/.test(l)
    || /^\|/.test(l) || /^>\s?/.test(l) || /^\s*(?:-{3,}|\*{3,})\s*$/.test(l);
  while (i < lines.length) {
    const line = lines[i];
    if (/^```/.test(line)) {
      const lang = line.slice(3).trim();
      const buf = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) { buf.push(lines[i]); i++; }
      i++; // closing fence
      const code = buf.join("\n");
      if (lang === "mermaid") {
        out.push(`<pre class="mermaid" tabindex="0">${esc(code)}</pre>`);
        out.push(`<details class="diagram-code"><summary>Diagram code — the machine-readable seed</summary><pre tabindex="0"><code>${esc(code)}</code></pre></details>`);
      } else {
        out.push(`<pre tabindex="0"><code>${esc(code)}</code></pre>`);
      }
      continue;
    }
    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) { const lvl = Math.min(6, h[1].length + 1); out.push(`<h${lvl}>${inline(h[2])}</h${lvl}>`); i++; continue; }
    if (/^\s*(?:-{3,}|\*{3,})\s*$/.test(line)) { out.push("<hr>"); i++; continue; }
    if (/^>\s?/.test(line)) {
      const buf = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) { buf.push(lines[i].replace(/^>\s?/, "")); i++; }
      out.push(`<blockquote>${buf.map(p => `<p>${inline(p)}</p>`).join("")}</blockquote>`);
      continue;
    }
    if (/^\|/.test(line) && i + 1 < lines.length && /^\|[\s:|-]+\|?\s*$/.test(lines[i + 1])) {
      const cells = (l) => l.replace(/^\||\|$/g, "").split("|").map(c => c.trim());
      const head = cells(line);
      i += 2;
      const rows = [];
      while (i < lines.length && /^\|/.test(lines[i])) { rows.push(cells(lines[i])); i++; }
      out.push(`<table><thead><tr>${head.map(c => `<th>${inline(c)}</th>`).join("")}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${inline(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
      continue;
    }
    if (/^\s*(?:[-*]|\d+\.)\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*(?:[-*]|\d+\.)\s+/.test(lines[i])) {
        const m = lines[i].match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
        items.push({ indent: m[1].length, ordered: /\d/.test(m[2]), text: m[3] });
        i++;
      }
      out.push(renderList(items));
      continue;
    }
    if (!line.trim()) { i++; continue; }
    const buf = [line];
    i++;
    while (i < lines.length && lines[i].trim() && !isBlockStart(lines[i])) { buf.push(lines[i]); i++; }
    out.push(`<p>${inline(buf.join(" "))}</p>`);
  }
  return sanitizePalette(out.join("\n"));
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  // Output is a DATA MODULE (lib/eco-content.mjs), never loose
  // files (James's visibility doctrine, 2026-11-19): the
  // deployment's static layer serves loose app files publicly,
  // and this material is gated — dev / principal / owner only.
  // The audience-cut masters live in the repo at
  // docs/design-surfaces/diagrams-jonathan.md and
  // docs/design-surfaces/diagrams-owners.md.
  const frag = {};
  for (const [src, dest] of DOCS) {
    const md = fs.readFileSync(path.join(SRC_DIR, src), "utf8");
    frag[dest.replace(/\.html$/, "")] = mdToHtml(md) + "\n";
    console.log(`${dest}: ${frag[dest.replace(/\.html$/, "")].length} bytes`);
  }
  const repoRoot = path.join(HERE, "..", "..", "..");
  const jonathan = fs.readFileSync(path.join(repoRoot, "docs/design-surfaces/diagrams-jonathan.md"), "utf8");
  const owners = fs.readFileSync(path.join(repoRoot, "docs/design-surfaces/diagrams-owners.md"), "utf8");
  const full = fs.readFileSync(path.join(SRC_DIR, "UZE-ECOSYSTEM-MAPPING-DIAGRAMS-2026-11-19.md"), "utf8");
  const humanSurface = fs.readFileSync(path.join(SRC_DIR, "HUMAN-DESIGN-SURFACE-FOR-UZE-ECOSYSTEM-2026-11-19.md"), "utf8");
  const agenticSurface = fs.readFileSync(path.join(SRC_DIR, "AGENTIC-DESIGN-SURFACE-FOR-UZE-ECOSYSTEM-2026-11-19.md"), "utf8");
  // The structured JSON representation of the diagrams (James,
  // 2026-11-19): the same content as the Mermaid and the renders,
  // as data — including the L2Launch island doctrine. DRAFT
  // PROPOSAL, version 0.1.
  const DIAGRAMS_JSON = {
    stage: "Draft proposal",
    version: "0.1",
    date: "2026-11-19",
    documents: "The UZE Ecosystem, Mapped — Three Diagrams (audience cuts: principal; owners)",
    l2launch: {
      name: "L2Launch — The Agency & Launchpad",
      form: "an island — an oval, outside the UZE ecosystem rectangles",
      partOfUZE: false,
      relationToUZE: "L2Launch has nothing to do with UZE. Nothing in the UZE sections of these diagrams is L2Launch, and nothing below the island is built.",
      status: "To be developed — a vision, built collaboratively by James Sr. and Jonathan Schmidt, possibly others. Nothing below it exists yet.",
      leftSide: "Creator Acceleration, Creative Intelligence Deal/Work Flow & Project Proof",
      rightSide: "Post-Formation, Pre-Seed, Project & Org architecture launchpad accelerator",
      oneBridge: {
        what: "agency clients — hot, enterprise, high-expectation",
        from: "UZEmarkets' agentic outreach: leads created and converted agentically, across graphic design, UGC, video and animation demand",
        vehicleProposed: "the outreach-sales-shortcut repo, going to niche verticals (Scope 4)",
        status: "proposed — does not exist yet",
      },
      carvedOffToTheAgency: ["motion", "video", "animation", "film", "UGC"],
    },
    uzeEcosystem: {
      market: "UZEmarkets — the information market (agents discover, negotiate, transact & settle here; launches January 2, 2027)",
      frontEnd: "UZEmarkets is the front end: the agentic outreach and lead-gen conversion solution, and the talent marketplace to source creatives — and enterprise demand for L2Launch Creative Intelligence and principal expertise.",
      theWork: ["graphic design", "animation", "illustration", "video production", "video editing", "sound editing", "UGC", "on-site global expertise", "photography and video execution"],
      coreFocusInitiative: "Convert and generate revenue within 120 days, and maintain — beginning June 30, 2027.",
      diagram1FrontEnd: ["agentic outreach & lead-gen conversion", "talent marketplace — to source creatives", "the work (the services list)", "enterprise demand — hot, high-expectation clients", "the core focus initiative"],
      diagram2AgenticSurface: ["the agents (enterprise · builder & creator · trading)", "discovery", "the door — UZE Instant MCP", "identity — every agent is wallet-bound", "three gates, checked before anything executes", "two tool families, never blended (product MCPs · trading MCPs)", "the chronicle — every call is recorded", "settlement — one rail law", "two domains, kept separate (trading · treasury — the ultimate focus)", "people supervise — the console"],
      note: "Everything in the UZE sections is UZEmarkets and the UZE ecosystem — what has been built, and what is being built.",
    },
  };
  fs.writeFileSync(path.join(repoRoot, "docs/design-surfaces/diagrams.json"), JSON.stringify(DIAGRAMS_JSON, null, 2) + "\n");
  console.log("docs/design-surfaces/diagrams.json written");
  const mod = `// GENERATED by eco/build-content.mjs — do not hand-edit.\n`
    + `export const DIAGRAMS_JSON = ${JSON.stringify(DIAGRAMS_JSON)};\n`
    + `export const ECO_FRAGMENTS = ${JSON.stringify(frag)};\n`
    + `export const DIAGRAMS_JONATHAN_MD = ${JSON.stringify(jonathan)};\n`
    + `export const DIAGRAMS_OWNERS_MD = ${JSON.stringify(owners)};\n`
    + `export const DIAGRAMS_FULL_MD = ${JSON.stringify(full)};\n`
    + `export const HUMAN_SURFACE_MD = ${JSON.stringify(humanSurface)};\n`
    + `export const AGENTIC_SURFACE_MD = ${JSON.stringify(agenticSurface)};\n`;
  const outPath = path.join(HERE, "..", "lib", "eco-content.mjs");
  fs.writeFileSync(outPath, mod);
  console.log(`lib/eco-content.mjs: ${mod.length} bytes`);
}
