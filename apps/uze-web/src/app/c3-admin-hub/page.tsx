import Link from "next/link";

const SECTIONS = [
  {
    href: "/c3-admin-hub/treasury",
    name: "Treasury",
    line: "The entity treasury — its reporting record, its agreements, and the annual budget beside the actuals.",
  },
  {
    href: "/c3-admin-hub/talent",
    name: "Talent",
    line: "Placement and outstaffing, run through the desk — clients hire directly, or UZE hires and pays on client payment.",
  },
  {
    href: "/c3-admin-hub/enterprise-services",
    name: "Enterprise Services",
    line: "The operating layer under the hub: the talent systems and payroll that serve every organization.",
  },
];

export default function C3Home() {
  return (
    <>
      <p className="c3-eyebrow">Command &amp; Control Console</p>
      <h1>C3 Admin Hub</h1>
      <p className="c3-muted">
        One console across the ecosystem. Choose a section:
      </p>
      <div className="c3-cards">
        {SECTIONS.map((s) => (
          <Link key={s.href} href={s.href} className="c3-card">
            <span className="c3-card-name">{s.name}</span>
            <span className="c3-card-line">{s.line}</span>
          </Link>
        ))}
      </div>
    </>
  );
}
