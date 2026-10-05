"""Export only the TrueVoice Gemma audio tower and bundle P1 inference assets.

Run this in a Linux cloud notebook runtime with a GPU. It downloads the parent
Gemma checkpoint to that runtime's Hugging Face cache, but it instantiates only
Gemma4AudioModel (not the full multimodal language model).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

MODEL_ID = "google/gemma-4-E4B-it"
EXPECTED_HIDDEN_SIZE = 1536
MIN_GPU_GIB = 8
MIN_RAM_GIB = 8
MIN_DISK_GIB = 24


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _memory_gib() -> tuple[float, float]:
    if sys.platform != "linux":
        raise RuntimeError("This export script is intended for a Linux cloud runtime.")
    values: dict[str, int] = {}
    with open("/proc/meminfo", encoding="ascii") as stream:
        for line in stream:
            key, raw = line.split(":", 1)
            if key in {"MemTotal", "MemAvailable"}:
                values[key] = int(raw.split()[0]) * 1024
    return values["MemTotal"] / 2**30, values["MemAvailable"] / 2**30


def _verify_classifier_head(path: Path) -> None:
    import torch

    state = torch.load(path, map_location="cpu", weights_only=True)
    expected = {
        "0.weight": (256, EXPECTED_HIDDEN_SIZE),
        "0.bias": (256,),
        "3.weight": (2, 256),
        "3.bias": (2,),
    }
    if not isinstance(state, dict) or set(state) != set(expected):
        raise ValueError(f"Unexpected classifier checkpoint keys in {path}.")
    for name, shape in expected.items():
        tensor = state[name]
        if tuple(tensor.shape) != shape or tensor.dtype != torch.float32:
            raise ValueError(
                f"Unexpected {name}: shape={tuple(tensor.shape)}, dtype={tensor.dtype}; "
                f"expected shape={shape}, dtype=torch.float32."
            )


def _hash_manifest(root: Path, model_revision: str, versions: dict[str, str]) -> dict:
    files = {
        str(path.relative_to(root)).replace("\\", "/"): {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    return {
        "format_version": 1,
        "model_id": MODEL_ID,
        "model_revision": model_revision,
        "audio_tower_class": "Gemma4AudioModel",
        "audio_tower_output_size": EXPECTED_HIDDEN_SIZE,
        "input_sampling_rate": 16000,
        "input_features": "processor output input_features, float32",
        "classifier_classes": {"0": "real", "1": "fake"},
        "classifier_head": "classifier_head.pt",
        "versions": versions,
        "files": files,
    }


def export_assets(classifier_path: Path, output_path: Path) -> None:
    import numpy as np
    import torch
    import transformers
    from transformers import AutoConfig, AutoProcessor, Gemma4AudioModel

    if not torch.cuda.is_available():
        raise RuntimeError("No CUDA GPU detected. Select a GPU-backed Colab runtime first.")
    gpu_gib = torch.cuda.get_device_properties(0).total_memory / 2**30
    total_ram_gib, available_ram_gib = _memory_gib()
    free_disk_gib = shutil.disk_usage(Path.cwd()).free / 2**30
    print(
        f"Runtime: {torch.cuda.get_device_name(0)}, GPU={gpu_gib:.1f} GiB, "
        f"RAM={total_ram_gib:.1f} GiB ({available_ram_gib:.1f} GiB available), "
        f"free disk={free_disk_gib:.1f} GiB"
    )
    if gpu_gib < MIN_GPU_GIB:
        raise RuntimeError(f"Need at least {MIN_GPU_GIB} GiB GPU RAM for a safe export run.")
    if total_ram_gib < MIN_RAM_GIB or available_ram_gib < MIN_RAM_GIB:
        raise RuntimeError(f"Need at least {MIN_RAM_GIB} GiB system RAM available.")
    if free_disk_gib < MIN_DISK_GIB:
        raise RuntimeError(
            f"Need at least {MIN_DISK_GIB} GiB free runtime disk for the 16 GB parent "
            "checkpoint cache, exported tower, and bundle. No model download was started."
        )

    classifier_path = classifier_path.resolve()
    output_path = output_path.resolve()
    if not classifier_path.is_file():
        raise FileNotFoundError(f"Classifier head not found: {classifier_path}")
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing bundle: {output_path}")
    _verify_classifier_head(classifier_path)

    config = AutoConfig.from_pretrained(MODEL_ID)
    model_revision = getattr(config, "_commit_hash", None)
    if not model_revision:
        raise RuntimeError("Hugging Face did not return a pinned model revision.")
    if getattr(config, "audio_config", None) is None:
        raise RuntimeError("The selected Gemma config has no audio tower.")

    processor = AutoProcessor.from_pretrained(MODEL_ID, revision=model_revision)

    # Gemma4AudioModel.base_model_prefix is "model.audio_tower". Its
    # from_pretrained loader uses that prefix to select only tower tensors from
    # the monolithic parent checkpoint; the full LM/vision modules are not built.
    audio_tower = Gemma4AudioModel.from_pretrained(
        MODEL_ID,
        config=config.audio_config,
        revision=model_revision,
        dtype=torch.float32,
        low_cpu_mem_usage=True,
        device_map={"": "cuda:0"},
        use_safetensors=True,
    )
    audio_tower.eval()
    hidden_size = int(audio_tower.output_proj.out_features)
    if hidden_size != EXPECTED_HIDDEN_SIZE:
        raise RuntimeError(
            f"Checkpoint audio output is {hidden_size}, but classifier expects "
            f"{EXPECTED_HIDDEN_SIZE}; refusing to create an incompatible bundle."
        )

    probe = np.zeros(16000 * 3, dtype=np.float32)
    encoded = processor(
        text="<audio>", audio=probe, sampling_rate=16000, return_tensors="pt"
    )
    features = encoded["input_features"].to(device="cuda:0", dtype=torch.float32)
    if features.ndim != 3 or features.shape[0] != 1 or features.shape[-1] != 128:
        raise RuntimeError(f"Unexpected processor feature shape: {tuple(features.shape)}")
    with torch.inference_mode():
        output = audio_tower(input_features=features)
    hidden = output.last_hidden_state if hasattr(output, "last_hidden_state") else output[0]
    if hidden.ndim != 3 or hidden.shape[-1] != hidden_size:
        raise RuntimeError(f"Unexpected audio tower output shape: {tuple(hidden.shape)}")
    if not torch.isfinite(hidden).all():
        raise RuntimeError("Audio tower produced non-finite values on the smoke input.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="decibel-truevoice-") as temp_name:
        root = Path(temp_name) / "decibel_truevoice_assets"
        tower_dir = root / "audio_tower"
        processor_dir = root / "processor"
        tower_dir.mkdir(parents=True)
        processor_dir.mkdir(parents=True)
        audio_tower.to("cpu").save_pretrained(tower_dir, safe_serialization=True)
        processor.save_pretrained(processor_dir)
        shutil.copy2(classifier_path, root / "classifier_head.pt")

        versions = {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "safetensors": importlib.metadata.version("safetensors"),
            "huggingface_hub": importlib.metadata.version("huggingface-hub"),
        }
        manifest = _hash_manifest(root, model_revision, versions)
        (root / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_STORED) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root.parent))

    print(f"Export smoke inference passed; output shape={tuple(hidden.shape)}")
    print(f"Model revision: {model_revision}")
    print(f"Bundle: {output_path} ({output_path.stat().st_size / 2**30:.2f} GiB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classifier-head", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("decibel_truevoice_assets.zip")
    )
    args = parser.parse_args()
    export_assets(args.classifier_head, args.output)


if __name__ == "__main__":
    main()
