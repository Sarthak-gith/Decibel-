export default function LatencyBadge({ latency, available }: { latency: number; available: boolean }) {
  return <div className="latency-badge"><span className="eyebrow">Inference latency</span><span className="font-mono">{available ? `${Math.round(latency)} ms` : "— ms"}</span></div>;
}
