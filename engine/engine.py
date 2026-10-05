"""Local inference engine for the exported P1 TrueVoice assets."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn


HIDDEN_SIZE = 1536
FEATURE_SIZE = 128
SAMPLE_RATE = 16000
MIN_AUDIO_SAMPLES = int(1.5 * SAMPLE_RATE)
MAX_AUDIO_SAMPLES = 29 * SAMPLE_RATE


class DecibelEngine:
    """Run Gemma4's exported audio tower and the frozen binary head locally."""

    def __init__(
        self,
        assets_dir: str | Path | None = None,
        device: str | torch.device | None = None,
    ) -> None:
        from transformers import AutoProcessor, Gemma4AudioModel

        self.assets_dir = Path(assets_dir) if assets_dir else Path(__file__).parent / "assets" / "truevoice"
        self.device = torch.device(
            device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        )
        if self.device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available.")

        manifest_path = self.assets_dir / "manifest.json"
        processor_dir = self.assets_dir / "processor"
        tower_dir = self.assets_dir / "audio_tower"
        head_path = self.assets_dir / "classifier_head.pt"
        required = (manifest_path, processor_dir, tower_dir / "config.json", head_path)
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError(f"TrueVoice assets missing: {missing}")

        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.processor = AutoProcessor.from_pretrained(
            processor_dir, local_files_only=True
        )
        self.audio_tower = Gemma4AudioModel.from_pretrained(
            tower_dir,
            local_files_only=True,
            dtype=torch.float32,
            low_cpu_mem_usage=True,
            device_map={"": str(self.device)} if self.device.type == "cuda" else None,
        )
        self.audio_tower.eval()

        output_size = int(self.audio_tower.output_proj.out_features)
        if output_size != HIDDEN_SIZE:
            raise ValueError(
                f"Audio tower output size {output_size} does not match {HIDDEN_SIZE}."
            )

        self.classifier = nn.Sequential(
            nn.Linear(HIDDEN_SIZE, 256),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(256, 2),
        )
        state = torch.load(head_path, map_location="cpu", weights_only=True)
        self.classifier.load_state_dict(state, strict=True)
        self.classifier.to(device=self.device, dtype=torch.float32).eval()

    def predict(
        self, audio: np.ndarray, sampling_rate: int = SAMPLE_RATE
    ) -> dict[str, Any]:
        """Predict from mono 16 kHz float32 audio and return the frozen contract."""
        if sampling_rate != SAMPLE_RATE:
            raise ValueError(f"Audio must be sampled at {SAMPLE_RATE} Hz.")
        if not isinstance(audio, np.ndarray):
            raise TypeError("Audio must be a numpy.ndarray with dtype float32.")
        if audio.dtype != np.float32:
            raise TypeError(f"Audio dtype must be float32, got {audio.dtype}.")
        if audio.ndim != 1:
            raise ValueError(f"Audio must be mono and one-dimensional, got {audio.shape}.")
        if audio.size < MIN_AUDIO_SAMPLES:
            raise ValueError("Audio duration must be at least 1.5 seconds.")
        if audio.size > MAX_AUDIO_SAMPLES:
            raise ValueError("Audio duration must not exceed 29 seconds.")
        if not np.isfinite(audio).all():
            raise ValueError("Audio contains NaN or infinite samples.")
        if np.any(audio < -1.0) or np.any(audio > 1.0):
            raise ValueError("Audio samples must be within [-1, 1].")

        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        started = time.perf_counter()
        encoded = self.processor(
            text="<audio>",
            audio=audio,
            sampling_rate=SAMPLE_RATE,
            return_tensors="pt",
            audio_kwargs={"max_length": MAX_AUDIO_SAMPLES},
        )
        features = encoded["input_features"]
        if features.ndim != 3 or features.shape[0] != 1 or features.shape[-1] != FEATURE_SIZE:
            raise RuntimeError(f"Unexpected processor feature shape: {tuple(features.shape)}")
        features = features.to(device=self.device, dtype=torch.float32)

        with torch.inference_mode():
            output = self.audio_tower(input_features=features)
            hidden = (
                output.last_hidden_state
                if hasattr(output, "last_hidden_state")
                else output[0]
            )
            if hidden.ndim != 3 or hidden.shape[0] != 1 or hidden.shape[-1] != HIDDEN_SIZE:
                raise RuntimeError(f"Unexpected audio tower output shape: {tuple(hidden.shape)}")
            if hidden.dtype != torch.float32 or not torch.isfinite(hidden).all():
                raise RuntimeError("Audio tower output must be finite float32.")
            logits = self.classifier(hidden.mean(dim=1))
            probabilities = torch.softmax(logits, dim=-1)[0]
            p_fake = float(probabilities[1].item())
            predicted_fake = p_fake >= 0.5
            confidence = max(p_fake, 1.0 - p_fake)

        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        latency_ms = (time.perf_counter() - started) * 1000.0
        return {
            "p_fake": p_fake,
            "fake_probability": p_fake,
            "verdict": "Fake" if predicted_fake else "Real",
            "confidence": confidence,
            "latency_ms": latency_ms,
        }


class FakeEngine:
    """Deterministic no-model fallback for P2's explicit DECIBEL_FAKE mode."""

    def predict(
        self, audio: np.ndarray, sampling_rate: int = SAMPLE_RATE
    ) -> dict[str, Any]:
        if sampling_rate != SAMPLE_RATE:
            raise ValueError(f"Audio must be sampled at {SAMPLE_RATE} Hz.")
        if (
            not isinstance(audio, np.ndarray)
            or audio.dtype != np.float32
            or audio.ndim != 1
        ):
            raise TypeError("Audio must be a one-dimensional float32 NumPy array.")
        p_fake = 0.0
        return {
            "p_fake": p_fake,
            "fake_probability": p_fake,
            "verdict": "Fake" if p_fake >= 0.5 else "Real",
            "confidence": max(p_fake, 1.0 - p_fake),
            "latency_ms": 0.0,
        }


# Keep the P1 script import path working while exposing the class name P2 imports.
Engine = DecibelEngine
