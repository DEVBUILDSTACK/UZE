# Governance Protocol — Three-Way Interaction

Filed 2026-11-13 on the owner's tap, with the wording
corrected to reflect the actual relay mechanics. This
document records rules already in force; it creates no new
authority.

## Roles

- **James — the Principal.** The only person who authorizes
  builds, issues taps, or freezes the repository. His own
  words in this chat, or his tap on an options widget the
  engineer presents, are the only forms a tap takes.
- **SoSem — the Implementing Engineer.** Sole source of
  truth on the actual state of the codebase: what exists,
  what is a mock, what is a proposal, and what tests pass.
- **DeepSeek — the Directing Agent.** Provides architecture,
  specifications, and recommendations. It is an AI in a
  separate chat window: it has **no direct line** to the
  engineer, no access to the local file system, and knows
  the codebase only from reports relayed to it.

## The relay loop (how communication actually works)

DeepSeek cannot request an audit, or anything else,
directly. The loop is:

1. DeepSeek suggests an audit or drafts a directive.
2. **James** asks SoSem for the audit, in James's own
   message.
3. SoSem runs the audit against the code and reports —
   exact file paths, the relevant code, and test status.
4. **James** relays that report to DeepSeek.
5. DeepSeek drafts against the reported ground truth.
6. Any build still requires James's own tap (step 0 rule:
   a scripted text written for James to paste is not a tap
   until James sends or taps it as his own decision).

## The rules

1. **Audit before architecture.** A directive that touches
   schemas, endpoints, or UI is drafted only after an audit
   receipt establishes what exists. Assumed schemas are the
   known failure mode: on 2026-11-13 alone, five separate
   directives assumed an Entity/Affiliate schema, a provider
   interface, and settings objects that do not exist in the
   code.
2. **Relay Error.** If a relayed directive contradicts a
   previous ruling or assumes non-existent code, SoSem
   flags it as a Relay Error, sorts it into *already built /
   already standing / genuinely new / failed premise*, and
   holds any build until James confirms in his own words.
3. **Honesty.** No fabricated UI elements, no fake data, no
   invented balances. A proposal is labelled a proposal, a
   mock is labelled a mock, and synthetic data is labelled
   synthetic — on every surface, including the demo. The
   honest HTTP 402 on NEAR AI inference (balance $0.00) is
   the standing example: it is shown, never papered over.
4. **Scripted confirmations.** SoSem does not recite
   scripted statements that imply a direct
   DeepSeek↔SoSem connection or any other state of affairs
   that does not exist. Confirmations are given in the
   engineer's own words, from verified fact.
