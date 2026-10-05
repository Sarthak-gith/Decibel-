# Decibel ML engine handoff

## P2 import and inference contract

The real model entry point is `from engine.engine import DecibelEngine`. Construct it with no arguments after installing the exported assets at `engine/assets/truevoice/`. `DecibelEngine.predict(audio)` accepts one mono, 16 kHz NumPy `float32` array with finite values in `[-1, 1]` and a duration from 1.5 through 29 seconds. The normal server window is 48,000 samples (3 seconds).

The result contains `p_fake`, `fake_probability` (identical to `p_fake`), `verdict` (`"Fake"` when `p_fake >= 0.5`, otherwise `"Real"`), `confidence` (`max(p_fake, 1 - p_fake)`), and `latency_ms`. The legacy `Engine` name remains an alias for `DecibelEngine`. `FakeEngine` is only a deterministic no-model fallback for the server's explicit `DECIBEL_FAKE=1` development mode; it is not the real engine and must not be used to verify model inference.

## Clean-clone setup

Run from the repository root. The exported ZIP must be provided out of band; model assets are intentionally not in Git.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cu130 "torch==2.11.0+cu130"
python -m pip install "transformers==5.18.0" "accelerate==1.15.0" "safetensors==0.8.0" "huggingface-hub==1.33.0" numpy
python scripts/import_truevoice_assets.py decibel_truevoice_assets.zip
```

On Linux/macOS, activate with `source .venv/bin/activate`; the pip commands and asset-import command are otherwise the same. The four versions in the export manifest are torch `2.11.0+cu130`, Transformers `5.18.0`, safetensors `0.8.0`, and huggingface-hub `1.33.0`. Accelerate `1.15.0` is also required by the engine's `device_map`/low-memory Transformers loading path, although it is not currently recorded in the asset manifest.

The importer validates file sizes and SHA-256 hashes before installing these files at `engine/assets/truevoice/`:

- `manifest.json`
- `audio_tower/config.json`
- `audio_tower/model.safetensors`
- `classifier_head.pt`
- `processor/chat_template.jinja`
- `processor/processor_config.json`
- `processor/tokenizer.json`
- `processor/tokenizer_config.json`

No Hugging Face token or network access to Hugging Face is needed after the exported bundle is installed. `DecibelEngine` loads the local `Gemma4AudioModel` tower with `local_files_only=True`; it does not download or instantiate the full Gemma multimodal parent model.

## Quick real-engine smoke check

With the real assets installed and a CUDA-capable GPU available:

```powershell
python -c "import numpy as np; from engine.engine import DecibelEngine; e=DecibelEngine(); x=np.zeros(48000,dtype=np.float32); print(e.predict(x)); print(e.predict(x))"
```

For the server integration, `server.main` imports `DecibelEngine()` by default and calls `predict(audio)` with the audio array only. `DECIBEL_FAKE=1` selects the separate `FakeEngine` solely for local server development.
