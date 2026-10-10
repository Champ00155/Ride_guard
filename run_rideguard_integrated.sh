#!/bin/bash
set -e
cd "$HOME/RIDEGUARD"
echo "========================================"
echo " RIDEGUARD - CAMERA + RADAR + HAPTICS"
echo "========================================"
echo "[1/3] Connecting ESP32 RFCOMM..."
./connect_esp32.sh
if [ ! -e /dev/rfcomm0 ]; then
  echo "ERROR: /dev/rfcomm0 is missing. Bluetooth connection failed."
  exit 1
fi
echo "[2/3] Activating Python environment..."
source .venv/bin/activate
echo "[3/3] Starting integrated application..."
exec python3 -u rideguard_integrated.py
