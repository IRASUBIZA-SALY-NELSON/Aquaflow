# 🌊 How AquaFlow Works - Complete System Explanation

## 🎯 System Overview

AquaFlow isa smart water leak detection system that monitors water flow in real-time and automatically shuts off water when it detects leaks, preventing water waste and damage.

---

## 🔧 Hardware Components

### 1. **Two Flow Sensors (YF-S201)**
```
Sensor A (Source) ━━━━━━━━━ [Water Pipe] ━━━━━━━━━ Sensor B (Tap)
     ↓                                                    ↓
  GPIO 2                                              GPIO 4
```

**How They Work:**
- Small turbine inside spins when water flows
- Each rotation generates electrical pulses
- ESP32 counts pulses → calculates flow rate
- Formula: `Flow (L/min) = Pulses per second ÷ 7.5`

**Why Two Sensors?**
- **Sensor A** = Water entering your house (source)
- **Sensor B** = Water reaching your tap (destination)
- If A flows but B doesn't → **LEAK IN THE PIPE!**

---

### 2. **ESP32 Microcontroller (The Brain)**

**What It Does:**
1. Reads pulse data from both sensors every second
2. Calculates flow rates (liters per minute)
3. Runs leak detection logic
4. Controls solenoid valve and pump via relays
5. Sends data to backend server via WiFi (every 1 second)
6. Receives commands from backend (open/close valve)

**Code Flow:**
```cpp
loop() {
  1. Read button presses (manual control)
  2. Count pulses from sensors (1 second interval)
  3. Calculate flow rates
  4. Classify status (IDLE, NORMAL_USE, LEAK, etc.)
  5. Control hardware (valve, pump, buzzer)
  6. Send JSON data to backend via WiFi POST
  7. Repeat every second
}
```

---

### 3. **Solenoid Valve (Water Gate)**

**Type:** Normally Closed (NC)
- **Power OFF** → Valve CLOSED (water blocked) ✅ Safe default!
- **Power ON** → Valve OPENS (water flows)

**Control:**
- Connected to GPIO 27 via relay
- When leak detected → ESP32 turns relay OFF → Valve closes
- Manual control: Single button click toggles state

---

### 4. **Water Pump/Motor**

**Purpose:** Pumps water when system is normal

**Control:**
- Connected to GPIO 14 via relay
- Automatically turns ON when: valve open + normal flow
- Automatically turns OFF when: valve closes or IDLE
- Manual control: Double-click button toggles state

---

### 5. **Buzzer (Alert System)**

**Connected to:** GPIO 13 via relay

**Alert Patterns:**
| Status | Buzzer Behavior |
|--------|----------------|
| IDLE / NORMAL_USE | OFF (silent) |
| SUSPECT_LEAK | BEEPING (300ms intervals) |
| MID_PIPE_LEAK | ON (continuous alarm) |
| BURST | ON (continuous alarm) |
| CONTINUOUS_FLOW | BEEPING (700ms intervals) |

---

### 6. **Push Button (Manual Override)**

**Connected to:** GPIO 12 (INPUT_PULLUP, active LOW)

**Controls:**
- **Single Click** → Toggle solenoid valve (open ↔ close)
- **Double Click** (within 450ms) → Toggle pump (on ↔ off)

**Why Manual Control?**
- Override automatic shutoff if false alarm
- Test system components
- Emergency manual control

---

## 🧠 Leak Detection Logic

### Rule-Based Detection (Fast & Reliable)

```python
# backend/leak_rules.py

if sensor_A == 0 and sensor_B == 0:
    status = "IDLE"  # Nowater flowing

elif sensor_A > 0 and sensor_B > 0:
    status = "NORMAL_USE"  # Both sensors detect water

elif sensor_A > 0 and sensor_B == 0:
    if duration < 5 seconds:
        status = "SUSPECT_LEAK"  # Warning period
        buzzer = BEEPING
    else:
        status = "MID_PIPE_LEAK"  # CONFIRMED LEAK
        solenoid = CLOSED
        pump = OFF
        buzzer = ON

elif sensor_A > 8 L/min:
    status = "BURST"  # Pipe burst!
    solenoid = CLOSED (immediate)
    pump = OFF
    buzzer = ON
```
CONTINUOUS_FLOW
- 100% accuracy on test set

**When AI Agrees:**
- If rules say "LEAK" AND AI says "LEAK" (>65% confidence)
- System is MORE confident → Faster response

---

## 📡 Data Flow (WiFi Mode)

```
┌─────────────────────────────────────────────────────────────┐
│  ESP32 (Firmware)                                           │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌──────┐         │
│  │ Sensor A │  │ Sensor B │  │ Button │  │Relays│         │
│  └────┬─────┘  └────┬─────┘  └───┬────┘  └──┬───┘         │
│       │             │            │          │              │
│       └─────────────┴────────────┴──────────┘              │
│                     │                                       │
│            ┌────────▼────────┐                             │
│            │  Main Loop      │                             │
│            │  (every 1 sec)  │                             │
│            └────────┬────────┘                             │
│                     │                                       │
│
──────┐  │
         │  │ /api/ingest          │  │
         │  │ - Receives JSON      │  │
         │  │ - Runs leak rules    │  │
         │  │ - Optional: AI check │  │
         │  │ - Stores history     │  │
         │  │ - Sends response     │  │
         │  └──────────┬───────────┘  │
         │             │               │
         │  ┌──────────▼───────────┐  │
         │  │ /api/data            │  │
         │  │ - Returns latest     │  │
         │  └──────────┬───────────┘  │
         └─────────────┼───
aph    │  │
         │  │ - System status      │  │
         │  │ - Control chips      │  │
         │  └──────────────────────┘  │
         └────────────────────────────┘
```

---

## 🎨 Dashboard Explained

### 1. **Splash Screen (First 2.5 seconds)**
```
┌─────────────────────────┐
│                         │
│       💧 (animated)     │
│                         │
│      AquaFlow           │
│  Smart Flow, Better     │
│       Living            │
│                         │
│     ● ● ● (loading)     │
│                         │
└─────────────────────────┘
```

### 2. **Main Dashboard Components**

**A. Hero Status Card (Top, Large Gradient Card)**
```
System Status
━━━━━━━━━━━━━━━━━━━━━━━━━━
NORMAL USE
Water flowing normally. Both sensors
detecting regular usage.

🔓 Valve Open  ⚡ Pump Off  🔔 Alarm Off
```

- Changes color based on status:
  - 🟦 Blue = Normal/Idle
  - 🟧 Orange = Warning (Suspect Leak)
  - 🟥 Red = Danger (Confirmed Leak)

**B. Stats Cards (4 cards)**
```
┌──────────────┐ ┌──────────────┐
│ Water Fl
───────────────→ time
       Last 60 seconds
```

**D. System Info Cards (4 cards)**
```
┌─────────────┐ ┌─────────────┐
│🔓 Valve     │ │⚡ Pump      │
│   OPEN      │ │   OFF       │
└─────────────┘ └─────────────┘

┌─────────────┐ ┌─────────────┐
│🔔 Leak Det  │ │🤖 AI System │
│ NO LEAK     │ │ NORMAL (98%)│
└─────────────┘ └─────────────┘
```

---

## 🎭 Demo Scenarios

### Scenario 1: Normal Water Use
```
1. User turns on tap
2. Sensor A: 2.5 L/min → ESP32
3. Sensor B: 2.4 L/min → ESP32
4. ESP32 Logic: Both flowing → NORMAL_USE
5. Solenoid: OPEN ✓
6. Pump: ON ✓
7. Buzzer: OFF ✓
8. ESP32 sends JSON to backend
9. Dashboard shows: "Water flowing normally"
```

### Scenario 2: Leak Detection
```
1. Pipe leaks between sensors
2. Sensor A: 2.5 L/min (water flowing in)
3. Sensor B: 0.0 L/min (no water at tap)
4. ESP32 Logic:
   t=0s → Status: SUSPECT_LEAK
   t=1s → Status: SUSPECT_LEAK (buzzer beeping)
   t=2s → Status: SUSPECT_LEAK (buzzer beeping)
   t=3s → Status: SUSPECT_LEAK (buzzer beeping)
   t=4s → Status: SUSPEC
e flag: SET
7. Water flows again
8. Dashboard shows: "Valve Open (Manual)"
```

### Scenario 4: Burst Detection
```
1. Pipe bursts
2. Sensor A: 12.0 L/min (very high!)
3. ESP32 Logic: Flow > 8 L/min → BURST
4. Response: IMMEDIATE (no 5-second wait)
   - Solenoid: CLOSED
   - Pump: OFF
   - Buzzer: ON
5. Dashboard: RED alert "PIPE BURST DETECTED!"
```

---

## 🔄 Simulation Mode (For Demo Without Hardware)

When you run:
```bash
AQUAFLOW_SIMULATE=1 python -m backend.app
```

**What Happens:**
1. Backend starts simulator thread
2. Cycles through scenarios automatically:
   - 8 seconds: IDLE (0.0, 0.0)
   - 12 seconds: NORMAL_USE (2.5, 2.4)
   - 14 seconds: MID_PIPE_LEAK (0.8, 0.0)
   - 20 seconds: CONTINUOUS_FLOW (2.0, 2.0)
   - 6 seconds: BURST (10.0, 8.0)
   - Repeat...

3. Dashboard shows live animated demo
4. No hardware needed!
5. Perfect for presentations

---

## 📊 Data Format (JSON)

**ESP32 sends to backend:**
```json
{
  "device_id": "aquaflow-esp32-01",
  "ts": 54321,
  "flow_a_lpm": 2.45,
  "flow_b_lpm": 2.38,
  "flow_a_lps": 0.041,
  "flow_b_lps": 0.040,
  "total_a_l": 15.234,
  "total_b_l": 14.892,
  "status": "NORMAL_USE",
  "leak_mid": false,
  "continuous_flow": false,
  "solenoid_open": true,
  "pump_on": true,
  "buzzer_on": false,
  "manual_override": false,
  "pump_manual_override": false,
  "wifi_rssi": -45
}
```

**Backend responds:**
```json
{
  "ok": true,
  "solenoid_open": true,
  "status": "NORMAL_USE"
}
```

**Dashboard fetches:**
```javascript
// Every 1 second
fetch('/api/data')
  .then(res => res.json())
  .then(data => {
    // Update all UI elements
    updateStats(data);
    updateGraph(data);
    updateStatus(data);
  });
```

---

## 🎓 Key Features Summary

| Feature | How It Works |
|---------|-------------|
| **Dual Sensors** | Detects leaks by comparing source vs tap flow |
| **5-Second Confirmation** | Prevents false alarms, confirms sustained leaks |
| **Automatic Shutoff** | Solenoid valve closes when leak confirmed |
| **Manual Override** | Button control for emergency situations |
| **Real-Time Monitoring** | WiFi sends data every second to dashboard |
| **Smart Alerts** | Buzzer patterns for different situations |
| **AI Enhancement** | LSTM model reinforces rule-based detection |
| **Beautiful UI** | Modern dashboard with splash screen, graphs |
| **Cost Tracking** | Estimates water billing in RWF |
| **Simulation Mode** | Demo without physical hardware |

---

## 🚀 Two Operating Modes

### Mode 1: Local (With Real Hardware)
```
ESP32 → WiFi → Laptop Backend → Browser Dashboard
        (192.168.0.115:9090)
```
- Real sensor data
- Physical valve/pump control
- Local network only

### Mode 2: Cloud (Simulation)
```
Backend (Render) → Simulated Data → Browser Dashboard
(your-app.onrender.com)
```
- No hardware needed
- Demo for anyone, anywhere
- Perfect for presentations

---

## 💡 Why It's Smart

1. **Prevents Water Damage** - Automatic shutoff saves you from floods
2. **Saves Money** - No wasted water from undetected leaks
3. **Always Monitoring** - 24/7 automatic detection
4. **Fast Response** - Detects and stops leaks in 5 seconds
5. **User Friendly** - Beautiful dashboard anyone can understand
6. **Manual Control** - You're always in charge with button override
7. **Scalable** - Add more sensors, connect to home automation
8. **Cost Effective** - Built with affordable IoT components

---

**Every Drop Counts!** 💧
