/** The UZEmarkets wordmark treatment (James, 2026-11-10): "UZE" is
 *  ALWAYS the default tangerine; "markets" is ink on cream/white
 *  grounds, or white reversed out of black on dark grounds. */
export default function Wordmark({
  tone = "ink",
}: {
  tone?: "ink" | "white";
}) {
  return (
    <span className="wordmark">
      <span className="wm-uze">UZE</span>
      <span className={tone === "white" ? "wm-markets-w" : "wm-markets"}>
        markets
      </span>
    </span>
  );
}
