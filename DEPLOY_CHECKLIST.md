# 🚀 AquaFlow Deployment Checklist

## ✅ Step 1: Deploy Backend to Render (5 minutes)

Go to Render form and enter **EXACTLY** these values:

### Basic Configuration
```
Name: aquaflow-backend
Source Code: IRASUBIZA-SALY-NELSON/Aquaflow
Branch: main
Language: Python 3
Region: Oregon (US West)
Root Directory: [LEAVE EMPTY]
```

### Build & Start Commands
```
Build Command: pip install -r requirements-backend.txt
Start Command: python -m backend.app
```

### Instance Type
```
Select: Free ($0/month)
```

### Environment Variables (Click "Add Environment Variable" 4 times)
```
1. AQUAFLOW_MODE = wifi
2. AQUAFLOW_PORT = 10000
3. AQUAFLOW_HOST = 0.0.0.0
4. AQUAFLOW_SIMULATE = 1
```

### Click "Deploy Web Service" Button

⏳ Wait 3-5 minutes for deployment...

---

## ✅ Step 2: Test Your Deployed Dashboard

Once deployed, you'll get a URL like:
```
https://aquaflow-backend-xxxx.onrender.com
```

Open it in your browser - you should see:
- ✨ Beautiful splash screen with AquaFlow logo
- 💧 Modern turquoise/cyan dashboard
- 📊 Real-time graphs with simulated data
- 🔄 Live updates every second

---

## ✅ Step 3: Upload Firmware to ESP32 (For Real Hardware Demo)

### 3.1 Connect ESP32 via USB

**NOW CONNECT YOUR ESP32 TO YOUR LAPTOP VIA USB CABLE**

Once connected, run:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

You should see: `/dev/ttyUSB0` (or similar)

### 3.2 Update Firmware Configuration

The firmware is already configured with:
- **WiFi**: MTN UrugoNet_CBC4
- **Password**: 9255E65C
- **Server IP**: 192.168.0.115 (your laptop)

### 3.3 Flash ESP32

Run this command:

```bash
bash scripts/flash_esp32.sh /dev/ttyUSB0
```

Wait for:
```
Compiling...
Uploading...
Flash OK. Opening serial monitor @115200
```

You'll see JSON data streaming:
```json
{"device_id":"aquaflow-esp32-01","flow_a_lpm":0.00,...}
```

### 3.4 Run Local Backend (To Receive ESP32 Data)

In a new terminal:

```bash
source .venv/bin/activate
AQUAFLOW_MODE=wifi python -m backend.app
```

Open: http://localhost:9090

You should see REAL data from your ESP32!

---

## 📋 Quick Reference

### Cloud Dashboard (Simulation)
```
https://your-render-url.onrender.com
```

### Local Dashboard (Real Hardware)
```
http://localhost:9090
```

### API Endpoints
```
GET  /api/data      - Current readings
GET  /api/history   - Historical data
POST /api/ingest    - ESP32 data upload
POST /api/command   - Manual controls
```

---

## 🎯 Demo Scenarios

### Online Demo (Cloud)
1. Share Render URL with anyone
2. They see live simulated data
3. Cycles through: IDLE → NORMAL_USE → LEAK → CONTINUOUS_FLOW

### Hardware Demo (Local)
1. Connect ESP32 to laptop
2. Flash firmware
3. Run local backend
4. Turn on water flow
5. Simulate leak (disconnect sensor B)
6. Watch automatic valve closure!

---

## 🎉 You're Ready!

Both deployment options are ready:
- ☁️ **Cloud**: Live demo at Render URL (simulation mode)
- 🔌 **Hardware**: Local demo with real sensors

**Next Step**: Tell me when you've connected the ESP32 USB cable, and I'll upload the firmware!
