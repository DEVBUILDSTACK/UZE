# Classification Amendment — the Mentor Class (Hammond, 2026-11-20)

**Amends the classification layer of 2026-11-19 by addition. The layer now carries six classes.**

## The change

- **Bruno Salles moves from advisor to mentor.** Hammond's reason of record: Bruno has absolutely no experience in productization; the mentor seat fits him. His L2Launch relationship is unchanged in substance — guidance and conversion counsel — but his class, and with it his visibility, is mentor.
- **The advisor class is redefined** and currently stands **unoccupied**.

## The classes as amended

- **Owner** — the family owners of 456iP: D4, D5, WCD. Full visibility.
- **Principal** — Jonathan Schmidt (L2Launch). Full visibility.
- **Advisor** — **visibility into the repo, but no access to code unless granted by OTP; an advisor's OTP expires at the 24-hour mark.**
- **Mentor** — **no repo visibility and no code access.** Mentors receive presented material only (renders, briefings) — the surfaces Hammond approves for them, never the repo itself.
- **Developer (internal / external)** — **developer OTPs do not expire until revoked.**

## Access intent (Hammond)

The product-development and branding material stays open to the family owners, to the principals of L2Launch, and — at the visibility each class carries — to those advising it. Visibility is by class, never by person-by-person exception.

## Implementation notes (2026-11-20)

- `lib/classifications.mjs` header doctrine and `CLASS_LABELS` carry the mentor class and the amended advisor definition; `data/classifications.json` re-seats Bruno as mentor; the suite's classification assertion follows the ruling.
- Bruno holds no production eco grant (verified against the production roster), so no live access changes hands with this amendment.
- The 24-hour advisor OTP expiry is the governing rule of the layer as of this amendment; per-class expiry enforcement in the session engine is the follow-on build when the first advisor is seated (the class is currently empty).
