import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import GiraDebug from "@/components/gira-debug";
import MermaidDiagram from "@/components/mermaid-diagram";
import PayloadGenerator from "@/components/payload-generator";
import {
  API_KEY_EMAIL,
  CONTENT,
  EXAMPLES,
  LOCALES,
  REPO_PARTNERS_URL,
  isLocale,
} from "@/lib/devpartner";

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  return { title: CONTENT[locale].title };
}

/** DevPartner portal — one locale. Public and ungated: the summary,
 *  the ingestion API reference, the partner schemas with example
 *  payloads, the downloadable documents, and the API-key request
 *  contact. Canonical documents live in the repo's partners/
 *  folder; downloads link there. */
export default async function DevPartnerLocalePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const c = CONTENT[locale];

  return (
    <main className="mk dp">
      <p className="dp-kicker">{c.kicker}</p>
      <h1>{c.h1}</h1>
      <p>{c.intro}</p>

      <p className="dp-langs">
        {c.languageLabel}:{" "}
        {LOCALES.map((l, i) => (
          <span key={l}>
            {i > 0 ? " · " : ""}
            {l === locale ? (
              <strong>{l}</strong>
            ) : (
              <Link href={`/devpartner/${l}`}>{l}</Link>
            )}
          </span>
        ))}
      </p>

      <h2>{c.howHeading}</h2>
      <div className="dp-tiers">
        {c.tiers.map((tier) => (
          <section key={tier.title} className="dp-tier">
            <h3>{tier.title}</h3>
            <p>{tier.body}</p>
          </section>
        ))}
      </div>

      <h2>{c.governanceHeading}</h2>
      <p>{c.governanceBody}</p>

      <h2>{c.apiHeading}</h2>
      <p>
        {c.endpointLabel}:{" "}
        <code>POST /api/v1/partners/ingest</code>
      </p>
      <p>
        {c.authLabel}: {c.authBody}
      </p>
      <h3>{c.responsesHeading}</h3>
      <table>
        <tbody>
          {c.responses.map((r) => (
            <tr key={r.code}>
              <td>
                <code>{r.code}</code>
              </td>
              <td>{r.meaning}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>{c.partnersHeading}</h2>
      <p>{c.partnersIntro}</p>
      {c.partners.map((partner) => (
        <section key={partner.id} className="dp-partner">
          <h3>{partner.displayName}</h3>
          <p>{partner.blurb}</p>
          <p>
            {c.schemaLabel}:{" "}
            <a href={`${REPO_PARTNERS_URL}/schemas/${partner.schemaFile}`}>
              <code>partners/schemas/{partner.schemaFile}</code>
            </a>
          </p>
          <p>{c.exampleLabel}:</p>
          <pre className="dp-code">{EXAMPLES[partner.id]}</pre>
        </section>
      ))}

      <h2>{c.diagrams.title}</h2>
      <MermaidDiagram chart={c.diagrams.journey} title={c.diagrams.journeyTitle} />
      <MermaidDiagram chart={c.diagrams.internal} title={c.diagrams.internalTitle} />

      <h2>{c.generator.title}</h2>
      <p>{c.generator.body}</p>
      <PayloadGenerator copyLabel={c.generator.copy} copiedLabel={c.generator.copied} />

      <h2>{c.debug.title}</h2>
      <p>{c.debug.body}</p>
      <GiraDebug runLabel={c.debug.run} copyLabel={c.debug.copy} copiedLabel={c.debug.copied} />

      <h2>{c.docs.title}</h2>
      <p>{c.docs.body}</p>
      <p>
        <Link className="dp-cta" href={`/devpartner/${locale}/docs`}>
          {c.docs.open}
        </Link>
      </p>

      <h2>{c.downloadsHeading}</h2>
      <ul>
        {c.downloads.map((d) => (
          <li key={d.file}>
            <a href={`${REPO_PARTNERS_URL}/${d.file}`}>{d.label}</a>
          </li>
        ))}
      </ul>

      <h2>{c.ctaHeading}</h2>
      <p>{c.ctaBody}</p>
      <p>
        <a
          className="dp-cta"
          href={`mailto:${API_KEY_EMAIL}?subject=${encodeURIComponent(
            "DevPartner API Key Request",
          )}`}
        >
          {c.ctaButton}
        </a>{" "}
        <code>{API_KEY_EMAIL}</code>
      </p>
    </main>
  );
}
