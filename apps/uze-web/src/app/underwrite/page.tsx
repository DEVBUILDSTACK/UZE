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
    "Submit a hospitality or income-property financial statement (T-12 / P&L) and receive a verified, micro-region-benchmarked PDF assessment. HiCRE only: hotels, motels, resorts, hostels, residential condos, rental units, mobile home parks. Routing: HiCRE/Hotel to SURA; use cases include emergency P&L verification, acquisition due-diligence valuation (NOI / Cap Rate on 12/18/36-month historicals), and human talent placement.",
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
      "string — include the HiCRE track keyword (HiCRE | Hotel); add intent and use-case keywords to direct the analysis",
    sender: "string — the forwarding party's email",
    attachment_base64: "base64-encoded financial document (T-12 / P&L)",
  },
  routing: {
    tracks: { "HiCRE | Hotel": "SURA" },
    direction: {
      intent: "pnl_verification | valuation (Acquisition | Due Diligence | Valuation)",
      modifiers:
        "Refinancing (focus: debt service coverage) | Distressed (rapid liquidity) | Cost Recovery (OpEx overspend) | standard acquisition (market comps)",
    },
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
    "422":
      '{ "error": "Could not determine asset track" } — or, for land/agriculture subjects, { "error": "UZE Underwrite currently processes Hospitality & Income CRE only. Please contact our team directly for A|NR|D spatial underwriting." }',
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
      <p className="gateway-sub">Gateway</p>
      <p className="lede">
        <strong>
          UZE Underwriting Gateway: Direct our Super Intelligence.
        </strong>
      </p>
      <p>
        Traditional financial analysis is slow and manual. UZE
        Underwrite replaces it with instant, verified intelligence.
      </p>
      <p>
        UZE Underwrite is built for Hospitality &amp; Income
        Commercial Real Estate. If it puts a head in a bed and
        charges a fee — from a global resort to a local hostel, a
        multifamily rental, or a mobile home park — SURA can
        verify the P&amp;L and calculate valuation based on
        regional comps.
      </p>
      <p>
        Stop paying for manual data entry. Unlock Cost Recovery
        today.
      </p>

      <section>
        <h2>You direct the analysis</h2>
        <p>
          The report is not generic — your subject line directs
          it. State what you need and why:
        </p>
        <p>
          <strong>Intent:</strong> P&amp;L verification (revenue,
          operating expenses, taxes, insurance — checked against
          regional comps), or property valuation (NOI ÷ cap rate).
        </p>
        <p>
          <strong>Use case:</strong> refinancing (the focus is
          debt service coverage), a distressed sale (rapid
          liquidity), a standard acquisition (market comps), or
          cost recovery (operating-expense overspend). SURA runs
          the analysis you directed and returns the verified PDF
          tailored to it.
        </p>
      </section>

      <section>
        <h2>Send your financials</h2>
        <p>
          Forward your T-12 or P&amp;L to{" "}
          <a href="mailto:uzemarket@uzemarkets.com">
            uzemarket@uzemarkets.com
          </a>{" "}
          — or use the upload box below. You receive a verified
          PDF in minutes: the P&amp;L verified against regional
          comps, or the valuation run on NOI and market cap rates.
        </p>
        <UploadBox />
      </section>

      <section>
        <h2>Need the people, too?</h2>
        <p>
          The report reads your payroll lines and names the
          operational roles this asset already pays for. Need to
          source a Property Manager or operational staff for this
          asset?{" "}
          <a href="https://uzemarkets.com/talent/placement">
            Go to Talent Placement
          </a>{" "}
          — the underwrite is the brief, and candidates are
          matched against the payroll budget it calculated.
        </p>
      </section>

      <section>
        <h2>For agents — the skill contract</h2>
        <p>AI agents can call UZE Underwrite directly. The contract:</p>
        <pre className="skill-json">{JSON.stringify(SKILL_JSON, null, 2)}</pre>
      </section>
    </main>
  );
}
