// M2 exit demonstrations (merged program amendment A2) + gate coverage.
//   (i)   within-limits provision -> meter -> terminate, full chronicle
//   (ii)  over-limit call refused BEFORE execution, refusal chronicled
//   (iii) revoke cascade: session dies, later calls refused, in-flight
//         call completes
// Plus: wallet auth (good + bad signature), tier gate, dark tools (A3),
// allowed-tools, per-day limit, cross-principal isolation, and a stdio
// transport smoke test. Run: node test.mjs
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import crypto from "node:crypto";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

process.env.INSTANT_MCP_DATA_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "instant-mcp-test-"));
process.env.INSTANT_MCP_ADMIN_TOKEN = "test-admin-token";
process.env.MOCK_PROVISION_MS = "500";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const { createServer } = await import("./server.mjs");
const { base58Encode } = await import("./lib/base58.mjs");

let passed = 0, failed = 0;
const check = (name, cond, detail = "") => {
  if (cond) { passed++; console.log(`ok - ${name}`); }
  else { failed++; console.log(`FAIL - ${name}${detail ? ` :: ${detail}` : ""}`); }
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function makeWallet() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync("ed25519");
  const der = publicKey.export({ format: "der", type: "spki" });
  const address = base58Encode(der.subarray(der.length - 32));
  return { address, sign: (msg) => crypto.sign(null, Buffer.from(msg), privateKey).toString("base64") };
}

const server = createServer();
await new Promise((r) => server.listen(0, r));
const BASE = `http://127.0.0.1:${server.address().port}`;
let rpcId = 0;

async function rpc(method, params = {}, token = null) {
  const res = await fetch(`${BASE}/mcp`, {
    method: "POST",
    headers: { "content-type": "application/json", ...(token ? { authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify({ jsonrpc: "2.0", id: ++rpcId, method, params }),
  });
  return res.json();
}
const callTool = (name, args, token) => rpc("tools/call", { name, arguments: args }, token);
const toolPayload = (r) => r?.result?.structuredContent || null;
const admin = async (method, p, b) => {
  const res = await fetch(`${BASE}${p}`, { method, headers: { "content-type": "application/json", "x-admin-token": "test-admin-token" }, body: b ? JSON.stringify(b) : undefined });
  return res.json();
};
const chronicle = async () => (await admin("GET", "/admin/chronicle")).events;
const eventsFor = async (wallet, type, tool) => (await chronicle()).filter((e) => e.principal === wallet && e.type === type && (!tool || e.tool === tool));

async function signIn(wallet) {
  const ch = await rpc("uze/challenge", { wallet: wallet.address });
  const v = await rpc("uze/verify", { wallet: wallet.address, signature: wallet.sign(ch.result.message) });
  return v.result?.sessionToken;
}

// ---------- setup: principals (layer a — user pre-authorization) ----------
const A = makeWallet(); // instance tier, generous limits
const B = makeWallet(); // instance tier, per-call max below the provision price
const C = makeWallet(); // markets tier
const D = makeWallet(); // instance tier, small per-day max
const E = makeWallet(); // authenticated but NO pre-authorization
const F = makeWallet(); // instance tier, generous — isolation counterpart
await admin("POST", "/admin/principals", { wallet: A.address, tier: "instance", limits: { perCallMax: 10000, perDayMax: 100000 } });
await admin("POST", "/admin/principals", { wallet: B.address, tier: "instance", limits: { perCallMax: 100, perDayMax: 100000 } });
await admin("POST", "/admin/principals", { wallet: C.address, tier: "markets", limits: { perCallMax: 10000, perDayMax: 100000 } });
await admin("POST", "/admin/principals", { wallet: D.address, tier: "instance", limits: { perCallMax: 10000, perDayMax: 1200 } });
await admin("POST", "/admin/principals", { wallet: F.address, tier: "instance", limits: { perCallMax: 10000, perDayMax: 100000 } });

// ---------- protocol + catalog ----------
const init = await rpc("initialize", { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "m2-test", version: "0" } });
check("initialize negotiates protocol 2025-06-18", init.result?.protocolVersion === "2025-06-18");
const list = await rpc("tools/list");
const toolNames = (list.result?.tools || []).map((t) => t.name).sort();
check("tools/list exposes exactly the 9 base tools", JSON.stringify(toolNames) === JSON.stringify(["create_escrow", "get_credentials", "get_status", "list_tiers", "pay_via_x402", "provision_instance", "query_balance", "release_milestone", "terminate_instance"]), toolNames.join(","));
check("dark tools are discoverable and labeled 'Available M3'", (list.result?.tools || []).filter((t) => ["create_escrow", "release_milestone"].includes(t.name)).every((t) => t.description.includes("Available M3")));

// ---------- auth ----------
const badCh = await rpc("uze/challenge", { wallet: A.address });
const badVerify = await rpc("uze/verify", { wallet: A.address, signature: B.sign(badCh.result.message) });
check("bad signature is refused", !!badVerify.error, JSON.stringify(badVerify));
check("bad signature refusal is chronicled", (await eventsFor(A.address, "auth.refused")).some((e) => e.reason === "bad_signature"));
const noAuth = await callTool("list_tiers", {}, null);
check("unauthenticated tools/call is refused", noAuth.error?.code === -32003, JSON.stringify(noAuth));

const tokenA = await signIn(A);
const tokenA2 = await signIn(A); // second session for the same principal
const tokenB = await signIn(B);
const tokenC = await signIn(C);
const tokenD = await signIn(D);
const tokenE = await signIn(E);
const tokenF = await signIn(F);
check("wallet sign-in issues sessions", !!(tokenA && tokenB && tokenC && tokenD && tokenE && tokenF));

// ---------- A2 demo (i): provision -> meter -> terminate within limits ----------
const prov = await callTool("provision_instance", { tier: "instance", spec: { size: "KVM1" } }, tokenA);
const provPayload = toolPayload(prov);
check("(i) provision executes within limits", provPayload?.instance_id?.startsWith("inst_") && provPayload.state === "active", JSON.stringify(prov));
const instId = provPayload?.instance_id;
await sleep(800);
const status = toolPayload(await callTool("get_status", { instance_id: instId }, tokenA));
check("(i) usage ticks accrue while active (metering)", status?.usageTicks >= 3 && status?.computeAccrued === status.usageTicks * 5, JSON.stringify(status));
const creds = toolPayload(await callTool("get_credentials", { instance_id: instId }, tokenA));
check("(i) credentials are labeled LOCAL MOCK", (creds?.provider || "").includes("LOCAL MOCK"), JSON.stringify(creds));
const term = toolPayload(await callTool("terminate_instance", { instance_id: instId }, tokenA));
check("(i) terminate executes with final usage", term?.state === "terminated" && term?.finalUsage?.usageTicks >= 3, JSON.stringify(term));
const aEvents = await chronicle();
const seqOf = (type, tool) => aEvents.find((e) => e.principal === A.address && e.type === type && (!tool || e.tool === tool))?.seq;
check("(i) full chronicle present, in order: provisioned < status < terminate",
  seqOf("instance.provisioned") < seqOf("tool.executed", "get_status") && seqOf("tool.executed", "get_status") < seqOf("instance.terminated"));
check("(i) provision call metered at 500 in the chronicle", aEvents.some((e) => e.principal === A.address && e.type === "tool.executed" && e.tool === "provision_instance" && e.meter === 500));

// ---------- A2 demo (ii): over-limit refused BEFORE execution ----------
const bBefore = (await chronicle()).length;
const over = await callTool("provision_instance", { tier: "instance", spec: { size: "KVM1" } }, tokenB);
const overPayload = toolPayload(over);
check("(ii) over-per-call-limit provision is refused", overPayload?.refused === true && overPayload?.reason === "over_per_call_limit", JSON.stringify(over));
const bEvents = (await chronicle()).slice(bBefore);
check("(ii) refusal recorded as a chronicle Event", bEvents.some((e) => e.principal === B.address && e.type === "tool.refused" && e.reason === "over_per_call_limit"));
check("(ii) nothing executed for B (refused before execution)", !bEvents.some((e) => e.principal === B.address && (e.type === "tool.executed" || e.type === "instance.provisioned")));

// ---------- dark tools (A3) + tier gate + pre-authorization ----------
const dark = toolPayload(await callTool("create_escrow", { engagement: "eng_1", amount: 100 }, tokenA));
check("create_escrow ships DARK: refused 'available_m3'", dark?.refused === true && dark?.reason === "available_m3" && /available M3/.test(dark?.message || ""), JSON.stringify(dark));
const dark2 = toolPayload(await callTool("release_milestone", { escrow: "esc_1", milestone: "m1" }, tokenA));
check("release_milestone ships DARK: refused 'available_m3'", dark2?.refused === true && dark2?.reason === "available_m3");
check("dark refusals are chronicled", (await eventsFor(A.address, "tool.refused", "create_escrow")).some((e) => e.reason === "available_m3"));
const tierRefusal = toolPayload(await callTool("open_position", { market: "m", side: "yes", amount: 1 }, tokenA));
check("tier gate: Instance principal cannot call Markets tool open_position", tierRefusal?.refused === true && tierRefusal?.reason === "tier_gate", JSON.stringify(tierRefusal));
const marketsDark = toolPayload(await callTool("open_position", { market: "m", side: "yes", amount: 1 }, tokenC));
check("Markets principal passes the tier gate (refused only as M3-dark)", marketsDark?.refused === true && marketsDark?.reason === "available_m3", JSON.stringify(marketsDark));
const tierProv = toolPayload(await callTool("provision_instance", { tier: "markets", spec: {} }, tokenA));
check("tier gate: Instance principal cannot provision a Markets instance", tierProv?.refused === true && tierProv?.reason === "tier_gate");
const noPre = toolPayload(await callTool("provision_instance", { tier: "instance", spec: {} }, tokenE));
check("no pre-authorization on file -> refused", noPre?.refused === true && noPre?.reason === "no_pre_authorization", JSON.stringify(noPre));

// ---------- metering: x402 payments + per-day limit + isolation ----------
const pay1 = toolPayload(await callTool("pay_via_x402", { amount: 800, currency: "USDC" }, tokenD));
check("pay_via_x402 executes within limits (mock ledger)", pay1?.status === "recorded" && pay1?.amount === 800, JSON.stringify(pay1));
const pay2 = toolPayload(await callTool("pay_via_x402", { amount: 800, currency: "USDC" }, tokenD));
check("second payment refused: over_daily_limit (800+800 > 1200)", pay2?.refused === true && pay2?.reason === "over_daily_limit", JSON.stringify(pay2));
const bal = toolPayload(await callTool("query_balance", { wallet: D.address }, tokenD));
check("mock balance reflects the one executed payment", bal?.balance === 1_000_000 - 800, JSON.stringify(bal));
const isoProv = toolPayload(await callTool("provision_instance", { tier: "instance", spec: {} }, tokenF));
const isoStatus = toolPayload(await callTool("get_status", { instance_id: isoProv?.instance_id }, tokenA));
check("isolation: A cannot read F's instance", isoStatus?.refused === true && isoStatus?.reason === "not_owner", JSON.stringify(isoStatus));

// ---------- A2 demo (iii): revoke cascade ----------
const inFlight = callTool("provision_instance", { tier: "instance", spec: { size: "KVM2" } }, tokenA);
await sleep(80); // the call is admitted and inside the mock spin-up
const revoke = await admin("POST", "/admin/revoke", { wallet: A.address });
check("(iii) revoke reports both sessions killed", revoke?.sessionsKilled === 2, JSON.stringify(revoke));
const inFlightRes = toolPayload(await inFlight);
check("(iii) in-flight call completes despite the revoke", inFlightRes?.instance_id?.startsWith("inst_") && inFlightRes?.state === "active", JSON.stringify(inFlightRes));
const after1 = await callTool("get_status", { instance_id: inFlightRes?.instance_id }, tokenA);
check("(iii) subsequent call on the killed session is refused", after1.error?.code === -32003, JSON.stringify(after1));
const after2 = await callTool("list_tiers", {}, tokenA2);
check("(iii) the principal's other session is dead too", after2.error?.code === -32003, JSON.stringify(after2));
const reAuth = await rpc("uze/challenge", { wallet: A.address });
const reVerify = await rpc("uze/verify", { wallet: A.address, signature: A.sign(reAuth.result.message) });
check("(iii) revoked principal cannot sign in again", !!reVerify.error, JSON.stringify(reVerify));
check("(iii) cascade is chronicled (principal.revoked + session.revoked + refusal)",
  (await eventsFor(A.address, "principal.revoked")).length === 1 &&
  (await eventsFor(A.address, "session.revoked")).length === 2 &&
  (await eventsFor(null, "tool.refused")).some((e) => e.reason === "unauthenticated"));

// ---------- stdio transport smoke ----------
{
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "instant-mcp-stdio-"));
  const w = makeWallet();
  fs.writeFileSync(path.join(dir, "state.json"), JSON.stringify({
    principals: [{ wallet: w.address, tier: "instance", limits: { perCallMax: 10000, perDayMax: 100000 }, revoked: false, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }],
    instances: [],
  }));
  const child = spawn(process.execPath, [path.join(ROOT, "server.mjs"), "--stdio"], {
    env: { ...process.env, INSTANT_MCP_DATA_DIR: dir, INSTANT_MCP_ADMIN_TOKEN: "x" },
    stdio: ["pipe", "pipe", "pipe"],
  });
  const pending = new Map();
  let buf = "";
  child.stdout.on("data", (d) => {
    buf += d;
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i); buf = buf.slice(i + 1);
      if (!line.trim()) continue;
      const msg = JSON.parse(line);
      if (msg.id !== undefined && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
    }
  });
  const send = (id, method, params) => new Promise((resolve, reject) => {
    pending.set(id, resolve);
    child.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
    setTimeout(() => reject(new Error(`stdio timeout: ${method}`)), 10000);
  });
  try {
    const si = await send(1, "initialize", { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "stdio-smoke", version: "0" } });
    check("stdio: initialize answers", si.result?.serverInfo?.name === "uze-instant-mcp", JSON.stringify(si));
    child.stdin.write(JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }) + "\n");
    const sl = await send(2, "tools/list", {});
    check("stdio: tools/list answers with 9 tools", (sl.result?.tools || []).length === 9);
    const sc = await send(3, "uze/challenge", { wallet: w.address });
    const sv = await send(4, "uze/verify", { wallet: w.address, signature: w.sign(sc.result.message) });
    check("stdio: wallet handshake issues a session", !!sv.result?.sessionToken, JSON.stringify(sv));
    const st = await send(5, "tools/call", { name: "list_tiers", arguments: {} });
    check("stdio: authenticated list_tiers executes", (st.result?.structuredContent?.tiers || []).length === 2, JSON.stringify(st));
  } catch (e) {
    check(`stdio smoke completed (${e.message})`, false);
  } finally {
    child.kill();
  }
}

server.close();
console.log(`\nRESULT: ${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
