import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { VENUE, SECTORS, RINGS, EVENTS, sectorPrice, fromPrice } from "./venue-data.js";

let ACTIVE_SECTORS = SECTORS;
let ACTIVE_RINGS = RINGS;
let CUR = "R$";
let EVENT = EVENTS[0];

// ---------------------------------------------------------------------------
// UZE Venue Ticketing — mock-up.
// Procedural bowl generated from the venue data tables (venue-data.js).
// Selection flow: orbit -> raycast pick a sector -> fly to it -> seat view
// -> quantity -> MOCK checkout. Settlement, inventory and attestation are
// stubbed and labelled MOCK; no funds move, no real inventory exists.
// ---------------------------------------------------------------------------

const TANGERINE = 0xff6b00;
const canvasWrap = document.getElementById("scene");
const tooltip = document.getElementById("tip");
const listEl = document.getElementById("sector-list");
const detailEl = document.getElementById("detail");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x101418);
scene.fog = new THREE.Fog(0x101418, 500, 1200);

const camera = new THREE.PerspectiveCamera(50, canvasWrap.clientWidth / canvasWrap.clientHeight, 0.1, 1000);
camera.position.set(175, 165, 175);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(canvasWrap.clientWidth, canvasWrap.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
canvasWrap.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.enableZoom = false; // wheel/pinch must scroll the PAGE, not trap it in the canvas (verified issue, 2026-11-12); fly-to on sector tap provides the close-up
controls.maxPolarAngle = Math.PI * 0.49;
controls.minDistance = 25;
controls.maxDistance = 320;

scene.add(new THREE.AmbientLight(0xffffff, 0.55));
scene.add(new THREE.HemisphereLight(0xdfeaff, 0x1a1d20, 0.55));
const sun = new THREE.DirectionalLight(0xffffff, 1.1);
sun.position.set(120, 180, 60);
sun.castShadow = true;
scene.add(sun);

// --- Pitch -----------------------------------------------------------------
const pitchMat = new THREE.MeshStandardMaterial({ color: 0x43a047, roughness: 1, emissive: 0x1d5c22, emissiveIntensity: 0.6 });
const pitch = new THREE.Mesh(new THREE.BoxGeometry(68, 1, 44), pitchMat);
pitch.position.y = 0.5;
pitch.receiveShadow = true;
scene.add(pitch);
const centreCircle = new THREE.Mesh(
  new THREE.RingGeometry(7.4, 8.1, 40),
  new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide })
);
centreCircle.rotation.x = -Math.PI / 2; centreCircle.position.y = 1.06; scene.add(centreCircle);
const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
[[0, 0, 68, 0.6], [0, 0, 0.6, 44],
 [0, -22, 68, 0.7], [0, 22, 68, 0.7], [-34, 0, 0.7, 44], [34, 0, 0.7, 44]].forEach(([x, z, w, d]) => {
  const l = new THREE.Mesh(new THREE.BoxGeometry(w, 0.1, d), lineMat);
  l.position.set(x, 1.05, z);
  scene.add(l);
});

// --- Bowl: one segment mesh per (ring, sector) ------------------------------
const bowlGroup = new THREE.Group();
scene.add(bowlGroup);
const pickables = [];
const sectorMeshes = new Map(); // sectorId -> meshes[]

function buildBowl() {
  while (bowlGroup.children.length) bowlGroup.remove(bowlGroup.children[0]);
  pickables.length = 0;
  sectorMeshes.clear();
  for (const ring of ACTIVE_RINGS) {
    const rMid = (ring.d0 + ring.d1) / 2;
    const height = ring.h1 - ring.h0;
    for (const sector of ACTIVE_SECTORS) {
      const a0 = THREE.MathUtils.degToRad(sector.a0);
      const a1 = THREE.MathUtils.degToRad(sector.a1);
      // Terraced: 3 steps per band, radius + shade stepping up — reads as seat rows.
      const STEPS = 3;
      for (let s = 0; s < STEPS; s++) {
        const rS = ring.d0 + (ring.d1 - ring.d0) * ((s + 0.5) / STEPS);
        const hS = height / STEPS;
        const geo = new THREE.CylinderGeometry(rS, rS, hS, 6, 1, true, a0, a1 - a0);
        const col = new THREE.Color(sector.color); col.offsetHSL(0, 0, (s - 1) * 0.05);
        const mat = new THREE.MeshStandardMaterial({ color: col, roughness: 0.85, side: THREE.DoubleSide });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.y = ring.h0 + hS * (s + 0.5);
        mesh.castShadow = true;
        mesh.userData = { sectorId: sector.id, ringId: ring.id };
        bowlGroup.add(mesh);
        pickables.push(mesh);
        if (!sectorMeshes.has(sector.id)) sectorMeshes.set(sector.id, []);
        sectorMeshes.get(sector.id).push(mesh);
      }
    }
    for (const sector of ACTIVE_SECTORS) {
      const t0 = THREE.MathUtils.degToRad(sector.a0), t1 = THREE.MathUtils.degToRad(sector.a1);
      const y = ring.h1 + 0.06;
      const P = (r, t) => [Math.sin(t) * r, y, Math.cos(t) * r];
      const quad = new Float32Array([
        ...P(ring.d0 + 0.4, t0), ...P(ring.d1, t0), ...P(ring.d1, t1),
        ...P(ring.d0 + 0.4, t0), ...P(ring.d1, t1), ...P(ring.d0 + 0.4, t1),
      ]);
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.BufferAttribute(quad, 3));
      g.computeVertexNormals();
      const col = new THREE.Color(sector.color); col.offsetHSL(0, 0, 0.07);
      const tread = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: col, roughness: 0.9, side: THREE.DoubleSide }));
      tread.userData = { sectorId: sector.id, ringId: ring.id };
      bowlGroup.add(tread);
      pickables.push(tread);
      if (!sectorMeshes.has(sector.id)) sectorMeshes.set(sector.id, []);
      sectorMeshes.get(sector.id).push(tread);
    }
    // ring walkway — a flat RING, never a solid disc (a capped cylinder here
    // hid the pitch and the lower bands from every elevated view).
    const walk = new THREE.Mesh(
      new THREE.RingGeometry(Math.max(1, ring.d0 - 2), ring.d1 + 1, 64),
      new THREE.MeshStandardMaterial({ color: 0x3a4149, roughness: 1, side: THREE.DoubleSide })
    );
    walk.rotation.x = -Math.PI / 2;
    walk.position.y = ring.h0 + 0.03;
    bowlGroup.add(walk);
  }
}
buildBowl();

// Apron floor so the bowl interior reads as a venue, not a void (top view).
const apron = new THREE.Mesh(
  new THREE.CircleGeometry(97, 48),
  new THREE.MeshStandardMaterial({ color: 0x5b6672, roughness: 1 })
);
apron.rotation.x = -Math.PI / 2; apron.position.y = 0.05; scene.add(apron);
// Roof ring + floodlight pylons — silhouette that reads "stadium" instantly.
const roofBand = new THREE.Mesh(
  new THREE.CylinderGeometry(93, 93, 3, 64, 1, true),
  new THREE.MeshStandardMaterial({ color: 0x22282e, roughness: 0.9, side: THREE.DoubleSide })
);
roofBand.position.y = 54; scene.add(roofBand);
const roofTop = new THREE.Mesh(
  new THREE.RingGeometry(76, 96, 64),
  new THREE.MeshStandardMaterial({ color: 0x2b3238, roughness: 1, side: THREE.DoubleSide })
);
roofTop.rotation.x = -Math.PI / 2; roofTop.position.y = 55.6; scene.add(roofTop);
for (const [fx, fz] of [[100, 75], [-100, 75], [100, -75], [-100, -75]]) {
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.9, 64, 6),
    new THREE.MeshStandardMaterial({ color: 0x555f68, roughness: 0.8 }));
  pole.position.set(fx, 32, fz); scene.add(pole);
  const head = new THREE.Mesh(new THREE.BoxGeometry(7, 3.5, 1),
    new THREE.MeshStandardMaterial({ color: 0x333333, emissive: 0xfff6d8, emissiveIntensity: 1.4 }));
  head.position.set(fx, 65, fz); head.lookAt(0, 0, 0); scene.add(head);
}

// --- Sector list (synced with the 3D scene both ways) -----------------------
let selected = null; // sector object
let selectedRing = RINGS[0];
let qty = 2;

function renderList() {
  listEl.innerHTML = "";
  for (const s of ACTIVE_SECTORS) {
    const row = document.createElement("button");
    row.className = "item" + (selected && selected.id === s.id ? " active" : "");
    row.dataset.sector = s.id;
    row.innerHTML = `<span class="swatch" style="background:#${s.color.toString(16).padStart(6, "0")}"></span>
      <span class="nm">${s.name}</span><span class="pr">from ${CUR}${fromPrice(s, ACTIVE_RINGS)}</span>`;
    row.addEventListener("click", () => selectSector(s, true));
    row.addEventListener("mouseenter", () => highlight(s, true));
    row.addEventListener("mouseleave", () => highlight(s, false));
    listEl.appendChild(row);
  }
}

function highlight(sector, on) {
  for (const m of sectorMeshes.get(sector.id) || []) {
    m.material.emissive = new THREE.Color(on || (selected && selected.id === sector.id) ? TANGERINE : 0x000000);
    m.material.emissiveIntensity = on ? 0.45 : selected && selected.id === sector.id ? 0.25 : 0;
  }
}

function selectSector(sector, fly) {
  if (selected !== sector) assignment = null;
  if (selected) highlight(selected, false);
  selected = sector;
  highlight(sector, true);
  renderList();
  renderDetail();
  if (fly) flyToSector(sector, selectedRing);
  inSeatView = false;
  showFlow(`${sector.name} — ${EVENT.ringLabel} from ${CUR}${fromPrice(sector, ACTIVE_RINGS)}`);
}

let assignment = null;
let inSeatView = false;
function makeAssignment() {
  return { row: 1 + Math.floor(Math.random() * 14), seatStart: 1 + Math.floor(Math.random() * 28) };
}

function renderDetail() {
  if (!selected) {
    detailEl.innerHTML = `<p class="hint">Pick a price area on the map or in the list — you choose the area and how many seats together; the allocating engine assigns the actual seats, and you accept or decline them.</p>`;
    return;
  }
  const price = sectorPrice(selected, selectedRing);
  detailEl.innerHTML = `
    <h3>${selected.name}</h3>
    <label class="ring-label">Price area — ${EVENT.ringLabel}
      <select id="ringSel">${ACTIVE_RINGS.map((r) => `<option value="${r.id}" ${r.id === selectedRing.id ? "selected" : ""}>${r.name} — ${CUR}${sectorPrice(selected, r)}</option>`).join("")}</select>
    </label>
    <div class="qtyrow">
      <button id="qMinus" aria-label=" fewer">−</button>
      <span id="qVal">${qty}</span>
      <button id="qPlus" aria-label="more">+</button>
      <span class="unit">× ${CUR}${price}</span>
    </div>
    <div class="total">Total <strong>${CUR}${price * qty}</strong> <span class="mocktag">MOCK PRICES</span></div>
    <div class="qtylabel">Seats together</div>
    <div class="btnrow">
      <button id="seatBtn" class="ghost">View from this area</button>
      <button id="assignBtn" class="cta">Assign my seats →</button>
    </div>
    <div id="assignBox">${assignment ? `
      <div class="receipt" style="border-left-color:var(--tang)">
        <strong>🎟 Assigned for you</strong> — ${selected.name} · ${selectedRing.name}<br>
        Row ${assignment.row} · Seats ${assignment.seatStart}–${assignment.seatStart + qty - 1} — together, by the allocating engine <span class="mocktag">MOCK ALLOCATION</span><br>
        Total <strong>${CUR}${price * qty}</strong>
        <div class="btnrow" style="margin-top:8px">
          <button id="acceptBtn" class="cta">✓ Accept — mint my tickets</button>
          <button id="reassignBtn" class="ghost">↻ Decline — different seats</button>
        </div>
      </div>` : ""}</div>
    <div id="receipt"></div>`;
  document.getElementById("ringSel").addEventListener("change", (e) => {
    selectedRing = ACTIVE_RINGS.find((r) => r.id === e.target.value);
    assignment = null;
    renderDetail();
  });
  document.getElementById("qMinus").addEventListener("click", () => { qty = Math.max(1, qty - 1); assignment = null; renderDetail(); });
  document.getElementById("qPlus").addEventListener("click", () => { qty = Math.min(10, qty + 1); assignment = null; renderDetail(); });
  document.getElementById("seatBtn").addEventListener("click", () => seatView(selected, selectedRing));
  document.getElementById("assignBtn").addEventListener("click", () => {
    assignment = makeAssignment();
    renderDetail();
    document.getElementById("assignBox").scrollIntoView({ behavior: "smooth", block: "center" });
  });
  const acc = document.getElementById("acceptBtn");
  if (acc) acc.addEventListener("click", () => mockCheckout(assignment));
  const rea = document.getElementById("reassignBtn");
  if (rea) rea.addEventListener("click", () => { assignment = makeAssignment(); renderDetail(); });
}

function mockCheckout(asg) {
  const unit = sectorPrice(selected, selectedRing);
  const minted = [];
  for (let i = 0; i < qty; i++) minted.push(mintTicket(selected, selectedRing, unit, "primary", asg ? { row: asg.row, seat: asg.seatStart + i } : null));
  const el = document.getElementById("receipt");
  const ref = "MOCK-" + Math.random().toString(36).slice(2, 8).toUpperCase();
  const idsLabel = minted.length > 1 ? "NFT Tickets #" + minted[0].id + "–#" + minted[minted.length - 1].id : "NFT Ticket #" + minted[0].id;
  el.innerHTML = `<div class="receipt">
    <strong>Mock order ${ref}</strong><br>
    ${qty} × ${selected.name} · ${selectedRing.name} — ${CUR}${sectorPrice(selected, selectedRing) * qty}<br>
    ${asg ? `Seats assigned together: Row ${asg.row} · Seats ${asg.seatStart}–${asg.seatStart + qty - 1}<br>` : ""}
    Event: ${EVENT.receipt}<br>
    <span class="mocktag">MOCK SETTLEMENT</span> ${idsLabel} minted to your wallet — one NFT per seat, each with its own provenance chain — see “My tickets” below. In production this settles in USDC
    on Solana, each ticket carrying its attestation. No funds move in this mock-up.
  </div>`;
}

// --- Camera moves ------------------------------------------------------------
let camAnim = null;
let flightSeq = 0;
function flyTo(targetPos, lookAt) {
  const id = ++flightSeq;
  camAnim = {
    fromPos: camera.position.clone(), toPos: targetPos,
    fromTg: controls.target.clone(), toTg: lookAt,
    start: performance.now(), id,
  };
  // Arrival guarantee: if animation frames are throttled (background tab,
  // busy phone), snap to the destination so the user is never left mid-flight.
  setTimeout(() => {
    if (camAnim && camAnim.id === id) {
      camera.position.copy(targetPos);
      controls.target.copy(lookAt);
      camAnim = null;
    }
  }, 1050);
}
function setRoof(v) { roofBand.visible = v; roofTop.visible = v; }
function sectorPoint(sector, ring, dist, heightPad) {
  const mid = THREE.MathUtils.degToRad((sector.a0 + sector.a1) / 2);
  const r = dist ?? (ring.d0 + ring.d1) / 2;
  return new THREE.Vector3(Math.sin(mid) * r, ring.h0 + (ring.h1 - ring.h0) / 2 + (heightPad ?? 0), Math.cos(mid) * r);
}
function flyToSector(sector, ring) {
  setRoof(true);
  const p = sectorPoint(sector, ring, (ring.d1 + 55), 18);
  flyTo(p, new THREE.Vector3(0, 6, 0));
}
function seatView(sector, ring) {
  setRoof(true);
  const p = sectorPoint(sector, ring, undefined, 1.5);
  flyTo(p, new THREE.Vector3(0, 2, 0));
  inSeatView = true;
  showFlow("The view from your seats");
}

// --- Fluid flow bar: the way out of any focused view, and forward to seats ---
const flowbar = document.getElementById("flowbar");
const flowLabel = document.getElementById("flowLabel");
const flowBack = document.getElementById("flowBack");
function showFlow(label) {
  if (!flowbar) return;
  flowLabel.textContent = label;
  flowBack.textContent = inSeatView ? "⌄ Back to sector" : "⌄ Full venue";
  flowbar.classList.remove("hidden");
}
flowBack.addEventListener("click", () => {
  if (inSeatView && selected) {
    inSeatView = false;
    flyToSector(selected, selectedRing);
    showFlow(`${selected.name} — ${EVENT.ringLabel} from ${CUR}${fromPrice(selected, ACTIVE_RINGS)}`);
  } else {
    inSeatView = false; selected = null; assignment = null;
    renderList(); renderDetail();
    setRoof(true);
    flyTo(new THREE.Vector3(175, 165, 175), new THREE.Vector3(0, 4, 0));
    flowbar.classList.add("hidden");
  }
});
document.getElementById("flowNext").addEventListener("click", () => {
  document.getElementById("detail").scrollIntoView({ behavior: "smooth", block: "center" });
});
document.getElementById("viewOverview").addEventListener("click", () => {
  inSeatView = false;
  setRoof(true);
  flyTo(new THREE.Vector3(175, 165, 175), new THREE.Vector3(0, 4, 0));
  if (!selected && flowbar) flowbar.classList.add("hidden");
});
document.getElementById("viewTop").addEventListener("click", () => {
  inSeatView = false;
  setRoof(false); // seat-map mode: roof off so the bowl interior reads from above
  flyTo(new THREE.Vector3(0.1, 250, 0.1), new THREE.Vector3(0, 0, 0));
  showFlow("Top view — the full seat map");
});

// --- Picking ------------------------------------------------------------------
const raycaster = new THREE.Raycaster();
const ndc = new THREE.Vector2();
let hovered = null;

renderer.domElement.addEventListener("pointermove", (e) => {
  const rect = renderer.domElement.getBoundingClientRect();
  ndc.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
  raycaster.setFromCamera(ndc, camera);
  const hit = raycaster.intersectObjects(pickables, false)[0];
  const sector = hit ? ACTIVE_SECTORS.find((s) => s.id === hit.object.userData.sectorId) : null;
  if (hovered && hovered !== sector) highlight(hovered, false);
  hovered = sector;
  if (sector) {
    highlight(sector, true);
    tooltip.style.display = "block";
    tooltip.style.left = e.clientX + 14 + "px";
    tooltip.style.top = e.clientY + 10 + "px";
    tooltip.textContent = `${sector.name} — from ${CUR}${fromPrice(sector, ACTIVE_RINGS)}`;
    renderer.domElement.style.cursor = "pointer";
  } else {
    tooltip.style.display = "none";
    renderer.domElement.style.cursor = "grab";
  }
});
renderer.domElement.addEventListener("click", () => {
  if (!hovered) return;
  selectedRing = ACTIVE_RINGS.find((r) => r.id === (raycaster.intersectObjects(pickables, false)[0]?.object.userData.ringId)) || selectedRing;
  selectSector(hovered, true);
});

// --- Loop ----------------------------------------------------------------------
function tick() {
  requestAnimationFrame(tick);
  if (camAnim) {
    const p = Math.min(1, (performance.now() - camAnim.start) / 900);
    const k = 1 - Math.pow(1 - p, 3);
    camera.position.lerpVectors(camAnim.fromPos, camAnim.toPos, k);
    controls.target.lerpVectors(camAnim.fromTg, camAnim.toTg, k);
    if (p >= 1) camAnim = null;
  }
  controls.update();
  renderer.render(scene, camera);
  if ((tick.n = (tick.n || 0) + 1) % 20 === 0) {
    const el = document.getElementById("camdbg");
    if (el) {
      const p = camera.position, t = controls.target;
      el.textContent = `CAM ${p.x.toFixed(0)},${p.y.toFixed(0)},${p.z.toFixed(0)} → TGT ${t.x.toFixed(0)},${t.y.toFixed(0)},${t.z.toFixed(0)} · pitch #${pitchMat.color.getHexString()} · roof ${roofBand.visible ? "on" : "off"} · anim ${camAnim ? "flying" : "idle"}`;
    }
  }
}
window.addEventListener("resize", () => {
  camera.aspect = canvasWrap.clientWidth / canvasWrap.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(canvasWrap.clientWidth, canvasWrap.clientHeight);
});

// --- Event switcher (soccer / music / tech convention) -----------------------
function setEvent(ev) {
  EVENT = ev;
  ACTIVE_SECTORS = ev.sectors;
  ACTIVE_RINGS = ev.rings || RINGS;
  CUR = ev.currency;
  selected = null;
  selectedRing = ACTIVE_RINGS[0];
  pitchMat.color.setHex(ev.centerColor);
  document.getElementById("venueName").textContent = `${ev.venue} — ${ev.city}`;
  document.getElementById("fixtureText").innerHTML = ev.banner;
  document.getElementById("eventCard").innerHTML = ev.card;
  document.querySelectorAll("#eventTabs button").forEach((b) =>
    b.classList.toggle("active", b.dataset.event === ev.id));
  buildBowl();
  renderList();
  renderDetail();
  seedResaleFor(ev);
  renderMarket();
  renderEventMarket();
}
const tabsEl = document.getElementById("eventTabs");
if (tabsEl) {
  tabsEl.innerHTML = EVENTS.map((e) =>
    `<button type="button" data-event="${e.id}">${e.tab}</button>`).join("");
  tabsEl.querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => setEvent(EVENTS.find((e) => e.id === b.dataset.event))));
  tabsEl.querySelector("button")?.classList.add("active");
}

document.getElementById("venueName").textContent = `${EVENT.venue} — ${EVENT.city}`;
renderList();
renderDetail();
tick();

// ===========================================================================
// MARKET LAYER (MOCK) — primary NFT mint + secondary resale on LightLink.
// All state is in-memory and labelled MOCK. Production: Tickify.io partner
// integration on LightLink EVM; confidential resale pricing via Arcium MPC
// is the roadmap seam (see the note in the secondary panel).
// ===========================================================================
const MARKET = { wallet: null, tickets: [], counter: 1042 };
const ISSUER = "UZEmarkets (issuer)";
const hex = (n) => [...crypto.getRandomValues(new Uint8Array(n))].map((b) => b.toString(16).padStart(2, "0")).join("");
const newAddr = () => "0x" + hex(20);
const short = (a) => (a === ISSUER ? a : a.slice(0, 6) + "…" + a.slice(-4));

function connectWallet() {
  if (!MARKET.wallet) MARKET.wallet = newAddr();
  document.getElementById("walletAddr").innerHTML =
    `<span class="addr">${MARKET.wallet}</span> <span class="badge mockb">LIGHTLINK · MOCK WALLET</span>`;
  document.getElementById("walletBtn").textContent = "Wallet connected";
  renderMarket();
}
document.getElementById("walletBtn").addEventListener("click", connectWallet);

function mintTicket(sector, ring, price, acquiredVia = "primary", seatInfo = null) {
  if (!MARKET.wallet) connectWallet();
  const t = {
    id: MARKET.counter++,
    eventId: EVENT.id,
    sector: sector.name, ring: ring.name, price,
    ...(seatInfo ? { row: seatInfo.row, seat: seatInfo.seat } : {}),
    owner: MARKET.wallet, listed: null, acquiredVia,
    ree: "0x" + hex(32),
    history: [{ from: ISSUER, to: MARKET.wallet, kind: "Primary mint", hash: "0x" + hex(32) }],
  };
  MARKET.tickets.push(t);
  renderMarket();
  return t;
}

function seedResaleFor(ev) {
  if (MARKET.tickets.some((t) => t.eventId === ev.id)) return;
  let seeds;
  if (ev.id === "soccer") {
    seeds = [
      { sector: "Tribuna Central", ring: "Lower Ring", price: 460 },
      { sector: "Gol Nord", ring: "Middle Ring", price: 165 },
      { sector: "Lateral Central", ring: "Upper Ring", price: 285 },
    ];
  } else {
    const rings = ev.rings || RINGS;
    const picks = [ev.sectors[0], ev.sectors[Math.floor(ev.sectors.length / 2)], ev.sectors[ev.sectors.length - 1]];
    seeds = picks.map((sec, i) => { const r = rings[i % rings.length]; return { sector: sec.name, ring: r.name, price: Math.round(sectorPrice(sec, r) * 1.1) }; });
  }
  for (const sd of seeds) {
    const owner = newAddr();
    MARKET.tickets.push({
      id: MARKET.counter++, eventId: ev.id, ...sd, owner, listed: sd.price, acquiredVia: "secondary", ree: "0x" + hex(32),
      history: [{ from: ISSUER, to: owner, kind: "Primary mint", hash: "0x" + hex(32) }],
    });
  }
}

function provenance(t) {
  return `<ul class="prov">${t.history.map((h) =>
    `<li><strong>${h.kind}:</strong> ${short(h.from)} → ${short(h.to)}<br><span class="hash">tx ${h.hash}</span></li>`).join("")}</ul>`;
}

// Mock secondary index: the premium the secondary market currently puts on a
// ticket over its primary (launch) price — deterministic per ticket (demo).
function secIndex(t) { return Math.round(t.price * (1.12 + (t.id % 34) / 100)); }
function secPct(t) { return Math.round((secIndex(t) / t.price - 1) * 100); }

function renderMarket() {
  const mine = MARKET.tickets.filter((t) => MARKET.wallet && t.owner === MARKET.wallet && t.eventId === EVENT.id);
  document.getElementById("myTickets").innerHTML = mine.length ? mine.map((t) => `
    <div class="ticket"><span class="tid">NFT Ticket #${t.id}</span> — ${t.sector} · ${t.ring}${t.seat ? ` · Row ${t.row} · Seat ${t.seat}` : ""} · ${CUR}${t.price}<br>
    <span class="badge">✓ REE + TEE ATTESTED (MOCK)</span> <span class="badge mockb">ISSUED BY UZEMARKETS</span><br>
    <span class="hash">REE receipt ${t.ree}</span><br>
    Primary (launch) price: <strong>${CUR}${t.price}</strong> · Secondary index now: <strong>${CUR}${secIndex(t)}</strong> <span class="prize">(+${secPct(t)}% hold margin)</span><br>
    ${t.listed ? `<em>Listed for resale at ${CUR}${t.listed}</em>` :
      `<span class="listrow">Ask ${CUR}<input type="number" class="askIn" data-ask="${t.id}" value="${secIndex(t)}" min="1" step="1"> <button class="list" data-list="${t.id}">List for resale</button></span>`}
    </div>`).join("")
    : `<p class="hint">No tickets yet — mint one with “Mock checkout” above.</p>`;

  const resale = MARKET.tickets.filter((t) => t.listed && t.eventId === EVENT.id);
  document.getElementById("resaleList").innerHTML = resale.length ? resale.map((t) => `
    <div class="ticket"><span class="tid">NFT Ticket #${t.id}</span> — ${t.sector} · ${t.ring}${t.seat ? ` · Row ${t.row} · Seat ${t.seat}` : ""}<br>
    ${t.owner === MARKET.wallet ? `<span class="badge mockb">YOUR LISTING</span> · <strong>${CUR}${t.listed}</strong><br>` : `Seller <span class="addr">${short(t.owner)}</span> · <strong>${CUR}${t.listed}</strong><br>`}
    <span class="badge">✓ PROVENANCE VERIFIABLE</span><br>
    ${t.owner === MARKET.wallet ? `<em>Your seat, live on the secondary market — the margin position, visible to every buyer here.</em>` : `<button class="buy" data-buy="${t.id}">Buy — NFT transfers to my wallet</button>`}</div>`).join("")
    : `<p class="hint">No resale listings right now.</p>`;

  const sel = document.getElementById("verifySel");
  const evTickets = MARKET.tickets.filter((t) => t.eventId === EVENT.id);
  sel.innerHTML = evTickets.map((t) => `<option value="${t.id}">NFT Ticket #${t.id} — ${t.sector} · ${t.ring}</option>`).join("");
  if (evTickets.length) showVerify(Number(sel.value || evTickets[0].id));

  document.querySelectorAll("[data-list]").forEach((b) => b.addEventListener("click", () => {
    const t = MARKET.tickets.find((x) => x.id === Number(b.dataset.list));
    const inp = document.querySelector(`[data-ask="${t.id}"]`);
    const ask = Number(inp && inp.value);
    if (ask > 0) { t.listed = ask; renderMarket(); }
  }));
  document.querySelectorAll("[data-buy]").forEach((b) => b.addEventListener("click", () => {
    if (!MARKET.wallet) connectWallet();
    const t = MARKET.tickets.find((x) => x.id === Number(b.dataset.buy));
    const paid = t.listed;
    t.history.push({ from: t.owner, to: MARKET.wallet, kind: `Secondary sale · ${CUR}${paid}`, hash: "0x" + hex(32) });
    t.owner = MARKET.wallet; t.price = paid; t.listed = null; t.acquiredVia = "secondary";
    renderMarket();
  }));
}

function showVerify(id) {
  const t = MARKET.tickets.find((x) => x.id === id);
  if (!t) return;
  document.getElementById("verifyOut").innerHTML = `
    <div class="ticket"><span class="tid">NFT Ticket #${t.id}</span> — ${t.sector} · ${t.ring}<br>
    Current owner <span class="addr">${short(t.owner)}</span><br>
    <span class="badge">✓ GENUINE — ISSUED BY UZEMARKETS (MOCK VERIFICATION)</span><br>
    <span class="hash">REE receipt ${t.ree} · TEE attestation sealed at mint</span>
    ${provenance(t)}</div>`;
}
document.getElementById("verifySel").addEventListener("change", (e) => showVerify(Number(e.target.value)));
seedResaleFor(EVENT);
renderMarket();

// --- UZE EVENT MARKET (MOCK) -------------------------------------------------
// Branding (James, 2026-11-12): the product is the UZE Event Market — the
// underlying market plumbing is never branded. Mechanic: call the settled
// secondary price; on settlement the two closest calls win tickets — closest
// wins a PAIR (grand prize), second closest a SINGLE (consolation), minted as
// the same attested NFTs into the winner's wallet.
const EM_BY_EVENT = {};
function makeEM(ev) {
  const rings = ev.rings || RINGS;
  let focus = ev.emFocus;
  if (!focus) {
    const top = ev.sectors.reduce((a, b) => (b.base > a.base ? b : a));
    focus = { sector: top.name, ring: rings[0].name };
  }
  if (ev.id === "soccer") {
    return { settled: false, settledPrice: 612, focus, minCall: 50,
      calls: [ { addr: newAddr(), call: 540 }, { addr: newAddr(), call: 588 },
        { addr: newAddr(), call: 645 }, { addr: newAddr(), call: 701 },
        { addr: newAddr(), call: 488 } ] };
  }
  const fs = ev.sectors.find((x) => x.name === focus.sector) || ev.sectors[0];
  const fr = rings.find((x) => x.name === focus.ring) || rings[0];
  const fp = sectorPrice(fs, fr);
  const settledPrice = Math.round((fp * 1.3) / 5) * 5;
  return { settled: false, settledPrice, focus, minCall: Math.max(5, Math.round(fp * 0.1)),
    calls: [0.82, 0.93, 1.02, 1.1, 1.21].map((m) => ({ addr: newAddr(), call: Math.round((settledPrice * m) / 5) * 5 })) };
}
const emState = () => (EM_BY_EVENT[EVENT.id] ??= makeEM(EVENT));

function emIntroHTML(EM) {
  return `For big fixtures, the market itself becomes the game. Call the price <strong>${EM.focus.sector} (${EM.focus.ring})</strong>
  will settle at in the secondary market by event week for <strong>${EVENT.emName}</strong>. When the market settles,
  the <strong>two closest calls</strong> win tickets: closest call takes the <span class="prize">grand prize \u2014 a PAIR of tickets</span>;
  second closest takes the <span class="prize">consolation \u2014 a SINGLE ticket</span>. Prize tickets are minted as the same attested
  NFTs, straight into the winner's wallet. Prize inventory is held back from the platform's own primary allocation \u2014 never bought
  off the secondary market, so nobody can pump the index to inflate a prize. Calls are open to primary ticket holders only:
  you must own the asset to price its secondary market. Every call is a signal the supply side prices against \u2014 demand, revealed
  before on-sale. Positions bridge in via <strong>NEAR Intents</strong> (mocked here).`;
}

function renderEventMarket() {
  const EM = emState();
  document.getElementById("emIntro").innerHTML = emIntroHTML(EM);
  document.getElementById("callLabel").textContent = `Your call (${CUR}):`;
  document.getElementById("callInput").placeholder = `e.g. ${EM.settledPrice}`;
  document.getElementById("callStatus").textContent = "Primary ticket holders only \u2014 buy in the primary market above and your call unlocks. One call per wallet in this mock.";
  const sb = document.getElementById("settleBtn");
  sb.disabled = EM.settled; sb.textContent = EM.settled ? "Market settled" : "Settle the market (mock)";
  document.getElementById("settleOut").textContent = "";
  renderBoard();
}

function renderBoard() {
  const EM = emState();
  const rows = [...EM.calls].sort((x, y) =>
    EM.settled
      ? Math.abs(x.call - EM.settledPrice) - Math.abs(y.call - EM.settledPrice)
      : x.call - y.call);
  const prizeOf = (i) => !EM.settled ? "" :
    i === 0 ? '<span class="prize">\U0001F947 PAIR OF TICKETS \u2014 GRAND PRIZE</span>' :
    i === 1 ? '<span class="prize">\U0001F948 SINGLE TICKET \u2014 CONSOLATION</span>' : "";
  document.getElementById("board").innerHTML =
    `<table class="board"><tr><th>Wallet</th><th>Call (${CUR})</th>${EM.settled ? "<th>Off by</th><th></th>" : ""}</tr>` +
    rows.map((c, i) => `<tr><td>${short(c.addr)}${MARKET.wallet && c.addr === MARKET.wallet ? " (you)" : ""}</td><td><strong>${c.call}</strong></td>` +
      (EM.settled ? `<td>${Math.abs(c.call - EM.settledPrice)}</td><td>${prizeOf(i)}</td>` : "") + `</tr>`).join("") +
    `</table>` + (EM.settled ? `<p class="hint" style="margin-top:6px">Settled at <strong>${CUR}${EM.settledPrice}</strong> (mock settlement).</p>` : "");
}
document.getElementById("callBtn").addEventListener("click", () => {
  if (!MARKET.wallet) connectWallet();
  const EM = emState();
  const v = Number(document.getElementById("callInput").value);
  const st = document.getElementById("callStatus");
  const holdsPrimary = MARKET.tickets.some((t) => t.owner === MARKET.wallet && t.acquiredVia === "primary" && t.eventId === EVENT.id);
  if (!holdsPrimary) { st.textContent = "Calls are open to primary ticket holders only \u2014 you must own the asset to price its secondary market. Buy in the primary market above; your call unlocks with your ticket."; return; }
  if (!v || v < EM.minCall) { st.textContent = `Enter a call of at least ${CUR}${EM.minCall}.`; return; }
  const mine = EM.calls.find((c) => c.addr === MARKET.wallet);
  if (mine) mine.call = v; else EM.calls.push({ addr: MARKET.wallet, call: v });
  st.textContent = `Call recorded: ${CUR}${v} from your wallet. Settle the market to see if you take the pair.`;
  renderBoard();
});
document.getElementById("settleBtn").addEventListener("click", (e) => {
  const EM = emState();
  if (EM.settled) return;
  EM.settled = true;
  e.target.disabled = true; e.target.textContent = "Market settled";
  const ranked = [...EM.calls].sort((x, y) =>
    Math.abs(x.call - EM.settledPrice) - Math.abs(y.call - EM.settledPrice));
  const out = document.getElementById("settleOut");
  let msg = `Settled at ${CUR}${EM.settledPrice}. Closest call: ${short(ranked[0].addr)} (${CUR}${ranked[0].call}) wins the PAIR. Second: ${short(ranked[1].addr)} (${CUR}${ranked[1].call}) wins a SINGLE.`;
  if (MARKET.wallet) {
    const myRank = ranked.findIndex((c) => c.addr === MARKET.wallet);
    if (myRank === 0) { mintTicket({ name: EM.focus.sector }, { name: EM.focus.ring }, EM.settledPrice, "prize"); mintTicket({ name: EM.focus.sector }, { name: EM.focus.ring }, EM.settledPrice, "prize"); msg += " \U0001F3C6 That's YOU \u2014 two prize NFTs minted to your wallet (see My tickets above)."; }
    else if (myRank === 1) { mintTicket({ name: EM.focus.sector }, { name: EM.focus.ring }, EM.settledPrice, "prize"); msg += " \U0001F948 That's YOU \u2014 one prize NFT minted to your wallet (see My tickets above)."; }
    else if (myRank > 1) msg += ` Your call placed #${myRank + 1} \u2014 no prize this time.`;
  }
  out.innerHTML = msg;
  renderBoard();
});
renderEventMarket();
