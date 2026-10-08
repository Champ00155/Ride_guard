# RIDEGUARD

## Affordable AI-Based Blind Spot Awareness System for Two-Wheelers

RIDEGUARD is an AI-based blind-spot awareness prototype designed to improve rider safety on existing two-wheelers.

The system uses a Raspberry Pi 5 and Raspberry Pi Camera Module Rev 1.3 (OV5647) to detect nearby vehicles using YOLO11n and determine whether a detected vehicle is inside a defined blind-spot region.

When a vehicle remains in the blind spot for multiple consecutive frames, the system generates a blind-spot alert. A vibration motor will be used as the physical rider alert.

## Team

**Team Name:** Jaegers

**Project:** RIDEGUARD

## Current Hardware

- Raspberry Pi 5 8GB
- Raspberry Pi Camera Module Rev 1.3
- OV5647 camera sensor
- Vibration motor

## Software

- Python
- OpenCV
- Picamera2
- Ultralytics YOLO11n

## Current Detection Pipeline

Camera
↓
Picamera2
↓
OpenCV
↓
YOLO11n
↓
Vehicle Detection
↓
Blind Spot Region
↓
Temporal Confirmation
↓
Rider Alert

## Detected Vehicles

The current prototype detects:

- Car
- Motorcycle
- Bus
- Truck

## Current Blind Spot Logic

The prototype currently uses temporary image-based blind-spot regions.

A vehicle must remain inside the blind-spot region for three consecutive detection frames before the alert is confirmed.

The blind-spot regions will be calibrated after the camera is mounted on the target two-wheeler.

## Project Status

### Completed

- Raspberry Pi 5 setup
- OV5647 camera configuration
- Camera streaming through Picamera2
- OpenCV integration
- YOLO11n installation
- Live vehicle detection
- Blind-spot region detection
- Three-frame temporal confirmation

### In Progress

- Vibration motor integration
- Physical alert testing
- Camera placement and blind-spot calibration
- Final prototype integration

## Disclaimer

This repository contains a hackathon prototype. Blind-spot regions and detection behavior are experimental and require physical calibration and testing before any real-world safety-critical use.
