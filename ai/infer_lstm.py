"""Live LSTM inference helper over a rolling window of [flow_a, flow_b]."""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Deque, Optional

import numpy as np

from backend.config import LABEL_PATH, LABELS, MODEL_PATH, SEQ_LEN


class LSTMLeakDetector:
    def __init__(self, seq_len: int = SEQ_LEN):
        self.seq_len = seq_len
        self.buffer: Deque[list[float]] = deque(maxlen=seq_len)
        self.model = None
        self.labels = LABELS
        self.ready = False
        self._try_load()

    def _try_load(self) -> None:
        if not MODEL_PATH.exists():
            print(f"[LSTM] No model at {MODEL_PATH} — rules-only mode")
            return
        try:
            import tensorflow as tf  # noqa: F401
            from tensorflow import keras

            self.model = keras.models.load_model(MODEL_PATH)
            if LABEL_PATH.exists():
                self.labels = json.loads(LABEL_PATH.read_text())["labels"]
            self.ready = True
            print(f"[LSTM] Loaded {MODEL_PATH}")
        except Exception as exc:
            print(f"[LSTM] Load failed ({exc}) — rules-only mode")
            self.model = None
            self.ready = False

    def push(self, flow_a: float, flow_b: float) -> Optional[dict]:
        self.buffer.append([float(flow_a), float(flow_b)])
        if not self.ready or self.model is None:
            return None
        if len(self.buffer) < self.seq_len:
            return {
                "lstm_status": "WARMUP",
                "confidence": 0.0,
                "probs": {},
                "window": len(self.buffer),
            }

        window = np.asarray(self.buffer, dtype=np.float32)[None, :, :]
        probs = self.model.predict(window, verbose=0)[0]
        idx = int(probs.argmax())
        return {
            "lstm_status": self.labels[idx],
            "confidence": float(probs[idx]),
            "probs": {self.labels[i]: float(probs[i]) for i in range(len(self.labels))},
            "window": self.seq_len,
        }
