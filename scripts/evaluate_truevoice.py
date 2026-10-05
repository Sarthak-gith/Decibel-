"""Evaluate TrueVoice from a CSV test pack with audio_path,label columns.

The EER operating threshold is derived from the labels and scores in the
provided pack. Do not use a validation pack here if reporting held-out test
metrics.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import librosa
import numpy as np
from sklearn.metrics import roc_curve

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.engine import Engine, SAMPLE_RATE


def summarize_predictions(
    labels: list[int], fake_scores: list[float], latencies_ms: list[float]
) -> dict[str, Any]:
    if not labels or len(labels) != len(fake_scores) or len(labels) != len(latencies_ms):
        raise ValueError("Labels, scores, and latencies must have equal nonzero lengths.")
    if set(labels) != {0, 1}:
        raise ValueError("The test pack must contain both real and fake labels.")
    scores = np.asarray(fake_scores, dtype=np.float64)
    if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
        raise ValueError("Fake scores must be finite probabilities between 0 and 1.")

    fpr, tpr, thresholds = roc_curve(labels, scores, pos_label=1)
    index = int(np.argmin(np.abs(fpr - (1.0 - tpr))))
    eer_threshold = float(thresholds[index])
    eer = float((fpr[index] + (1.0 - tpr[index])) / 2.0)
    predictions = scores >= eer_threshold
    truth = np.asarray(labels, dtype=np.int64)
    true_fake = truth == 1
    true_real = ~true_fake
    pred_fake = predictions
    pred_real = ~predictions
    latency = np.asarray(latencies_ms, dtype=np.float64)

    return {
        "samples": len(labels),
        "real_samples": int(true_real.sum()),
        "fake_samples": int(true_fake.sum()),
        "eer_threshold": eer_threshold,
        "eer": eer,
        "at_eer_threshold": {
            "accuracy": float(np.mean(predictions == true_fake)),
            "real_recall": float(np.mean(pred_real[true_real])),
            "fake_recall": float(np.mean(pred_fake[true_fake])),
            "true_real": int(np.sum(true_real & pred_real)),
            "false_fake": int(np.sum(true_real & pred_fake)),
            "false_real": int(np.sum(true_fake & pred_real)),
            "true_fake": int(np.sum(true_fake & pred_fake)),
        },
        "latency_ms": {
            "median": float(np.median(latency)),
            "p95": float(np.percentile(latency, 95)),
        },
    }


def evaluate_manifest(manifest_path: Path, engine: Engine) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    labels: list[int] = []
    scores: list[float] = []
    latencies: list[float] = []
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"audio_path", "label"}.issubset(reader.fieldnames):
            raise ValueError("CSV must contain audio_path and label columns.")
        for line_number, row in enumerate(reader, start=2):
            label = (row.get("label") or "").strip().lower()
            if label not in {"real", "fake"}:
                raise ValueError(f"Line {line_number}: label must be 'real' or 'fake'.")
            audio_name = (row.get("audio_path") or "").strip()
            if not audio_name:
                raise ValueError(f"Line {line_number}: audio_path is empty.")
            audio_path = Path(audio_name)
            if not audio_path.is_absolute():
                audio_path = manifest_path.parent / audio_path
            if not audio_path.is_file():
                raise FileNotFoundError(f"Line {line_number}: {audio_path}")

            audio, _ = librosa.load(
                audio_path, sr=SAMPLE_RATE, mono=True, dtype=np.float32
            )
            result = engine.predict(audio, sampling_rate=SAMPLE_RATE)
            labels.append(1 if label == "fake" else 0)
            scores.append(float(result["p_fake"]))
            latencies.append(float(result["latency_ms"]))

    summary = summarize_predictions(labels, scores, latencies)
    summary["threshold_source"] = str(manifest_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="CSV with audio_path,label columns")
    parser.add_argument(
        "--assets-dir", type=Path, help="Defaults to engine/assets/truevoice"
    )
    parser.add_argument("--output", type=Path, help="Optional JSON results path")
    args = parser.parse_args()

    engine = Engine(assets_dir=args.assets_dir)
    result = evaluate_manifest(args.manifest, engine)
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
