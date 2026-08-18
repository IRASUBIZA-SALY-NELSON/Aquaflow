#!/usr/bin/env python3
"""Live monitoring dashboard for AquaFlow system."""
import requests
import time
import sys
from datetime import datetime

BACKEND_URL = "http://127.0.0.1:9090"

def get_status_color(status):
    colors = {
        "IDLE": "\033[90m",  # Gray
        "NORMAL_USE": "\033[92m",  # Green
        "MID_PIPE_LEAK": "\033[91m",  # Red
        "SUSPECT_LEAK": "\033[93m",  # Yellow
        "CONTINUOUS_FLOW": "\033[94m",  # Blue
        "BURST": "\033[91m\033[1m",  # Bold Red
    }
    return colors.get(status, "\033[0m")

def main():
    print("=" * 70)
    print("   AquaFlow Live Monitoring Dashboard")
    print("=" * 70)
    print(f"Backend: {BACKEND_URL}")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            try:
                resp = requests.get(f"{BACKEND_URL}/api/data", timeout=2)
                if resp.status_code == 200:
                    data = resp.json()

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    status = data.get("status", "UNKNOWN")
                    color = get_status_color(status)
                    reset = "\033[0m"

                    print(f"\n[{timestamp}] {color}{status:20}{reset}", end="")
                    print(f" | Device: {data.get('device_id', 'N/A'):20} | Source: {data.get('source', 'N/A')}")
                    print(f"  Flow A: {data.get('flow_a_lpm', 0):6.2f} L/min", end="")
                    print(f" | Flow B: {data.get('flow_b_lpm', 0):6.2f} L/min", end="")
                    print(f" | Total: {data.get('total_b_l', 0):7.3f} L")
                    print(f"  Leak: {str(data.get('leak_mid', False)):5}", end="")
                    print(f" | Solenoid: {str(data.get('solenoid_open', False)):5}", end="")
                    print(f" | Pump: {str(data.get('pump_on', False)):5}", end="")
                    print(f" | Buzzer: {str(data.get('buzzer_on', False)):5}")

                    if data.get('lstm_status'):
                        conf = data.get('lstm_confidence', 0) * 100
                        print(f"  AI: {data.get('lstm_status'):20} (confidence: {conf:.1f}%)")

                    reason = data.get('reason', '')
                    if reason and reason != 'boot':
                        print(f"  Reason: {reason}")

                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Backend error: HTTP {resp.status_code}")

            except requests.RequestException as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection error: {e}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
