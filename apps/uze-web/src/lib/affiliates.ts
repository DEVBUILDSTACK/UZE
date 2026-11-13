/** Affiliate directory fixtures (owner tap, 2026-11-13).
 * Demonstration data only: both firms are invented, their
 * projects and awards are invented, and the pages say so.
 * Real affiliate pages render from AffiliateProfile records
 * created at onboarding (services/compose affiliate_profile);
 * these fixtures pin the page shape until the compose API is
 * publicly deployed — the same honest-fixture pattern as the
 * alpha intake. Ordering mirrors the backend rule: sponsored
 * affiliates first. */

export interface AffiliateFixture {
  slug: string;
  name: string;
  kind: string;
  summary: string;
  services: string[];
  specialties: string[];
  mediaNote: string;
  projects: { name: string; location: string; year: number; type: string }[];
  awards: { name: string; year: number; organization: string }[];
  sponsorshipStatus: boolean;
}

export const AFFILIATES: AffiliateFixture[] = [
  {
    slug: "atelier-meridian",
    name: "Atelier Meridian",
    kind: "Creative Intelligence Agency — demonstration firm",
    summary:
      "Visualization studio for developments: drone footage, motion graphics, and 3D renders that let a developer pre-sell a project before ground is broken.",
    services: ["Drone visualization", "Motion graphics", "3D renders"],
    specialties: ["Oceanfront Resort", "Golf Course Integration", "Luxury Lobby"],
    mediaNote: "Portfolio media (drone video, renders, interior photography) is hosted by the firm and embedded here at onboarding.",
    projects: [
      { name: "Casa Brisa Resort", location: "Tamarindo, Costa Rica", year: 2025, type: "Hospitality resort" },
      { name: "Fairway Villas", location: "Kissimmee, Florida", year: 2024, type: "Residential community" },
    ],
    awards: [
      { name: "Best Architectural Visualization", year: 2025, organization: "Americas Design Media Awards" },
    ],
    sponsorshipStatus: true,
  },
  {
    slug: "northbeam-studio",
    name: "Northbeam Studio",
    kind: "Institutional Software Partner — demonstration firm",
    summary:
      "Traditional software engineering for operating assets: booking engines, tenant portals, and property management dashboards, built to the project's own stack preference.",
    services: ["Booking engines", "Tenant portals", "Property dashboards"],
    specialties: ["Hospitality Systems", "Resident Experience", "Owner Reporting"],
    mediaNote: "Product walkthroughs and dashboard captures are hosted by the firm and embedded here at onboarding.",
    projects: [
      { name: "Harborline Booking Engine", location: "Baltimore, Maryland", year: 2025, type: "Hospitality platform" },
      { name: "Tenant Portal Suite", location: "Fort Lauderdale, Florida", year: 2023, type: "Residential platform" },
    ],
    awards: [],
    sponsorshipStatus: false,
  },
];

export function orderedAffiliates(): AffiliateFixture[] {
  return [...AFFILIATES].sort(
    (a, b) =>
      Number(b.sponsorshipStatus) - Number(a.sponsorshipStatus)
  );
}

export function findAffiliate(slug: string): AffiliateFixture | undefined {
  return AFFILIATES.find((a) => a.slug === slug);
}
