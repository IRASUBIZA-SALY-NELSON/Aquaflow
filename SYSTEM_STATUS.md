# AquaFlow System Status - WiFi Mode

## 🎯 Active Monitoring Terminals

### Terminal 14 - ESP32 Serial Monitor (USB)
- **Port:** `/dev/ttyUSB0` @ 115200 baud
- **Purpose:** View raw ESP32 serial output for debugging
- **Status:** ✅ Connected
- **Command:** `stty -F /dev/ttyUSB0 115200 && cat /dev/ttyUSB0`

### Terminal 16 - Backend Server
- **URL:** `http://192.168.0.115:9090`
- **Mode:** WiFi (receiving data from ESP32)
- **Status:** ✅ Running
- **Logs:** Shows POST requests from `192.168.0.109` (ESP32)
- **Command:** `AQUAFLOW_MODE=wifi python -m backend.app`

### Terminal 15 - Live Monitoring Dashboard
- **Status:** ✅ Active
- **Updates:** Real-time (every 1 second)
- **Display:** Flow rates, leak status, device state
- **Command:** `python scripts/monitor_live.py`

## 🌐 Network Configuration

```
ESP32 Device:     192.168.0.109 (esp32-24D870)
Backend Server:   192.168.0.115 (kali)
WiFi Network:     MTN UrugoNet_CBC4
Communication:    ✅ Active (POST every 1 second)
```

## 📡 Current System State

- **Device ID:** aquaflow-esp32-01
- **Status:** IDLE
- **Flow A:** 0.00 L/min (Source sensor)
- **Flow B:** 0.00 L/min (Tap sensor)
- **Leak Detection:** No leak
- **Solenoid:** OPEN
- **Pump:** OFF
- **Buzzer:** OFF
- **Data Source:** WiFi

## 🎛️ Available Commands

### View Logs
```bash
# Watch backend logs (Terminal 16)
# Already running - shows ESP32 POST requests

# Watch monitoring dashboard (Terminal 15)
# Already running - shows real-time status

# Watch ESP32 serial output (Terminal 14)
# Already running - shows raw ESP32 debug messages
```

### Test Leak Detection
```bash
# Simulate leak via API
curl -X POST http://192.168.0.115:9090/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","flow_a_lpm":2.5,"flow_b_lpm":0.1}'
```

### View Current Data
```bash
curl -s http://127.0.0.1:9090/api/data | python -m json.tool
```

### Open Web Interface
```bash
xdg-open http://192.168.0.115:9090
```

## 📋 Next Steps

1. **Test water flow** - Turn on water to see flow detection
2. **Test leak detection** - Create flow imbalance (A high, B low)
3. **View web interface** - Open browser to see dashboard
4. **Check AI predictions** - Install TensorFlow for LSTM model

## 🔧 Troubleshooting

If ESP32 stops sending data:
1. Check power (USB or external)
2. Check WiFi connection: `ping 192.168.0.109`
3. Check ESP32 serial output in Terminal 14

If backend stops responding:
1. Restart backend: Stop Terminal 16 and run:
   ```bash
   AQUAFLOW_MODE=wifi python -m backend.app
   ```

---
**Last Updated:** 2026-08-18 09:57:00
**System:** AquaFlow Water Leak Detection System

