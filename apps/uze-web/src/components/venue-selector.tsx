"use client";

// UZE Venue Selector — demo filler for the Tickets (B2C) surface.
// Venue-as-data: the bowl is generated procedurally from the SECTORS x
// RINGS tables in @/lib/venue-data. Three.js is loaded from the pinned
// CDN build (the same r128 UMD line the standalone mock-up in
// DEVBUILDSTACK/uze-venue-ticketing uses) so this page adds no package
// dependency to uze-web. MOCK: no live inventory, no real settlement.

import { useEffect, useRef, useState } from "react";
import { VENUE, SECTORS, RINGS, sectorPrice, fromPrice, type Sector, type Ring } from "@/lib/venue-data";

declare global {
  interface Window { THREE: any }
}

const THREE_CDN = [
  "https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js",
  "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js",
];

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("failed to load " + src));
    document.head.appendChild(s);
  });
}

interface SceneApi {
  select: (sector: Sector, ring: Ring, fly: boolean) => void;
  seatView: (sector: Sector, ring: Ring) => void;
  overview: () => void;
  top: () => void;
}

export default function VenueSelector() {
  const mountRef = useRef<HTMLDivElement>(null);
  const apiRef = useRef<SceneApi | null>(null);
  const [ready, setReady] = useState(false);
  const [selected, setSelected] = useState<Sector | null>(null);
  const [ring, setRing] = useState<Ring>(RINGS[0]);
  const [qty, setQty] = useState(2);
  const [receipt, setReceipt] = useState<string | null>(null);

  useEffect(() => {
    let disposed = false;
    (async () => {
      for (const src of THREE_CDN) {
        if (!(window as any).THREE || src.includes("OrbitControls")) await loadScript(src);
      }
      if (disposed || !mountRef.current) return;
      const THREE = window.THREE;
      const mount = mountRef.current;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x101418);
      const camera = new THREE.PerspectiveCamera(50, mount.clientWidth / mount.clientHeight, 0.1, 1000);
      camera.position.set(150, 110, 150);
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(mount.clientWidth, mount.clientHeight);
      mount.appendChild(renderer.domElement);
      const controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.maxPolarAngle = Math.PI * 0.49;
      controls.minDistance = 25;
      controls.maxDistance = 320;

      scene.add(new THREE.AmbientLight(0xffffff, 0.55));
      const sun = new THREE.DirectionalLight(0xffffff, 1.1);
      sun.position.set(120, 180, 60);
      scene.add(sun);

      const pitch = new THREE.Mesh(
        new THREE.BoxGeometry(68, 1, 44),
        new THREE.MeshStandardMaterial({ color: 0x2f7d32, roughness: 1 })
      );
      pitch.position.y = 0.5;
      scene.add(pitch);

      const pickables: any[] = [];
      const bySector = new Map<string, any[]>();
      for (const r of RINGS) {
        const rMid = (r.d0 + r.d1) / 2;
        const h = r.h1 - r.h0;
        for (const s of SECTORS) {
          const a0 = THREE.MathUtils.degToRad(s.a0);
          const a1 = THREE.MathUtils.degToRad(s.a1);
          const mesh = new THREE.Mesh(
            new THREE.CylinderGeometry(rMid, rMid, h, 6, 1, true, a0, a1 - a0),
            new THREE.MeshStandardMaterial({ color: s.color, roughness: 0.85, side: THREE.DoubleSide })
          );
          mesh.position.y = r.h0 + h / 2;
          mesh.userData = { sectorId: s.id, ringId: r.id };
          scene.add(mesh);
          pickables.push(mesh);
          if (!bySector.has(s.id)) bySector.set(s.id, []);
          bySector.get(s.id)!.push(mesh);
        }
        const walk = new THREE.Mesh(
          new THREE.CylinderGeometry(r.d1 + 1, r.d1 + 1, 0.8, 64, 1, false),
          new THREE.MeshStandardMaterial({ color: 0x3a4149, roughness: 1 })
        );
        walk.position.y = r.h0 - 0.4;
        scene.add(walk);
      }

      let current: Sector | null = null;
      const highlight = (sector: Sector | null, on: boolean) => {
        if (!sector) return;
        for (const m of bySector.get(sector.id) || []) {
          m.material.emissive = new THREE.Color(on ? 0xff6b00 : 0x000000);
          m.material.emissiveIntensity = on ? 0.35 : 0;
        }
      };

      let anim: any = null;
      const flyTo = (pos: any, tg: any) => {
        anim = { fp: camera.position.clone(), tp: pos, ft: controls.target.clone(), tt: tg, t: 0 };
      };
      const midAngle = (s: Sector) => THREE.MathUtils.degToRad((s.a0 + s.a1) / 2);
      const api: SceneApi = {
        select: (sector, r, fly) => {
          highlight(current, false);
          current = sector;
          highlight(sector, true);
          if (fly) {
            const mid = midAngle(sector);
            const dist = r.d1 + 55;
            flyTo(new THREE.Vector3(Math.sin(mid) * dist, r.h0 + (r.h1 - r.h0) / 2 + 18, Math.cos(mid) * dist), new THREE.Vector3(0, 6, 0));
          }
        },
        seatView: (sector, r) => {
          const mid = midAngle(sector);
          const dist = (r.d0 + r.d1) / 2;
          flyTo(new THREE.Vector3(Math.sin(mid) * dist, r.h0 + (r.h1 - r.h0) / 2 + 1.5, Math.cos(mid) * dist), new THREE.Vector3(0, 2, 0));
        },
        overview: () => flyTo(new THREE.Vector3(150, 110, 150), new THREE.Vector3(0, 4, 0)),
        top: () => flyTo(new THREE.Vector3(0.1, 240, 0.1), new THREE.Vector3(0, 0, 0)),
      };
      apiRef.current = api;

      const raycaster = new THREE.Raycaster();
      const ndc = new THREE.Vector2();
      const onClick = (e: MouseEvent) => {
        const rect = renderer.domElement.getBoundingClientRect();
        ndc.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
        raycaster.setFromCamera(ndc, camera);
        const hit = raycaster.intersectObjects(pickables, false)[0];
        if (!hit) return;
        const sector = SECTORS.find((s) => s.id === hit.object.userData.sectorId);
        const r = RINGS.find((x) => x.id === hit.object.userData.ringId) || RINGS[0];
        if (sector) {
          setRing(r);
          setSelected(sector);
          setReceipt(null);
          api.select(sector, r, true);
        }
      };
      renderer.domElement.addEventListener("click", onClick);

      let raf = 0;
      const tick = () => {
        raf = requestAnimationFrame(tick);
        if (anim) {
          anim.t = Math.min(1, anim.t + 0.02);
          const k = 1 - Math.pow(1 - anim.t, 3);
          camera.position.lerpVectors(anim.fp, anim.tp, k);
          controls.target.lerpVectors(anim.ft, anim.tt, k);
          if (anim.t >= 1) anim = null;
        }
        controls.update();
        renderer.render(scene, camera);
      };
      tick();
      setReady(true);

      return () => {
        cancelAnimationFrame(raf);
        renderer.domElement.removeEventListener("click", onClick);
        renderer.dispose();
        mount.removeChild(renderer.domElement);
      };
    })();
    return () => { disposed = true; };
  }, []);

  const pickFromList = (s: Sector) => {
    setSelected(s);
    setReceipt(null);
    apiRef.current?.select(s, ring, true);
  };

  const price = selected ? sectorPrice(selected, ring) : 0;

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
        <button type="button" onClick={() => apiRef.current?.overview()}>Overview</button>
        <button type="button" onClick={() => apiRef.current?.top()}>Top view</button>
        {!ready && <span style={{ opacity: 0.65 }}>Loading 3D…</span>}
      </div>
      <div ref={mountRef} style={{ width: "100%", height: 520, borderRadius: 12, overflow: "hidden", background: "#101418" }} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(150px,1fr))", gap: 8, marginTop: 14 }}>
        {SECTORS.map((s) => (
          <button key={s.id + s.name} type="button" onClick={() => pickFromList(s)}
            style={{ textAlign: "left", padding: "8px 10px", borderRadius: 9, border: selected?.id === s.id ? "2px solid #ff6b00" : "1px solid #ddd", background: "#fff", cursor: "pointer" }}>
            <span style={{ display: "inline-block", width: 11, height: 11, borderRadius: 3, background: "#" + s.color.toString(16).padStart(6, "0"), marginRight: 7 }} />
            {s.name}<br /><span style={{ opacity: 0.65, fontSize: 12 }}>from €{fromPrice(s)}</span>
          </button>
        ))}
      </div>
      {selected ? (
        <div style={{ marginTop: 16, borderTop: "1px solid #e3ded6", paddingTop: 12 }}>
          <h3 style={{ margin: "0 0 8px" }}>{selected.name} — {VENUE.name}, {VENUE.city}</h3>
          <label>Ring{" "}
            <select value={ring.id} onChange={(e) => setRing(RINGS.find((r) => r.id === e.target.value) || RINGS[0])}>
              {RINGS.map((r) => <option key={r.id} value={r.id}>{r.name} — €{sectorPrice(selected, r)}</option>)}
            </select>
          </label>{" "}
          <label>Qty{" "}
            <select value={qty} onChange={(e) => setQty(Number(e.target.value))}>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>{" "}
          <strong>Total €{price * qty}</strong>{" "}
          <span style={{ background: "#ff6b00", color: "#fff", fontSize: 10, letterSpacing: ".1em", padding: "2px 7px", borderRadius: 999 }}>MOCK PRICES</span>
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <button type="button" onClick={() => apiRef.current?.seatView(selected, ring)}>Seat view</button>
            <button type="button" onClick={() => setReceipt("MOCK-" + Math.random().toString(36).slice(2, 8).toUpperCase())}
              style={{ background: "#ff6b00", color: "#fff", border: "none", padding: "10px 18px", borderRadius: 999, cursor: "pointer" }}>
              Mock checkout
            </button>
          </div>
          {receipt && (
            <p style={{ marginTop: 12, border: "1px dashed #ff6b00", borderRadius: 9, padding: 10 }}>
              <strong>Mock order {receipt}</strong> — {qty} × {selected.name} · {ring.name} — €{price * qty}.<br />
              Event: Internacional vs São Paulo FC · January 2027 (demo fixture).<br />
              <em>Mock settlement:</em> in production this settles in USDC on Solana with GIRAx attestation of the ticket. No funds move in this demo.
            </p>
          )}
        </div>
      ) : (
        <p style={{ marginTop: 16, fontStyle: "italic", opacity: 0.7 }}>Pick a sector on the map or in the list. Drag to rotate, scroll to zoom.</p>
      )}
    </div>
  );
}
