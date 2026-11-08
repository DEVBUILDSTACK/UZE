"use client";

import { useEffect, useRef, useState } from "react";

/** Renders a Mermaid diagram in the browser. Mermaid is loaded
 *  from the jsDelivr CDN at runtime (no bundle dependency); if the
 *  CDN is unreachable the diagram source is shown instead, so the
 *  information is never lost. */

declare global {
  interface Window {
    mermaid?: {
      initialize: (cfg: Record<string, unknown>) => void;
      render: (id: string, text: string) => Promise<{ svg: string }>;
    };
  }
}

let loader: Promise<NonNullable<Window["mermaid"]>> | null = null;

function loadMermaid(): Promise<NonNullable<Window["mermaid"]>> {
  if (window.mermaid) return Promise.resolve(window.mermaid);
  if (!loader) {
    loader = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src =
        "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js";
      script.onload = () => {
        if (window.mermaid) {
          window.mermaid.initialize({
            startOnLoad: false,
            securityLevel: "loose",
          });
          resolve(window.mermaid);
        } else {
          reject(new Error("mermaid failed to initialize"));
        }
      };
      script.onerror = () => reject(new Error("mermaid CDN unreachable"));
      document.head.appendChild(script);
    });
  }
  return loader;
}

export default function MermaidDiagram({
  chart,
  title,
}: {
  chart: string;
  title: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let live = true;
    loadMermaid()
      .then(async (mermaid) => {
        if (!live || !ref.current) return;
        const id = `mmd-${Math.random().toString(36).slice(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);
        if (live && ref.current) ref.current.innerHTML = svg;
      })
      .catch(() => {
        if (live) setFailed(true);
      });
    return () => {
      live = false;
    };
  }, [chart]);

  return (
    <figure className="dg">
      <figcaption>{title}</figcaption>
      {failed ? (
        <pre className="dg-src">{chart}</pre>
      ) : (
        <div ref={ref} className="dg-svg" aria-label={title} />
      )}
    </figure>
  );
}
