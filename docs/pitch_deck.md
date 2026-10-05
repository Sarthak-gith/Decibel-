# DECIBEL — Pitch content (8 slides)

Presenter target: approximately four minutes, plus questions. Keep claims tied to the demonstrated mode. This document is P3-owned pitch material, not a performance certificate.

## Slide 1 — When a familiar voice stops being enough

**On screen:** A cloned voice can make an urgent OTP or payment request sound familiar. Identity should be checked through a trusted independent channel.

**Speaker note:** “We focus on the moment a caller asks for something sensitive. The aim is to surface a screening signal while a person still has time to pause.” No unverified fraud statistics or prevention claims.

## Slide 2 — DECIBEL: a browser monitoring console

**On screen:** Realtime voice-authenticity screening, visible risk history, timestamped telemetry, and a separate scam-intent signal when available.

**Speaker note:** “The primary gauge shows smoothed voice risk; the feed exposes raw probabilities. The second panel reports intent separately. This is a local prototype, not an identity guarantee.” Show [the mock SECURE view](assets/decibel-secure-mock.jpg), labelled as simulation.

## Slide 3 — From audio to a visible decision

**On screen:** Browser microphone / shared tab → AudioWorklet → 16 kHz mono Int16 little-endian PCM → WebSocket → rolling 3-second buffer → local engine → smoothing/state machine → dashboard.

**Architecture detail:** About 500 ms of audio per frame (8,000 samples / 16,000 bytes); server endpoint `ws://localhost:8000/stream`. States: Disconnected, Listening, Analyzing, Secure, Caution, Threat detected.

**Speaker note:** “The frontend consumes the frozen team contract. P4 owns capture and the waveform; P2 owns buffering and state logic; P1 owns the engine. Chrome speech recognition, when enabled by the audio layer, may process audio through Google.” The diagram describes the implementation; P3 has not verified a real-model end-to-end run locally.

## Slide 4 — Three demo stories, with honest fallbacks

**On screen:**

1. A teammate speaking normally: observed authenticity signal.
2. A cloned sample made with consent: observe whether risk rises.
3. A scripted scam-style request: inspect intent separately, if the layer is available.

**Speaker note:** Follow [demo_script.md](demo_script.md). Do not guarantee a clip's classification. If using Mock demo, explicitly say that scores and latency are simulated. Recorded replay requires an approved recorded session and P2's server. Show [the THREAT mock view](assets/decibel-threat-mock.jpg) only as a UI example.

## Slide 5 — What DECIBEL adds to TrueVoice

**On screen:**

| Original TrueVoice foundation | DECIBEL team additions |
| --- | --- |
| Frozen Gemma audio features and binary classifier | AudioWorklet capture and WebSocket streaming |
| Notebook/browser-accessible demonstration | Monitoring dashboard, smoothed gauge and timeline |
| Voice real/fake inference | Optional scam-intent metadata as a separate signal |
| Original evaluation work | Mock checkpoint, replay adapter, session transitions and incident export |

**Speaker note:** Credit the original model work. These are implementation additions, not evidence that DECIBEL has improved detector accuracy or prevents fraud. Original TrueVoice metrics belong to the original work.

## Slide 6 — Results: engineering smoke test, evaluation pending

**On screen:** **Insert verified P1 test-pack results** — labelled clip count, real/fake split, codec conditions, machine context, accuracy/EER and measured latency. No labelled DECIBEL evaluation is currently available.

**Optional supporting engineering measurement, clearly labelled:** P1 reports **one generated 3-second 16 kHz mono sine-wave input**, with **7 timing runs after one warm-up**, on Windows / NVIDIA RTX 3050 (4 GiB), float32. Engine `predict()` median **42.52 ms**, range **37.54–44.61 ms**. This is not a speech-classification evaluation or end-to-end latency measurement.

**Source:** [P1 results.md](results.md), brought into `develop` by merge `40c9a00`; asset revision `ee0ef6023621cff504d758262d4e04895a5af4a2`. P3 did not independently rerun these measurements. Reference-path parity was reported on the same synthetic signal; it does not establish accuracy on real or cloned speech.

**Speaker note:** “We have an engineering smoke result and a working mock UI checkpoint. We still need a consented labelled test pack and measured end-to-end testing.” Do not quote synthetic mock latency as measured latency. Do not relabel the original README's TrueVoice accuracy/EER as a DECIBEL result.

## Slide 7 — Limits and next steps

**On screen:**

- Original training focused on older ASVspoof spoofing data; newer cloning methods need evaluation.
- English-centric demo/transcription limitations; no multilingual claim.
- Codec simulation is an approximation of real calling conditions.
- False positives and missed synthetic voices are possible; a low signal is not proof of authenticity.
- Browser microphone/tab capture is the present scope. Phone-network integration is future work.
- Complete consented clip evaluation, live rehearsal, measured latency and privacy review before broader use.

**Speaker note:** The dashboard avoids conflating voice risk with intent. Optional scam metadata may be unavailable or retained from a previous message; the UI labels it as the latest reported signal. No claim of production readiness or broad fraud prevention.

## Slide 8 — Credits and team ownership

**On screen:** TrueVoice by **Shiwon Oh**; retain the upstream **MIT licence** attribution (the root README states MIT). **Gemma 4** model work where applicable, with its separate upstream terms. Credit ASVspoof datasets and the original authors.

**Team:** P1 — ML engine; P2 — backend and protocol; P3 — frontend and pitch; P4 — audio capture and waveform.

**Speaker note:** Attribution must remain visible. `docs/ATTRIBUTION.md` is currently absent; the repository maintainer should verify the original source link, author and exact licence/notice files and add the canonical attribution document. P3 has not changed upstream licence or model files. Do not describe third-party model/dataset assets as covered solely by the project's source licence.

## Final presentation checks

HUMAN ACTION REQUIRED: replace the labelled-results placeholder only after P1 supplies a measured evaluation with clip count and context; rehearse the demo; verify live consent, permissions, backup video and projected readability; confirm canonical attribution with the maintainer.
