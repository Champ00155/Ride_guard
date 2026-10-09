#!/bin/bash

ESP32_MAC="8C:94:DF:6D:D0:9A"
RFCOMM_DEVICE="/dev/rfcomm0"
CHANNEL="1"

echo "================================"
echo " RIDEGUARD ESP32 CONNECTION"
echo "================================"

# If the RFCOMM device already exists, use it
if [ -e "$RFCOMM_DEVICE" ]; then
    echo "Bluetooth connection already exists."
    echo "Using $RFCOMM_DEVICE"
    exit 0
fi

echo "Connecting to RIDEGUARD-ESP32..."
echo "MAC: $ESP32_MAC"
echo "RFCOMM channel: $CHANNEL"

sudo rfcomm bind "$RFCOMM_DEVICE" "$ESP32_MAC" "$CHANNEL"

if [ -e "$RFCOMM_DEVICE" ]; then
    echo
    echo "SUCCESS!"
    echo "Bluetooth serial device:"
    echo "$RFCOMM_DEVICE"
else
    echo
    echo "ERROR: Could not create $RFCOMM_DEVICE"
    exit 1
fi
