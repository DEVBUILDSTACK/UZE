/** DevPartner portal content — DevPartner Software Stack Portal
 *  (partners/README.md in the monorepo). The portal is public and
 *  ungated and serves three locales: /devpartner/en,
 *  /devpartner/pt-BR, /devpartner/es. The canonical documents live
 *  in the repo's partners/ folder; this module carries the rendered
 *  copy so the pages stay static. */

export const LOCALES = ["en", "pt-BR", "es"] as const;
export type Locale = (typeof LOCALES)[number];

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}

/** Where API-key requests go until the UZE ci product email exists:
 *  the configured developer mailbox. No new mailbox is created. */
export const API_KEY_EMAIL = "dev.build@decensat.org";

export const REPO_PARTNERS_URL =
  "https://github.com/DEVBUILDSTACK/UZE/tree/hackathon/nov-2026/partners";

export interface PartnerInfo {
  id: string;
  schemaFile: string;
  blurb: string;
}

export interface PortalContent {
  title: string;
  kicker: string;
  h1: string;
  intro: string;
  howHeading: string;
  tiers: { title: string; body: string }[];
  governanceHeading: string;
  governanceBody: string;
  apiHeading: string;
  endpointLabel: string;
  authLabel: string;
  authBody: string;
  responsesHeading: string;
  responses: { code: string; meaning: string }[];
  partnersHeading: string;
  partnersIntro: string;
  partners: PartnerInfo[];
  schemaLabel: string;
  exampleLabel: string;
  downloadsHeading: string;
  downloads: { label: string; file: string }[];
  ctaHeading: string;
  ctaBody: string;
  ctaButton: string;
  languageLabel: string;
}

const DOWNLOADS: PortalContent["downloads"] = [
  { label: "README", file: "README.md" },
  { label: "OpenAPI", file: "openapi.yaml" },
  { label: "01", file: "diagrams/01-partner-ingestion.md" },
  { label: "02", file: "diagrams/02-sosem-internal.md" },
];

export const CONTENT: Record<Locale, PortalContent> = {
  en: {
    title: "DevPartner Developer Portal — UZEmarkets",
    kicker: "UZEmarkets · DevPartner",
    h1: "The technical bridge for UZEmarkets data partners",
    intro:
      "UZEmarkets cannot depend on partner APIs staying online. This portal is the standardized way for our data partners — Agro Digital, BDCS and Effatha — to push spatial, soil, feedlot and agrotechnical data into the UZEmarkets A/D/R pipeline, and the public reference for how that data is validated, cached and consumed.",
    howHeading: "How it works",
    tiers: [
      {
        title: "1 · Public knowledge base",
        body: "Documentation, diagrams and the OpenAPI specification — open to anyone, in English, Brazilian Portuguese and Spanish.",
      },
      {
        title: "2 · Gated REST ingestion",
        body: "Partners push JSON payloads to the ingestion endpoint with a Bearer token (API key). Each token maps to exactly one partner, and every payload is validated against that partner's published JSON schema.",
      },
      {
        title: "3 · The Snapshot Pattern",
        body: "Every accepted payload lands in a staging area for engineering review. Once approved, it is timestamped and permanently cached in our ProviderSnapshot store. Lenders and AI agents query our database — never the partner's API — so the market keeps working when a partner is offline.",
      },
    ],
    governanceHeading: "Partner status",
    governanceBody:
      "Every partner is UNVERIFIED until an agreement is signed and its API is reviewed. Snapshots are stored as partner-claimed data with provider status UNVERIFIED; a snapshot never triggers financing, treatment or auction execution on its own.",
    apiHeading: "Ingestion API",
    endpointLabel: "Endpoint",
    authLabel: "Authentication",
    authBody:
      "Authorization: Bearer <API key>. The key identifies the partner; a payload whose partner_id does not match the key's partner is rejected.",
    responsesHeading: "Responses",
    responses: [
      { code: "202", meaning: "Accepted — payload staged for review, staging_id returned" },
      { code: "401", meaning: "Missing or unknown API key" },
      { code: "403", meaning: "Key's partner does not match payload partner_id" },
      { code: "422", meaning: "Payload failed schema validation" },
      { code: "503", meaning: "Ingestion not configured on this deployment" },
    ],
    partnersHeading: "Partner schemas",
    partnersIntro:
      "One schema per partner, version-controlled with this portal. Payloads that do not validate are rejected — nothing is silently repaired.",
    partners: [
      {
        id: "AGRO_DIGITAL",
        schemaFile: "agro-digital.json",
        blurb:
          "Natural resources & agriculture — soil chemistry, ZARC climate risk, spatial mapping.",
      },
      {
        id: "BDCS",
        schemaFile: "bdcs.json",
        blurb: "Agriculture — feedlot integration and cattle optimization.",
      },
      {
        id: "EFFATHA",
        schemaFile: "effatha.json",
        blurb:
          "Agriculture — satellite frequency treatment and crop yield.",
      },
    ],
    schemaLabel: "Schema",
    exampleLabel: "Example payload",
    downloadsHeading: "Downloads",
    downloads: DOWNLOADS.map((d) => ({
      ...d,
      label:
        d.file === "README.md"
          ? "Executive summary (README)"
          : d.file === "openapi.yaml"
            ? "OpenAPI specification"
            : d.file.includes("01")
              ? "Diagram — partner ingestion flow"
              : "Diagram — internal orchestration",
    })),
    ctaHeading: "Need an API key?",
    ctaBody:
      "Keys are issued per partner after review. Request one from the developer team:",
    ctaButton: "Request API Key",
    languageLabel: "Language",
  },
  "pt-BR": {
    title: "Portal do Desenvolvedor DevPartner — UZEmarkets",
    kicker: "UZEmarkets · DevPartner",
    h1: "A ponte técnica para os parceiros de dados da UZEmarkets",
    intro:
      "A UZEmarkets não pode depender da disponibilidade das APIs dos parceiros. Este portal é a forma padronizada para os nossos parceiros de dados — Agro Digital, BDCS e Effatha — enviarem dados espaciais, de solo, de confinamento e agrotécnicos para o pipeline A/D/R da UZEmarkets, e a referência pública de como esses dados são validados, armazenados e consumidos.",
    howHeading: "Como funciona",
    tiers: [
      {
        title: "1 · Base de conhecimento pública",
        body: "Documentação, diagramas e a especificação OpenAPI — abertos a todos, em inglês, português brasileiro e espanhol.",
      },
      {
        title: "2 · Ingestão REST com acesso controlado",
        body: "Os parceiros enviam payloads JSON ao endpoint de ingestão com um token Bearer (chave de API). Cada token corresponde a exatamente um parceiro, e cada payload é validado contra o schema JSON publicado desse parceiro.",
      },
      {
        title: "3 · O padrão Snapshot",
        body: "Cada payload aceito entra em uma área de staging para revisão da engenharia. Depois de aprovado, ele recebe um carimbo de tempo e é armazenado permanentemente no nosso repositório ProviderSnapshot. Credores e agentes de IA consultam o nosso banco de dados — nunca a API do parceiro — para que o mercado continue funcionando quando um parceiro estiver offline.",
      },
    ],
    governanceHeading: "Status do parceiro",
    governanceBody:
      "Todo parceiro é NÃO VERIFICADO até que um acordo seja assinado e sua API seja revisada. Os snapshots são armazenados como dados declarados pelo parceiro, com status de provedor NÃO VERIFICADO; um snapshot nunca aciona, por si só, financiamento, tratamento ou execução de leilão.",
    apiHeading: "API de ingestão",
    endpointLabel: "Endpoint",
    authLabel: "Autenticação",
    authBody:
      "Authorization: Bearer <chave de API>. A chave identifica o parceiro; um payload cujo partner_id não corresponda ao parceiro da chave é rejeitado.",
    responsesHeading: "Respostas",
    responses: [
      { code: "202", meaning: "Aceito — payload em staging para revisão, staging_id retornado" },
      { code: "401", meaning: "Chave de API ausente ou desconhecida" },
      { code: "403", meaning: "O parceiro da chave não corresponde ao partner_id do payload" },
      { code: "422", meaning: "O payload não passou na validação do schema" },
      { code: "503", meaning: "Ingestão não configurada nesta implantação" },
    ],
    partnersHeading: "Schemas dos parceiros",
    partnersIntro:
      "Um schema por parceiro, versionado junto com este portal. Payloads que não validam são rejeitados — nada é corrigido silenciosamente.",
    partners: [
      {
        id: "AGRO_DIGITAL",
        schemaFile: "agro-digital.json",
        blurb:
          "Recursos naturais e agricultura — química do solo, risco climático ZARC, mapeamento espacial.",
      },
      {
        id: "BDCS",
        schemaFile: "bdcs.json",
        blurb: "Agricultura — integração de confinamentos e otimização de gado.",
      },
      {
        id: "EFFATHA",
        schemaFile: "effatha.json",
        blurb:
          "Agricultura — tratamento por frequência de satélite e produtividade de safras.",
      },
    ],
    schemaLabel: "Schema",
    exampleLabel: "Payload de exemplo",
    downloadsHeading: "Downloads",
    downloads: DOWNLOADS.map((d) => ({
      ...d,
      label:
        d.file === "README.md"
          ? "Resumo executivo (README)"
          : d.file === "openapi.yaml"
            ? "Especificação OpenAPI"
            : d.file.includes("01")
              ? "Diagrama — fluxo de ingestão do parceiro"
              : "Diagrama — orquestração interna",
    })),
    ctaHeading: "Precisa de uma chave de API?",
    ctaBody:
      "As chaves são emitidas por parceiro, após revisão. Solicite uma à equipe de desenvolvimento:",
    ctaButton: "Solicitar chave de API",
    languageLabel: "Idioma",
  },
  es: {
    title: "Portal del Desarrollador DevPartner — UZEmarkets",
    kicker: "UZEmarkets · DevPartner",
    h1: "El puente técnico para los socios de datos de UZEmarkets",
    intro:
      "UZEmarkets no puede depender de que las API de los socios estén siempre en línea. Este portal es la vía estandarizada para que nuestros socios de datos — Agro Digital, BDCS y Effatha — envíen datos espaciales, de suelo, de feedlots y agrotécnicos al pipeline A/D/R de UZEmarkets, y la referencia pública de cómo esos datos se validan, se almacenan y se consumen.",
    howHeading: "Cómo funciona",
    tiers: [
      {
        title: "1 · Base de conocimiento pública",
        body: "Documentación, diagramas y la especificación OpenAPI — abiertos a todos, en inglés, portugués brasileño y español.",
      },
      {
        title: "2 · Ingesta REST con acceso controlado",
        body: "Los socios envían payloads JSON al endpoint de ingesta con un token Bearer (clave de API). Cada token corresponde exactamente a un socio, y cada payload se valida contra el esquema JSON publicado de ese socio.",
      },
      {
        title: "3 · El patrón Snapshot",
        body: "Cada payload aceptado entra en un área de staging para revisión de ingeniería. Una vez aprobado, recibe una marca de tiempo y se almacena permanentemente en nuestro repositorio ProviderSnapshot. Los prestamistas y los agentes de IA consultan nuestra base de datos — nunca la API del socio — para que el mercado siga funcionando cuando un socio está fuera de línea.",
      },
    ],
    governanceHeading: "Estado del socio",
    governanceBody:
      "Todo socio está NO VERIFICADO hasta que se firma un acuerdo y se revisa su API. Los snapshots se almacenan como datos declarados por el socio, con estado de proveedor NO VERIFICADO; un snapshot nunca activa por sí solo financiación, tratamiento ni ejecución de subastas.",
    apiHeading: "API de ingesta",
    endpointLabel: "Endpoint",
    authLabel: "Autenticación",
    authBody:
      "Authorization: Bearer <clave de API>. La clave identifica al socio; un payload cuyo partner_id no coincida con el socio de la clave es rechazado.",
    responsesHeading: "Respuestas",
    responses: [
      { code: "202", meaning: "Aceptado — payload en staging para revisión, se devuelve staging_id" },
      { code: "401", meaning: "Clave de API ausente o desconocida" },
      { code: "403", meaning: "El socio de la clave no coincide con el partner_id del payload" },
      { code: "422", meaning: "El payload no superó la validación del esquema" },
      { code: "503", meaning: "Ingesta no configurada en esta implementación" },
    ],
    partnersHeading: "Esquemas de los socios",
    partnersIntro:
      "Un esquema por socio, versionado junto con este portal. Los payloads que no validan son rechazados — nada se corrige en silencio.",
    partners: [
      {
        id: "AGRO_DIGITAL",
        schemaFile: "agro-digital.json",
        blurb:
          "Recursos naturales y agricultura — química del suelo, riesgo climático ZARC, mapeo espacial.",
      },
      {
        id: "BDCS",
        schemaFile: "bdcs.json",
        blurb: "Agricultura — integración de feedlots y optimización ganadera.",
      },
      {
        id: "EFFATHA",
        schemaFile: "effatha.json",
        blurb:
          "Agricultura — tratamiento por frecuencia satelital y rendimiento de cultivos.",
      },
    ],
    schemaLabel: "Esquema",
    exampleLabel: "Payload de ejemplo",
    downloadsHeading: "Descargas",
    downloads: DOWNLOADS.map((d) => ({
      ...d,
      label:
        d.file === "README.md"
          ? "Resumen ejecutivo (README)"
          : d.file === "openapi.yaml"
            ? "Especificación OpenAPI"
            : d.file.includes("01")
              ? "Diagrama — flujo de ingesta del socio"
              : "Diagrama — orquestación interna",
    })),
    ctaHeading: "¿Necesitas una clave de API?",
    ctaBody:
      "Las claves se emiten por socio, tras revisión. Solicita una al equipo de desarrollo:",
    ctaButton: "Solicitar clave de API",
    languageLabel: "Idioma",
  },
};

/** Example payloads — identical across locales (the wire format is
 *  language-neutral; each payload declares its own language). */
export const EXAMPLES: Record<string, string> = {
  AGRO_DIGITAL: `{
  "partner_id": "AGRO_DIGITAL",
  "polygon_id": "BR-MT-36400",
  "geojson_polygon": {
    "type": "Polygon",
    "coordinates": [[[-56.1, -12.5], [-56.0, -12.5], [-56.0, -12.4], [-56.1, -12.4], [-56.1, -12.5]]]
  },
  "soil_profile": {
    "ph_level": 5.8,
    "nitrogen_ppm": 12.4,
    "phosphorus_ppm": 8.2,
    "potassium_ppm": 45.0,
    "organic_matter_pct": 2.1
  },
  "crop_suitability": {
    "crop_type": "CORN_SILAGE",
    "yield_potential_tons_per_ha": 14.5,
    "zarc_risk_score": "LOW"
  },
  "attestation": {
    "provider_timestamp": "2026-11-08T14:00:00Z",
    "cryptographic_hash": "sha256:a1b2c3d4...",
    "satellite_source": "Sentinel-2"
  }
}`,
  BDCS: `{
  "partner_id": "BDCS",
  "polygon_id": "BR-MT-36400",
  "language": "pt-BR",
  "feedlot_context": {
    "cattle_head_count": 1500,
    "feed_type": "CORN_SILAGE",
    "target_slaughter_weight_kg": 550,
    "feed_optimization_index": 0.85
  }
}`,
  EFFATHA: `{
  "partner_id": "EFFATHA",
  "polygon_id": "BR-MT-36400",
  "language": "pt-BR",
  "agrotechnical_context": {
    "delivery_mechanism": "SATELLITE_FREQUENCY",
    "treatment_protocol_id": "EFFATHA-CORN-01",
    "target_crop": "CORN_SILAGE",
    "activation_date": "2026-11-08T00:00:00Z"
  },
  "attestation": {
    "provider_timestamp": "2026-11-08T14:00:00Z",
    "cryptographic_hash": "sha256:e5f6g7h8..."
  }
}`,
};
