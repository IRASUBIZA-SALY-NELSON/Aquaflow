"""AquaFlow backend: ingest WiFi/Serial dual-sensor data + rules + LSTM."""
from __future__ import annotations

import json
import sys
import threading
import time
from collections import deque
from pathlib import Path

from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.infer_lstm import LSTMLeakDetector  # noqa: E402
from backend.config import (  # noqa: E402
    BAUD_RATE,
    HOST,
    MODE,
    PORT,
    ROOT as PROJECT_ROOT,
    RWF_PER_LITER,
    SERIAL_PORT,
    SIMULATE,
)
from backend.leak_rules import RuleState, classify_rules  # noqa: E402

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static") if (PROJECT_ROOT / "static").exists() else None,
)

_lock = threading.Lock()
_rule_state = RuleState()
_lstm = LSTMLeakDetector()
_history = deque(maxlen=120)

latest = {
    "device_id": "sim",
    "ts": None,
    "flow_a_lpm": 0.0,
    "flow_b_lpm": 0.0,
    "flow_a_lps": 0.0,
    "flow_b_lps": 0.0,
    "total_a_l": 0.0,
    "total_b_l": 0.0,
    "status": "IDLE",
    "leak_mid": False,
    "continuous_flow": False,
    "solenoid_open": True,
    "pump_on": False,
    "buzzer_on": False,
    "reason": "boot",
    "lstm_status": None,
    "lstm_confidence": 0.0,
    "lstm_probs": {},
    "estimated_cost": 0.0,
    "source": "none",
}


def _apply_reading(payload: dict, source: str) -> dict:
    now = time.time()
    flow_a = float(payload.get("flow_a_lpm", 0.0))
    flow_b = float(payload.get("flow_b_lpm", 0.0))

    rules = classify_rules(flow_a, flow_b, now, _rule_state)
    lstm = _lstm.push(flow_a, flow_b) or {}

    # Safety priority: hardware/rules close solenoid on mid-leak or burst
    solenoid_open = rules["solenoid_open"]
    status = rules["status"]
    buzzer_on = status in {"MID_PIPE_LEAK", "BURST", "SUSPECT_LEAK", "CONTINUOUS_FLOW"}
    pump_on = status == "NORMAL_USE" and solenoid_open

    # If LSTM is confident about MID_PIPE_LEAK / BURST, reinforce
    lstm_status = lstm.get("lstm_status")
    conf = float(lstm.get("confidence") or 0.0)
    if lstm_status in {"MID_PIPE_LEAK", "BURST"} and conf >= 0.65:
        status = lstm_status
        if lstm_status == "MID_PIPE_LEAK":
            rules["leak_mid"] = True
        solenoid_open = False
        rules["reason"] = f"{rules['reason']} | LSTM confirms ({conf:.2f})"

    total_a = float(payload.get("total_a_l", latest["total_a_l"]))
    total_b = float(payload.get("total_b_l", latest["total_b_l"]))

    with _lock:
        latest.update(
            {
                "device_id": payload.get("device_id", latest["device_id"]),
                "ts": payload.get("ts", now),
                "flow_a_lpm": round(flow_a, 3),
                "flow_b_lpm": round(flow_b, 3),
                "flow_a_lps": round(float(payload.get("flow_a_lps", flow_a / 60.0)), 4),
                "flow_b_lps": round(float(payload.get("flow_b_lps", flow_b / 60.0)), 4),
                "total_a_l": round(total_a, 3),
                "total_b_l": round(total_b, 3),
                "status": status,
                "leak_mid": bool(rules["leak_mid"]),
                "continuous_flow": bool(rules["continuous_flow"]),
                "solenoid_open": bool(solenoid_open),
                "pump_on": bool(payload.get("pump_on", pump_on)),
                "buzzer_on": bool(payload.get("buzzer_on", buzzer_on)),
                "reason": rules["reason"],
                "lstm_status": lstm_status,
                "lstm_confidence": round(conf, 3),
                "lstm_probs": lstm.get("probs") or {},
                "estimated_cost": round(total_b * RWF_PER_LITER, 2),
                "source": source,
            }
        )
        _history.append(
            {
                "t": now,
                "a": latest["flow_a_lpm"],
                "b": latest["flow_b_lpm"],
                "status": status,
            }
        )
        return dict(latest)


def _parse_serial_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None
    # legacy: Flow: 1.23 L/min | ...
    if "Flow:" in line:
        try:
            parts = (
                line.replace("|", "")
                .replace("L/min", "")
                .replace("L/sec", "")
                .replace("Total:", "")
                .replace("L", "")
                .split()
            )
            flow = float(parts[1])
            total = float(parts[3])
            return {
                "device_id": "legacy-serial",
                "flow_a_lpm": flow,
                "flow_b_lpm": 0.0,
                "total_a_l": total,
                "total_b_l": 0.0,
            }
        except Exception:
            return None
    return None


def serial_worker():
    if SIMULATE:
        return
    try:
        import serial
    except ImportError:
        print("pyserial missing")
        return

    ser = None
    while True:
        try:
            if ser is None:
                ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                print(f"Serial connected {SERIAL_PORT} @ {BAUD_RATE}")
            raw = ser.readline().decode(errors="ignore")
            payload = _parse_serial_line(raw)
            if payload:
                _apply_reading(payload, source="serial")
        except Exception as exc:
            print(f"Serial error: {exc}")
            ser = None
            time.sleep(2)


def simulator_worker():
    """Cycles through IDLE -> NORMAL -> MID_LEAK -> CONTINUOUS for live demos without hardware."""
    import random

    scenarios = [
        ("IDLE", 8, lambda: (0.0, 0.0)),
        ("NORMAL_USE", 12, lambda: (random.uniform(1.8, 3.5), random.uniform(1.6, 3.4))),
        ("MID_PIPE_LEAK", 14, lambda: (random.uniform(0.4, 1.0), random.uniform(0.0, 0.05))),
        ("CONTINUOUS_FLOW", 20, lambda: (random.uniform(1.5, 2.5), random.uniform(1.5, 2.5))),
        ("BURST", 6, lambda: (random.uniform(9.0, 12.0), random.uniform(6.0, 10.0))),
    ]
    total_a = 0.0
    total_b = 0.0
    idx = 0
    while True:
        name, seconds, gen = scenarios[idx % len(scenarios)]
        print(f"[SIM] scenario={name} for {seconds}s")
        end = time.time() + seconds
        while time.time() < end:
            a, b = gen()
            total_a += a / 60.0
            total_b += b / 60.0
            _apply_reading(
                {
                    "device_id": "simulator",
                    "flow_a_lpm": a,
                    "flow_b_lpm": b,
                    "flow_a_lps": a / 60.0,
                    "flow_b_lps": b / 60.0,
                    "total_a_l": total_a,
                    "total_b_l": total_b,
                },
                source="simulate",
            )
            time.sleep(1)
        idx += 1


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    with _lock:
        return jsonify(latest)


@app.route("/api/history")
def api_history():
    with _lock:
        return jsonify(list(_history))


@app.route("/api/ingest", methods=["POST"])
def api_ingest():
    """ESP32 WiFi endpoint."""
    payload = request.get_json(force=True, silent=True) or {}
    result = _apply_reading(payload, source="wifi")
    # Command solenoid state back to ESP32
    return jsonify({"ok": True, "solenoid_open": result["solenoid_open"], "status": result["status"]})


@app.route("/api/command", methods=["POST"])
def api_command():
    body = request.get_json(force=True, silent=True) or {}
    with _lock:
        if "solenoid_open" in body:
            latest["solenoid_open"] = bool(body["solenoid_open"])
        return jsonify(latest)


def main():
    # Keep root app.py importable too
    if SIMULATE or MODE == "simulate":
        target = simulator_worker
        mode_label = "SIMULATE"
    elif MODE == "wifi":
        target = None
        mode_label = "WIFI ingest /api/ingest"
    else:
        target = serial_worker
        mode_label = f"SERIAL {SERIAL_PORT}"

    if target is not None:
        threading.Thread(target=target, daemon=True).start()
    print(f"AquaFlow backend on http://{HOST}:{PORT}  mode={mode_label}")
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
