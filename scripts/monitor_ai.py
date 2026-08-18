#!/usr/bin/env python3
"""Monitor AI predictions from the backend."""
import requests
import time
from datetime import datetime

BACKEND_URL = "http://127.0.0.1:9090"

print("=" * 70)
print("   AquaFlow AI Inference Monitor")
print("=" * 70)
print("Monitoring AI predictions and confidence scores\n")

last_lstm_status = None

try:
    while True:
        try:
            resp = requests.get(f"{BACKEND_URL}/api/data", timeout=2)
            if resp.status_code == 200:
                data = resp.json()

                lstm_status = data.get('lstm_status')
                lstm_confidence = data.get('lstm_confidence', 0)
                lstm_probs = data.get('lstm_probs', {})

                if lstm_status and lstm_status != "WARMUP":
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    # Only print when status changes or every 10 seconds
                    if lstm_status != last_lstm_status:
                        print(f"\n[{timestamp}] AI Prediction: {lstm_status}")
                        print(f"Confidence: {lstm_confidence*100:.1f}%")

                        if lstm_probs:
                            print("  All probabilities:")
                            for label, prob in sorted(lstm_probs.items(), key=lambda x: x[1], reverse=True):
                                bar = "█" * int(prob * 20)
                                print(f"    {label:20} {prob*100:5.1f}% {bar}")

                        last_lstm_status = lstm_status
                elif lstm_status == "WARMUP":
                    window = data.get('lstm_probs', {}).get('window', 0)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] AI warming up... ({window}/30 samples)", end='\r')
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] AI not available (TensorFlow not installed)", end='\r')

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(2)

except KeyboardInterrupt:
    print("\n\nAI monitoring stopped.")
