import os
import sys
from pathlib import Path

os.environ["DECIBEL_FAKE"] = "1"
os.environ["HOP_SEC"] = "0.2"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from fastapi.testclient import TestClient

from server.main import app


CONTRACT_KEYS = {
    "type",
    "ts",
    "timestamp_ms",
    "window_ms",
    "voiced",
    "p_fake",
    "fake_probability",
    "smoothed",
    "verdict",
    "confidence",
    "state",
    "latency_ms",
}


def loud_frame():
    samples = np.arange(8000, dtype=np.float32)
    signal = 0.3 * np.sin(2 * np.pi * 220 * samples / 16000)
    return (signal * 32767).astype("<i2").tobytes()


def receive_verdict(ws):
    while True:
        message = ws.receive_json()
        if message.get("type") == "verdict":
            return message


def test_connect_starts_with_listening_status():
    with TestClient(app) as client:
        with client.websocket_connect("/stream") as ws:
            message = ws.receive_json()

    assert message["type"] == "status"
    assert message["state"] == "LISTENING"


def test_loud_pcm_produces_contract_verdict():
    with TestClient(app) as client:
        with client.websocket_connect("/stream") as ws:
            status = ws.receive_json()
            assert status["type"] == "status"

            frame = loud_frame()
            for _ in range(6):
                ws.send_bytes(frame)

            message = receive_verdict(ws)

    assert CONTRACT_KEYS <= message.keys()
    assert message["type"] == "verdict"
    assert message["voiced"] is True
    assert 0 <= message["p_fake"] <= 1
    assert message["fake_probability"] == message["p_fake"]
    assert message["timestamp_ms"] == message["ts"]
    assert message["window_ms"] == 3000
    assert message["verdict"] == ("Fake" if message["p_fake"] >= 0.5 else "Real")
    assert message["confidence"] == max(message["p_fake"], 1 - message["p_fake"])


def test_silence_has_null_verdict_and_preserves_state():
    with TestClient(app) as client:
        with client.websocket_connect("/stream") as ws:
            ws.receive_json()
            frame = loud_frame()
            for _ in range(6):
                ws.send_bytes(frame)
            previous = receive_verdict(ws)
            assert previous["voiced"] is True

            silent = None
            for _ in range(10):
                ws.send_bytes(bytes(16000))
                message = receive_verdict(ws)
                if message["voiced"]:
                    previous = message
                else:
                    silent = message
                    break

    assert silent is not None
    assert silent["verdict"] is None
    assert silent["confidence"] == 0
    assert silent["p_fake"] == 0
    assert silent["fake_probability"] == 0
    assert silent["smoothed"] == previous["smoothed"]
    assert silent["state"] == previous["state"]


def test_odd_frame_and_malformed_json_do_not_close_connection():
    with TestClient(app) as client:
        with client.websocket_connect("/stream") as ws:
            status = ws.receive_json()
            assert status["type"] == "status"

            ws.send_text("{not valid json")
            ws.send_bytes(b"\x01")
            for _ in range(6):
                ws.send_bytes(loud_frame())

            message = receive_verdict(ws)

    assert message["type"] == "verdict"
    assert message["voiced"] is True
