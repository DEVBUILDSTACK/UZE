import type { Metadata } from "next";
import UploadBox from "@/components/upload-box";

export const metadata: Metadata = {
  title: "UZE Underwrite | UZEmarkets",
  description:
    "UZE Underwrite: Underwriting Super Intelligence. Forward a T-12 or P&L and get a verified, micro-region-benchmarked PDF report in minutes.",
};

const API_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "WebAPI",
  name: "UZE Underwrite",
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

/** UZE Underwrite landing (positioning corrected 2026-11-10):
 *  Underwriting Super Intelligence; the value proposition is
 *  Cost Recovery; NO specific pricing in public copy (pricing
 *  lives in the API docs / economics note); the words broker,
 *  middleman, and gateway do not appear in public copy. The two
 *  functional tasks are stated: P&L verification against
 *  regional comps, and valuation (NOI / Cap Rate). */
export default function UnderwritePage() {
  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(API_SCHEMA) }}
      />
      <h1>UZE Underwrite</h1>
      <p className="lede">
        <strong>Underwriting Super Intelligence.</strong>
      </p>
      <p>
        Traditional financial analysis is slow and manual. UZE
        Underwrite replaces it with instant, verified intelligence.
      </p>
      <p>
        Forward your T-12s or P&amp;Ls to our system. Our AI
        agents (SURA for HiCRE, GIRA for ANRD) verify your
        operating expenses against micro-region comps, or
        calculate your asset valuation based on NOI and market cap
        rates.
      </p>
      <p>
        Stop paying for manual data entry. Unlock Cost Recovery
        today.
      </p>

      <section>
        <h2>Send your financials</h2>
        <p>
          Forward your T-12 or P&amp;L to{" "}
          <a href="mailto:ingest@uzemarkets.com">
            ingest@uzemarkets.com
          </a>{" "}
          — or use the upload box below. You receive a verified
          PDF in minutes: the P&amp;L verified against regional
          comps, or the valuation run on NOI and market cap rates.
        </p>
        <UploadBox />
      </section>

      <section>
        <h2>For agents — the skill contract</h2>
        <p>AI agents can call UZE Underwrite directly. The contract:</p>
        <pre className="skill-json">{JSON.stringify(SKILL_JSON, null, 2)}</pre>
      </section>
    </main>
  );
}
