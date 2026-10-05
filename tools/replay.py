"""Replay a JSONL backend session over WebSocket on ws://localhost:8001/stream."""
import argparse
import asyncio
import json
import math
import sys
from pathlib import Path

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed


HOST = "localhost"
PORT = 8001
PATH = "/stream"


def load_records(log_path):
    path = Path(log_path)
    if not path.is_file():
        raise FileNotFoundError(f"Log file does not exist: {path}")

    records = []
    with path.open(encoding="utf-8") as log:
        for line_number, line in enumerate(log, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line, parse_constant=_reject_nonstandard_number)
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}: {exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"Expected a JSON object on line {line_number} of {path}.")
            timestamp = payload.get("ts")
            if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp):
                raise ValueError(f"Missing or invalid numeric 'ts' on line {line_number} of {path}.")
            records.append((line.strip(), timestamp))

    if not records:
        raise ValueError(f"Log file is empty: {path}")
    return records


def _reject_nonstandard_number(value):
    raise ValueError(f"Invalid JSON number {value}")


async def replay_client(websocket, records):
    request = getattr(websocket, "request", None)
    request_path = getattr(request, "path", None)
    if request_path != PATH:
        await websocket.close(code=1008, reason=f"Connect to {PATH}")
        return

    previous_ts = None
    try:
        for raw_payload, timestamp in records:
            if previous_ts is not None:
                delay = max(0.0, (timestamp - previous_ts) / 1000.0)
                await asyncio.sleep(delay)
            await websocket.send(raw_payload)
            previous_ts = timestamp
    except ConnectionClosed:
        # A client may leave before the full session has been replayed.
        return


async def run_server(records):
    async with serve(lambda websocket: replay_client(websocket, records), HOST, PORT):
        print(f"Replaying on ws://{HOST}:{PORT}{PATH}; press Ctrl+C to stop.")
        await asyncio.Future()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="JSONL session log to replay")
    args = parser.parse_args()

    try:
        records = load_records(args.log_file)
        asyncio.run(run_server(records))
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except KeyboardInterrupt:
        print("Replay server stopped.")


if __name__ == "__main__":
    main()
