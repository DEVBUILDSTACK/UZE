/**
 * Content Desk snapshot — the micro-region index, details and pulses
 * exactly as served by the composition API (demo dataset), captured
 * 2026-11-13. Served ONLY when the live composition API is
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
    "id": "alexandria",
    "label": "Alexandria — Old Town",
    "metro": "Washington DC",
    "region": "VA",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "annapolis",
    "label": "Annapolis",
    "metro": "Annapolis",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "arlington-va",
    "label": "Arlington",
    "metro": "Washington DC",
    "region": "VA",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "baltimore-canton",
    "label": "Baltimore — Canton & Fells Point",
    "metro": "Baltimore",
    "region": "MD",
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
    "id": "boca-raton",
    "label": "Boca Raton",
    "metro": "Boca Raton",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "bwi-linthicum",
    "label": "BWI — Linthicum",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "coconut-grove",
    "label": "Miami — Coconut Grove",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "columbia-md",
    "label": "Columbia",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "coral-gables",
    "label": "Coral Gables",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "dc-capitol-hill",
    "label": "Washington DC — Capitol Hill & NoMa",
    "metro": "Washington DC",
    "region": "DC",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "dc-downtown",
    "label": "Washington DC — Downtown",
    "metro": "Washington DC",
    "region": "DC",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "dc-georgetown",
    "label": "Washington DC — Georgetown",
    "metro": "Washington DC",
    "region": "DC",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "dc-navy-yard",
    "label": "Washington DC — Navy Yard",
    "metro": "Washington DC",
    "region": "DC",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "delray-beach",
    "label": "Delray Beach",
    "metro": "Boca Raton",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "doral",
    "label": "Doral — Airport West",
    "metro": "Miami",
    "region": "FL",
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
    "id": "hollywood-fl",
    "label": "Hollywood",
    "metro": "Fort Lauderdale",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "homestead-fl",
    "label": "Homestead — Florida City",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "islamorada",
    "label": "Islamorada",
    "metro": "Florida Keys",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "jupiter-fl",
    "label": "Jupiter",
    "metro": "West Palm Beach",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "key-largo",
    "label": "Key Largo",
    "metro": "Florida Keys",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "key-west",
    "label": "Key West",
    "metro": "Florida Keys",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "marathon-fl",
    "label": "Marathon",
    "metro": "Florida Keys",
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
    "id": "miami-beach",
    "label": "Miami Beach",
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
    "specCount": 1,
    "comparableCount": 0
  },
  {
    "id": "miami-wynwood",
    "label": "Miami — Wynwood & Midtown",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "national-harbor",
    "label": "National Harbor",
    "metro": "Washington DC",
    "region": "MD",
    "specCount": 0,
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
    "id": "palm-beach-gardens",
    "label": "Palm Beach Gardens",
    "metro": "West Palm Beach",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "palm-beach-island",
    "label": "Palm Beach Island",
    "metro": "West Palm Beach",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "pompano-beach",
    "label": "Pompano Beach",
    "metro": "Fort Lauderdale",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "rockville",
    "label": "Rockville",
    "metro": "Washington DC",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "silver-spring",
    "label": "Silver Spring",
    "metro": "Washington DC",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "stuart-fl",
    "label": "Stuart",
    "metro": "Stuart",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "sunny-isles",
    "label": "Sunny Isles Beach",
    "metro": "Miami",
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
  },
  {
    "id": "tysons",
    "label": "Tysons",
    "metro": "Washington DC",
    "region": "VA",
    "specCount": 0,
    "comparableCount": 0
  },
  {
    "id": "west-palm-beach",
    "label": "West Palm Beach",
    "metro": "West Palm Beach",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0
  }
];

export const MICRO_REGION_DETAILS_SNAPSHOT: Record<
  string,
  MicroRegionDetail
> = {
  "alexandria": {
    "id": "alexandria",
    "label": "Alexandria — Old Town",
    "metro": "Washington DC",
    "region": "VA",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "annapolis": {
    "id": "annapolis",
    "label": "Annapolis",
    "metro": "Annapolis",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "arlington-va": {
    "id": "arlington-va",
    "label": "Arlington",
    "metro": "Washington DC",
    "region": "VA",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "baltimore-canton": {
    "id": "baltimore-canton",
    "label": "Baltimore — Canton & Fells Point",
    "metro": "Baltimore",
    "region": "MD",
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
  "boca-raton": {
    "id": "boca-raton",
    "label": "Boca Raton",
    "metro": "Boca Raton",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "bwi-linthicum": {
    "id": "bwi-linthicum",
    "label": "BWI — Linthicum",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "coconut-grove": {
    "id": "coconut-grove",
    "label": "Miami — Coconut Grove",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "columbia-md": {
    "id": "columbia-md",
    "label": "Columbia",
    "metro": "Baltimore",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "coral-gables": {
    "id": "coral-gables",
    "label": "Coral Gables",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "dc-capitol-hill": {
    "id": "dc-capitol-hill",
    "label": "Washington DC — Capitol Hill & NoMa",
    "metro": "Washington DC",
    "region": "DC",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "dc-downtown": {
    "id": "dc-downtown",
    "label": "Washington DC — Downtown",
    "metro": "Washington DC",
    "region": "DC",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "dc-georgetown": {
    "id": "dc-georgetown",
    "label": "Washington DC — Georgetown",
    "metro": "Washington DC",
    "region": "DC",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "dc-navy-yard": {
    "id": "dc-navy-yard",
    "label": "Washington DC — Navy Yard",
    "metro": "Washington DC",
    "region": "DC",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "delray-beach": {
    "id": "delray-beach",
    "label": "Delray Beach",
    "metro": "Boca Raton",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "doral": {
    "id": "doral",
    "label": "Doral — Airport West",
    "metro": "Miami",
    "region": "FL",
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
  "hollywood-fl": {
    "id": "hollywood-fl",
    "label": "Hollywood",
    "metro": "Fort Lauderdale",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "homestead-fl": {
    "id": "homestead-fl",
    "label": "Homestead — Florida City",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "islamorada": {
    "id": "islamorada",
    "label": "Islamorada",
    "metro": "Florida Keys",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "jupiter-fl": {
    "id": "jupiter-fl",
    "label": "Jupiter",
    "metro": "West Palm Beach",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "key-largo": {
    "id": "key-largo",
    "label": "Key Largo",
    "metro": "Florida Keys",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "key-west": {
    "id": "key-west",
    "label": "Key West",
    "metro": "Florida Keys",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "marathon-fl": {
    "id": "marathon-fl",
    "label": "Marathon",
    "metro": "Florida Keys",
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
  "miami-beach": {
    "id": "miami-beach",
    "label": "Miami Beach",
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
    "specCount": 1,
    "comparableCount": 0,
    "specs": [
      {
        "id": "6fd3cfd7-97d2-4f6d-a20b-a4005fcda73d",
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
        "targetArea": {
          "type": "Radius",
          "epicenterLat": 25.7587,
          "epicenterLng": -80.1912,
          "radiusMiles": 37.5
        },
        "subterraneanContext": null,
        "entityId": "a380c150-1fb9-49fb-992a-1e3b89593472",
        "affiliateId": null,
        "executionEnvironment": "near_intents",
        "agentAttestation": "human",
        "countryCode": null,
        "macroDistressExit": null,
        "onSiteDays": 10,
        "remoteDays": 20,
        "budgetMinUsdc": 4000,
        "budgetMaxUsdc": 25000,
        "availableFrom": 1794096000,
        "availableUntil": 1796688000,
        "tier": "ANY",
        "referringPartner": null,
        "status": "BIDDING",
        "chainIntentRef": null,
        "bidCount": 2
      }
    ]
  },
  "miami-wynwood": {
    "id": "miami-wynwood",
    "label": "Miami — Wynwood & Midtown",
    "metro": "Miami",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "national-harbor": {
    "id": "national-harbor",
    "label": "National Harbor",
    "metro": "Washington DC",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
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
  "palm-beach-gardens": {
    "id": "palm-beach-gardens",
    "label": "Palm Beach Gardens",
    "metro": "West Palm Beach",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "palm-beach-island": {
    "id": "palm-beach-island",
    "label": "Palm Beach Island",
    "metro": "West Palm Beach",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "pompano-beach": {
    "id": "pompano-beach",
    "label": "Pompano Beach",
    "metro": "Fort Lauderdale",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "rockville": {
    "id": "rockville",
    "label": "Rockville",
    "metro": "Washington DC",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "silver-spring": {
    "id": "silver-spring",
    "label": "Silver Spring",
    "metro": "Washington DC",
    "region": "MD",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "stuart-fl": {
    "id": "stuart-fl",
    "label": "Stuart",
    "metro": "Stuart",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "sunny-isles": {
    "id": "sunny-isles",
    "label": "Sunny Isles Beach",
    "metro": "Miami",
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
  },
  "tysons": {
    "id": "tysons",
    "label": "Tysons",
    "metro": "Washington DC",
    "region": "VA",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  },
  "west-palm-beach": {
    "id": "west-palm-beach",
    "label": "West Palm Beach",
    "metro": "West Palm Beach",
    "region": "FL",
    "specCount": 0,
    "comparableCount": 0,
    "specs": []
  }
};

export const MICRO_REGION_PULSES_SNAPSHOT: Record<string, PulseView> = {
  "alexandria": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Alexandria — Old Town Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "annapolis": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Annapolis Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
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
  "baltimore-canton": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Baltimore — Canton & Fells Point Pulse",
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
  "boca-raton": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Boca Raton Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "bwi-linthicum": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "BWI — Linthicum Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "coconut-grove": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Miami — Coconut Grove Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "columbia-md": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Columbia Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "coral-gables": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Coral Gables Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "dc-capitol-hill": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Washington DC — Capitol Hill & NoMa Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "dc-downtown": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Washington DC — Downtown Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "dc-georgetown": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Washington DC — Georgetown Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "dc-navy-yard": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Washington DC — Navy Yard Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "delray-beach": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Delray Beach Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "doral": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Doral — Airport West Pulse",
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
  "hollywood-fl": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Hollywood Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "homestead-fl": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Homestead — Florida City Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "islamorada": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Islamorada Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "jupiter-fl": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Jupiter Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "key-largo": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Key Largo Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "key-west": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Key West Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "marathon-fl": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Marathon Pulse",
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
  "miami-beach": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Miami Beach Pulse",
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
      "spec_count": 1,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "miami-wynwood": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Miami — Wynwood & Midtown Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "national-harbor": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "National Harbor Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
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
  "palm-beach-gardens": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Palm Beach Gardens Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "palm-beach-island": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Palm Beach Island Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "pompano-beach": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Pompano Beach Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "rockville": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Rockville Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "silver-spring": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Silver Spring Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "stuart-fl": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Stuart Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "sunny-isles": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Sunny Isles Beach Pulse",
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
  },
  "tysons": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Tysons Pulse",
    "temporalCoverage": null,
    "variableMeasured": {
      "spec_count": 0,
      "comparable_count": 0,
      "settled_volume_usdc": 0
    },
    "pulse_data": null,
    "agent_action": "POST /api/v1/specs to initiate underwriting"
  },
  "west-palm-beach": {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "West Palm Beach Pulse",
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
