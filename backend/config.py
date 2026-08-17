"""AquaFlow shared configuration."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "ai" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Ingest / serial
SERIAL_PORT = os.getenv("AQUAFLOW_SERIAL", "/dev/ttyACM0")
BAUD_RATE = int(os.getenv("AQUAFLOW_BAUD", "115200"))  # ESP32=115200, Uno dual=9600
# Modes: simulate | wifi | serial
MODE = os.getenv("AQUAFLOW_MODE", "simulate").strip().lower()
SIMULATE = os.getenv("AQUAFLOW_SIMULATE", "1" if MODE == "simulate" else "0") == "1"
if MODE == "simulate":
    SIMULATE = True
elif MODE in {"wifi", "serial"}:
    SIMULATE = False

# Rule thresholds (L/min)
FLOW_ON_LPM = float(os.getenv("AQUAFLOW_FLOW_ON", "0.15"))
LEAK_CONFIRM_SEC = float(os.getenv("AQUAFLOW_LEAK_SEC", "5"))
CONTINUOUS_SEC = float(os.getenv("AQUAFLOW_CONTINUOUS_SEC", "45"))
BURST_LPM = float(os.getenv("AQUAFLOW_BURST_LPM", "8.0"))

# Cost estimate
RWF_PER_LITER = 0.35

# LSTM
SEQ_LEN = 30          # seconds of history
FEATURES = 2          # flow_a, flow_b
LABELS = ["IDLE", "NORMAL_USE", "MID_PIPE_LEAK", "BURST", "CONTINUOUS_FLOW"]
MODEL_PATH = MODEL_DIR / "lstm_leak_classifier.keras"
LABEL_PATH = MODEL_DIR / "label_map.json"

HOST = "0.0.0.0"
PORT = int(os.getenv("AQUAFLOW_PORT", "9090"))
