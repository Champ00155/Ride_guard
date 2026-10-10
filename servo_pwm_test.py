#!/usr/bin/env python3
"""Stationary hardware-PWM servo test. Keep HC-SR04 mount clear."""
import platform, time
from rpi_hardware_pwm import HardwarePWM

CHANNEL = 2  # Pi 5 GPIO18 with pwm-2chan overlay
release = platform.release().split('-')[0]
version = tuple(int(part) for part in release.split('.')[:2])
chip = 0 if version >= (6, 12) else 2

def duty(angle):
    angle = max(-35, min(35, float(angle)))
    pulse_ms = 0.5 + ((angle + 90.0) / 180.0) * 2.0
    return pulse_ms / 20.0 * 100.0

pwm = HardwarePWM(pwm_channel=CHANNEL, hz=50, chip=chip)
try:
    pwm.start(duty(0))
    time.sleep(1)
    for angle in [-30, -20, -10, 0, 10, 20, 30, 20, 10, 0, -10, -20, -30, 0]:
        print(f'Servo angle target: {angle}°')
        pwm.change_duty_cycle(duty(angle))
        time.sleep(0.7)
finally:
    try:
        pwm.change_duty_cycle(duty(0))
        time.sleep(0.5)
        pwm.stop()
    except Exception:
        pass
    print('Servo PWM stopped.')
