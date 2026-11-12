# Talent Placement — Ingestion & Parsing Architecture

**Status: MIXED — the JSON path is 🟢 BUILT (2026-11-12);
the document-parsing layer is 🔴 PROPOSAL, deferred to the
January 2nd update by the owner's directive.** Creative
architecture input requested by the owner and provided by
SoSem, 2026-11-12. Scope label (ratified): human-talent/CV
claims sit outside the hackathon build; this document designs
the ingestion layer, it does not enroll it in the submission
narrative.

## One schema, two doors

Every talent — human or agent — lands in a single
**TalentProfile**:

```json
{
  "name": "string, required",
  "role": "string, required",
  "experience_years": "number ≥ 0, required",
  "skills": ["string, …], required, non-empty",
  "expected_rate_usd": "number > 0, required",
  "certifications": ["string, …"], optional"
}
```

**Taxonomy (built 2026-11-12, owner's supplemental tap):**
two optional fields separate who the employer is from what
the worker is — `asset_class_focus` (HOSPITALITY: hired by
organizations · RESIDENTIAL: hired by syndicates/owners) and
`talent_type` (HUMAN_EMPLOYEE · HUMAN_CONTRACTOR ·
AGENTIC_SERVICE). Optional so pre-taxonomy profiles stay
valid; strict when present. The matcher (`match_profiles`)
matches on role family (operations vs knowledge work, read
from the role), the role itself, and focus compatibility —
an unset focus serves any. The underwrite's
`talent_placement` object offers both paths: Operations
(the payroll's roles) and Knowledge Work (outsource the
asset's ongoing financial analysis).

**Door 1 — the agent (built).** An agentic talent submits
the JSON directly. The email gateway's talent track validates
it (`talent_profile.validate_profile`): valid profiles are
normalized and recorded (v1: append-only JSONL, the alpha
intake's pattern; a database table is a later migration);
invalid ones return `INSUFFICIENT_DATA` with the exact
missing/invalid field names. Nothing is inferred to complete
a profile.

**Door 2 — the human (deferred, designed here).** A human
uploads a PDF or Word resume. Today the gateway answers with
the clean deferral: *"PDF/Word resume parsing is deferred to
our January 2nd update. Please provide your resume in JSON
format."* The January design, in three stages:

1. **Text layer.** Extract text with a real PDF parser
   (pypdf/pdfplumber class). Note what does *not* work:
   openpyxl reads spreadsheets — it is the T-12 tool, not a
   document tool — and the gateway today extracts no document
   text at all. Scanned-image resumes would need OCR, a
   further step, separately labelled if ever added.
2. **Structuring.** The extracted text is structured into
   TalentProfile by the inference layer, with every field
   traced to the resume text it came from (the same
   provenance discipline as the underwrite). Fields the
   resume does not support are left empty — and the profile
   then fails validation with those fields named, exactly as
   a hand-written JSON would. The parser proposes; the schema
   disposes.
3. **Confirmation.** Because structuring is interpretive, a
   human-submitted profile is presented back for the talent's
   own confirmation before it is matchable. An agent's JSON
   needs no such step: it asserted the schema itself.

## Rate matching against the underwrite

The bridge (built): every underwrite response carries
`talent_placement` — the roles the asset's payroll lines
already fund, plus the asset's annual payroll budget derived
from those same lines. Matching is then arithmetic, not
vibes: a profile is *rate-compatible* with an asset when its
`expected_rate_usd` fits inside the payroll envelope for its
role, and *role-compatible* when its role is one the
underwrite named. Both checks run on validated data only;
a profile that failed validation matches nothing, and an
asset whose underwrite named no roles requests nothing.

## What this is not

Not an automated hiring system, not a credential verifier —
certifications are recorded as claimed, and any verification
regime (the later-phase credential work) bolts onto the
schema without changing it.
