// Three-layer gating (Scope 3 spec §4; merged §4):
//   (a) user pre-authorization — the principal record with explicit
//       limits (per-call max, per-day max, allowed tool set), set via
//       the admin path (the user's re-authenticated act);
//   (b) MCP-side enforcement — this module, consulted BEFORE any tool
//       executes; a refusal here means the handler never runs;
//   (c) the tier gate — Instance-tier principals cannot call
//       Markets-tier tools, and cannot provision Markets-tier instances.
// Every refusal is returned to the dispatcher, which records it as a
// chronicle Event. Nothing in this module executes a tool.
import { CATALOG, priceOf } from "./tools.mjs";

export function admit({ store, chronicle }, session, name, args = {}) {
  const refuse = (reason, message) => ({ ok: false, reason, message });
  const principal = store.getPrincipal(session.wallet);

  // Layer (a): a pre-authorization must exist and be in force.
  if (!principal) return refuse("no_pre_authorization", "no pre-authorization on file for this wallet; the user must set limits before the agent may call tools");
  if (principal.revoked) return refuse("principal_revoked", "this principal has been revoked");

  const tool = CATALOG[name];
  if (!tool) return refuse("unknown_tool", `unknown tool: ${name}`);

  // Layer (c): tier gate.
  if (tool.tier === "markets" && principal.tier !== "markets") {
    return refuse("tier_gate", `${name} is a Markets-tier tool; this principal is authorized for the Instance tier only`);
  }
  if (name === "provision_instance" && args?.tier === "markets" && principal.tier !== "markets") {
    return refuse("tier_gate", "an Instance-tier principal cannot provision a UZE Markets Instance");
  }
  if (name === "provision_instance" && !["instance", "markets"].includes(args?.tier)) {
    return refuse("bad_tier", "provision_instance requires tier: 'instance' or 'markets'");
  }

  // Layer (a) continued: the user's allowed tool set.
  if (Array.isArray(principal.limits?.allowedTools) && !principal.limits.allowedTools.includes(name)) {
    return refuse("tool_not_allowed", `${name} is not in this principal's authorized tool set`);
  }

  // Dark tools (amendment A3): registered and discoverable, refused
  // until M3 — with the refusal recorded like every other refusal.
  if (tool.status === "dark") {
    return refuse("available_m3", `${name} is available M3 — it ships dark in M2 and every call is refused and recorded until the M3 settlement substrate lands`);
  }

  // Layer (b): metering enforcement, before execution.
  const price = priceOf(name, args);
  const limits = principal.limits || {};
  if (typeof limits.perCallMax === "number" && price > limits.perCallMax) {
    return refuse("over_per_call_limit", `call meter ${price} exceeds the principal's per-call max ${limits.perCallMax} — refused before execution`);
  }
  if (typeof limits.perDayMax === "number") {
    const used = chronicle.meterUsedToday(session.wallet);
    if (used + price > limits.perDayMax) {
      return refuse("over_daily_limit", `call meter ${price} would bring today's total to ${used + price}, over the principal's per-day max ${limits.perDayMax} — refused before execution`);
    }
  }
  return { ok: true, price };
}
