import type { ScamMetadata } from "@/lib/types";

export default function ScamPanel({ scam }: { scam?: ScamMetadata }) {
  return <section className="panel scam-panel" aria-labelledby="scam-title"><div className="scam-heading"><div><p className="eyebrow">Signal 02 / Intent</p><h2 id="scam-title">Scam indicators</h2></div>{scam && <span className={`scam-risk ${scam.risk.toLowerCase() === "high" ? "high" : ""}`}>Risk: {scam.risk}</span>}</div>
    {scam ? <div className="scam-detail"><div className="tactic-chips">{scam.tactics?.map((tactic, index) => <span key={`${tactic}-${index}`}>{tactic.replaceAll("_", " ")}</span>)}</div><p>{scam.reason ?? "No explanation supplied"}</p></div> : <p className="empty-copy">Scam signal unavailable. No intent assessment received.</p>}
    <p className="panel-footnote">{scam ? "Latest reported intent signal · separate from voice risk" : "Voice authenticity and scam intent are separate signals."}</p>
  </section>;
}
