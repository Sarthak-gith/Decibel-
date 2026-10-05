import type { DecibelState } from "@/lib/types";
import { percent, statePresentation } from "./statePresentation";

type Props = { state: DecibelState; smoothed: number; confidence: number; verdict: "Real" | "Fake" | null; voiced: boolean; hasPrediction: boolean };

export default function RiskGauge(props: Props) {
  const value = percent(props.smoothed);
  return <section className="panel risk-panel" data-state={props.state} aria-labelledby="risk-title">
    <div><p className="eyebrow">Signal 01 / Voice</p><h2 id="risk-title">Authenticity risk</h2></div>
    <div className={`risk-reading ${!props.voiced ? "muted-prediction" : ""}`}><div className="risk-number font-mono">{props.hasPrediction ? value : "—"}<span>%</span></div><p className="eyebrow">Smoothed risk score</p></div>
    <div className="risk-meter" role="meter" aria-label="Smoothed voice risk" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value} aria-valuetext={props.hasPrediction ? `${value} percent, ${statePresentation[props.state].label}` : "Awaiting predictions"}><div style={{ width: `${value}%` }} /></div>
    <div className="risk-scale font-mono"><span>0</span><span>40</span><span>70</span><span>100</span></div>
    <div className="prediction-summary"><span className="state-text">{statePresentation[props.state].label}</span><strong>{!props.hasPrediction ? "Awaiting predictions" : !props.voiced ? "No speech detected" : props.verdict === "Fake" ? "Possible synthetic voice" : props.verdict === "Real" ? "Real voice" : "Awaiting verdict"}</strong><p>{props.voiced && props.verdict ? <><span className="font-mono">{percent(props.confidence)}%</span> confidence · {props.verdict}</> : "Score retained until the next voiced window"}</p></div>
    <p className="panel-footnote">A screening signal, not proof of identity.</p>
  </section>;
}
