RIDEGUARD INTEGRATED BUILD — SETUP NOTES
========================================

This bundle leaves rideguard_fullv2.py unchanged and adds:
- rideguard_integrated.py: original V2 camera/YOLO/hitbox pipeline with radar gating
- radar_control_pwm.py: HC-SR04 sweep and hardware PWM servo control
- servo_pwm_test.py: test servo separately before the integrated app
- run_rideguard_integrated.sh: connects ESP32 and launches the integrated app
- connect_esp32.sh: your existing Bluetooth RFCOMM script

IMPORTANT: The existing camera hitbox geometry is preserved (x<30%, x>70%, y>=55%).
Since the camera faces backward, the physical-side mapping is inverted in the integrated
code: image-left -> physical RIGHT; image-right -> physical LEFT. Radar side mapping
assumes negative servo angles physically point left and positive angles physically point
right. Verify this with the mounted sensor while stationary.

THREAT DISTANCE
---------------
THREAT_DISTANCE_CM is 25.0 cm (not 25 metres), matching the current code and the
normal HC-SR04 range. A single HC-SR04 measures reflecting surfaces, not vehicle identity.
Camera vehicle detection AND radar threat are both required for vibration.

SERVO HARDWARE PWM — RASPBERRY PI 5
----------------------------------
The old code used gpiozero AngularServo with LGPIOFactory, which emitted
PWMSoftwareFallback and jittered. This build uses rpi-hardware-pwm on GPIO18.

1. Inspect the current boot config before editing:
   grep -n 'pwm-2chan' /boot/firmware/config.txt
2. Back up config:
   sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.rideguard-backup
3. Add this line ONCE at the end of /boot/firmware/config.txt:
   dtoverlay=pwm-2chan
   Do not add a duplicate if it already exists. If other hardware uses PWM0/PWM1,
   stop and inspect config before proceeding.
4. Install the library in the project's venv:
   cd ~/RIDEGUARD
   source .venv/bin/activate
   pip install rpi-hardware-pwm
5. Reboot:
   sudo reboot
6. Verify PWM is exposed:
   ls -l /sys/class/pwm/
   grep -n 'pwm-2chan' /boot/firmware/config.txt
7. Test servo alone first:
   cd ~/RIDEGUARD
   source .venv/bin/activate
   python3 servo_pwm_test.py

GPIO wiring (as currently reported):
- Servo signal -> BCM GPIO18 / physical pin 12
- Servo V+ -> physical pin 2 (5V), GND -> physical pin 14
- HC-SR04 TRIG -> BCM GPIO23 / physical pin 16
- HC-SR04 ECHO -> BCM GPIO24 / physical pin 18 THROUGH A VOLTAGE DIVIDER
- HC-SR04 VCC -> physical pin 4 (5V), GND -> physical pin 20
Never connect HC-SR04 5V ECHO directly to a Pi GPIO.

The PWM signal timing is hardware-generated, but power/mechanical issues can still
cause jitter. An SG90 plus sensor can draw current spikes; if the Pi browns out or the
servo twitches under load, a separate regulated 5V servo supply with common ground is
more reliable than powering the servo from the Pi. Do not exceed the Pi's available
power budget. Keep the mount light and stop if the servo heats up.

INSTALL INTO EXISTING ~/RIDEGUARD
---------------------------------
Extract this bundle on your Pi or copy the files into ~/RIDEGUARD. Keep the original
rideguard_fullv2.py, radar_control.py, and run_rideguard.sh as backups. Do not overwrite
them with these new files. Make the new launcher executable:
   chmod +x ~/RIDEGUARD/run_rideguard_integrated.sh

Then run the servo-only test FIRST. If it moves smoothly and the sensor mount clears
all objects, run the integrated app:
   ~/RIDEGUARD/run_rideguard_integrated.sh

The integrated app preserves V2's YOLO model settings (640x480 camera, imgsz=416,
confidence 0.40, vehicle classes car/motorcycle/bus/truck, 3-frame confirmation).
A camera alert only causes LEFT/RIGHT vibration when that physical radar side has a
fresh <=25 cm reading. Radar proximity uses one sweep; camera still requires three frames. On shutdown, the app attempts to send OFF and stop
radar hardware.

This is a prototype; do not rely on it as a sole road-safety device. Validate it while
stationary with known objects at measured distances before road use.
