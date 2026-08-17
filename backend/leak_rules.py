"""Rule-based prototype leak logic (instant, demo-safe)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.config import (
    BURST_LPM,
    CONTINUOUS_SEC,
    FLOW_ON_LPM,
    LEAK_CONFIRM_SEC,
)


@dataclass
class RuleState:
    mid_leak_start: Optional[float] = None
    continuous_start: Optional[float] = None
    last_status: str = "IDLE"


def classify_rules(
    flow_a: float,
    flow_b: float,
    now: float,
    state: RuleState,
) -> dict:
    """
    Returns status dict matching the physical demo:
      A LOW  + B LOW  -> IDLE
      A HIGH + B HIGH -> NORMAL_USE / CONTINUOUS_FLOW
      A HIGH + B LOW  -> SUSPECT_LEAK -> MID_PIPE_LEAK
      very high A or B -> BURST
    """
    a_on = flow_a >= FLOW_ON_LPM
    b_on = flow_b >= FLOW_ON_LPM

    if flow_a >= BURST_LPM or flow_b >= BURST_LPM:
        state.mid_leak_start = None
        state.continuous_start = None
        state.last_status = "BURST"
        return {
            "status": "BURST",
            "leak_mid": False,
            "continuous_flow": False,
            "solenoid_open": False,
            "reason": "Sudden high-magnitude spike",
        }

    if not a_on and not b_on:
        state.mid_leak_start = None
        state.continuous_start = None
        state.last_status = "IDLE"
        return {
            "status": "IDLE",
            "leak_mid": False,
            "continuous_flow": False,
            "solenoid_open": True,
            "reason": "No source flow",
        }

    if a_on and b_on:
        state.mid_leak_start = None
        if state.continuous_start is None:
            state.continuous_start = now
        held = now - state.continuous_start
        if held >= CONTINUOUS_SEC:
            state.last_status = "CONTINUOUS_FLOW"
            return {
                "status": "CONTINUOUS_FLOW",
                "leak_mid": False,
                "continuous_flow": True,
                "solenoid_open": True,
                "reason": f"Tap flow continuous for {int(held)}s",
            }
        state.last_status = "NORMAL_USE"
        return {
            "status": "NORMAL_USE",
            "leak_mid": False,
            "continuous_flow": False,
            "solenoid_open": True,
            "reason": "Source and tap both flowing",
        }

    if a_on and not b_on:
        state.continuous_start = None
        if state.mid_leak_start is None:
            state.mid_leak_start = now
        held = now - state.mid_leak_start
        if held >= LEAK_CONFIRM_SEC:
            state.last_status = "MID_PIPE_LEAK"
            return {
                "status": "MID_PIPE_LEAK",
                "leak_mid": True,
                "continuous_flow": False,
                "solenoid_open": False,
                "reason": f"Source flowing, tap dry for {int(held)}s (mid-pipe leak)",
            }
        state.last_status = "SUSPECT_LEAK"
        return {
            "status": "SUSPECT_LEAK",
            "leak_mid": False,
            "continuous_flow": False,
            "solenoid_open": True,
            "reason": f"Confirming mid-pipe leak ({int(held)}s/{int(LEAK_CONFIRM_SEC)}s)",
        }

    state.mid_leak_start = None
    state.last_status = "SENSOR_MISMATCH"
    return {
        "status": "SENSOR_MISMATCH",
        "leak_mid": False,
        "continuous_flow": False,
        "solenoid_open": True,
        "reason": "Tap flow without source flow",
    }
