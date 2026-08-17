# AquaFlow - Smart Water Management System

**Smart Flow, Better Living**

AquaFlow is an IoT-based smart water management system that uses dual flow sensors, AI-powered leak detection, and automated valve control to prevent water waste and damage from leaks.

## Features

- 🚰 **Dual Sensor Monitoring** - Real-time flow tracking at source and tap points
- 🤖 **AI Leak Detection** - LSTM neural network for intelligent pattern recognition
- 🔒 **Automatic Shutoff** - Solenoid valve closes automatically when leaks detected
- 📊 **Live Dashboard** - Beautiful web interface with real-time monitoring
- 💰 **Cost Tracking** - Estimated water billing in RWF
- 🔔 **Smart Alerts** - Buzzer notifications for leaks and continuous flow
- ⚡ **Manual Control** - Push button for valve and pump override

## System Architecture

- **ESP32 Microcontroller** - WiFi-enabled IoT device
- **YF-S201 Flow Sensors** (x2) - Source and tap monitoring
- **Solenoid Valve** - Normally closed, automated shutoff
- **Water Pump** - Controlled via relay
- **Buzzer** - Audio alerts
- **Push Button** - Manual override control

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Flash ESP32 Firmware

Update WiFi credentials in `firmware/aquaflow_esp32/aquaflow_esp32.ino`:

```cpp
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_HOST   = "YOUR_LAPTOP_IP";
```

Flash firmware:

```bash
bash scripts/flash_esp32.sh /dev/ttyUSB0
```

### 3. Run Backend Server

```bash
source .venv/bin/activate
AQUAFLOW_MODE=wifi python -m backend.app
```

### 4. Open Dashboard

Navigate to: **http://localhost:9090**

## Hardware Wiring

```
ESP32 Pin Assignments:
  GPIO 2  → Flow Sensor A (source)
  GPIO 4  → Flow Sensor B (tap)
  GPIO 27 → Solenoid Valve Relay
  GPIO 14 → Pump Relay
  GPIO 13 → Buzzer Relay
  GPIO 12 → Push Button (INPUT_PULLUP)
```

## Button Controls

- **Single Click** - Toggle solenoid valve (open/close)
- **Double Click** - Toggle pump (on/off)

## Leak Detection Logic

1. **Normal Flow** - Both sensors active → Status: NORMAL_USE
2. **Suspect Leak** - Sensor A flows, Sensor B dry (0-4 seconds) → Warning beep
3. **Confirmed Leak** - Condition persists for 5 seconds → Valve closes, buzzer ON
4. **Burst Detection** - Very high flow → Immediate shutoff

## AI Model

- **Architecture**: LSTM Neural Network
- **Accuracy**: 100% on test set
- **Classes**: IDLE, NORMAL_USE, MID_PIPE_LEAK, BURST, CONTINUOUS_FLOW
- **Input**: 30-second rolling window of flow data

## Project Structure

```
aquaflow/
├── ai/                      # AI/ML models and training
│   ├── models/              # Trained LSTM model
│   ├── train_lstm.py        # Model training script
│   └── infer_lstm.py        # Real-time inference
├── backend/                 # Flask web server
│   ├── app.py               # Main server
│   ├── config.py            # Configuration
│   └── leak_rules.py        # Rule-based detection
├── firmware/                # ESP32 Arduino code
│   └── aquaflow_esp32/      # Main firmware
├── templates/               # Web dashboard
│   └── index.html           # Modern UI
├── scripts/                 # Utility scripts
└── data/                    # Training datasets
```

## Environment Variables

- `AQUAFLOW_MODE` - `wifi` (ESP32) or `serial` (Arduino Uno)
- `AQUAFLOW_SIMULATE` - `1` for demo mode without hardware
- `AQUAFLOW_PORT` - Server port (default: 9090)
- `AQUAFLOW_HOST` - Server host (default: 0.0.0.0)

## Demo Mode

Run without hardware:

```bash
AQUAFLOW_SIMULATE=1 python -m backend.app
```

## Training AI Model

```bash
source .venv/bin/activate
bash scripts/train_ai.sh
```

## License

MIT License - Open source water management for everyone.

## Team

Rwanda Coding Academy
- Irasubiza Saly Nelson
- Nishimwe Cynthia Marie
- Unirwe Esther Hope

---

**AquaFlow** - Every drop counts. 💧
