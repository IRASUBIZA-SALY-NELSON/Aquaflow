# AquaFlow Setup Guide

Complete guide to set up and run the AquaFlow waterleak detection system on your PC.

## Prerequisites

- **Python 3.13** (required for TensorFlow compatibility)
- **Git** (for cloning the repository)
- **ESP32** hardware with sensors (already configured and sending data)
- **Linux/macOS** system (Windows requires minor path adjustments)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Aquaflow
```

### 2. Install Python 3.13

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.13 python3.13-venv
```

**Check your Python version:**
```bash
python3.13 --version
```

### 3. Create Virtual Environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web server)
- TensorFlow (AI model)
- NumPy, Pandas, scikit-learn (data processing)
- PySerial (optional, for serial communication)
- All other required packages

### 5. Configure Your ESP32 IP

Edit `firmware/aquaflow_esp32/aquaflow_esp32.ino` and update:

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverHost = "YOUR_PC_IP";  // e.g., "192.168.0.115"
const int serverPort = 9090;
```

Flash this to your ESP32 using Arduino IDE.

### 6. Run the Backend Server

**WiFi Mode (ESP32 sends data over WiFi):**
```bash
source .venv/bin/activate
AQUAFLOW_MODE=wifi python backend/app.py
```

**Simulation Mode (for testing without hardware):**
```bash
source .venv/bin/activate
AQUAFLOW_MODE=simulate python backend/app.py
```

**Serial Mode (direct USB connection):**
```bash
source .venv/bin/activate
AQUAFLOW_MODE=serial AQUAFLOW_SERIAL=/dev/ttyUSB0 python backend/app.py
```

### 7. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:9090
```

You should see:
- Real-time flow rates from both sensors
- Leak detection status
- AI predictions
- Water consumption and cost estimates

## System Architecture

```
ESP32 (Sensors) --WiFi--> Backend Server ---> Web Dashboard
                              |
                              +---> Rule-Based Detection
                              +---> LSTM AI Model
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AQUAFLOW_MODE` | `simulate` | Mode: `wifi`, `serial`, or `simulate` |
| `AQUAFLOW_PORT` | `9090` | Backend server port |
| `AQUAFLOW_SERIAL` | `/dev/ttyACM0` | Serial port for Arduino |
| `AQUAFLOW_BAUD` | `115200` | Baud rate (115200 for ESP32) |
| `AQUAFLOW_FLOW_ON` | `0.15` | Flow threshold (L/min) |
| `AQUAFLOW_LEAK_SEC` | `5` | Leak confirmation time (seconds) |
| `AQUAFLOW_CONTINUOUS_SEC` | `45` | Continuous flow threshold (seconds) |
| `AQUAFLOW_BURST_LPM` | `8.0` | Burst detection threshold (L/min) |

### Example: Custom Configuration

```bash
AQUAFLOW_MODE=wifi \
AQUAFLOW_PORT=8080 \
AQUAFLOW_BURST_LPM=10.0 \
python backend/app.py
```

## File Structure

```
Aquaflow/
├── backend/
│   ├── app.py              # Flask backend server
│   ├── config.py           # Configuration settings
│   └── leak_rules.py       # Rule-based leak detection
├── ai/
│   ├── train_lstm.py       # Train AI model
│   ├── infer_lstm.py # AI inference engine
│   └── models/
│       └── lstm_leak_classifier.keras  # Pre-trained model
├── firmware/
│   └── aquaflow_esp32/
│       └── aquaflow_esp32.ino  # ESP32 Arduino code
├── templates/
│   └── index.html          # Web dashboard
├── scripts/
│   ├── monitor_live.py     # Live monitoring script
│   └── test_complete_system.py  # System tests
├── requirements.txt        # Python dependencies
└── SETUP_GUIDE.md         # This file
```

## API Endpoints

### GET /api/data
Returns current sensor readings and system status.

**Response:**
```json
{
  "device_id": "esp32-aquaflow",
  "flow_a_lpm": 2.45,
  "flow_b_lpm": 2.38,
  "status": "NORMAL_USE",
  "leak_mid": false,
  "solenoid_open": true,
  "lstm_status": "NORMAL_USE",
  "lstm_confidence": 0.94,
  "total_b_l": 45.23,
  "estimated_cost": 15.83
}
```

### POST /api/ingest
ESP32 endpoint to send sensor data.

**Request:**
```json
{
  "device_id": "esp32-aquaflow",
  "flow_a_lpm": 2.45,
  "flow_b_lpm": 2.38,
  "flow_a_lps": 0.041,
  "flow_b_lps": 0.040,
  "total_a_l": 45.10,
  "total_b_l": 45.23
}
```

### GET /api/history
Returns historical data (last 120 readings).

## Troubleshooting

### TensorFlow Installation Issues

If you get "No matching distribution found for tensorflow":

1. **Check Python version** (must be 3.9-3.13):
   ```bash
   python --version
   ```

2. **Use correct Python version:**
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

### Port Already in Use

If port 9090 is occupied:

```bash
# Find process using port 9090
lsof -i :9090  # Linux/macOS
netstat -ano | findstr :9090  # Windows

# Kill the process
kill <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows
```

Or use a different port:
```bash
AQUAFLOW_PORT=8080 python backend/app.py
```

### ESP32 Not Connecting

1. **Check WiFi credentials** in the Arduino code
2. **Verify PC IP address:**
   ```bash
   ip addr show  # Linux
   ifconfig  # macOS
   ipconfig  # Windows
   ```
3. **Ensure firewall allows port 9090**
4. **Check ESP32 serial monitor** for connection logs

### AI Model Not Loading

If you see "LSTM Load failed":

1. Verify TensorFlow is installed:
   ```bash
   pip show tensorflow
   ```

2. Check model file exists:
   ```bash
   ls -lh ai/models/lstm_leak_classifier.keras
   ```

3. Retrain model if needed:
   ```bash
   python ai/train_lstm.py
   ```

## Running in Production

For production deployment, use a proper WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9090 backend.app:app
```

Or deploy to cloud platforms like Render, Heroku, or AWS. See `DEPLOYMENT.md` for details.

## Testing

### Run System Tests
```bash
python scripts/test_complete_system.py
```

### Monitor Live Data
```bash
python scripts/monitor_live.py
```

### Test with Simulation
```bash
AQUAFLOW_MODE=simulate python backend/app.py
```

## Hardware Setup

### Required Components

- ESP32 development board
- 2× YF-S201 water flow sensors
- Solenoid valve (12V)
- Relay module
- Piezo buzzer
- Power supply (12V for solenoid)
- Pipes and fittings

### Wiring Diagram

See `ESP32_UPLOAD_GUIDE.md` and `HOW_IT_WORKS.md` for detailed hardware setup.

## Features

✓ **Real-time monitoring** - Live water flow from dual sensors
✓ **AI leak detection** - LSTM neural network predictions
✓ **Rule-based alerts** - Instant detection of anomalies
✓ **Web dashboard** - Beautiful real-time visualization
✓ **Cost tracking** - Water consumption and cost estimates
✓ **Automatic shutoff** - Solenoid valve control on leak detection
✓ **Multiple modes** - WiFi, Serial, or Simulation

## Support

For issues, questions, or contributions:
1. Check existing documentation in the repo
2. Review troubleshooting section above
3. Open an issue on GitHub

## License

See LICENSE file for details.

---

**Built with ❤️ for water conservation**
