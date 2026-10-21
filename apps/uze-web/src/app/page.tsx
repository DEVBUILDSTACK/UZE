import Link from "next/link";

/** Public front door. Evaluation-first: anyone can look around;
 *  profile creation is an invitation, not a gate. The email-code
 *  signup flow lives at /onboard and activates with the API deploy. */
export default function Home() {
  return (
    <main>
      <h1>UZE</h1>
      <p>Talent, tickets, touring and stay — one AI ecosystem.</p>
      <p>
        Meet GIRA, your concierge for what&apos;s on, where it&apos;s
        happening, and how to be there.
      </p>
      <nav>
        <ul className="home-links">
          <li>
            <Link href="/guidance">See how GIRA guidance works</Link>
          </li>
          <li>
            <Link href="/onboard">Create your UZE profile</Link>
          </li>
        </ul>
      </nav>
    </main>
  );
}
