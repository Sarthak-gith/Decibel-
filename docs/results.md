# P1 ML engine results

## Local inference smoke test

- Asset revision: `ee0ef6023621cff504d758262d4e04895a5af4a2`
- Runtime: Windows, NVIDIA GeForce RTX 3050 (4 GiB), float32
- Input: generated 3-second, 16 kHz mono float32 sine wave
- Processor output: `(1, 299, 128)`, float32
- Audio tower output: batch 1, hidden size 1536, finite float32
- `predict()` latency after one warm-up: median **42.52 ms**, range **37.54–44.61 ms** over 7 runs
- Result contract fields and probability bounds: passed

This is an engineering smoke measurement, not an accuracy evaluation. No labeled Decibel test pack is present in the checked-out repository, so no accuracy metrics or decision threshold are reported or selected.

## Labeled test-pack workflow

Prepare a CSV with `audio_path,label` columns. Labels must be `real` or `fake`; paths may be absolute or relative to the CSV. Audio is decoded, converted to mono, and resampled to 16 kHz before inference. Run:

```powershell
python scripts/evaluate_truevoice.py path\to\test_pack.csv --output test_pack_results.json
```

The evaluator reports the EER operating threshold derived from the supplied labels and scores, metrics at that threshold, and measured inference latency. No test-pack CSV or audio is currently available in this checkout, so the workflow has not produced Decibel accuracy results or a selected threshold.
