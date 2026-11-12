/**
 * Content Desk snapshot — the micro-region index, details and pulses
 * exactly as served by the composition API (demo dataset), captured
 * 2026-11-10. Served ONLY when the live composition API is
 * unreachable (e.g. a deployment without COMPOSE_API_URL configured);
 * the moment the API answers, live records replace this snapshot.
 * Regenerate by re-capturing GET /api/v1/micro-regions (+ /{id} and
 * /{id}/pulse per region) from a running compose service.
 */
import type {
  MicroRegionDetail,
  MicroRegionView,
  PulseView,
} from "@/lib/compose";

export const MICRO_REGIONS_SNAPSHOT: MicroRegionView[] = [
  {
    "id": "arlington-va",
    "label": "Arlington",
    "metro": "Washington DC",
    "region": "VA",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "baltimore-city",
    "label": "Baltimore City",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "baltimore-nw",
    "label": "Northwest Baltimore",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "bethesda-cbd",
    "label": "Bethesda CBD",
    "metro": "Washington DC",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "fort-lauderdale",
    "label": "Fort Lauderdale",
    "metro": "Fort Lauderdale",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "miami-aventura",
    "label": "Miami — Aventura",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "miami-brickell",
    "label": "Miami — Brickell",
    "metro": "Miami",
    "region": "FL",
    "specCount": 4,
    "comparableCount": 0
  },
  {
    "id": "orlando-kissimmee",
    "label": "Orlando — Kissimmee",
    "metro": "Orlando",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "tampa-fl",
    "label": "Tampa",
    "metro": "Tampa",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "towson",
    "label": "Towson",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0
  }
];

export const MICRO_REGION_DETAILS_SNAPSHOT: Record<
  string,
  MicroRegionDetail
> = {
  "arlington-va": {
    "id": "arlington-va",
    "label": "Arlington",
    "metro": "Washington DC",
    "region": "VA",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "baltimore-city": {
    "id": "baltimore-city",
    "label": "Baltimore City",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "baltimore-nw": {
    "id": "baltimore-nw",
    "label": "Northwest Baltimore",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "bethesda-cbd": {
    "id": "bethesda-cbd",
    "label": "Bethesda CBD",
    "metro": "Washington DC",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "fort-lauderdale": {
    "id": "fort-lauderdale",
    "label": "Fort Lauderdale",
    "metro": "Fort Lauderdale",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "miami-aventura": {
    "id": "miami-aventura",
    "label": "Miami — Aventura",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "miami-brickell": {
    "id": "miami-brickell",
    "label": "Miami — Brickell",
    "metro": "Miami",
    "region": "FL",
    "specCount": 4,
    "comparableCount": 0,
    "specs": [
      {
        "id": "96a6b169-658c-40cd-a9db-338c4c6d3269",
        "kind": "demand",
        "posterKind": "human",
        "posterAccount": "syndicate.acme.testnet",
        "domain": "cre_expense_analysis",
        "workProduct": "operating_budget",
        "deliverable": {
          "operatingBudget": "full-year operating budget, every role, every opex line A-Z, brand fees included",
          "pmSpec": "property manager specification derived from the budget"
        },
        "microRegionId": "miami-brickell",
        "assetContext": {
          "propertyType": "branded_hotel",
          "doorCount": 340,
          "brandAffiliation": "Aloft",
          "acquisitionStage": "underwriting"
        },
        "assetSubclass": "H",
        "entityId": "a380c150-1fb9-49fb-992a-1e3b89593472",
        "targetArea": {
          "type": "Radius",
          "epicenterLat": 25.7587,
          "epicenterLng": -80.1912,
          "radiusMiles": 37.5
        },
        "subterraneanContext": null,
        "onSiteDays": 10,
        "remoteDays": 20,
        "budgetMinUsdc": 4000,
        "budgetMaxUsdc": 25000,
        "availableFrom": 1794096000,
        "availableUntil": 1796688000,
        "tier": "ANY",
        "referringPartner": null,
        "status": "SELECTED",
        "chainIntentRef": "stub_intent_id",
        "bidCount": 2
      },
      {
        "id": "2271c90e-48e1-485c-af43-e8142520a02c",
        "kind": "demand",
        "posterKind": "human",
        "posterAccount": "syndicate.acme.testnet",
        "domain": "cre_expense_analysis",
        "workProduct": "operating_budget",
        "deliverable": {
          "operatingBudget": "full-year operating budget, every role, every opex line A-Z, brand fees included",
          "pmSpec": "property manager specification derived from the budget"
        },
        "microRegionId": "miami-brickell",
        "assetContext": {
          "propertyType": "branded_hotel",
          "doorCount": 340,
          "brandAffiliation": "Aloft",
          "acquisitionStage": "underwriting"
        },
        "assetSubclass": "H",
        "entityId": "a380c150-1fb9-49fb-992a-1e3b89593472",
        "targetArea": {
          "type": "Radius",
          "epicenterLat": 25.7587,
          "epicenterLng": -80.1912,
          "radiusMiles": 37.5
        },
        "subterraneanContext": null,
        "onSiteDays": 10,
        "remoteDays": 20,
        "budgetMinUsdc": 4000,
        "budgetMaxUsdc": 25000,
        "availableFrom": 1794096000,
        "availableUntil": 1796688000,
        "tier": "ANY",
        "referringPartner": null,
        "status": "POSTED",
        "chainIntentRef": null,
        "bidCount": 0
      },
      {
        "id": "a06c1571-c060-4a8d-bed1-14b67ec16737",
        "kind": "demand",
        "posterKind": "human",
        "posterAccount": "syndicate.acme.testnet",
        "domain": "cre_expense_analysis",
        "workProduct": "operating_budget",
        "deliverable": {
          "operatingBudget": "full-year operating budget, every role, every opex line A-Z, brand fees included",
          "pmSpec": "property manager specification derived from the budget"
        },
        "microRegionId": "miami-brickell",
        "assetContext": {
          "propertyType": "branded_hotel",
          "doorCount": 340,
          "brandAffiliation": "Aloft",
          "acquisitionStage": "underwriting"
        },
        "assetSubclass": "H",
        "entityId": "a380c150-1fb9-49fb-992a-1e3b89593472",
        "targetArea": {
          "type": "Radius",
          "epicenterLat": 25.7587,
          "epicenterLng": -80.1912,
          "radiusMiles": 37.5
        },
        "subterraneanContext": null,
        "onSiteDays": 10,
        "remoteDays": 20,
        "budgetMinUsdc": 4000,
        "budgetMaxUsdc": 25000,
        "availableFrom": 1794096000,
        "availableUntil": 1796688000,
        "tier": "ANY",
        "referringPartner": null,
        "status": "POSTED",
        "chainIntentRef": null,
        "bidCount": 0
      },
      {
        "id": "57691a1a-95d0-4b16-af0e-af93a8384133",
        "kind": "demand",
        "posterKind": "human",
        "posterAccount": "syndicate.acme.testnet",
        "domain": "cre_expense_analysis",
        "workProduct": "operating_budget",
        "deliverable": {
          "operatingBudget": "full-year operating budget, every role, every opex line A-Z, brand fees included",
          "pmSpec": "property manager specification derived from the budget"
        },
        "microRegionId": "miami-brickell",
        "assetContext": {
          "propertyType": "branded_hotel",
          "doorCount": 340,
          "brandAffiliation": "Aloft",
          "acquisitionStage": "underwriting"
        },
        "assetSubclass": "H",
        "entityId": "a380c150-1fb9-49fb-992a-1e3b89593472",
        "targetArea": {
          "type": "Radius",
          "epicenterLat": 25.7587,
          "epicenterLng": -80.1912,
          "radiusMiles": 37.5
        },
        "subterraneanContext": null,
        "onSiteDays": 10,
        "remoteDays": 20,
        "budgetMinUsdc": 4000,
        "budgetMaxUsdc": 25000,
        "availableFrom": 1794096000,
        "availableUntil": 1796688000,
        "tier": "ANY",
        "referringPartner": null,
        "status": "POSTED",
        "chainIntentRef": null,
        "bidCount": 0
      }
    ]
  },
  "orlando-kissimmee": {
    "id": "orlando-kissimmee",
    "label": "Orlando — Kissimmee",
    "metro": "Orlando",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "tampa-fl": {
    "id": "tampa-fl",
    "label": "Tampa",
    "metro": "Tampa",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "towson": {
    "id": "towson",
    "label": "Towson",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  }
};

export const MICRO_REGION_PULSES_SNAPSHOT: Record<string, PulseView> = {
  "arlington-va": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Arlington Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "baltimore-city": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Baltimore City Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "baltimore-nw": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Northwest Baltimore Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "bethesda-cbd": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Bethesda CBD Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "fort-lauderdale": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Fort Lauderdale Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "miami-aventura": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Miami — Aventura Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "miami-brickell": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Miami — Brickell Pulse",
    "temporalCoverage": "2026-11/2026-11",
    "variableMeasured": {
      "spec_count": 4,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "orlando-kissimmee": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Orlando — Kissimmee Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "tampa-fl": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Tampa Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "towson": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Towson Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  }
};
