import WaveformCanvas from "./audio/WaveformCanvas";
import type { DecibelState } from "@/lib/types";

export default function WaveformSlot({ analyser, state, mock, replay = false }: { analyser: AnalyserNode | null; state: DecibelState; mock: boolean; replay?: boolean }) {
  return <section className="waveform-section" aria-labelledby="waveform-title"><div className="section-heading"><h2 id="waveform-title">Audio input</h2><span className="eyebrow">{analyser ? "16 kHz · Mono" : mock ? "Simulated telemetry" : "No audio input"}</span></div>
    <div className="waveform-slot">{analyser ? <WaveformCanvas analyser={analyser} threat={state === "THREAT_DETECTED"} /> : <div className="waveform-empty"><svg viewBox="0 0 600 60" aria-hidden="true"><path d="M0 30 H600" /></svg><p>{mock ? "Mock mode · no microphone captured" : replay ? "Recorded telemetry · no audio waveform" : "Start live audio to view the waveform"}</p></div>}</div>
  </section>;
}
