#!/bin/bash
# Monitor all AquaFlow components in real-time

echo "============================================"
echo "   AquaFlow Live Monitoring Dashboard"
echo "============================================"
echo ""
echo "Backend: http://192.168.0.115:9090"
echo "ESP32 Device ID: aquaflow-esp32-01"
echo ""
echo "Monitoring backend logs..."
echo "Press Ctrl+C to stop"
echo "============================================"
echo ""

# Follow backend logs by checking API data endpoint
while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    DATA=$(curl -s http://127.0.0.1:9090/api/data 2>/dev/null)
 grep -o '"solenoid_open":[a-z]*' | cut -d':' -f2)
        SOURCE=$(echo "$DATA" | grep -o '"source":"[^"]*"' | cut -d'"' -f4)

        echo "[$TIMESTAMP] Device: $DEVICE | Status: $STATUS | Source: $SOURCE"
        echo "  └─ Flow A: ${FLOW_A}L/min | Flow B: ${FLOW_B}L/min | Leak: $LEAK | Solenoid: $SOLENOID"
    else
        echo "[$TIMESTAMP] Backend not responding..."
    fi

    sleep 1
done
