"use client";

import { useState } from "react";

/** GIRA debug widget — the browser mirror of the API's
 *  POST /api/v1/agents/gira/debug endpoint. Same deterministic
 *  rules for AGRO_DIGITAL payloads: report every error with its
 *  field, coerce numbers sent as strings, nest a top-level
 *  zarc_risk_score into crop_suitability, drop keys the schema
 *  does not define, and never guess at the rest. */

type Issue = { field: string; error: string };

const NUMERIC_PATHS: [string, string][] = [
  ["soil_profile", "ph_level"],
  ["soil_profile", "nitrogen_ppm"],
  ["soil_profile", "phosphorus_ppm"],
  ["soil_profile", "potassium_ppm"],
  ["soil_profile", "organic_matter_pct"],
  ["crop_suitability", "yield_potential_tons_per_ha"],
];

const ALLOWED = new Set([
  "partner_id",
  "polygon_id",
  "geojson_polygon",
  "soil_profile",
  "crop_suitability",
  "attestation",
]);

const REQUIRED: Record<string, string[]> = {
  "": ["partner_id", "polygon_id", "geojson_polygon", "soil_profile", "crop_suitability", "attestation"],
  soil_profile: ["ph_level", "nitrogen_ppm", "phosphorus_ppm", "potassium_ppm", "organic_matter_pct"],
  crop_suitability: ["crop_type", "yield_potential_tons_per_ha", "zarc_risk_score"],
  attestation: ["provider_timestamp", "cryptographic_hash"],
};

function validate(payload: Record<string, unknown>): Issue[] {
  const issues: Issue[] = [];
  for (const [parent, fields] of Object.entries(REQUIRED)) {
    const node = parent ? payload[parent] : payload;
    if (parent && (typeof node !== "object" || node === null)) {
      issues.push({ field: parent, error: `${parent} is required and must be an object` });
      continue;
    }
    for (const field of fields) {
      const value = (node as Record<string, unknown>)?.[field];
      if (value === undefined || value === null || value === "") {
        issues.push({
          field: parent ? `${parent}.${field}` : field,
          error: `'${field}' is a required property`,
        });
      }
    }
  }
  if (payload.partner_id !== undefined && payload.partner_id !== "AGRO_DIGITAL") {
    issues.push({ field: "partner_id", error: "partner_id must be AGRO_DIGITAL" });
  }
  for (const [parent, field] of NUMERIC_PATHS) {
    const node = payload[parent] as Record<string, unknown> | undefined;
    const value = node?.[field];
    if (value !== undefined && typeof value !== "number") {
      issues.push({
        field: `${parent}.${field}`,
        error: `Expected number, got ${typeof value}`,
      });
    }
  }
  const zarc = (payload.crop_suitability as Record<string, unknown> | undefined)
    ?.zarc_risk_score;
  if (zarc !== undefined && !["LOW", "MEDIUM", "HIGH"].includes(String(zarc))) {
    issues.push({
      field: "crop_suitability.zarc_risk_score",
      error: "zarc_risk_score must be LOW, MEDIUM or HIGH",
    });
  }
  for (const key of Object.keys(payload)) {
    if (!ALLOWED.has(key)) {
      issues.push({ field: key, error: `${key} is not defined in the schema` });
    }
  }
  return issues;
}

function debugAgro(payload: Record<string, unknown>) {
  const errors = validate(payload);
  const corrected = JSON.parse(JSON.stringify(payload)) as Record<string, unknown>;
  const fixes: string[] = [];

  for (const [parent, field] of NUMERIC_PATHS) {
    const node = corrected[parent] as Record<string, unknown> | undefined;
    if (node && typeof node[field] === "string") {
      const raw = String(node[field]).trim();
      const value = Number(raw);
      if (raw !== "" && Number.isFinite(value)) {
        node[field] = value;
        fixes.push(`${parent}.${field}: coerced string "${raw}" to number ${value}`);
      }
    }
  }
  if ("zarc_risk_score" in corrected) {
    const crop = (corrected.crop_suitability ?? {}) as Record<string, unknown>;
    if (!("zarc_risk_score" in crop)) {
      crop.zarc_risk_score = corrected.zarc_risk_score;
      corrected.crop_suitability = crop;
      fixes.push("zarc_risk_score: moved from the top level into crop_suitability");
    }
    delete corrected.zarc_risk_score;
  }
  for (const key of Object.keys(corrected)) {
    if (!ALLOWED.has(key)) {
      delete corrected[key];
      fixes.push(`${key}: removed (not defined in the AGRO_DIGITAL schema)`);
    }
  }
  return { errors, fixes, corrected, remaining: validate(corrected) };
}

export default function GiraDebug({
  runLabel,
  copyLabel,
  copiedLabel,
}: {
  runLabel: string;
  copyLabel: string;
  copiedLabel: string;
}) {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<ReturnType<typeof debugAgro> | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const run = () => {
    setParseError(null);
    try {
      const parsed = JSON.parse(input);
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        setParseError("The payload must be a JSON object.");
        setResult(null);
        return;
      }
      setResult(debugAgro(parsed as Record<string, unknown>));
    } catch {
      setParseError("That is not valid JSON — check for missing commas or quotes and try again.");
      setResult(null);
    }
  };

  return (
    <div className="dbg">
      <textarea
        rows={10}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder='{"partner_id": "AGRO_DIGITAL", "soil_profile": {"ph_level": "5.8", ...}, ...}'
      />
      <button type="button" className="dp-cta" onClick={run}>
        {runLabel}
      </button>
      {parseError ? <p className="dbg-err">{parseError}</p> : null}
      {result ? (
        <div className="dbg-out">
          {result.errors.length === 0 ? (
            <p>✓ This payload already validates — nothing to fix.</p>
          ) : (
            <>
              <p>
                <strong>{result.errors.length} error(s) found:</strong>
              </p>
              <ul>
                {result.errors.map((e, i) => (
                  <li key={i}>
                    <code>{e.field}</code> — {e.error}
                  </li>
                ))}
              </ul>
            </>
          )}
          {result.fixes.length > 0 ? (
            <>
              <p>
                <strong>Fixes applied:</strong>
              </p>
              <ul>
                {result.fixes.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
              <pre>{JSON.stringify(result.corrected, null, 2)}</pre>
              <button
                type="button"
                className="dp-cta"
                onClick={async () => {
                  await navigator.clipboard.writeText(
                    JSON.stringify(result.corrected, null, 2),
                  );
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
              >
                {copied ? copiedLabel : copyLabel}
              </button>
            </>
          ) : null}
          {result.remaining.length > 0 ? (
            <p className="dbg-err">
              Still to fix by hand:{" "}
              {result.remaining.map((e) => `${e.field} (${e.error})`).join("; ")}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
