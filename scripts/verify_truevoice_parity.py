"""Compare Engine.predict with the TrueVoice notebook's reference forward path."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.engine import Engine, SAMPLE_RATE


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audio",
        type=Path,
        help="Optional audio file; decoded as mono 16 kHz. Defaults to a generated 3-second tone.",
    )
    args = parser.parse_args()

    if args.audio:
        audio, _ = librosa.load(
            args.audio, sr=SAMPLE_RATE, mono=True, dtype=np.float32
        )
    else:
        time = np.arange(SAMPLE_RATE * 3, dtype=np.float32) / SAMPLE_RATE
        audio = np.sin(2 * np.pi * 440 * time).astype(np.float32)

    engine = Engine()
    predicted = engine.predict(audio)
    encoded = engine.processor(
        text="<audio>",
        audio=audio,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt",
        audio_kwargs={"max_length": 480000},
    )
    features = encoded["input_features"].to(
        device=engine.device, dtype=torch.float32
    )
    with torch.inference_mode():
        output = engine.audio_tower(input_features=features)
        hidden = (
            output.last_hidden_state
            if hasattr(output, "last_hidden_state")
            else output[0]
        )
        # This is the reference path in notebooks/truevoice_demo.ipynb:
        # temporal mean pooling followed by the saved classifier head.
        logits = engine.classifier(hidden.mean(dim=1))
        reference_p_fake = float(torch.softmax(logits, dim=-1)[0, 1].item())

    difference = abs(predicted["p_fake"] - reference_p_fake)
    result = {
        "reference": "truevoice_demo.ipynb AudioDeepfakeClassifier.forward",
        "p_fake_engine": predicted["p_fake"],
        "p_fake_reference": reference_p_fake,
        "absolute_difference": difference,
        "input_features_shape": list(features.shape),
        "input_features_dtype": str(features.dtype),
        "tower_hidden_shape": list(hidden.shape),
        "tower_hidden_dtype": str(hidden.dtype),
    }
    print(json.dumps(result, indent=2))
    if difference > 1e-6:
        raise SystemExit("Engine and notebook reference outputs do not match.")


if __name__ == "__main__":
    main()
