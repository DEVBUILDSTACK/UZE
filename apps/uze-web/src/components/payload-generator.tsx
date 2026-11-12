"use client";

import { useMemo, useState } from "react";

/** Payload Generator — builds the exact ADV Americas ingestion
 *  payload from form values. Field names are the schema's own;
 *  numeric inputs are emitted as JSON numbers, and the polygon is
 *  a single GeoJSON ring. */

const DEFAULT_RING = `[[-56.0728, -12.5453], [-56.01, -12.5453], [-56.01, -12.49], [-56.0728, -12.49], [-56.0728, -12.5453]]`;

export default function PayloadGenerator({
  copyLabel,
  copiedLabel,
}: {
  copyLabel: string;
  copiedLabel: string;
}) {
  const [values, setValues] = useState<Record<string, string>>({
    polygon_id: "BR-MT-36400",
    ph_level: "5.8",
    nitrogen_ppm: "42",
    phosphorus_ppm: "18",
    potassium_ppm: "120",
    organic_matter_pct: "3.4",
    crop_type: "soybean",
    yield_potential_tons_per_ha: "3.6",
    zarc_risk_score: "LOW",
    satellite_source: "Sentinel-2",
    provider_timestamp: "2026-11-08T14:32:00Z",
    cryptographic_hash: "sha256:9f2c…",
    ring: DEFAULT_RING,
  });
  const [copied, setCopied] = useState(false);

  const payload = useMemo(() => {
    const num = (key: string) => {
      const n = Number(values[key]);
      return Number.isFinite(n) ? n : values[key];
    };
    let ring: unknown = [];
    try {
      ring = JSON.parse(values.ring);
    } catch {
      ring = values.ring;
    }
    return {
      partner_id: "AGRO_DIGITAL",
      polygon_id: values.polygon_id,
      geojson_polygon: { type: "Polygon", coordinates: [ring] },
      soil_profile: {
        ph_level: num("ph_level"),
        nitrogen_ppm: num("nitrogen_ppm"),
        phosphorus_ppm: num("phosphorus_ppm"),
        potassium_ppm: num("potassium_ppm"),
        organic_matter_pct: num("organic_matter_pct"),
      },
      crop_suitability: {
        crop_type: values.crop_type,
        yield_potential_tons_per_ha: num("yield_potential_tons_per_ha"),
        zarc_risk_score: values.zarc_risk_score,
      },
      attestation: {
        provider_timestamp: values.provider_timestamp,
        cryptographic_hash: values.cryptographic_hash,
        satellite_source: values.satellite_source,
      },
    };
  }, [values]);

  const text = JSON.stringify(payload, null, 2);
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setValues((v) => ({ ...v, [key]: e.target.value }));

  const fields: [string, string][] = [
    ["polygon_id", "polygon_id"],
    ["ph_level", "soil_profile.ph_level"],
    ["nitrogen_ppm", "soil_profile.nitrogen_ppm"],
    ["phosphorus_ppm", "soil_profile.phosphorus_ppm"],
    ["potassium_ppm", "soil_profile.potassium_ppm"],
    ["organic_matter_pct", "soil_profile.organic_matter_pct"],
    ["crop_type", "crop_suitability.crop_type"],
    ["yield_potential_tons_per_ha", "crop_suitability.yield_potential_tons_per_ha"],
    ["satellite_source", "attestation.satellite_source"],
    ["provider_timestamp", "attestation.provider_timestamp"],
    ["cryptographic_hash", "attestation.cryptographic_hash"],
  ];

  return (
    <div className="gen">
      <div className="gen-form">
        {fields.map(([key, label]) =>
          key === "zarc_risk_score" ? null : (
            <label key={key}>
              <span>{label}</span>
              <input value={values[key]} onChange={set(key)} />
            </label>
          ),
        )}
        <label>
          <span>crop_suitability.zarc_risk_score</span>
          <select value={values.zarc_risk_score} onChange={set("zarc_risk_score")}>
            <option>LOW</option>
            <option>MEDIUM</option>
            <option>HIGH</option>
          </select>
        </label>
        <label className="gen-wide">
          <span>geojson_polygon.coordinates[0] — one ring of [lng, lat] pairs</span>
          <textarea rows={3} value={values.ring} onChange={set("ring")} />
        </label>
      </div>
      <pre className="gen-out">{text}</pre>
      <button
        type="button"
        className="dp-cta"
        onClick={async () => {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        }}
      >
        {copied ? copiedLabel : copyLabel}
      </button>
    </div>
  );
}
