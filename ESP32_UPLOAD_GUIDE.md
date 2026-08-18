# ESP32 Upload Troubleshooting Guide

## ⚠️ Current Issue: Flash Communication Error

Your ESP32 is having trouble entering flash mode automatically. This is common and easily fixed!

## 🔧 Solution: Manual Boot Mode

### Method 1: Boot Button Method (Recommended)

**Follow these steps EXACTLY:**

1. **Locate the buttons on your ESP32:**
   - BOOT button (usually labeled "BOOT" or "IO0")
   - RESET button (usually labeled "RST" or "RESET" or "EN")

2. **Put ESP32 in flash mode:**
   ```
   Step 1: Hold down the BOOT button (keep holding!)
   Step 2: While holding BOOT, press and release RESET
   Step 3: Keep holding BOOT for 2 more seconds
   Step 4: Release BOOT
   ```

3. **Now run the upload command:**
   ```bash
   arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 firmware/aquaflow_esp32
   ```

4. **Watch for "Connecting..." then the upload will start!**

### Method 2: Use Arduino IDE (Easiest!)

If the command line is giving issues, use the Arduino IDE:

1. **Open Arduino IDE**
   ```bash
   arduino-ide
   ```

2. **Open the sketch:**
   - File → Open → Browse to `/home/minister/Documents/PROJECTS/Aquaflow/firmware/aquaflow_esp32/aquaflow_esp32.ino`

3. **Select board:**
   - Tools → Board → ESP32 Arduino → ESP32 Dev Module

4. **Select port:**
   - Tools → Port → /dev/ttyUSB0

5. **Click Upload button (→)**
   - If it says "Connecting...", hold BOOT button during this time
   - Release when you see "Writing at 0x..."

### Method 3: Try Different USB Cable

Sometimes USB cables are charge-only (no data). Try another cable if available.

---

## ✅ What's Already Done

While we work on ESP32 upload, the backend is **ALREADY RUNNING**!

### Backend Status: ✓ RUNNING

```
AquaFlow backend on http://0.0.0.0:9090
Mode: SIMULATE (demo data cycling)
```

### Dashboard Access:

**Open in your browser:**
```
http://localhost:9090
```

or

```
http://192.168.0.115:9090
```

You should see:
1. ✨ **Splash screen** with AquaFlow logo (2.5 seconds)
2. 💧 **Beautiful dashboard** with cyan/turquoise theme
3. 📊 **Live graphs** showing simulated water flow
4. 🔄 **Auto-updating** every second

---

## 🎭 Current Demo Mode

The backend is running in **SIMULATION MODE**, cycling through scenarios:

| Time | Scenario | Flow A | Flow B | Status |
|------|----------|--------|--------|--------|
| 0-8s | IDLE | 0.0 | 0.0 | No water flowing |
| 8-20s | NORMAL_USE | 2.5 | 2.4 | Normal flow |
| 20-34s | MID_PIPE_LEAK | 0.8 | 0.0 | LEAK! Valve closes |
| 34-54s | CONTINUOUS_FLOW | 2.0 | 2.0 | Long running water |
| 54-60s | BURST | 10.0 | 8.0 | Pipe burst! |

Watch your dashboard change colors and status!

---

## 🔄 Once ESP32 is Uploaded...

After successfully uploading firmware:

1. **Stop simulation backend:**
   ```bash
   # Press Ctrl+C in the terminal running backend
   ```

2. **Start WiFi mode backend:**
   ```bash
   AQUAFLOW_MODE=wifi python -m backend.app
   ```

3. **ESP32 will connect to:**
   - WiFi: MTN UrugoNet_CBC4
   - Server: 192.168.0.115:9090

4. **Dashboard will show REAL DATA** from your sensors!

---

## 🆘 Still Having Issues?

### Check USB Connection
```bash
ls -la /dev/ttyUSB*
# Should show: /dev/ttyUSB0
```

### Check Permissions
```bash
sudo usermod -a -G dialout $USER
# Then log out and log back in
```

### Reset ESP32
```bash
# Unplug USB
# Wait 5 seconds
# Plug back in
# Try upload again
```

### Alternative: Use PlatformIO
```bash
cd firmware/aquaflow_esp32
pio run --target upload
```

---

## 📱 Meanwhile, Enjoy the Live Demo!

Your dashboard is live at:
### http://localhost:9090

Try these:
- Watch the real-time graph update
- See different leak scenarios
- Check the beautiful UI animations
- Test on mobile browser too!

---

**When you're ready to try ESP32 upload again, just let me know!** 🚀
