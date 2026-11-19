const ROWS = [
  {
    name: "Talent systems",
    line: "The applicant tracking layer under the Talent section — pipelines, engagements, and the revoke cascade.",
  },
  {
    name: "Payroll",
    line: "Pay runs for outstaffed talent, released on client payment — never before it.",
  },
  {
    name: "Organizations",
    line: "DealFi · Fundio · UZEmarkets · L2 Launchpad — the four organizations the console serves.",
  },
];

export default function C3EnterpriseServices() {
  return (
    <>
      <p className="c3-eyebrow">C3 Admin Hub</p>
      <h1>Enterprise Services</h1>
      <p className="c3-muted">
        The operating layer under both the human and the agentic
        surfaces — the systems the sections run on.
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
