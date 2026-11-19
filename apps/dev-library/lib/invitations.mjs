// The invitation composer (James, 2026-11-19): macro before micro.
// An invitee's invitation is composed from the set of surfaces
// their EMAIL holds grants on — the eco contributor registry and
// the Dev Library allowlist are checked together:
//   eco only     → the eco invitation (kind "eco-invitation")
//   library only → the existing library invitation, composed by
//                  lib/lifecycle.mjs exactly as before (this module
//                  returns null and the library path stands)
//   BOTH         → ONE combined invitation (kind "invitation_dual")
//                  that presents the ecosystem FIRST and the Dev
//                  Library second — never two competing invitations.
// Composing queues a comms entry; sending follows the standing
// rules (James's tap; everything tested to James first).
import { commsSend } from "./store.mjs";
import { findContributor } from "./eco-contributors.mjs";
import { findDeveloper } from "./gate.mjs";

const ECO_URL = "https://buildr-eco.uzemarkets.com";
const LIBRARY_URL = "https://dev.uzemarkets.com";

export function surfacesFor(email) {
  const eco = !!findContributor(email);
  const d = findDeveloper(email);
  const library = !!(d && d.readingRoom?.active);
  return { eco, library };
}
export function invitationKindFor(email) {
  const { eco, library } = surfacesFor(email);
  if (eco && library) return "invitation_dual";
  if (eco) return "eco-invitation";
  if (library) return "invitation";
  return null;
}
const ECO_EXTRA = { app: "eco", siteUrl: ECO_URL, siteLabel: "buildr-eco.uzemarkets.com",
  bandLabel: "BUILDR TEAM", footerEyebrow: "THE ECOSYSTEM DESK · BUILDR TEAM", footerEyebrowHtml: `THE ECOSYSTEM DESK · <a href="https://buildr-eco.uzemarkets.com" style="color:#6b655e;text-decoration:none">BUILDR TEAM</a>` };
const DUAL_EXTRA = { app: "eco", siteUrl: ECO_URL, siteLabel: "buildr-eco.uzemarkets.com",
  bandLabel: "BUILDR TEAM + DEV LIBRARY", footerEyebrow: "THE ECOSYSTEM DESK · BUILDR TEAM", footerEyebrowHtml: `THE ECOSYSTEM DESK · <a href="https://buildr-eco.uzemarkets.com" style="color:#6b655e;text-decoration:none">BUILDR TEAM</a>` };

export const ECO_INVITATION_SUBJECT = "Your access to the UZE Buildr Team";
export const ECO_INVITATION_BODY =
  "You have been granted access to the UZE Buildr Team — the ecosystem contributors' surface. " +
  "The whole ecosystem is there: both design surfaces, the pillars, the architecture, and the sections your role carries. " +
  `Sign in with this email address to receive a one-time code — no password to keep, no GitHub account needed. ${ECO_URL}`;
export const DUAL_INVITATION_SUBJECT = "Start here: UZE Buildr Team — then the UZE Dev Partner Library";
export const DUAL_INVITATION_BODY =
  "You hold access to two UZE surfaces, and they are meant to be taken in order.\n" +
  `1) UZE Buildr Team — start here: the whole ecosystem, both design surfaces, the pillars. ${ECO_URL}\n` +
  `2) UZE Dev Partner Library — then step into the library, where the work itself lives. ${LIBRARY_URL}\n` +
  "Start with the ecosystem — the whole picture. Then the library, where the work itself lives.\n" +
  "Sign-in on both surfaces is by a one-time code sent to this email address — no password to keep, and no GitHub account needed for the Buildr Team.";

// The diagrams attachment (James, 2026-11-19): the diagrams ship
// in AUDIENCE CUTS (James's ruling, 2026-11-19). The principal —
// Jonathan Schmidt — receives the cut framed on UZE and L2Launch
// only: DFI and FVC are excluded from his diagrams
// (eco/content/diagrams-jonathan.md). The family owners (D4, D5,
// WCD) receive the owners' cut with all four organizations in
// frame (eco/content/diagrams-owners.md). A segmented contributor
// gets only material consistent with their visibility: no
// visibility-consistent subset file exists today, so nothing is
// attached and the reason is recorded on the entry instead —
// sections are never leaked by attachment.
const ALL_ORG_KEYS = ["UZE", "L2Launch", "DFI", "FVC"];
const PRINCIPAL_EMAIL = "schmidtcommunications@gmail.com";
export function diagramsAttachmentFor(email) {
  const c = findContributor(email);
  if (!c) return {};
  const full = ALL_ORG_KEYS.every(k => (c.orgs || []).includes(k));
  if (!full) return { attachmentNote: "No visibility-consistent diagrams file exists for this contributor's sections — nothing attached." };
  if (String(email).toLowerCase() === PRINCIPAL_EMAIL)
    return { attachments: [{ filename: "UZE-ecosystem-diagrams.md", file: "diagram-md:jonathan" }] };
  return { attachments: [{ filename: "UZE-ecosystem-diagrams.md", file: "diagram-md:owners" }] };
}

// Compose (queue) the invitation an email's grants call for.
// Returns the comms entry, or null when the email holds only a
// library grant (the library invitation is lifecycle's own) or no
// grant at all.
export function composeInvitation(email) {
  const kind = invitationKindFor(email);
  if (kind === "invitation_dual") return commsSend(email, "invitation_dual", DUAL_INVITATION_SUBJECT, DUAL_INVITATION_BODY, { ...DUAL_EXTRA, ...diagramsAttachmentFor(email) });
  if (kind === "eco-invitation") return commsSend(email, "eco-invitation", ECO_INVITATION_SUBJECT, ECO_INVITATION_BODY, { ...ECO_EXTRA, ...diagramsAttachmentFor(email) });
  return null;
}
