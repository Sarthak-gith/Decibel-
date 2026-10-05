import type { DecibelState } from "@/lib/types";
import type { DecibelMode } from "@/lib/useDecibelSocket";
import LatencyBadge from "./LatencyBadge";
import StatusPill from "./StatusPill";

type Props = {
  state: DecibelState; latency: number; hasLatency: boolean; mode: DecibelMode;
  setMode: (mode: DecibelMode) => void; running: boolean; starting: boolean;
  start: () => void; stop: () => void; reset: () => void;
};

export default function Header(props: Props) {
  return <header className="dashboard-header">
    <div className="brand"><span className="brand-mark" aria-hidden="true">D</span><div><h1>DECIBEL</h1><p>Voice authenticity screening</p></div></div>
    <div className="header-status" role="status"><StatusPill state={props.state} /></div>
    <div className="header-controls">
      <LatencyBadge latency={props.latency} available={props.hasLatency} />
      <label className="mode-label"><span className="sr-only">Stream mode</span><select aria-label="Stream mode" value={props.mode} onChange={(event) => props.setMode(event.target.value as DecibelMode)}><option value="mock">Mock demo</option><option value="live">Live audio</option></select></label>
      {props.running || props.starting ? <button className="button button-primary" onClick={props.stop}>Stop</button> : <button className="button button-primary" onClick={props.start}>Start</button>}
      <button className="button" onClick={props.reset}>Reset session</button>
    </div>
  </header>;
}
