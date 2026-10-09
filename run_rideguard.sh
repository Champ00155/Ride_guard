#!/bin/bash

cd ~/RIDEGUARD

echo "================================"
echo "     STARTING RIDEGUARD"
echo "================================"

echo
echo "[1/2] Connecting to ESP32..."
./connect_esp32.sh

if [ ! -e /dev/rfcomm0 ]; then
    echo
    echo "ERROR: ESP32 Bluetooth connection failed."
    exit 1
fi

echo
echo "[2/2] Starting RIDEGUARD..."
echo

source .venv/bin/activate

python3 rideguard_fullv2.py
