# AquaFlow - Smart Water Management System

**Smart Flow, Better Living**

AquaFlow is an IoT-based smart water management system that uses dual flow sensors, AI-powered leak detection, and automated valve control to prevent water waste and damage from leaks.

## 📋 Quick Links

- **[Setup Guide](SETUP_GUIDE.md)** - Complete installation instructions
- **[How It Works](HOW_IT_WORKS.md)** - System architecture and logic
- **[Deployment Guide](DEPLOYMENT.md)** - Cloud deployment instructions
- **[ESP32 Upload Guide](ESP32_UPLOAD_GUIDE.md)** - Firmware flashing

## ✨ Features

- 🚰 **Dual Sensor Monitoring** - Real-time flow tracking at source and tap points
- 🤖 **AI Leak Detection** - LSTM neural network for intelligent pattern recognition
- 🔒 **Automatic Shutoff** - Solenoid valve closes automatically when leaks detected
- 📊 **Live Dashboard** - Beautiful web interface with real-time monitoring
- 💰 **Cost Tracking** - Estimated water billing in RWF
- 🔔 **Smart Alerts** - Buzzer notifications for leaks and continuous flow
- ⚡ **Manual Control** - Push button for valve and pump override

## 🚀 Quick Start

### 1. Install Python 3.13 & Dependencies

```bash
# Create virtual environment with Python 3.13
python3.13 -m venv .venv
source .venv/bin/activate

# Install all dependencies including TensorFlow
pip install -r requirements.txt
```

### 2. Configure & Flash ESP32

Update WiFi and server settings in `firmware/aquaflow_esp32/aquaflow_esp32.ino`:

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverHost = "YOUR_PC_IP";  // e.g., "192.168.0.115"
```

Flash using Arduino IDE or:
```bash
bash scripts/flash_esp32.sh /dev/ttyUSB0
```

### 3. Run Backend Server

```bash
source .venv/bin/activate
AQUAFLOW_MODE=wifi python backend/app.py
```

### 4. Open Dashboard

Navigate to: **http://localhost:9090**

## 🎯 System Modes

| Mode | Command | Description |
|------|---------|-------------|
| **WiFi** | `AQUAFLOW_MODE=wifi python backend/app.py` | ESP32 sends data over WiFi (production) |
| **Serial** | `AQUAFLOW_MODE=serial python backend/app.py` | Direct USB connection to Arduino |
| **Simulate** | `AQUAFLOW_MODE=simulate python backend/app.py` | Demo mode without hardware |


## 🔧 Hardware Components

- **ESP32 Development Board** - WiFi-enabled microcontroller
- **YF-S201 Flow Sensors (x2)** - Source and tap monitoring
- **12V Solenoid Valve** - Normally closed, automated shutoff
- **Water Pump** - Controlled via relay
- **Relay Module (3-channel)** - Controls solenoid, pump, buzzer
- **Piezo Buzzer** - Audio alerts
- **Push Button** - Manual override control

## 📡 ESP32 Pin Assignments

```
GPIO 2  → Flow Sensor A (source)
GPIO 4  → Flow Sensor B (tap)
GPIO 27 → Solenoid Valve Relay
GPIO 14 → Pump Relay
GPIO 13 → Buzzer Relay
GPIO 12 → Push Button (INPUT_PULLUP)
```

## 🎮 Button Controls

- **Single Click** - Toggle solenoid valve (open/close)
- **Double Click** - Toggle pump (on/off)

## 🧠 AI Model Details

- **Architecture**: LSTM (Long Short-Term Memory) Neural Network
- **Training Accuracy**: 100% on test set
- **Input**: 30-second rolling window of dual sensor flow data
- **Classes**: IDLE, NORMAL_USE, MID_PIPE_LEAK, BURST, CONTINUOUS_FLOW
- **Framework**: TensorFlow/Keras 3.x

## 🔍 Leak Detection Logic

1. **Normal Flow** - Both sensors active → Status: NORMAL_USE ✅
2. **Suspect Leak** - Sensor A flows, Sensor B dry (0-4s) → Warning beep ⚠️
3. **Confirmed Mid-Pipe Leak** - Condition persists 5+ seconds → Valve closes, buzzer ON 🚨
4. **Burst Detection** - Flow > 8.0 L/min → Immediate shutoff 💥
5. **Continuous Flow** - Uninterrupted flow 45+ seconds → Alert 🔔


## 📁 Project Structure

```
Aquaflow/
├── ai/                           # AI/ML components
│   ├── models/                   # Trained LSTM model
│   │   ├── lstm_leak_classifier.keras
│   │   └── label_map.json
│   ├── train_lstm.py             # Model training script
│   ├── infer_lstm.py             # Real-time inference engine
│   └── generate_dataset.py       # Dataset generation
├── backend/                      # Flask web server
│   ├── app.py                    # Main server application
│   ├── config.py                 # Configuration settings
│   └── leak_rules.py             # Rule-based detection logic
├── firmware/                     # Embedded systems code
│   └── aquaflow_esp32/           # ESP32 Arduino firmware
│       └── aquaflow_esp32.ino
├── templates/                    # Web frontend
│   └── index.html                # Real-time dashboard UI
├── scripts/                      # Utility scripts
│   ├── monitor_live.py           # Live monitoring CLI
│   ├── test_complete_system.py  # System integration tests
│   └── flash_esp32.sh            # Firmware upload helper
├── data/                         # Training datasets
├── requirements.txt              # Python dependencies (full)
├── requirements-backend.txt      # Backend-only dependencies
├── SETUP_GUIDE.md               # Detailed setup instructions
└── README.md                    # This file
```

## ⚙️ Configuration

Environment variables for customization:

```bash
# Operating mode
AQUAFLOW_MODE=wifi              # wifi | serial | simulate

# Network settings
AQUAFLOW_PORT=9090              # Backend server port
AQUAFLOW_HOST=0.0.0.0           # Bind address

# Serial settings (for serial mode)
AQUAFLOW_SERIAL=/dev/ttyACM0    # Serial port
AQUAFLOW_BAUD=115200            # Baud rate

# Detection thresholds
AQUAFLOW_FLOW_ON=0.15           # Flow on threshold (L/min)
AQUAFLOW_LEAK_SEC=5             # Leak confirmation time (seconds)
AQUAFLOW_CONTINUOUS_SEC=45      # Continuous flow threshold (seconds)
AQUAFLOW_BURST_LPM=8.0          # Burst threshold (L/min)
```

## 🧪 Testing & Development

### Run System Tests
```bash
python scripts/test_complete_system.py
```

### Live Monitoring (CLI)
```bash
python scripts/monitor_live.py
```

### Retrain AI Model
```bash
bash scripts/train_ai.sh
# Or manually:
python ai/generate_dataset.py
python ai/train_lstm.py
```

### Demo Mode (No Hardware)
```bash
AQUAFLOW_MODE=simulate python backend/app.py
```

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web dashboard |
| `/api/data` | GET | Current sensor readings and status |
| `/api/history` | GET | Historical data (last 120 readings) |
| `/api/ingest` | POST | ESP32 data ingestion endpoint |
| `/api/command` | POST | Manual valve/pump control |

## 🚀 Deployment

For production deployment options (Render, AWS, Heroku), see [DEPLOYMENT.md](DEPLOYMENT.md).

Quick production server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9090 backend.app:app
```

## 📝 Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Step-by-step installation and setup
- **[HOW_IT_WORKS.md](HOW_IT_WORKS.md)** - Technical architecture and algorithms
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Cloud deployment guide
- **[ESP32_UPLOAD_GUIDE.md](ESP32_UPLOAD_GUIDE.md)** - Firmware upload instructions
- **[SYSTEM_STATUS.md](SYSTEM_STATUS.md)** - Project status and roadmap

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - Free and open source for everyone.

## 👥 Team

**Rwanda Coding Academy - Smart Water Management Project**

- **Irasubiza Saly Nelson** - Hardware & Firmware
- **Nishimwe Cynthia Marie** - AI/ML & Backend
- **Unirwe Esther Hope** - Frontend & Integration

## 🙏 Acknowledgments

Built with passion for water conservation and sustainable development in Rwanda.

---

**AquaFlow** - Every drop counts. 💧
*Saving water, one leak at a time.*
