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

const ECO_URL = "https://buildr-team.uzemarkets.com";
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
const ECO_EXTRA = { app: "eco", siteUrl: ECO_URL, siteLabel: "buildr-team.uzemarkets.com",
  bandLabel: "BUILDR TEAM", footerEyebrow: "THE ECOSYSTEM DESK · BUILDR TEAM" };
const DUAL_EXTRA = { app: "eco", siteUrl: ECO_URL, siteLabel: "buildr-team.uzemarkets.com",
  bandLabel: "BUILDR TEAM + DEV LIBRARY", footerEyebrow: "THE ECOSYSTEM DESK · BUILDR TEAM" };

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

// Compose (queue) the invitation an email's grants call for.
// Returns the comms entry, or null when the email holds only a
// library grant (the library invitation is lifecycle's own) or no
// grant at all.
export function composeInvitation(email) {
  const kind = invitationKindFor(email);
  if (kind === "invitation_dual") return commsSend(email, "invitation_dual", DUAL_INVITATION_SUBJECT, DUAL_INVITATION_BODY, DUAL_EXTRA);
  if (kind === "eco-invitation") return commsSend(email, "eco-invitation", ECO_INVITATION_SUBJECT, ECO_INVITATION_BODY, ECO_EXTRA);
  return null;
}
