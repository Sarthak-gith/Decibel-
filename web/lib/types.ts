export type DecibelState =
  | "DISCONNECTED"
  | "LISTENING"
  | "ANALYZING"
  | "SECURE"
  | "CAUTION"
  | "THREAT_DETECTED";

export type ScamMetadata = {
  risk: string;
  tactics?: string[];
  reason?: string;
};

// Status messages may contain only state; verdict messages add optional data.
export type DecibelPayload = {
  type?: string;
  ts?: number;
  timestamp_ms?: number;
  window_ms?: number;
  voiced?: boolean;
  p_fake?: number;
  fake_probability?: number;
  smoothed?: number;
  verdict?: "Fake" | "Real" | null;
  confidence?: number;
  state: DecibelState;
  latency_ms?: number;
  scam?: ScamMetadata;
  [key: string]: unknown;
};
