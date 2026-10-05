"use client";

import { useState } from "react";
import Header from "@/components/Header";
import RiskGauge from "@/components/RiskGauge";
import Timeline from "@/components/Timeline";
import WaveformSlot from "@/components/WaveformSlot";
import EventFeed from "@/components/EventFeed";
import ScamPanel from "@/components/ScamPanel";
import SourceSelector, { type SourceLabel } from "@/components/SourceSelector";
import ThreatBanner from "@/components/ThreatBanner";
import { useDecibelStore } from "@/lib/store";
import { useDecibelSocket } from "@/lib/useDecibelSocket";

export default function Home() {
  const session = useDecibelStore();
  const socket = useDecibelSocket();
  const [source, setSource] = useState<SourceLabel>("phone");
  const hasPrediction = session.feed.some((payload) => payload.smoothed !== undefined);
  const reset = () => { socket.stop(); session.reset(); };

  return <main className="dashboard" data-state={session.state}>
    <Header state={session.state} latency={session.latencyMs} hasLatency={session.feed.some((payload) => payload.latency_ms !== undefined)} mode={socket.mode} setMode={socket.setMode} running={Boolean(socket.handle)} starting={socket.starting} start={() => { void socket.start(source === "tab" ? "tab" : "mic"); }} stop={socket.stop} reset={reset} />
    <div className="session-notice"><ThreatBanner state={session.state} />{session.state !== "THREAT_DETECTED" && <p role="status">{socket.error ?? (socket.starting ? source === "tab" ? "Choose a tab and enable Share tab audio." : "Microphone permission needed. Allow access to begin." : socket.mode === "mock" ? "MOCK DEMO · Simulated predictions. No audio is recorded." : session.connected ? "Live session connected to the local screening service." : "Live audio · Start when the local server is ready.")}</p>}</div>
    {socket.error && session.state === "THREAT_DETECTED" && <p role="alert" className="connection-error">{socket.error}</p>}
    <div className="monitoring-grid">
      <RiskGauge state={session.state} smoothed={session.smoothed} confidence={session.confidence} verdict={session.verdict} voiced={session.voiced} hasPrediction={hasPrediction} />
      <div className="panel signal-panel"><WaveformSlot analyser={socket.handle?.analyser ?? null} state={session.state} mock={socket.mode === "mock"} /><Timeline history={session.history} /></div>
      <EventFeed feed={session.feed} events={session.events} />
    </div>
    <div className="secondary-grid"><ScamPanel scam={session.scam} /><SourceSelector value={source} onChange={setSource} disabled={Boolean(socket.handle) || socket.starting} /></div>
    <footer className="dashboard-footer"><span>{socket.mode === "mock" ? "Demonstration data" : "Local browser capture"} · Not a definitive identity check</span><span>{socket.mode === "live" ? "Speech recognition may process audio through Google." : "DECIBEL / Monitoring console"}</span></footer>
  </main>;
}
