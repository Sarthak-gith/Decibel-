## A3. The FROZEN CONTRACT (v1). Nobody changes this alone.

The team's planning docs used two slightly different message shapes. We keep the starter's fields and **also** send the planning doc's fields, so both work. This is the "superset".

**Audio, browser to server (binary WebSocket frames):** signed 16-bit little-endian PCM (Int16), 16000 Hz, mono, about 500 ms per frame = 8000 samples = 16000 bytes. No echo cancellation, no noise suppression, no auto gain in the browser. Server decodes with `np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768.0`.

**Engine:** `engine.predict(audio)` where `audio` is a float32 numpy array, 1-D, 16 kHz mono, values in [-1, 1], length 1.5 s to 29 s (normal case: 48000 samples = 3 s). It returns:

```json
{ "p_fake": 0.83, "fake_probability": 0.83, "verdict": "Fake", "confidence": 0.83, "latency_ms": 240 }
```

`verdict` is "Fake" if p_fake >= 0.5 else "Real". `confidence` is max(p_fake, 1 - p_fake). `fake_probability` is an alias of `p_fake`.

**WebSocket server to browser (text JSON), one per tick:**

```json
{
  "type": "verdict",
  "ts": 1730000000000,
  "timestamp_ms": 1730000000000,
  "window_ms": 3000,
  "voiced": true,
  "p_fake": 0.83,
  "fake_probability": 0.83,
  "smoothed": 0.71,
  "verdict": "Fake",
  "confidence": 0.83,
  "state": "THREAT_DETECTED",
  "latency_ms": 240,
  "scam": { "risk": "high", "tactics": ["urgency", "payment_request"], "reason": "max 20 words" }
}
```

- `scam` is optional. When `voiced` is false: `verdict` is null, `confidence` is 0, `p_fake` is 0, and `smoothed` / `state` keep their previous values.
- On connect the server also sends a status message: `{"type":"status","state":"LISTENING","ts":...}`. The browser sends `{"type":"status","state":"DISCONNECTED"}`-style events to its own UI when the socket drops (this is generated client side, never sent over the wire).
- **Consumers must accept messages with or without `type`, and ignore unknown fields.**

**States (exactly six):** `DISCONNECTED`, `LISTENING`, `ANALYZING`, `SECURE`, `CAUTION`, `THREAT_DETECTED`.

**Browser text message (optional, scam layer):** `{"type":"transcript","text":"...","final":true}`.

**Endpoints:** `ws://localhost:8000/stream`, `http://localhost:8000/health`. Everything runs on one laptop, so no HTTPS is needed (localhost counts as a secure context for the microphone). A second device such as a phone needs HTTPS and is out of scope.

**Frontend/audio hand-off interface (P3 and P4 agree on this exact API):**
- P4 exports from `web/lib/audioStream.ts`: `startStream(url, onMessage, source): Promise<{ stop(), analyser, ws }>` with `source` of `"mic"` or `"tab"`.
- P4 exports `web/components/audio/WaveformCanvas.tsx` with props `{ analyser: AnalyserNode | null; threat: boolean }`.
- P3 owns the single hook `web/lib/useDecibelSocket.ts` that calls `startStream` in live mode and a mock generator in mock mode. `onMessage` receives parsed contract JSON.
