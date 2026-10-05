import { useDecibelStore } from "@/lib/store";
import type { DecibelMode } from "@/lib/useDecibelSocket";

export default function IncidentExport({ mode }: { mode: DecibelMode }) {
  const hasData = useDecibelStore((session) => session.feed.length > 0);
  const download = () => {
    const session = useDecibelStore.getState();
    const summary = {
      exported_at: new Date().toISOString(),
      mode,
      data_notice: "Mode is selected mode at export time. Retained telemetry may include earlier modes. Mock data is simulated; replay data is recorded. This is not an accuracy evaluation.",
      retention: { smoothed_samples: 60, payloads: 50, transitions: "All transitions in this session" },
      state: session.state,
      transitions: session.events,
      smoothed_history: session.history,
      // Export contract fields only: omit unknown fields, transcripts and secrets.
      payloads: session.feed.map((payload) => ({
        type: payload.type, ts: payload.ts, timestamp_ms: payload.timestamp_ms,
        window_ms: payload.window_ms, state: payload.state, voiced: payload.voiced,
        p_fake: payload.p_fake, fake_probability: payload.fake_probability,
        smoothed: payload.smoothed, verdict: payload.verdict,
        confidence: payload.confidence, latency_ms: payload.latency_ms,
        scam: payload.scam ? { risk: payload.scam.risk, tactics: payload.scam.tactics, reason: payload.scam.reason } : undefined,
      })),
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(summary, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `decibel-${mode}-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <button className="export-button" disabled={!hasData} onClick={download}>Export incident summary ↓</button>;
}
