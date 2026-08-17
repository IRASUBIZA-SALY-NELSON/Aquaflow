#!/usr/bin/env bash
# Flash AquaFlow ESP32 firmware via arduino-cli
set -euo pipefail
export PATH="/usr/local/bin:$PATH"
SKETCH_DIR="$(cd "$(dirname "$0")/../firmware/aquaflow_esp32" && pwd)"
FQBN="${FQBN:-esp32:esp32:esp32}"
PORT="${1:-}"

if [[ -z "$PORT" ]]; then
  echo "Detecting serial ports..."
  /usr/local/bin/arduino-cli board list || true
  for p in /dev/ttyUSB0 /dev/ttyACM0 /dev/ttyUSB1 /dev/ttyACM1; do
    if [[ -e "$p" ]]; then PORT="$p"; break; fi
  done
fi

if [[ -z "${PORT}" || ! -e "${PORT}" ]]; then
  echo "ERROR: No ESP32 serial port found."
  echo "Plug the ESP32 via USB, then run:"
  echo "  bash scripts/flash_esp32.sh /dev/ttyUSB0"
  exit 1
fi

echo "Compiling $SKETCH_DIR for $FQBN ..."
arduino-cli compile --fqbn "$FQBN" "$SKETCH_DIR"
echo "Uploading to $PORT ..."
arduino-cli upload -p "$PORT" --fqbn "$FQBN" "$SKETCH_DIR"
echo "Flash OK. Opening serial monitor @115200 (Ctrl+C to exit)"
arduino-cli monitor -p "$PORT" -c baudrate=115200
