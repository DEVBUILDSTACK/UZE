// The four org section pages of the UZE Buildr Team surface.
// Every statement here is composed ONLY from the internal reference
// set (the two design-surface documents, the mapping diagrams, and
// the verbal overview) — no invented facts, no figures the sources
// do not carry. Keys are the org-registry keys (db/orgs.mjs); the
// route slugs are the lowercase short forms.
export const ORG_ROUTES = [
  { slug: "uze", key: "UZE", acronym: "UZE", name: "UZEmarkets" },
  { slug: "l2l", key: "L2Launch", acronym: "L2L", name: "L2 Launchpad — Learn2Launch" },
  { slug: "dfi", key: "DFI", acronym: "DFI", name: "DealFi" },
  { slug: "fvc", key: "FVC", acronym: "FVC", name: "Fundio" },
];
export const orgRoute = (slug) => ORG_ROUTES.find(r => r.slug === slug) || null;

export const ORG_PAGES = {
  UZE: `
<p class="lede">UZEmarkets is the information market at the center of the ecosystem — the place where offerings are not just traded but <em>tested and used</em>.</p>
<h3>Its place in the architecture</h3>
<p>UZEmarkets launches January 2, 2027. Buyers' demand shapes what is offered; what is offered is proven genuine; and use improves it every round. The one-line version of the whole ecosystem runs through it: <strong>Learn2Launch builds it, Assurative makes it trustworthy, UZE Markets is where it's tested and used.</strong> Underneath sits the shared core, AssurativeV2, where claims about real things are judged and resolved — claims that pass are <strong>Assuratized</strong>: reliance-grade, the kind a financing partner can build on.</p>
<h3>The human surface here</h3>
<p>Every UZEmarkets page a person sees is written in the one design language and passes the car wash before it ships — palette, phone and desktop renders, the wordmark on one line. UZEmarkets is a prospective project; Learn2Launch is the present phase. The design system governs both, and does not change what either is.</p>
<h3>The agentic surface here</h3>
<p>Agents reach UZEmarkets through one door, the <strong>UZE Instant MCP</strong>: wallet-bound identity, three gates before anything executes, every call written to the chronicle, and settlement under one rail law — <strong>USDC on Solana</strong> by default. The product tools that face this market are <strong>UZE Underwrite</strong> (the Autonomous Underwriting desk), <strong>UZE Assign</strong> and <strong>UZE Auction</strong> — one family, never blended with the trading tools. The desks are named in one line: <em>Autonomous Underwriting, Talent &amp; DealFi matching desks — UZEmarkets superIntelligence.</em></p>`,
  L2Launch: `
<p class="lede">L2Launch — Learn2Launch — is a launchpad first and a Creative Intelligence agency second. It is the present, real phase of the ecosystem.</p>
<h3>Its place in the architecture</h3>
<p>As a launchpad, L2Launch takes builders and creators and launches them — with financing readiness, grant access, and their work protected and credited. What the Launchpad launches flows into UZE Markets, where demand tests it and use improves it.</p>
<h3>The Creative Intelligence model</h3>
<p>As a Creative Intelligence agency, the model is simple and powerful: global creators — contractors, never employees — compete to produce artwork, music films, and ticket designs; the company, venue, or event producer who engaged the Launchpad selects the work; the house holds an intellectual-property interest so the work cannot be stolen, and the creator keeps a pre-negotiated fractional interest.</p>
<h3>The people</h3>
<p>The Launchpad is led by its principals: James, the founder; WCD (William), artist and commercial artistic entrepreneur; Jonathan Schmidt, the Creative Intelligence Principal; and Joey Hunter in Fort Lauderdale. Creative input from the principals returns to the design standard as <em>amendments</em> — never one-off page edits — and James ratifies them; then everything updates at once.</p>
<h3>The two surfaces here</h3>
<p>People experience L2Launch through the human design surface — its films and ticket art are among the things people see, washed like everything else. Its builders and creators are served by the same guarded, recorded agent door as the rest of the ecosystem when they transact.</p>`,
  DFI: `
<p class="lede">DealFi — DFI — is a separate firm on the business side of the ecosystem. Its matching desk is served through the ecosystem.</p>
<h3>Its place in the architecture</h3>
<p>DFI sits outside the UZE + L2Launch core, on the business side, alongside Fundio (FVC). The matching desks are named in one line: <em>Autonomous Underwriting, Talent &amp; DealFi matching desks — UZEmarkets superIntelligence.</em> On the agentic surface, the DealFi matching desk is <strong>UZE Assign</strong> — one of the product MCPs, a family that is never blended with the trading tools.</p>
<h3>Bring-online order</h3>
<p>The matching desks come online in their own order: <strong>DealFi (DFI) first, then Fundio (FVC)</strong>. DealFi leads.</p>
<h3>The two surfaces here</h3>
<p>The human design standard stays resident in DealFi's surfaces — the same eight values, the same car wash before anything ships — while its desk work runs through the agentic surface: wallet-bound identity, three-layer gating before execution, and every call on the chronicle.</p>`,
  FVC: `
<p class="lede">Fundio — FVC — is a separate firm on the business side of the ecosystem. Its matching desk is served through the ecosystem, and its filed direction meets the agentic surface's ultimate focus: treasury.</p>
<h3>Its place in the architecture</h3>
<p>FVC sits outside the UZE + L2Launch core, on the business side, alongside DealFi (DFI). The matching desks come online in their own order — <strong>DealFi (DFI) first, then Fundio (FVC)</strong> — under the line that names them: <em>Autonomous Underwriting, Talent &amp; DealFi matching desks — UZEmarkets superIntelligence.</em></p>
<h3>The treasury focus</h3>
<p>The agentic design surface keeps two money domains separate. Trading — maximizing gains, sizing positions, setting risk tolerance — is real, and explicitly <em>not</em> the focus. <strong>Treasury is the ultimate focus</strong>: entities hold balances they do not currently need — seasonal cash flow, operating reserves above the working line, fiat balances sitting idle — and Digital Asset Treasury is the discipline of putting them to work, optimizing yield under mandates the entity sets, with records the entity can audit. Agents do the watching; the mandate does the deciding; every action is a chronicle event; settlement of record is USDC on Solana under the rail law.</p>
<p>Fundio's filed direction points the same way: its Enterprise Services level — payroll, payouts, the Command &amp; Control console — already names a self-directed Web3 treasury for business partners as a later extension. The treasury domain is where the agentic surface meets that enterprise offer. No treasury product is live today; what exists is the substrate — identity, gating, chronicle, metering, settlement law — and this design for the service it makes possible.</p>
<h3>The two surfaces here</h3>
<p>Fundio is one of the front ends the human design standard anchors — the shared Command &amp; Control Console must stay consistent across all three front ends — and its surfaces pass the same car wash as everything else in the ecosystem.</p>`,
};
