import type { DecibelState } from "@/lib/types";

export const statePresentation: Record<DecibelState, { label: string; cue: string }> = {
  DISCONNECTED: { label: "Disconnected", cue: "○" },
  LISTENING: { label: "Listening", cue: "◉" },
  ANALYZING: { label: "Analyzing", cue: "≈" },
  SECURE: { label: "Secure", cue: "✓" },
  CAUTION: { label: "Caution", cue: "!" },
  THREAT_DETECTED: { label: "Threat detected", cue: "⚠" },
};

export const probability = (value: number) => Number.isFinite(value) ? Math.min(1, Math.max(0, value)) : 0;
export const percent = (value: number) => Math.round(probability(value) * 100);
export const clock = (value?: number) => value !== undefined && Number.isFinite(value)
  ? new Date(value).toLocaleTimeString("en-GB", { hour12: false }) : "—";
