# DECIBEL — Presenter and operator runbook

## Verification and honest claims

The browser dashboard and deterministic mock checkpoint have been tested. Live audio is wired to P4's `startStream()` API, but microphone-to-server-to-model inference has **not** been verified from this P3 environment. The local Python runtime lacks the backend/model dependencies, and the exported real-model asset bundle is absent. Do not call the mock or a fake-engine session a real-model demo.

Voice authenticity risk and scam intent are two separate signals. A screening result is not proof of identity or a guarantee of fraud prevention. This is a browser prototype, not phone-network integration or a production-ready service.

P1's engineering smoke measurement is documented in [results.md](results.md). There is no labelled DECIBEL test-pack accuracy result. Mock latency values are synthetic. Never cite the original TrueVoice metrics as DECIBEL measurements.

## Operator setup

1. From `web/`, run `npm ci`, `npm run build`, then `npm run start`. Open `http://localhost:3000` in Chrome.
2. Use fullscreen at 100% zoom with a 1280×720 viewport. Keep a backup browser tab ready. For projector verification use production mode, which has no Next.js development overlay.
3. Select **Mock demo**, click **Reset session**, then **Start**. Check that the status, gauge, timeline, telemetry and transition list update. Stop and reset before the presentation.
4. For real live testing, first arrange P1's exported assets and engine dependencies using [engine/README.md](../engine/README.md), plus P2's FastAPI/Uvicorn setup. Start the backend from the repository root:

   ```powershell
   # Real model: remove a development-only fake-engine override if set.
   Remove-Item Env:DECIBEL_FAKE -ErrorAction SilentlyContinue
   python -m uvicorn server.main:app --port 8000
   ```

   Verify `http://localhost:8000/health` identifies the intended engine. For a development-only smoke test, use the commands below and clearly label the result as fake-engine output:

   ```powershell
   $env:DECIBEL_FAKE = "1"
   python -m uvicorn server.main:app --port 8000
   ```

5. Select **Live audio** and choose **Phone mode** or **Speakerphone**; both use this computer's microphone. **Tab audio** uses tab capture; select the correct tab and enable “Share tab audio”. The source selector locks while running; Stop before changing sources.
6. Live mode may start Chrome speech recognition. Explain before capture: **audio may be processed by Google**. Use consenting participants and recordings only. No actual OTP, account number, payment details or credentials in the script.
7. Clicking **Start** requests permission through P4's layer. Keep **Stop** visible. Connection failures show Disconnected while retaining history. If permission or audio capture fails, Stop, review permissions and retry; never silently substitute mock output.

## Scenario 1 — A teammate's real voice (about 45 seconds)

**Presenter:** “DECIBEL screens a rolling audio window and reports a voice-authenticity signal. This is a screening aid; it does not establish who the caller is.”

**Operator:** Reset session, select Live audio → Speakerphone, then Start. Allow microphone access. A consenting teammate speaks normally: “This is our live demonstration. I am speaking into the laptop microphone.”

**Expected visual story, subject to real rehearsal:** Listening while capture begins; analyzing or changing scores as server messages arrive; potentially Secure for the validated real-voice clip. The backend's current state machine may not emit every intermediate state, so do not promise an Analyzing transition in live mode.

**Presenter:** Point out the smoothed risk score, current verdict/confidence, inference latency and newest telemetry messages. “The gauge uses the smoothed signal. The raw probability remains visible in the feed. Silence retains the score and shows ‘No speech detected’.”

**If the result differs:** “That is the model's observed output for this window. We do not force the expected result. Our labelled test pack is still pending.” Stop after the demonstration.

## Scenario 2 — A consenting cloned voice (about 45 seconds)

Use only a clip whose speaker explicitly consented to the clone and demo. Record that consent outside this public repository. Do not clone public figures or non-consenting people.

**Presenter:** “This second sample was generated with the speaker's consent. We are testing whether the screen can surface a possible synthetic voice.”

**Operator:** Stop, reset and select the rehearsed capture source. For a browser playback clip use Tab audio and enable tab sharing. Start, then play the consented sample.

**Expected visual story, not guaranteed:** Risk rises through Caution and may reach Threat detected. Point to timestamps and raw probabilities to show actual arriving messages. The red banner reads: “Possible AI-cloned voice detected. Do not share OTP or money.”

**Presenter:** “A high signal calls for independent verification, not an accusation. We recommend ending the exchange and contacting the person through a trusted channel.” If the model misses the clip, report that observation honestly and switch to the clearly labelled UI mock fallback.

## Scenario 3 — Scam-intent stretch (about 40 seconds)

Only demonstrate live scam intent if P2's scam layer and speech transcription have been verified. Otherwise describe it as a stretch integration and show its mock UI with the simulation label visible.

A consenting participant or consented clone reads: “For this demonstration only: I need the code urgently. Please tell me your one-time password.” No real code is used.

**Operator:** Start the rehearsed live source. Watch for optional scam metadata; do not promise that it arrives on every window. Point to **Signal 01 / Voice** and **Signal 02 / Intent** separately.

**Presenter:** “Voice authenticity and suspicious intent are independent concepts. These chips summarize the reported tactics, such as urgency and an OTP request. We have not measured scam-classifier accuracy.” The intent panel displays the latest reported assessment; it is not a fresh assessment on every tick. Do not fabricate a safe result when the layer is unavailable.

## Fallbacks

### Guaranteed UI fallback — Mock demo

Stop, select Mock demo, Reset session, then Start. Say: “The live model is unavailable, so this is deterministic simulated telemetry demonstrating the interface. It is not evidence of detector performance.”

At roughly one tick per second: Listening ×3 → Analyzing ×2 → Secure ×10 → Caution ×4 → Threat detected ×10 → Secure ×1, then repeat. Caution rises through 40%, 48%, 57%, 65%; threat spans 75–95%. Two Secure ticks contain silence. Scam metadata arrives only on the last five threat ticks of the first cycle. Later cycles retain the latest assessment until reset, just as the store retains absent optional fields. Mock latency is generated between 80 and 300 ms, **not measured inference**.

### Recorded replay

The frontend includes Recorded replay for P2's existing `tools/replay.py`. The actual Python replay server and a recorded session must be available. This environment has not run that server end to end.

```powershell
python tools/replay.py path\to\approved-session.jsonl
```

Stop, reset, select Recorded replay, then Start. Say: “This is a previously recorded session, not current inference.” Playback uses recorded timestamps and ends in Disconnected while retaining the session. No audio waveform is available because the replay contains telemetry, not live audio. Do not present a generated fixture as a real-model recording.

### Backup video / slow inference / permissions

- **Backup video:** HUMAN ACTION REQUIRED — record a successful, clearly labelled rehearsal; store it outside Git and verify playback before presenting. No backup video has been produced by P3 automation.
- **Slow inference:** “The screen is waiting for the next model result. The displayed latency is inference time from the payload, not total call-to-alert delay.” Retain the observed state; do not invent a latency figure. Switch to labelled mock if the delay prevents the demo.
- **Permission failure:** Stop, check Chrome microphone/site permissions and the chosen input, then retry once. If unavailable, select Mock demo and announce the change. Do not claim live audio connected.
- **Incident export:** Export incident summary downloads JSON containing retained contract telemetry and state transitions. Only the latest 60 smoothed samples and 50 payloads are retained; events span the session. It is not an audio recording or a complete forensic log. The selected mode at export may differ from earlier retained messages; the export warns about this.

## Rehearsal checklist — HUMAN ACTION REQUIRED

- [ ] Run from cold start using the final production build.
- [ ] Run a second time without restarting the machine.
- [ ] Verify live microphone permission, input selection and Stop cleanup.
- [ ] Verify the mock fallback with no backend running.
- [ ] Verify Caution, Threat detected, unvoiced messaging and separate scam indicators.
- [ ] Verify Reset clears scores, history, feed, events and intent data.
- [ ] Verify 1280×720, Chrome 100% zoom, fullscreen and projector readability.
- [ ] Verify keyboard controls and reduced-motion preference.
- [ ] Verify recorded replay with an approved actual session, if used.
- [ ] Verify incident-summary download in Chrome and check its mode/retention notice.
- [ ] Verify actual live end-to-end results and record consenting clip count/context.
- [ ] Rehearse presenter/operator timing and fallback narration.
- [ ] Verify backup video exists and can play offline.
- [ ] Confirm credits and the upstream licence/attribution with the repository maintainer.

These boxes are intentionally unchecked: automated UI checks do not establish that the human team rehearsed.

## UI screenshots

[SECURE mock view](assets/decibel-secure-mock.jpg) and [THREAT mock view](assets/decibel-threat-mock.jpg) are interface screenshots with simulated data, not detector evaluation results.
