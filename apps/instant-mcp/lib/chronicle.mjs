// Chronicle — the append-only Event store. Every action in this program
// (executed, refused, revoked) is a chronicle Event; status is derived
// from the events, never written. Events are JSON lines on disk, appended
// synchronously so a crash cannot lose an admitted call's record.
import fs from "node:fs";
import path from "node:path";

export class Chronicle {
  constructor(file) {
    this.file = file;
    this.events = [];
    this.seq = 0;
    // Derived index: "wallet|YYYY-MM-DD" -> metered total of executed calls.
    this.dailyMeter = new Map();
    fs.mkdirSync(path.dirname(file), { recursive: true });
    if (fs.existsSync(file)) {
      for (const line of fs.readFileSync(file, "utf8").split("\n")) {
        if (!line.trim()) continue;
        const ev = JSON.parse(line);
        this.events.push(ev);
        if (ev.seq > this.seq) this.seq = ev.seq;
        this.#index(ev);
      }
    }
  }

  #index(ev) {
    if (ev.type === "tool.executed" && ev.principal && typeof ev.meter === "number") {
      const key = `${ev.principal}|${ev.ts.slice(0, 10)}`;
      this.dailyMeter.set(key, (this.dailyMeter.get(key) || 0) + ev.meter);
    }
  }

  append(type, fields = {}) {
    const ev = { seq: ++this.seq, id: `evt_${this.seq}`, ts: new Date().toISOString(), type, ...fields };
    fs.appendFileSync(this.file, JSON.stringify(ev) + "\n");
    this.events.push(ev);
    this.#index(ev);
    return ev;
  }

  meterUsedToday(wallet, now = new Date()) {
    return this.dailyMeter.get(`${wallet}|${now.toISOString().slice(0, 10)}`) || 0;
  }

  // Sum of executed pay_via_x402 amounts for a wallet (mock balance source).
  paymentsTotal(wallet) {
    let total = 0;
    for (const ev of this.events) {
      if (ev.type === "tool.executed" && ev.tool === "pay_via_x402" && ev.principal === wallet) {
        total += ev.detail?.amount || 0;
      }
    }
    return total;
  }

  forPrincipal(wallet) {
    return this.events.filter((e) => e.principal === wallet);
  }

  all() {
    return [...this.events];
  }
}
