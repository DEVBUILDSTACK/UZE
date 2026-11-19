import report from "@/lib/scope-report.json";

/* Project Scope Performance and Status (James, 2026-11-19): the
 * C3 Admin Hub's own copy of the multi-scope performance report,
 * under Enterprise Services — the same data the Buildr Team
 * surface renders, refreshed nightly at the developer-day mark
 * (10:29 PM EST) from the same scope-report.json discipline. */
type Blocker = { kind: string; text: string };
type Scope = {
  id: string; name: string; description: string;
  tierA: string; tierB: string; tierC: number;
  stage: string; blockers: Blocker[];
};
type RepoActivity = {
  repo: string; scope: string; pushedAt: string;
  pushes24h: { author: string; n: number }[];
  openPrs: number; openItems: number;
};
const R = report as {
  updated: string; devDayNote: string;
  scopes: Scope[];
  activity: { windowNote: string; repos: RepoActivity[] };
};

export default function C3ScopePerformance() {
  return (
    <>
      <p className="c3-eyebrow">C3 Admin Hub · Enterprise Services</p>
      <h1>Project Scope Performance and Status</h1>
      <p className="c3-muted">
        Where the code is moving, where deployment is moving, and
        where we are hung up — blockers classified technical ·
        financial · talent · agreement · grant. Updated {R.updated}.{" "}
        {R.devDayNote}
      </p>
      {R.scopes.map((s) => (
        <div key={s.id} style={{ marginTop: 28 }}>
          <h2>
            {s.id} — {s.name}
          </h2>
          <p>{s.description}</p>
          <p>
            <strong>Tier A — scope &amp; phased specs:</strong> {s.tierA}
          </p>
          <p>
            <strong>Tier B — build:</strong> {s.tierB}
          </p>
          <p>
            <strong>
              Tier C — to final audited production: {s.tierC}%
            </strong>
          </p>
          <p>
            <strong>Stage:</strong> {s.stage}
          </p>
          <div className="c3-rows">
            {s.blockers.map((b) => (
              <div key={b.kind + b.text} className="c3-row">
                <span className="c3-row-mark">—</span>
                <div>
                  <p className="c3-row-name">{b.kind}</p>
                  <p className="c3-row-line">{b.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      <div style={{ marginTop: 32 }}>
        <h2>Repository drill-down</h2>
        <p className="c3-muted">{R.activity.windowNote}</p>
        <div className="c3-rows">
          {R.activity.repos.map((x) => (
            <div key={x.repo} className="c3-row">
              <span className="c3-row-mark">—</span>
              <div>
                <p className="c3-row-name">
                  {x.repo} ({x.scope})
                </p>
                <p className="c3-row-line">
                  Last push {x.pushedAt}; pushes, last 24h:{" "}
                  {x.pushes24h.length
                    ? x.pushes24h.map((p) => `${p.author} ×${p.n}`).join(" · ")
                    : "no pushes in the window"}
                  ; open pull requests: {x.openPrs}; open items (issues
                  + PRs, as GitHub counts them): {x.openItems}.
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
