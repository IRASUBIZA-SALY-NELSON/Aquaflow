import serial
import threading
import time
import random
from flask import Flask, jsonify, render_template

# ---------------- CONFIG ----------------
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
LEAK_FLOW_THRESHOLD = 0.2    # L/min
LEAK_TIME_THRESHOLD = 30     # seconds
SIMULATE = True              # Set to True to work without Arduino
# ----------------------------------------

app = Flask(__name__)

latest_data = {
    "flow_l_min": 0.0,
    "flow_l_sec": 0.0,
    "total_l": 0.0,
    "water_status": "IDLE",
    "leak": False,
    "leak_duration": 0,
    "estimated_cost": 0.0,
    "session_start": None,
    "session_duration": 0
}

leak_start_time = None
simulated_total = 0.0

def read_serial():
    global leak_start_time, simulated_total

    ser = None
    if not SIMULATE:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            print(f"Connected to Arduino on {SERIAL_PORT}")
        except Exception as e:
            print(f"Could not open serial port: {e}. Falling back to Simulation Mode.")
            # Fallback handled in the loop

    # Simulation State Machine
    states = ["IDLE", "FLOWING", "LEAK"]
    current_state = "IDLE"
    state_timer = time.time()

    while True:
        try:
            if SIMULATE or ser is None:
                # --- SIMULATION LOGIC ---
                # Change state every 15 seconds for variety
                if time.time() - state_timer > 15:
                    current_state = random.choice(states)
                    state_timer = time.time()
                    print(f"Simulating State: {current_state}")

                if current_state == "IDLE":
                    flow_l_min = 0.0
                elif current_state == "FLOWING":
                    # Normal usage: 1.5 to 4.5 L/min
                    flow_l_min = round(random.uniform(1.5, 4.5), 2)
                else: # LEAK
                    # Steady leak: 0.25 to 0.4 L/min
                    flow_l_min = round(random.uniform(0.25, 0.4), 2)

                flow_l_sec = round(flow_l_min / 60.0, 3)
                simulated_total += flow_l_sec
                total_l = round(simulated_total, 3)

                # Simulate a small delay like a real sensor
                time.sleep(1)

                # We skip reading from ser and just process these values below
            else:
                # --- REAL SERIAL READING ---
                line = ser.readline().decode().strip()
                if "Flow:" not in line:
                    continue

                parts = line.replace("|", "").replace("L/min", "").replace("L/sec", "").replace("Total:", "").replace("L", "").split()
                flow_l_min = float(parts[1])
                flow_l_sec = float(parts[2])
                total_l = float(parts[3])

            # --- Data Processing (Shared between Real & Simulated) ---

            latest_data["flow_l_min"] = flow_l_min
            latest_data["flow_l_sec"] = flow_l_sec
            latest_data["total_l"] = total_l

            # Estimate cost (0.35 RWF per Liter)
            latest_data["estimated_cost"] = round(total_l * 0.35, 2)

            # Water Status & Session Tracking
            if flow_l_min > 0:
                if latest_data["session_start"] is None:
                    latest_data["session_start"] = time.time()

                latest_data["water_status"] = "FLOWING"
                latest_data["session_duration"] = int(time.time() - latest_data["session_start"])
            else:
                latest_data["water_status"] = "IDLE"
                latest_data["session_start"] = None
                latest_data["session_duration"] = 0

            # Leak Detection Logic
            if flow_l_min >= LEAK_FLOW_THRESHOLD:
                if leak_start_time is None:
                    leak_start_time = time.time()

                time_leaking = time.time() - leak_start_time
                if time_leaking >= LEAK_TIME_THRESHOLD:
                    latest_data["leak"] = True
                    latest_data["leak_duration"] = int(time_leaking)
                    latest_data["water_status"] = "LEAK DETECTED"
            else:
                leak_start_time = None
                latest_data["leak"] = False
                latest_data["leak_duration"] = 0

        except Exception as e:
            print("Processing error:", e)
            time.sleep(1)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    return jsonify(latest_data)

if __name__ == "__main__":
    t = threading.Thread(target=read_serial, daemon=True)
    t.start()

    print("Dashboard starting at http://localhost:9090")
    app.run(host="0.0.0.0", port=9090)
