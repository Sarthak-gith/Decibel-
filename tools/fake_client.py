"""Stream a WAV to the server like the browser would.  python tools/fake_client.py clip.wav"""
import asyncio, json, sys
import librosa, numpy as np, websockets

async def main(path, url="ws://localhost:8000/stream"):
    a, _ = librosa.load(path, sr=16000, mono=True)
    pcm = (np.clip(a, -1, 1) * 32767).astype("<i2")
    async with websockets.connect(url) as ws:
        async def rx():
            async for m in ws:
                d = json.loads(m)
                print(d.get("state"), d.get("p_fake"), d.get("smoothed"), d.get("latency_ms"))
        t = asyncio.create_task(rx())
        for i in range(0, len(pcm), 8000):               # 500 ms chunks, real time
            await ws.send(pcm[i:i + 8000].tobytes())
            await asyncio.sleep(0.5)
        await asyncio.sleep(2)
        t.cancel()

asyncio.run(main(sys.argv[1]))
