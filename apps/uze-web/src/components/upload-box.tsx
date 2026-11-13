"use client";

import { useRef, useState } from "react";

/** Drag-and-drop intake box for the UZE Underwrite page.
 *  DEMO SCOPE, stated on the box itself: public intake activates
 *  with the public API launch; today the working intake is the
 *  email gateway (forward financials to desk@uzemarkets.com).
 *  The box accepts and identifies the file locally — it does not
 *  pretend an upload happened. */
export default function UploadBox() {
  const [file, setFile] = useState<File | null>(null);
  const [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload financials"
        onClick={() => input.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") input.current?.click();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          const f = e.dataTransfer.files?.[0];
          if (f) setFile(f);
        }}
        style={{
          border: `2px dashed ${drag ? "#ff6b00" : "var(--border)"}`,
          borderRadius: 12,
          padding: "1.4rem",
          textAlign: "center",
          cursor: "pointer",
          background: drag ? "#fff4ec" : "var(--panel)",
        }}
      >
        {file ? (
          <p style={{ margin: 0 }}>
            <strong>{file.name}</strong> ({Math.max(1, Math.round(file.size / 1024))} KB)
            selected.
          </p>
        ) : (
          <p style={{ margin: 0 }}>
            Drag &amp; drop your T-12 or P&amp;L here, or click to
            choose the file.
          </p>
        )}
        <input
          ref={input}
          type="file"
          accept=".pdf,.csv,.xlsx,.xls"
          hidden
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) setFile(f);
          }}
        />
      </div>
      <p className="note">
        Public intake activates with the API launch. Today, forward
        your financials to{" "}
        <a href="mailto:desk@uzemarkets.com">desk@uzemarkets.com</a>{" "}
        and UZE Underwrite returns the verified PDF report.
      </p>
    </div>
  );
}
