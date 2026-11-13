# CRM & Multi-Tenant Integration — PROPOSAL

**Status: 🔴 POST-HACKATHON ROADMAP — PROPOSAL, not built,
not scheduled.** Filed 2026-11-13 on the owner's tap as a
documentation-only record. No tables, no webhook service, no
endpoint, and no UI were built. The compose suite stands at
345 tests; nothing in this document describes running code.

## Origin and premise check

This proposal records a relayed design for a CRM layer. Its
premises were verified against the codebase before filing,
and one failed:

- **There is no Entity table, no Affiliate table, and no
  Lead table in `services/compose/src/models.py`.** Entity
  and affiliate exist today only as plain string identifiers
  carried on other records (e.g. Intent). There is no
  `crm_config` field, no `crm_webhooks.py`, no
  `/api/v1/crm/*` endpoint, and no `/crm/pipeline` page.
- The relayed directive's first step — "add a `crm_config`
  JSONB field to the Entity and Affiliate schemas" — is
  therefore not an additive patch. It requires creating the
  prerequisite models first (see Gating dependencies).
- Pricing figures for third-party CRM platforms circulated
  with the relay were **not verified** and are not recorded
  here as facts. No build or buy decision should rest on
  them without a live check.

## The concept

The CRM layer would serve two populations from one design:

1. **Affiliates without a CRM** use a native UZE pipeline:
   a Kanban board with the stages
   NEW → CONTACTED → QUALIFIED → PRE_SALES_CONTRACT.
2. **Affiliates with an external CRM** keep it. UZEmarkets
   connects to it and feeds agent-captured leads directly
   into their existing pipeline, in both directions.

### Configuration sketch (proposed, not a schema)

A per-entity / per-affiliate configuration object,
conceptually:

```json
{
  "provider": "HUBSPOT",
  "webhook_url": "https://...",
  "api_key_hash": "...",
  "auto_sync": true,
  "sync_direction": "OUTBOUND"
}
```

`sync_direction` ∈ OUTBOUND · INBOUND · BOTH. If no
configuration exists, the affiliate defaults to the native
CRM. This sketch presupposes the Entity/Affiliate models
that do not yet exist.

### Outbound (UZE → external CRM, proposed)

When a Lead is created or updated in the native CRM, the
system checks the parent entity/affiliate configuration.
If a `webhook_url` exists, it fires a POST with a
standardized Lead payload:

```json
{
  "lead_id": "...",
  "source_agent_id": "...",
  "human_contact_name": "...",
  "human_contact_email": "...",
  "entity_id": "...",
  "partner_id": "...",
  "stage": "...",
  "asset_interest": "..."
}
```

The request carries an HMAC signature header so the
receiving system can verify the payload's origin and
integrity.

### Inbound (external CRM → UZE, proposed)

`POST /api/v1/crm/sync/{affiliate_id}` — an external CRM
reports a stage change (e.g. a lead closed in the external
system); UZE updates its record and logs the event.

### Native dashboard (proposed UI)

A Kanban pipeline view with a "Connect to External CRM"
action and a per-affiliate connection status indicator
(connected / disconnected).

## Naming boundary

Provider names considered for the integration hub —
HubSpot, Zoho, Pipedrive, Salesforce, Freshsales,
AppStudio, and Yardi — appear **in this internal document
only**. They must not appear on any public-facing UI
surface or in active code without the owner's direction,
per the standing rule that vendor names stay in internal
documentation. Note: Yardi's current role in this codebase
is the underwrite chart-of-accounts dialect pack; it is
not a CRM integration today.

## Security requirement — gating, not detail

**The webhook credential system requires the owner's
explicit architectural authorization before any
implementation.** Storing webhook URLs, API-key material
(even hashed), HMAC signing secrets, and lead contact PII
for outside parties is a credential-and-privacy
architecture decision. It is not authorized by this
proposal, and no part of it may be built on relayed
authority alone. A future build must first settle, with
the owner: secret storage and rotation, signature scheme,
PII retention for lead contacts, and per-tenant isolation.

## Gating dependencies (all open)

1. Entity, Affiliate, and Lead models — to be designed and
   created, with an Alembic migration proven by the
   standing from-empty replay standard.
2. The owner's explicit architectural authorization for
   the credential system (above).
3. A publicly deployed compose API (the Render step on the
   owner's log) — webhooks to and from an unreachable API
   are fiction.
4. The owner's build tap on this proposal, post-hackathon.

## What this proposal is not

Not a commitment to build, not a description of the
current system, and not a claim that any external CRM
integration exists. Today there is no CRM in the codebase
at all — native or integrated.
