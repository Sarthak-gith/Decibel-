"""Run from project root:  uvicorn server.main:app --port 8000
Dev without the model:    DECIBEL_FAKE=1 uvicorn server.main:app --port 8000   (Windows: set DECIBEL_FAKE=1)
"""
import asyncio, json, os, time
from contextlib import asynccontextmanager
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from server.buffer import RollingBuffer
from server.state import StateMachine
from server import scam

SR = 16000
WINDOW_SEC = float(os.getenv("WINDOW_SEC", "3"))
HOP_SEC = float(os.getenv("HOP_SEC", "1"))
MIN_SEC = 1.5
VAD_RMS = float(os.getenv("VAD_RMS", "0.01"))
ENGINE = None

@asynccontextmanager
async def lifespan(app):
    global ENGINE
    if os.getenv("DECIBEL_FAKE") == "1":
        from engine.engine import FakeEngine
        ENGINE = FakeEngine()
    else:
        from engine.engine import DecibelEngine
        ENGINE = DecibelEngine()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"engine": type(ENGINE).__name__}

def is_voiced(audio, frame=480, min_frac=0.3):
    n = len(audio) // frame
    if n == 0:
        return False
    rms = np.sqrt((audio[: n * frame].reshape(n, frame) ** 2).mean(axis=1))
    return float((rms > VAD_RMS).mean()) >= min_frac

@app.websocket("/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    buf = RollingBuffer(int(WINDOW_SEC * SR))
    sm = StateMachine()
    scam_state = {"last": None}
    os.makedirs("logs", exist_ok=True)
    log = open(os.path.join("logs", "session.jsonl"), "a")
    await ws.send_json({"type": "status", "state": "LISTENING", "ts": int(time.time() * 1000)})

    async def ticker():
        while True:                       # sequential loop: a slow inference just delays the next tick, no backlog
            await asyncio.sleep(HOP_SEC)
            if buf.seconds < MIN_SEC:
                continue
            snap = buf.snapshot()
            voiced = is_voiced(snap)
            p, lat = 0.0, 0
            if voiced:
                res = await asyncio.to_thread(ENGINE.predict, snap)
                p, lat = res["p_fake"], res["latency_ms"]
            smoothed, state = sm.update(p, voiced)
            p_fake = round(p, 4) if voiced else 0
            timestamp_ms = int(time.time() * 1000)
            payload = {"type": "verdict", "ts": timestamp_ms, "timestamp_ms": timestamp_ms,
                       "window_ms": WINDOW_SEC * 1000, "voiced": voiced, "p_fake": p_fake,
                       "fake_probability": p_fake,
                       "verdict": ("Fake" if p_fake >= 0.5 else "Real") if voiced else None,
                       "confidence": max(p_fake, 1 - p_fake) if voiced else 0,
                       "smoothed": round(smoothed, 4), "state": state, "latency_ms": lat}
            if scam_state["last"]:
                payload["scam"] = scam_state["last"]
            log.write(json.dumps(payload) + "\n"); log.flush()
            await ws.send_json(payload)

    task = asyncio.create_task(ticker())
    try:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            if msg.get("bytes"):
                buf.append(np.frombuffer(msg["bytes"], dtype="<i2").astype(np.float32) / 32768.0)
            elif msg.get("text"):
                data = json.loads(msg["text"])
                if data.get("type") == "transcript" and data.get("text"):
                    res = await asyncio.to_thread(scam.classify, data["text"])
                    if res:
                        scam_state["last"] = res
    except WebSocketDisconnect:
        pass
    finally:
        task.cancel()
        log.close()
