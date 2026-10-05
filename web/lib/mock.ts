import type { DecibelPayload, DecibelState } from "./types";

export type MockHandle = {
  stop: () => void;
};

type Phase = {
  state: DecibelState;
  ticks: number;
  values?: readonly number[];
};

const phases: readonly Phase[] = [
  { state: "LISTENING", ticks: 3 },
  { state: "ANALYZING", ticks: 2 },
  {
    state: "SECURE",
    ticks: 10,
    values: [0.14, 0.18, 0.12, 0.22, 0.19, 0.15, 0.21, 0.17, 0.13, 0.2],
  },
  { state: "CAUTION", ticks: 4, values: [0.4, 0.48, 0.57, 0.65] },
  {
    state: "THREAT_DETECTED",
    ticks: 10,
    values: [0.75, 0.78, 0.82, 0.85, 0.88, 0.91, 0.89, 0.93, 0.95, 0.92],
  },
  { state: "SECURE", ticks: 1, values: [0.16] },
];

const clamp = (value: number): number => Math.min(1, Math.max(0, value));

export function startMock(
  onMessage: (payload: DecibelPayload) => void,
): MockHandle {
  let phaseIndex = 0;
  let phaseTick = 0;
  let previousSmoothed = 0;

  const timer = setInterval(() => {
    const phase = phases[phaseIndex];
    const timestamp = Date.now();
    const payload: DecibelPayload = {
      type: "status",
      state: phase.state,
      ts: timestamp,
      timestamp_ms: timestamp,
      window_ms: 3000,
    };

    if (phase.values) {
      // Brief silence preserves the previous signal within the SECURE phase.
      const voiced = !(phaseIndex === 2 && (phaseTick === 4 || phaseTick === 8));
      const smoothed = voiced
        ? clamp(phase.values[phaseTick])
        : previousSmoothed;
      const pFake = voiced ? smoothed : 0;

      Object.assign(payload, {
        type: "verdict",
        voiced,
        smoothed,
        p_fake: pFake,
        fake_probability: pFake,
        confidence: voiced ? clamp(Math.max(pFake, 1 - pFake)) : 0,
        verdict: voiced ? (pFake >= 0.5 ? "Fake" : "Real") : null,
        latency_ms: 80 + Math.floor(Math.random() * 221),
      });
      previousSmoothed = smoothed;

      if (phase.state === "THREAT_DETECTED" && phaseTick >= 5) {
        payload.scam = {
          risk: "high",
          tactics: ["urgency", "otp_request"],
          reason: "Caller urgently requests an OTP.",
        };
      }
    }

    phaseTick += 1;
    if (phaseTick === phase.ticks) {
      phaseTick = 0;
      phaseIndex = (phaseIndex + 1) % phases.length;
    }
    onMessage(payload);
  }, 1000);

  return {
    stop: () => clearInterval(timer),
  };
}
