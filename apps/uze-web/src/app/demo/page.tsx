/** Demo / sandbox environment placeholder.
 *
 *  demo.uzemarkets.com routes here via middleware once the DNS is
 *  configured (see src/middleware.ts). The dedicated hackathon demo
 *  and sandbox surface is built here in a later sprint; this page
 *  exists so the subdomain never lands on a 404. */
export default function DemoHome() {
  return (
    <main className="mk">
      <h1>UZEmarkets demo environment</h1>
      <p>
        This is the sandbox host for hackathon demos and pre-release
        testing. Nothing here is a live market: balances are testnet,
        and listings are fixtures.
      </p>
      <p>
        The Sprint 1.5 marketplace demo runs from the repository —
        see <code>docs/hackathon/nov-2026/DEMO-SCRIPT.md</code> in
        DEVBUILDSTACK/UZE.
      </p>
    </main>
  );
}
