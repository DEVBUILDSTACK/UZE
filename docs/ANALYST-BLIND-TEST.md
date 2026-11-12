# Analyst Blind Test — UZE Underwrite Pro Forma Ingestion

**Purpose:** prove the engine ingests a pro forma workbook it
has never seen — not the Graham Hill file it was built against.
You send a file in the institutional format; the engine parses
it and returns EGI, NOI and the 5-year projection, plus a
parse report showing exactly what it mapped, what it
defaulted, and what it did not recognize.

## Status — read first (honest, 2026-11-12)

- ✅ **The parser and the direct API method below are live**
  in the compose service and test-pinned (suite: see repo).
- ⏳ **The email method is NOT live yet.** Mail to
  `underwriting@uzemarkets.com` cannot be received until the
  mailbox/DNS setup is completed by the owner (iCloud Custom
  Email Domain / GoDaddy), and the API is not yet publicly
  deployed. When both land, an .xlsx attachment emailed to the
  gateway address routes to this same parser automatically —
  that routing is already built and tested. Until then, use
  Method A.

## Method A — direct API call (works today)

Against a running compose API (locally:
`uvicorn app:app --port 8100` from `services/compose/src`, or
the deployed URL when available):

```bash
# 1. Encode the workbook
base64 -i YourProforma.xlsx | tr -d '\n' > /tmp/proforma.b64

# 2. Send it
curl -s -X POST http://127.0.0.1:8100/api/v1/ingest/proforma \
  -H 'Content-Type: application/json' \
  -d "{\"file_base64\": \"$(cat /tmp/proforma.b64)\"}" | python3 -m json.tool
```

Or through the email gateway endpoint (the same route an
emailed attachment will take):

```bash
curl -s -X POST http://127.0.0.1:8100/api/v1/ingest/email \
  -H 'Content-Type: application/json' \
  -d "{\"subject\": \"HiCRE proforma\", \"sender\": \"you@example.com\", \
       \"attachment_base64\": \"$(cat /tmp/proforma.b64)\"}" | python3 -m json.tool
```

## What to send

A multifamily pro forma in the institutional 4-sheet format
(sheets: **Assumptions**, **Lease-Up Schedule**, **Pro Forma**,
Comps optional for this test). The parser reads the
Assumptions tab **by label**, so rows may move — labels may
not be renamed. Required labels include: Total Units · Annual
Rent Growth Rate · Initial Occupancy at Purchase · Stabilized
Vacancy Rate (Yr 2+) · Credit Loss / Bad Debt · Management
(% of EGI) · Expense Growth Rate · the per-unit expense lines
(Payroll / Utilities / Building & Mechanical / Repairs &
Maintenance / Interior Improvements / Materials & Supplies /
Marketing / General & Admin / Professional Fees / Insurance /
Taxes, each "/ Unit") · a unit-mix table (type, units, market
rent) · the Reserve — Year N schedule. Numbers may be plain,
"$1,615"-style strings, or "3%" strings — all are coerced.
File limit 10 MB, .xlsx only.

## What comes back

- `years[1..5]`: GPR, vacancy, credit loss, Net Rental Income,
  other income, **EGI**, itemized expenses (Taxes and
  Insurance as their own lines), Replacement Reserve, **NOI**,
  and a `uze_view` with OpEx excluding Taxes/Insurance.
- `valuation`: Year 1 NOI ÷ cap rate (default 5.5%, pass
  `"cap_rate"` to change it) and price per unit.
- `parse_report`:
  - `defaulted` — optional assumptions your file didn't carry
    (they were computed at 0/default — check these first);
  - `unmapped_labels` — numeric fields present in your file
    that the engine does not consume (nothing breaks; they're
    listed so you can see what was ignored);
  - `warnings` — e.g. unit mix not summing to Total Units.

If a **required** assumption is missing, you get one 422
error naming **every** missing label at once — fix and resend.
Nothing fails silently, and nothing is guessed.

## Method B — email (pending, see Status)

When the mailbox and public deployment land: email the .xlsx
to **underwriting@uzemarkets.com**. The gateway detects the
workbook, routes it to the parser, and the response is the
same payload as Method A. Production correspondence address
remains desk@uzemarkets.com (gated affiliates) and the
published intake uzemarket@uzemarkets.com; underwriting@ is
the beta/dev ingestion address for this test programme.
