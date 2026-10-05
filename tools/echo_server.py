import asyncio
import json
import time
import numpy as np
import websockets

frame_count = 0
last_rms = 0.0
latest_state = "LISTENING"

async def ticker(websocket):
    global last_rms, latest_state
    states = ["LISTENING", "ANALYZING", "SECURE"]
    state_idx = 0
    
    while True:
        await asyncio.sleep(1.0)
        now_ms = int(time.time() * 1000)
        voiced = last_rms > 0.015

        if voiced:
            state_idx = (state_idx + 1) % len(states)
            latest_state = states[state_idx]
            p_fake = float(round(min(0.85, max(0.05, last_rms * 4.0)), 2))
            verdict = "Fake" if p_fake >= 0.5 else "Real"
            conf = float(round(max(p_fake, 1.0 - p_fake), 2))
        else:
            p_fake = 0.0
            verdict = None
            conf = 0.0

        payload = {
            "type": "verdict",
            "ts": now_ms,
            "timestamp_ms": now_ms,
            "window_ms": 3000,
            "voiced": voiced,
            "p_fake": p_fake,
            "fake_probability": p_fake,
            "smoothed": p_fake,
            "verdict": verdict,
            "confidence": conf,
            "state": latest_state,
            "latency_ms": 12
        }
        try:
            await websocket.send(json.dumps(payload))
        except Exception:
            break

async def handler(websocket):
    global frame_count, last_rms, latest_state
    # Check path if available
    path = getattr(websocket, "path", getattr(websocket.request, "path", "/stream"))
    if path != "/stream":
        print(f"[WARN] Connection rejected on path {path} (expected /stream)")
        await websocket.close()
        return

    print(f"\n[+] Client connected on {path}")
    frame_count = 0
    latest_state = "LISTENING"
    connect_msg = {
        "type": "status",
        "state": "LISTENING",
        "ts": int(time.time() * 1000)
    }
    await websocket.send(json.dumps(connect_msg))

    tick_task = asyncio.create_task(ticker(websocket))

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                byte_len = len(message)
                if byte_len != 16000:
                    print(f"[WARN] Expected 16000 bytes, received {byte_len} bytes")
                
                samples = np.frombuffer(message, dtype="<i2").astype(np.float32) / 32768.0
                frame_count += 1
                last_rms = float(np.sqrt(np.mean(samples**2)))
                peak = float(np.max(np.abs(samples))) if len(samples) > 0 else 0.0

                print(f"\r[Frame #{frame_count:04d}] samples={len(samples)} | rms={last_rms:.4f} | peak={peak:.4f}", end="", flush=True)
            else:
                print(f"\n[Text message received]: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("\n[-] Client disconnected.")
    finally:
        tick_task.cancel()

async def main():
    print("==================================================")
    print("   Decibel Echo Server listening on ws://localhost:8000/stream")
    print("==================================================")
    async with websockets.serve(handler, "localhost", 8000):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")
