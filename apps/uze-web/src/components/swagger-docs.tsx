"use client";

import { useEffect } from "react";

/** Swagger UI, loaded from the jsDelivr CDN and pointed at the
 *  portal's own copy of the OpenAPI spec (/openapi.yaml). When the
 *  staging API is deployed, the same spec drives its live docs. */

declare global {
  interface Window {
    SwaggerUIBundle?: (cfg: Record<string, unknown>) => unknown;
  }
}

export default function SwaggerDocs() {
  useEffect(() => {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href =
      "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css";
    document.head.appendChild(css);
    const script = document.createElement("script");
    script.src =
      "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js";
    script.onload = () => {
      window.SwaggerUIBundle?.({
        url: "/openapi.yaml",
        dom_id: "#swagger-ui",
        deepLinking: true,
      });
    };
    document.body.appendChild(script);
  }, []);
  return <div id="swagger-ui" className="swagger-wrap" />;
}
