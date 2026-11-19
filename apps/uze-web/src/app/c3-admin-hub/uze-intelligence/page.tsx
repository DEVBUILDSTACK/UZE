const ROWS = [
  {
    name: "Create new API key",
    line: "Keys are issued per officer and scoped — a key carries only the sections its holder is cleared for.",
  },
  {
    name: "Existing keys",
    line: "Every key in one list: its name, its scope, when it was created, and when it was last used.",
  },
  {
    name: "Revoke",
    line: "Revoking a key cascades at the call boundary — the next call it makes is the last one it is offered.",
  },
];

export default function C3UzeIntelligence() {
  return (
    <>
      <p className="c3-eyebrow">C3 Admin Hub</p>
      <h1>UZE Intelligence</h1>
      <p className="c3-muted">
        All API keys live here — the agentic surface of the hub, where
        officers issue and revoke the keys their systems call with.
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
