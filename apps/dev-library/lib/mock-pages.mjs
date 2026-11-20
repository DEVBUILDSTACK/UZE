// The public prediction-markets mock page (James, 2026-11-19):
// carried as data, served at /mock/prediction-markets — public
// BY DESIGN (noindex), so the family owners can open them from a
// letter without any sign-in. Two markets on each: São Paulo
// (Porto Alegre, the primary — we run the sale) and Miami (the
// secondary market). One seat and four seats, separately.
const HEAD = (title) => `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>${title} — UZEmarkets (mock)</title>
<style>
body{margin:0;background:#f5f2ee;color:#1a1a1a;font:16px/1.55 Georgia,serif}
header{background:#1a1a1a;color:#f5f2ee;padding:22px 20px}
header .wm{font:700 22px Arial,sans-serif}header .wm b{color:#ff6b00;font-weight:700}
header p{margin:6px 0 0;font:14px Arial,sans-serif;color:#f5f2ee}
main{max-width:860px;margin:0 auto;padding:24px 20px 48px}
.card{background:#fff;border:1px solid #e5ded4;border-radius:10px;padding:20px;margin:0 0 18px}
.card h2{margin:0 0 4px;font:700 19px Arial,sans-serif}
.tag{display:inline-block;background:#FDEEE2;border-radius:20px;padding:2px 10px;font:12px Arial,sans-serif;margin:0 6px 8px 0}
.stand{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:12px 0}
.stand div{border:1.5px solid #1a1a1a;border-radius:6px;padding:10px 4px;text-align:center;font:12px Arial,sans-serif;cursor:pointer;background:#fff}
.stand div.sel{background:#ff6b00;color:#fff;border-color:#ff6b00}
.row{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
button{font:700 13px Arial,sans-serif;border-radius:20px;border:1.5px solid #1a1a1a;background:#fff;padding:7px 16px;cursor:pointer}
button.on{background:#1a1a1a;color:#fff}
.out{font:14px Arial,sans-serif;background:#FDEEE2;border-radius:8px;padding:10px 14px;min-height:20px}
.q{border-top:1px solid #e5ded4;padding:12px 0}
.q:first-of-type{border-top:0}
.q b{font-family:Arial,sans-serif}
.bar{height:10px;background:#f5f2ee;border-radius:5px;overflow:hidden;margin:6px 0}
.bar i{display:block;height:100%;background:#ff6b00}
.small{font:13px Arial,sans-serif;color:#1a1a1a;opacity:.75}
footer{max-width:860px;margin:0 auto;padding:0 20px 40px;font:12px Arial,sans-serif;opacity:.7}
</style></head><body>
<header><div class="wm"><b>UZE</b>markets</div><p>${title} — a mock-up. Nothing here is a real sale or a real market.</p></header><main>`;
const FOOT = `<section class="card"><h2>Surf, Skate, Tri, Lax it Up</h2>
<span class="tag">BE DECENSAT &amp; DONATE</span><span class="tag">THE PATH TO LA28</span>
<p><strong>Be Decensat &amp; Donate</strong> — at UZEmarkets.com, donate programmatically to the training budget for <strong>amateur artists, athletes, and performers</strong> on their path to LA28. Donations over the threshold — funded by stablecoin — participate in the marketplace: <strong>Merch · Train · Supplements · Support</strong>, across surfing, skateboarding, triathlon, and lacrosse Sixes. It routes to the shopping &amp; commerce store experience at <strong>decensat.org</strong>.</p></section>
</main><footer>© 2026 UZEmarkets · Mock-up for review — prices and splits are illustrative.</footer>
<script>
document.querySelectorAll("[data-pick]").forEach(b=>b.addEventListener("click",()=>{
  const card=b.closest(".card");card.querySelectorAll("[data-pick]").forEach(x=>x.classList.remove("on"));b.classList.add("on");
  const n=b.dataset.pick,out=card.querySelector(".out");
  out.textContent = n==="1" ? "One seat — allocated in the stand you picked. The pass is an NFT ticket: encrypted proof it is real and paid for, transferable on chain." : "Four seats together — one block of four, allocated in the stand you picked. One NFT pass set, transferable on chain as a block or split by the holder.";
}));
document.querySelectorAll(".stand div").forEach(d=>d.addEventListener("click",()=>{
  d.closest(".stand").querySelectorAll("div").forEach(x=>x.classList.remove("sel"));d.classList.add("sel");
}));
</script></body></html>`;

export const TICKETS_MOCK_HTML = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Tickets — one and four, primary and secondary — UZEmarkets (mock)</title>
<style>
body{margin:0;background:#f5f2ee;color:#1a1a1a;font:16px/1.55 Georgia,serif}
header{background:#1a1a1a;color:#f5f2ee;padding:22px 20px}
header .wm{font:700 22px Arial,sans-serif}header .wm b{color:#ff6b00}
header p{margin:6px 0 0;font:14px Arial,sans-serif}
main{max-width:960px;margin:0 auto;padding:24px 20px 48px}
.card{background:#fff;border:1px solid #e5ded4;border-radius:10px;padding:20px;margin:0 0 18px}
.card h2{margin:0 0 4px;font:700 19px Arial,sans-serif}
.tag{display:inline-block;background:#FDEEE2;border-radius:20px;padding:2px 10px;font:12px Arial,sans-serif;margin:0 6px 8px 0}
iframe{width:100%;height:980px;border:1px solid #e5ded4;border-radius:10px;background:#fff}
.stand{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:12px 0}
.stand div{border:1.5px solid #1a1a1a;border-radius:6px;padding:10px 4px;text-align:center;font:12px Arial,sans-serif;cursor:pointer}
.stand div.sel{background:#ff6b00;color:#fff;border-color:#ff6b00}
.row{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
button{font:700 13px Arial,sans-serif;border-radius:20px;border:1.5px solid #1a1a1a;background:#fff;padding:7px 16px;cursor:pointer}
button.on{background:#1a1a1a;color:#fff}
.out{font:14px Arial,sans-serif;background:#FDEEE2;border-radius:8px;padding:10px 14px;min-height:20px}
.small{font:13px Arial,sans-serif;opacity:.75}
footer{max-width:960px;margin:0 auto;padding:0 20px 40px;font:12px Arial,sans-serif;opacity:.7}
</style></head><body>
<header><div class="wm"><b>UZE</b>markets</div><p>Tickets — purchase, one, two, and five, primary and secondary. A mock-up; nothing here is a real sale.</p></header><main>
<section class="card"><h2>Primary — São Paulo · Porto Alegre, Beira-Rio</h2>
<span class="tag">PRIMARY MARKET</span><span class="tag">We run this sale</span>
<p>The original mock: pick a price area on the stadium map, choose how many seats together — one, two, or five — and the engine allocates the actual seats. This is the primary purchase face.</p>
<iframe src="/mock/venue-ticketing" title="Primary market — venue ticketing mock"></iframe></section>
<section class="card" id="secondary"><h2>Secondary — Miami</h2>
<span class="tag">SECONDARY MARKET</span><span class="tag">Resale purchase, on chain</span>
<p>The resale purchase face: passes listed by their first buyers. Pick a stand, then one, two, or five seats together — the same pass, with its proof, transfers to you on chain. Or bid for it: the sealed-bid vault auction.</p>
<div class="stand"><div>North Stand</div><div>East Stand</div><div>South Stand</div><div>West Stand</div></div>
<div class="row"><button data-pick="1">One seat</button><button data-pick="2">Two seats together</button><button data-pick="5">Five seats together</button></div>
<div class="row"><button data-auction="1">Secondary sealed bid on-chain vault auction</button><button data-countdown="1">Auction countdown</button></div>
<div class="out">Pick one, two, or five seats together — or open the sealed-bid vault auction.</div>
<h2 style="margin-top:22px">Engage — digital, via the NFT ticket</h2>
<p>The ticket itself is the engagement channel. Through it:</p>
<p>· <strong>Pre-event track drops</strong> — the artist's music lands with ticket holders before the event.<br>
· <strong>Merch drops</strong> — holder-only merchandise, released through the ticket.<br>
· <strong>VIP access</strong> — the pass carries its tier with it.<br>
· <strong>Venue-geo partner offers</strong> — offers and access from partners at the venue's location, delivered to the pass.<br>
· <strong>Consolation ticket pairs</strong> — in the sealed vault auction, the <strong>top three encrypted sealed bids following the lot's winning bid</strong> receive a consolation pair of tickets. Losing at the top still lands you in the room.</p>
<p class="small">Programmatic receipt on every pass — encrypted proof the pass is genuine and payment verified. A lifetime license for one or four seats, a full season, or a single night — the same pass carries all of them.</p></section>
</main><footer>© 2026 UZEmarkets · Mock-up for review — prices are illustrative.</footer>
<script>
document.querySelectorAll("[data-pick]").forEach(b=>b.addEventListener("click",()=>{
  const card=b.closest(".card");card.querySelectorAll("[data-pick]").forEach(x=>x.classList.remove("on"));b.classList.add("on");
  const n = b.dataset.pick;
  card.querySelector(".out").textContent = n==="1" ? "One seat — a listed pass in the stand you picked, transferred to you on chain with its proof." : n + " seats together — a listed block of " + n + " in the stand you picked, transferred to you on chain with its proof.";
}));
document.querySelectorAll("[data-countdown]").forEach(b=>b.addEventListener("click",()=>{
  const card=b.closest(".card");
  card.querySelector(".out").textContent = "Auction countdown: the countdown never begins more than 151 calendar days before the first day of the event — festival, convention, or single event. On-ramp by the 3D venue seat selector, with KYC — or your existing UZEmarkets KYC/KYB. UZE Auction: sealed bid, encrypted by supercomputer, on-chain REE | TEE, digital NFT. Simultaneous auctions may be conducted — but every seat offered is unique: a vaulted, escrow-gated real-world asset with perpetual collectible rights, including any programmatically paired artist, performance, or team in-person attendance — or ticket-donation to a needy fan or adult as a contribution in lieu of attendance — as fractional outcome participation. (Mock — no live countdown.)";
}));
document.querySelectorAll("[data-auction]").forEach(b=>b.addEventListener("click",()=>{
  const card=b.closest(".card");
  card.querySelector(".out").textContent = "Sealed bid vault auction: your bid is encrypted and held in the on-chain vault until the auction closes — no one sees it, not even us. The winning bid takes the pass; every other bid is returned whole. (Mock — no real bids.)";
}));
document.querySelectorAll(".stand div").forEach(d=>d.addEventListener("click",()=>{
  d.closest(".stand").querySelectorAll("div").forEach(x=>x.classList.remove("sel"));d.classList.add("sel");
}));
</script></body></html>`;

export const PREDICTION_MOCK_HTML = HEAD("Prediction markets — day-of, two markets") + `
<section class="card"><h2>How these markets work</h2>
<p>Prediction markets here are <b>day-of only</b>. Each market opens at midnight — as Asia turns, the first edge of the Pacific first — for that day's events, and closes when the event ends. An extension well beyond ticket sales: the same venues, the same day.</p>
<p>World.xyz — live by API, sports only: launching 2026 with international football (soccer), plus three more by the NFL playoffs. Music event venue information and auction market innovation follow in 2027. Sixes rides with them.</p>
<p class="small">Sport only. Extreme sports — the LA28 qualification pathways: lacrosse Sixes at the front, with skateboarding, surfing, and triathlon. The first Olympics with surfing and lacrosse Sixes together.</p></section>
<section class="card"><h2>São Paulo — today's card</h2>
<span class="tag">DAY-OF</span><span class="tag">Opens 00:00, Asia-Pacific edge</span>
<div class="q"><b>Inter vs São Paulo — Inter wins?</b><div class="bar"><i style="width:57%"></i></div><span class="small">Yes 57 · No 43 (mock)</span></div>
<div class="q"><b>Three or more goals in the match?</b><div class="bar"><i style="width:41%"></i></div><span class="small">Yes 41 · No 59 (mock)</span></div>
<div class="q"><b>Skateboarding — the favorite takes the street final?</b><div class="bar"><i style="width:63%"></i></div><span class="small">Yes 63 · No 37 (mock)</span></div></section>
<section class="card"><h2>Miami — today's card</h2>
<span class="tag">DAY-OF</span><span class="tag">Opens 00:00, Asia-Pacific edge</span>
<div class="q"><b>Surfing — a perfect 10 in today's final?</b><div class="bar"><i style="width:22%"></i></div><span class="small">Yes 22 · No 78 (mock)</span></div>
<div class="q"><b>Lacrosse Sixes — the day's final goes to overtime?</b><div class="bar"><i style="width:31%"></i></div><span class="small">Yes 31 · No 69 (mock)</span></div>
<div class="q"><b>Skateboarding — a first-time winner today?</b><div class="bar"><i style="width:48%"></i></div><span class="small">Yes 48 · No 52 (mock)</span></div></section>
` + FOOT;
