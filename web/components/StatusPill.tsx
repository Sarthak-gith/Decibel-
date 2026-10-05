import type { DecibelState } from "@/lib/types";
import { statePresentation } from "./statePresentation";

export default function StatusPill({ state }: { state: DecibelState }) {
  const { label, cue } = statePresentation[state];
  return <span className="status-pill" data-state={state}><span aria-hidden="true">{cue}</span>{label}</span>;
}
