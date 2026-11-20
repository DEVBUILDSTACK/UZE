// The two public mock pages (James, 2026-11-19): carried as data,
// served at /mock/tickets and /mock/prediction-markets — public
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
const FOOT = `</main><footer>© 2026 UZEmarkets · Mock-up for review — prices and splits are illustrative.</footer>
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

export const TICKETS_MOCK_HTML = HEAD("Tickets — two markets") + `
<section class="card"><h2>São Paulo — Porto Alegre, Beira-Rio</h2>
<span class="tag">PRIMARY MARKET</span><span class="tag">We run this sale</span>
<p>Inter vs São Paulo. We create the NFT tickets and run the whole sale here — every seat, every pass. Pick a stand, then one seat or four.</p>
<div class="stand"><div>North Stand</div><div>East Stand</div><div>South Stand</div><div>West Stand</div></div>
<div class="row"><button data-pick="1">One seat</button><button data-pick="4">Four seats together</button></div>
<div class="out">Pick one seat, or four seats together.</div>
<p class="small">Programmatic receipt on every pass — encrypted proof the pass is genuine and payment verified.</p></section>
<section class="card"><h2>Miami</h2>
<span class="tag">SECONDARY MARKET</span><span class="tag">Resale, on chain</span>
<p>The same event, the resale side. Passes move from the first buyer to the next on chain — the proof travels with the pass, so a fake cannot enter.</p>
<div class="stand"><div>North Stand</div><div>East Stand</div><div>South Stand</div><div>West Stand</div></div>
<div class="row"><button data-pick="1">One seat</button><button data-pick="4">Four seats together</button></div>
<div class="out">Pick one seat, or four seats together.</div>
<p class="small">A lifetime license for one or four seats, a full season, or a single night — the same pass carries all of them.</p></section>
` + FOOT;

export const PREDICTION_MOCK_HTML = HEAD("Prediction markets — day-of, two markets") + `
<section class="card"><h2>How these markets work</h2>
<p>Prediction markets here are <b>day-of only</b>. Each market opens at midnight — as Asia turns, the first edge of the Pacific first — for that day's events, and closes when the event ends. An extension well beyond ticket sales: the same venues, the same day.</p>
<p class="small">Sport only. Extreme sports included — skateboarding and surfing at the front, and lacrosse Sixes with them.</p></section>
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
