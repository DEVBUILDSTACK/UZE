const ROWS = [
  {
    name: "SigLayer",
    line: "The treasury reporting record — daily reports, filed and read back, balances verified on-chain.",
  },
  {
    name: "Agreements & financial transactions",
    line: "The control-plane inbox — AGR-FIN-TX@uzemarkets.com. Agreements are signed under it, so terms sit beside the money.",
  },
  {
    name: "Annual budget",
    line: "Burn & P&L — projections by month, converted to actuals as each month closes.",
  },
];

export default function C3Treasury() {
  return (
    <>
      <p className="c3-eyebrow">C3 Admin Hub</p>
      <h1>Treasury</h1>
      <p className="c3-muted">
        The entity treasury and enterprise services run for it —
        optimized as one system, reported on a daily rhythm.
      </p>
      <div className="c3-rows">
        {ROWS.map((r) => (
          <div key={r.name} className="c3-row">
            <span className="c3-row-mark">—</span>
            <div>
              <p className="c3-row-name">{r.name}</p>
              <p className="c3-row-line">{r.line}</p>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
