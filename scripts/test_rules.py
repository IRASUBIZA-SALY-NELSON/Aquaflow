"""Quick sanity checks for rule-based leak logic."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.leak_rules import RuleState, classify_rules


def test_mid_pipe_leak_confirms_after_window():
    state = RuleState()
    t0 = time.time()
    first = classify_rules(0.6, 0.0, t0, state)
    assert first["status"] == "SUSPECT_LEAK"
    confirmed = classify_rules(0.6, 0.0, t0 + 6, state)
    assert confirmed["status"] == "MID_PIPE_LEAK"
    assert confirmed["solenoid_open"] is False


def test_normal_use():
    state = RuleState()
    out = classify_rules(2.0, 1.9, time.time(), state)
    assert out["status"] == "NORMAL_USE"
    assert out["solenoid_open"] is True


def test_idle():
    state = RuleState()
    out = classify_rules(0.0, 0.0, time.time(), state)
    assert out["status"] == "IDLE"


if __name__ == "__main__":
    test_idle()
    test_normal_use()
    test_mid_pipe_leak_confirms_after_window()
    print("rule tests OK")
