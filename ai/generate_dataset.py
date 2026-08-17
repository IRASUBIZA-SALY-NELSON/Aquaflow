"""Generate synthetic dual-sensor time-series for LSTM training."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from backend.config import DATA_DIR, LABELS, SEQ_LEN


RNG = np.random.default_rng(42)


def _segment(kind: str, n: int) -> np.ndarray:
    """Return (n, 2) array: [flow_a, flow_b]."""
    t = np.arange(n)
    if kind == "IDLE":
        a = RNG.normal(0.0, 0.02, n).clip(0)
        b = RNG.normal(0.0, 0.02, n).clip(0)
    elif kind == "NORMAL_USE":
        # intermittent household use with pauses
        base = RNG.uniform(1.5, 4.0)
        pulse = ((np.sin(t / 8.0) > -0.2) & ((t % 17) > 3)).astype(float)
        a = (base * pulse) + RNG.normal(0, 0.08, n)
        b = a * RNG.uniform(0.85, 1.0) + RNG.normal(0, 0.05, n)
        a = a.clip(0)
        b = b.clip(0)
    elif kind == "MID_PIPE_LEAK":
        a = RNG.uniform(0.3, 1.2) + RNG.normal(0, 0.05, n)
        b = RNG.normal(0.0, 0.03, n).clip(0)  # almost nothing at tap
        a = a.clip(0.2)
    elif kind == "BURST":
        a = RNG.uniform(8.0, 14.0) + RNG.normal(0, 0.4, n)
        b = a * RNG.uniform(0.4, 0.9)
        a = a.clip(7.5)
        b = b.clip(0)
    elif kind == "CONTINUOUS_FLOW":
        a = RNG.uniform(1.2, 3.0) + RNG.normal(0, 0.05, n)
        b = a * RNG.uniform(0.9, 1.05) + RNG.normal(0, 0.04, n)
        a = a.clip(0.8)
        b = b.clip(0.8)
    else:
        raise ValueError(kind)
    return np.column_stack([a, b]).astype(np.float32)


def build_dataset(samples_per_class: int = 400, seq_len: int = SEQ_LEN):
    X, y = [], []
    for label_idx, label in enumerate(LABELS):
        for _ in range(samples_per_class):
            # build a slightly longer stream then take a window
            stream = _segment(label, seq_len + RNG.integers(0, 10))
            start = 0 if len(stream) == seq_len else int(RNG.integers(0, len(stream) - seq_len + 1))
            window = stream[start : start + seq_len]
            X.append(window)
            y.append(label_idx)
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int64)
    return X, y


def main():
    X, y = build_dataset()
    out_x = DATA_DIR / "lstm_X.npy"
    out_y = DATA_DIR / "lstm_y.npy"
    np.save(out_x, X)
    np.save(out_y, y)
    meta = {
        "labels": LABELS,
        "seq_len": int(X.shape[1]),
        "features": int(X.shape[2]),
        "samples": int(X.shape[0]),
        "class_counts": {LABELS[i]: int((y == i).sum()) for i in range(len(LABELS))},
    }
    (DATA_DIR / "dataset_meta.json").write_text(json.dumps(meta, indent=2))
    # also a CSV preview of flattened last samples for inspection
    rows = []
    for i in range(min(50, len(X))):
        rows.append(
            {
                "label": LABELS[y[i]],
                "mean_a": float(X[i, :, 0].mean()),
                "mean_b": float(X[i, :, 1].mean()),
                "max_a": float(X[i, :, 0].max()),
                "max_b": float(X[i, :, 1].max()),
            }
        )
    pd.DataFrame(rows).to_csv(DATA_DIR / "dataset_preview.csv", index=False)
    print(f"Saved {out_x} {X.shape}")
    print(f"Saved {out_y} {y.shape}")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
