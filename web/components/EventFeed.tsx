import type { DecibelPayload } from "@/lib/types";
import type { StateChangeEvent } from "@/lib/store";
import { clock, percent, statePresentation } from "./statePresentation";

export default function EventFeed({ feed, events }: { feed: Partial<DecibelPayload>[]; events: StateChangeEvent[] }) {
  return <section className="panel feed-panel" aria-labelledby="feed-title"><div className="section-heading"><h2 id="feed-title">Session telemetry</h2><span className="count-badge font-mono">{feed.length}/50</span></div><p className="eyebrow">Newest messages first</p>
    <div className="telemetry-list" tabIndex={0} aria-label="Received payloads">{feed.length ? feed.map((payload, index) => <div className="telemetry-row font-mono" key={index} data-state={payload.state}><div><time>{clock(payload.ts ?? payload.timestamp_ms)}</time><span>{payload.state ? statePresentation[payload.state].label : "Update"}</span></div><div className="telemetry-values"><span>p_fake {payload.p_fake !== undefined || payload.fake_probability !== undefined ? `${percent(payload.p_fake ?? payload.fake_probability ?? 0)}%` : "—"}</span><span>{payload.latency_ms !== undefined ? `${Math.round(payload.latency_ms)} ms` : "—"}</span></div></div>) : <p className="empty-copy">No messages yet.<br />Start the mock demo or live session.</p>}</div>
    <div className="transition-heading"><h3>State transitions</h3><span className="font-mono">{events.length}</span></div><div className="transition-list font-mono" tabIndex={0} aria-label="State transition history">{events.length ? events.slice(-20).reverse().map((event, index) => <p key={index}><time>{clock(event.timestamp)}</time><span>{event.from} → {event.to}</span></p>) : <p className="empty-copy">No transitions recorded</p>}</div>
  </section>;
}
