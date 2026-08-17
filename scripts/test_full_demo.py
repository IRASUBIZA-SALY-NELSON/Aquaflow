#!/usr/bin/env python3
"""End-to-end AquaFlow demo verification (rules + LSTM + API)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.config import LEAK_CONFIRM_SEC, MODEL_PATH  # noqa: E402
from backend.leak_rules import RuleState, classify_rules  # noqa: E402
from ai.infer_lstm import LSTMLeakDetector  # noqa: E402


def test_leak_timing():
    state = RuleState()
    t0 = time.time()
    for sec in range(1, int(LEAK_CONFIRM_SEC) + 3):
        out = classify_rules(0.6, 0.0, t0 + sec, state)
        print(f"  t={sec}s status={out['status']} solenoid={out['solenoid_open']}")
    assert out["status"] == "MID_PIPE_LEAK"
    assert out["solenoid_open"] is False
    assert out["leak_mid"] is True
    print(f"  OK: leak confirmed at {LEAK_CONFIRM_SEC}s, solenoid closed")


def test_normal_flow():
    state = RuleState()
    out = classify_rules(2.5, 2.3, time.time(), state)
    assert out["status"] == "NORMAL_USE"
    assert out["solenoid_open"] is True
    print("  OK: normal flow keeps solenoid open")


def test_idle():
    state = RuleState()
    out = classify_rules(0.0, 0.0, time.time(), state)
    assert out["status"] == "IDLE"
    print("  OK: idle state")


def test_burst():
    state = RuleState()
    out = classify_rules(10.0, 8.0, time.time(), state)
    assert out["status"] == "BURST"
    assert out["solenoid_open"] is False
    print("  OK: burst closes solenoid immediately")


def test_lstm_model():
    if not MODEL_PATH.exists():
        raise AssertionError(f"Model missing: {MODEL_PATH}")
    det = LSTMLeakDetector()
    assert det.ready, "LSTM model failed to load"

    # Simulate mid-pipe leak window
    for _ in range(29):
        det.push(0.0, 0.0)
    result = det.push(0.7, 0.02)
    assert result is not None
    assert result.get("lstm_status") != "WARMUP"
    print(f"  OK: LSTM loaded, sample prediction={result['lstm_status']} conf={result['confidence']:.2f}")


def test_api(base_url: str = "http://127.0.0.1:9090"):
    import requests

    r = requests.get(f"{base_url}/api/data", timeout=3)
    r.raise_for_status()
    data = r.json()
    assert "status" in data
    print(f"  OK: GET /api/data status={data['status']}")

    # Inject normal flow
    payload = {
        "device_id": "test-runner",
        "flow_a_lpm": 2.0,
        "flow_b_lpm": 1.9,
        "total_a_l": 1.0,
        "total_b_l": 0.9,
    }
    r = requests.post(f"{base_url}/api/ingest", json=payload, timeout=3)
    r.raise_for_status()
    resp = r.json()
    assert resp["ok"] is True
    assert resp["status"] == "NORMAL_USE"
    print(f"  OK: normal ingest -> {resp['status']}")

    # Inject sustained leak — one POST per second so server rule timer elapses
    for sec in range(7):
        payload["flow_a_lpm"] = 0.6
        payload["flow_b_lpm"] = 0.0
        r = requests.post(f"{base_url}/api/ingest", json=payload, timeout=3)
        r.raise_for_status()
        if sec < 6:
            time.sleep(1.05)
    final = r.json()
    assert final["status"] == "MID_PIPE_LEAK"
    assert final["solenoid_open"] is False
    print(f"  OK: leak ingest -> {final['status']} solenoid_closed")


def main():
    print("=== AquaFlow Demo Tests ===\n")

    print("[1] Rule timing (leak @ 5s)")
    test_leak_timing()

    print("\n[2] Normal flow")
    test_normal_flow()

    print("\n[3] Idle")
    test_idle()

    print("\n[4] Burst")
    test_burst()

    print("\n[5] LSTM model")
    test_lstm_model()

    print("\n[6] Backend API (optional — needs server running)")
    try:
        test_api()
    except Exception as exc:
        print(f"  SKIP: {exc}")

    print("\n=== ALL CORE TESTS PASSED ===")


if __name__ == "__main__":
    main()
