import type { Metadata } from "next";
import UploadBox from "@/components/upload-box";

export const metadata: Metadata = {
  title: "UZE Underwrite | UZEmarkets",
  description:
    "Forward a T-12 or P&L and get a verified, micro-region-benchmarked PDF report in minutes. The $289 verified analysis that replaces a $6,000 manual one.",
};

const API_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "WebAPI",
  name: "UZE Underwrite — Agentic Email Gateway",
  description:
    "Submit a property financial statement (T-12 / P&L) and receive a verified, micro-region-benchmarked PDF assessment. Routing: HiCRE/Hotel to SURA, ANRD/Farm to GIRA; use cases include emergency P&L verification, acquisition due-diligence valuation (NOI / Cap Rate on 12/18/36-month historicals), and human talent placement.",
  url: "https://uzemarkets.com/underwrite",
  documentation: "https://uzemarkets.com/knowledge-base",
  provider: { "@type": "Organization", name: "UZEmarkets" },
};

const SKILL_JSON = {
  skill: "uze-underwrite",
  version: "0.1-demo",
  endpoint: "POST /api/v1/ingest/email",
  payload: {
    subject:
      "string — include a track keyword (HiCRE | Hotel | ANRD | Farm); add a use-case keyword to select the flow",
    sender: "string — the forwarding party's email",
    attachment_base64: "base64-encoded financial document (T-12 / P&L)",
  },
  routing: {
    tracks: { "HiCRE | Hotel": "SURA", "ANRD | Farm": "GIRA" },
    useCases: {
      "Urgent P&L | Replacement | Immediate": "emergency_replacement",
      "Acquisition | Due Diligence | Valuation":
        "acquisition_due_diligence",
      "Talent | Management | Hiring": "talent_placement",
    },
  },
  responses: {
    "200":
      "{ status, useCase, agent, extracted, pdf_base64 } — or the talent-placement routing object for placement subjects",
    "422": '{ "error": "Could not determine asset track" }',
  },
};

/** UZE Underwrite landing (directed, 2026-11-10): the lead-gen
 *  surface for the Email Gateway — value prop, the three ruled
 *  pricing tiers, the intake address and upload box, and the
 *  agent-facing skill contract. Copy discipline: the gateway's
 *  demo scope is stated on the page (public intake activates
 *  with the API launch); no capability is claimed beyond the
 *  filed build. */
export default function UnderwritePage() {
  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(API_SCHEMA) }}
      />
      <h1>UZE Underwrite</h1>
      <p className="lede">
        A verified P&amp;L and a benchmarked valuation — in minutes,
        not weeks. The manual version of this analysis is a
        $6,000 analyst engagement. UZE Underwrite returns the
        verified PDF for $289.
      </p>

      <section>
        <h2>How it works</h2>
        <p>
          Forward your T-12 or P&amp;L to{" "}
          <a href="mailto:ingest@uzemarkets.com">
            ingest@uzemarkets.com
          </a>{" "}
          — or use the upload box below. The gateway routes your
          document to the underwriting agent for its asset class:
          SURA for income property, GIRA for land. You get back a
          one-page PDF: the full P&amp;L verified line by line —
          revenue, operating expenses, taxes, and insurance, each
          benchmarked against the property&apos;s own micro-region
          — and, for acquisitions, a valuation from the
          12/18/36-month historicals at the market cap rate.
        </p>
        <UploadBox />
      </section>

      <section>
        <h2>Pricing</h2>
        <p>
          <strong>Emergency P&amp;L Service — $289.</strong> The
          full retail service: verified P&amp;L PDF with
          human-in-the-loop review. Built for the moment the
          analyst is gone and the board or the lender needs the
          numbers now.
        </p>
        <p>
          <strong>API Bundle — $5.00 per document.</strong> For
          agents hitting the endpoint directly: parsing, inference,
          the PDF, and the routing in one price. No human review.
        </p>
        <p>
          <strong>Permissionless Routing — $1.00 per document.</strong>{" "}
          Your agent pays the parsing and inference providers
          directly; UZEmarkets takes $1.00 for the orchestration
          and the report.
        </p>
      </section>

      <section>
        <h2>For agents — the skill contract</h2>
        <p>
          AI agents can call the gateway directly. The contract:
        </p>
        <pre className="skill-json">{JSON.stringify(SKILL_JSON, null, 2)}</pre>
      </section>
    </main>
  );
}
