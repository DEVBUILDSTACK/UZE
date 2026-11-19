const ROWS = [
  {
    name: "Placement",
    line: "The client hires and pays the talent directly. The placement fee runs from one month of salary.",
  },
  {
    name: "Outstaffing",
    line: "UZE hires, marks up the labor rate, and pays the talent after the client pays UZE. Labor is never fronted.",
  },
  {
    name: "Assessment",
    line: "Employer-configured assessments with human gates — agents build them, people approve them.",
  },
  {
    name: "UZE Dev Library",
    line: "The developer surface of the talent system — dev.uzemarkets.com, gated by its own one-time code.",
  },
];

export default function C3Talent() {
  return (
    <>
      <p className="c3-eyebrow">C3 Admin Hub</p>
      <h1>Talent</h1>
      <p className="c3-muted">
        The dual-plane talent system: the programmatic core that recruits,
        assesses, and settles — and the desk that faces clients.
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
