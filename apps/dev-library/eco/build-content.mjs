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
  fs.mkdirSync(OUT_DIR, { recursive: true });
  for (const [src, dest] of DOCS) {
    const md = fs.readFileSync(path.join(SRC_DIR, src), "utf8");
    const html = mdToHtml(md);
    fs.writeFileSync(path.join(OUT_DIR, dest), html + "\n");
    console.log(`${dest}: ${html.length} bytes`);
  }
  // The invitation attachment (James, 2026-11-19): the diagrams
  // document itself, as a .md file — the complete set of three
  // Mermaid diagrams. The mailer attaches it to invitations for
  // full-visibility contributors only (lib/invitations.mjs).
  const diagramsSrc = path.join(SRC_DIR, "UZE-ECOSYSTEM-MAPPING-DIAGRAMS-2026-11-19.md");
  fs.copyFileSync(diagramsSrc, path.join(OUT_DIR, "diagrams.md"));
  console.log(`diagrams.md: ${fs.statSync(path.join(OUT_DIR, "diagrams.md")).size} bytes (attachment copy)`);
}
