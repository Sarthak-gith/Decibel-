import { probability } from "./statePresentation";

export default function Timeline({ history }: { history: number[] }) {
  const values = history.slice(-60);
  const point = (value: number, index: number) => `${44 + index * (600 / 59)},${158 - probability(value) * 130}`;
  return <section className="timeline-section" aria-labelledby="timeline-title"><div className="section-heading"><h2 id="timeline-title">Risk over time</h2><span className="eyebrow">Last 60 samples</span></div>
    <svg className="timeline" viewBox="0 0 680 188" role="img" aria-label={values.length ? `Smoothed risk timeline, ${values.length} samples` : "Timeline awaiting predictions"}>
      {[0.4, 0.55, 0.7].map((level) => <g key={level}><line x1="44" x2="644" y1={158 - level * 130} y2={158 - level * 130} className="reference-line" /><text x="4" y={162 - level * 130} className="chart-label">{level.toFixed(2)}</text></g>)}
      <line x1="44" x2="644" y1="158" y2="158" className="chart-baseline" />
      {values.length > 1 && <polyline points={values.map(point).join(" ")} className="chart-signal" />}
      {values.length > 0 && <circle cx={44 + (values.length - 1) * (600 / 59)} cy={158 - probability(values[values.length - 1]) * 130} r="4" className="chart-point" />}
      {!values.length && <text x="344" y="85" textAnchor="middle" className="chart-empty">Start a session to see risk history</text>}
      <text x="44" y="182" className="chart-label">Earlier</text><text x="644" y="182" textAnchor="end" className="chart-label">Latest →</text>
    </svg>
  </section>;
}
