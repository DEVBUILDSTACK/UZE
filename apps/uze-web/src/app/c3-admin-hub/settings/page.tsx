const ROWS = [
  {
    name: "KYC",
    line: "Identity verification for the officers behind an entity account — a person stands behind every hub sign-in.",
  },
  {
    name: "KYB",
    line: "Business verification for the entity itself — the partner company the corporate domain belongs to.",
  },
  {
    name: "Gate policy",
    line: "Corporate domains only. Consumer mail — Gmail, Yahoo, and their class — is refused at the door, before any code is sent.",
  },
];

export default function C3Settings() {
  return (
    <>
      <p className="c3-eyebrow">C3 Admin Hub</p>
      <h1>Settings</h1>
      <p className="c3-muted">
        Verification and gate policy for the hub — who may hold an
        account here, and how that is proven.
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
