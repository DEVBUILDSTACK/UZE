// LOCAL MOCK provisioner. Real provisioning is NEAR AI Cloud, and that
// is blocked on org credits (merged program M0-B) — so tonight nothing
// here talks to NEAR or any network. The mock behaves like the real
// surface for metering purposes: provision (with a realistic spin-up
// delay) -> active -> usage ticks accrue -> terminate with a final
// usage reading. Every output is labeled as the mock it is.
import crypto from "node:crypto";

export const PROVIDER_LABEL = "LOCAL MOCK — NEAR AI Cloud provisioning pending M0-B (credits)";
const TICK_MS = 250;
const TICK_COST = 5; // micro-USDC per tick of compute usage

const spinUpMs = () => Number(process.env.MOCK_PROVISION_MS || 500);
const delay = (ms) => new Promise((r) => setTimeout(r, ms));

export class MockProvisioner {
  constructor(store) {
    this.store = store;
  }

  async provision({ owner, tier, size }) {
    await delay(spinUpMs()); // simulated spin-up; also the in-flight window
    const now = new Date().toISOString();
    const inst = {
      id: `inst_${crypto.randomBytes(6).toString("hex")}`,
      owner,
      tier,
      size: size || "KVM1",
      state: "active",
      provider: PROVIDER_LABEL,
      createdAt: now,
      activatedAt: now,
      terminatedAt: null,
    };
    return this.store.putInstance(inst);
  }

  usageOf(inst, at = Date.now()) {
    const end = inst.terminatedAt ? Date.parse(inst.terminatedAt) : at;
    const ticks = Math.max(0, Math.floor((end - Date.parse(inst.activatedAt)) / TICK_MS));
    return { usageTicks: ticks, computeAccrued: ticks * TICK_COST, tickMs: TICK_MS, tickCost: TICK_COST };
  }

  status(inst) {
    return {
      instance_id: inst.id,
      state: inst.state,
      tier: inst.tier,
      size: inst.size,
      owner: inst.owner,
      provider: inst.provider,
      createdAt: inst.createdAt,
      terminatedAt: inst.terminatedAt,
      ...this.usageOf(inst),
    };
  }

  credentials(inst) {
    return {
      instance_id: inst.id,
      endpoint: `mock://uze-instance/${inst.id}`,
      ssh_user: "uze",
      ssh_key_fingerprint: "MOCK: no real key — no real instance exists",
      provider: PROVIDER_LABEL,
    };
  }

  terminate(inst) {
    const final = this.usageOf(inst);
    const updated = { ...inst, state: "terminated", terminatedAt: new Date().toISOString() };
    this.store.putInstance(updated);
    return { ...this.status(updated), finalUsage: final };
  }
}
