import { create } from "zustand";
import type { DecibelPayload, DecibelState, ScamMetadata } from "./types";

export type StateChangeEvent = {
  timestamp: number;
  from: DecibelState;
  to: DecibelState;
};

type SessionState = {
  state: DecibelState;
  smoothed: number;
  pFake: number;
  confidence: number;
  verdict: "Fake" | "Real" | null;
  voiced: boolean;
  latencyMs: number;
  scam: ScamMetadata | undefined;
  connected: boolean;
  history: number[];
  feed: Partial<DecibelPayload>[];
  events: StateChangeEvent[];
};

export type DecibelStore = SessionState & {
  ingest: (payload: Partial<DecibelPayload>) => void;
  reset: () => void;
};

const initialSession = (): SessionState => ({
  state: "DISCONNECTED",
  smoothed: 0,
  pFake: 0,
  confidence: 0,
  verdict: null,
  voiced: false,
  latencyMs: 0,
  scam: undefined,
  connected: false,
  history: [],
  feed: [],
  events: [],
});

export const useDecibelStore = create<DecibelStore>((set) => ({
  ...initialSession(),
  ingest: (payload) =>
    set((current) => {
      const state = payload.state !== undefined ? payload.state : current.state;

      return {
        state,
        connected:
          payload.state !== undefined
            ? state !== "DISCONNECTED"
            : current.connected,
        smoothed:
          payload.smoothed !== undefined ? payload.smoothed : current.smoothed,
        pFake:
          payload.p_fake !== undefined
            ? payload.p_fake
            : payload.fake_probability !== undefined
              ? payload.fake_probability
              : current.pFake,
        confidence:
          payload.confidence !== undefined
            ? payload.confidence
            : current.confidence,
        verdict:
          payload.verdict !== undefined ? payload.verdict : current.verdict,
        voiced: payload.voiced !== undefined ? payload.voiced : current.voiced,
        latencyMs:
          payload.latency_ms !== undefined
            ? payload.latency_ms
            : current.latencyMs,
        scam: payload.scam !== undefined ? payload.scam : current.scam,
        history:
          payload.smoothed !== undefined
            ? [...current.history, payload.smoothed].slice(-60)
            : current.history,
        feed: [payload, ...current.feed].slice(0, 50),
        events:
          state !== current.state
            ? [
                ...current.events,
                {
                  timestamp: payload.ts ?? payload.timestamp_ms ?? Date.now(),
                  from: current.state,
                  to: state,
                },
              ]
            : current.events,
      };
    }),
  reset: () => set(initialSession()),
}));
