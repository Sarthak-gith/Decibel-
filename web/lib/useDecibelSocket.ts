"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { startStream } from "./audioStream";
import { startMock } from "./mock";
import { useDecibelStore } from "./store";
import type { DecibelPayload, DecibelState } from "./types";

export type DecibelMode = "mock" | "live";
export type AudioSource = "mic" | "tab";
export type StreamHandle = {
  stop: () => void;
  analyser?: AnalyserNode;
  ws?: WebSocket;
};

const states: readonly DecibelState[] = [
  "DISCONNECTED", "LISTENING", "ANALYZING", "SECURE", "CAUTION", "THREAT_DETECTED",
];

// P4 callbacks are untyped. Accept partial contract objects; ignore malformed data.
function contractMessage(message: unknown): Partial<DecibelPayload> | null {
  if (!message || typeof message !== "object" || Array.isArray(message)) return null;
  const payload = { ...message } as Partial<DecibelPayload>;
  if (payload.state !== undefined && !states.includes(payload.state)) delete payload.state;
  for (const key of ["ts", "timestamp_ms", "window_ms", "p_fake", "fake_probability", "smoothed", "confidence", "latency_ms"] as const) {
    if (payload[key] !== undefined && (typeof payload[key] !== "number" || !Number.isFinite(payload[key]))) delete payload[key];
  }
  if (payload.voiced !== undefined && typeof payload.voiced !== "boolean") delete payload.voiced;
  if (payload.verdict !== undefined && payload.verdict !== null && payload.verdict !== "Real" && payload.verdict !== "Fake") delete payload.verdict;
  if (payload.scam !== undefined) {
    const scam = payload.scam;
    if (!scam || typeof scam !== "object" || typeof scam.risk !== "string") delete payload.scam;
    else payload.scam = {
      risk: scam.risk,
      tactics: Array.isArray(scam.tactics) ? scam.tactics.filter((tactic) => typeof tactic === "string") : undefined,
      reason: typeof scam.reason === "string" ? scam.reason : undefined,
    };
  }
  return payload;
}

export function useDecibelSocket() {
  const [mode, updateMode] = useState<DecibelMode>("mock");
  const [handle, setHandle] = useState<StreamHandle | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const active = useRef<StreamHandle | null>(null);
  const generation = useRef(0);

  const stop = useCallback(() => {
    generation.current += 1;
    const previous = active.current;
    active.current = null;
    previous?.stop();
    setHandle(null);
    setStarting(false);
    useDecibelStore.getState().ingest({ type: "status", state: "DISCONNECTED", ts: Date.now() });
  }, []);

  const setMode = useCallback((next: DecibelMode) => {
    if (next === mode) return;
    stop();
    setError(null);
    updateMode(next);
  }, [mode, stop]);

  const start = useCallback(async (source: AudioSource = "mic") => {
    stop();
    setError(null);
    setStarting(true);
    const token = generation.current;
    const onMessage = (message: unknown) => {
      if (token !== generation.current) return;
      const payload = contractMessage(message);
      if (!payload) return;
      if (payload.type === "error") {
        setError(typeof payload.message === "string" ? payload.message : "Inference failed. Stop and retry.");
        stop();
        return;
      }
      useDecibelStore.getState().ingest(payload);
      if (payload.state === "DISCONNECTED") setError("Connection lost. Waiting for the audio layer to reconnect.");
      else if (payload.state) setError(null);
    };
    try {
      const next: StreamHandle = mode === "mock"
        ? startMock(onMessage)
        : await startStream("ws://localhost:8000/stream", onMessage, source);
      if (token !== generation.current) {
        next.stop();
        return;
      }
      active.current = next;
      setHandle(next);
      setStarting(false);
    } catch (failure) {
      if (token !== generation.current) return;
      stop();
      setError(failure instanceof Error ? failure.message : "Connection failed. Check microphone permission and the local server.");
    }
  }, [mode, stop]);

  useEffect(() => () => {
    generation.current += 1;
    active.current?.stop();
    active.current = null;
    useDecibelStore.getState().ingest({ type: "status", state: "DISCONNECTED", ts: Date.now() });
  }, []);

  return { mode, setMode, start, stop, handle, starting, error };
}
