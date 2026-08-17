#!/usr/bin/env python3
"""Manual scenario injector for live demos (no hardware required).

Examples:
  python scripts/simulate_prototype.py --scenario leak
  python scripts/simulate_prototype.py --scenario normal --seconds 20
  python scripts/simulate_prototype.py --scenario continuous
  python scripts/simulate_prototype.py --scenario burst
"""
from __future__ import annotations

import argparse
import random
import time

import requests

API = "http://127.0.0.1:9090/api/ingest"


def send(a: float, b: float, total_a: float, total_b: float, api_url: str = API, device="manual-demo"):
    payload = {
        "device_id": device,
        "flow_a_lpm": round(a, 3),
        "flow_b_lpm": round(b, 3),
        "flow_a_lps": round(a / 60.0, 4),
        "flow_b_lps": round(b / 60.0, 4),
        "total_a_l": round(total_a, 3),
        "total_b_l": round(total_b, 3),
    }
    r = requests.post(api_url, json=payload, timeout=3)
    print(r.status_code, r.json())


def run(scenario: str, seconds: int, api_url: str = API):
    total_a = total_b = 0.0
    for i in range(seconds):
        if scenario == "idle":
            a, b = 0.0, 0.0
        elif scenario == "normal":
            a = random.uniform(1.8, 3.8)
            b = a * random.uniform(0.9, 1.0)
        elif scenario == "leak":
            a = random.uniform(0.35, 0.9)
            b = random.uniform(0.0, 0.04)
        elif scenario == "continuous":
            a = random.uniform(1.6, 2.4)
            b = a * random.uniform(0.95, 1.02)
        elif scenario == "burst":
            a = random.uniform(9.0, 13.0)
            b = random.uniform(7.0, 11.0)
        else:
            raise SystemExit(f"Unknown scenario: {scenario}")

        total_a += a / 60.0
        total_b += b / 60.0
        print(f"t={i+1}s A={a:.2f} B={b:.2f}")
        try:
            send(a, b, total_a, total_b, api_url=api_url)
        except Exception as exc:
            print("POST failed:", exc)
        time.sleep(1)


def main():
    p = argparse.ArgumentParser(description="AquaFlow prototype scenario injector")
    p.add_argument(
        "--scenario",
        choices=["idle", "normal", "leak", "continuous", "burst"],
        default="leak",
    )
    p.add_argument("--seconds", type=int, default=15)
    p.add_argument("--url", default=API)
    args = p.parse_args()
    run(args.scenario, args.seconds, args.url)


if __name__ == "__main__":
    main()
