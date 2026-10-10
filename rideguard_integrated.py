import os
import time
import cv2

from picamera2 import Picamera2
from ultralytics import YOLO
from radar_control_pwm import RadarController


# ============================================================
# RIDEGUARD - COMPLETE BLIND-SPOT AWARENESS SYSTEM
# ============================================================
#
# Raspberry Pi 5
#   ↓
# OV5647 Camera
#   ↓
# Picamera2
#   ↓
# YOLO11n
#   ↓
# Blind-spot detection
#   ↓
# Bluetooth RFCOMM
#   ↓
# ESP32
#   ↓
# LEFT  = GPIO14 + GPIO2
# RIGHT = GPIO4 + GPIO27
#
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

YOLO_SIZE = 416
CONFIDENCE = 0.40

# Number of consecutive frames required to confirm
# a blind-spot detection or clearance.
CONFIRM_FRAMES = 3

# Bluetooth serial device
RFCOMM_DEVICE = "/dev/rfcomm0"


# ============================================================
# VEHICLE CLASSES
# ============================================================
#
# COCO:
# 2 = car
# 3 = motorcycle
# 5 = bus
# 7 = truck
#

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


def radar_allows_physical_side(status, side):
    """Only allow a camera alert if that physical radar side is close and fresh."""
    data = status.get(side.lower(), {})
    return bool(data.get("threat") and data.get("valid") and not data.get("stale"))


# ============================================================
# HAPTIC STATE
# ============================================================

current_haptic = None


def send_haptic(command):
    """
    Send LEFT / RIGHT / BOTH / OFF to the ESP32.

    The same command is not repeatedly transmitted.
    """

    global current_haptic

    command = command.strip().upper()

    if command not in ("LEFT", "RIGHT", "BOTH", "OFF"):
        print(f"Invalid haptic command: {command}")
        return

    # Don't repeatedly send the same command
    if command == current_haptic:
        return

    # Check Bluetooth serial device
    if not os.path.exists(RFCOMM_DEVICE):

        print()
        print("WARNING:")
        print(f"{RFCOMM_DEVICE} was not found.")
        print("Run ./connect_esp32.sh")
        print()

        return

    try:

        with open(RFCOMM_DEVICE, "w") as bluetooth:

            bluetooth.write(command + "\n")
            bluetooth.flush()

        current_haptic = command

        print(f"HAPTIC -> {command}")

    except Exception as error:

        print(f"Bluetooth error: {error}")


# ============================================================
# BLIND-SPOT DETECTION
# ============================================================

def get_blindspot_side(cx, cy, width, height):

    """
    Determine whether the center of a vehicle
    is inside the left or right blind-spot region.

    Current prototype geometry:

        LEFT:
            x = 0% - 30%
            y = 55% - 100%

        RIGHT:
            x = 70% - 100%
            y = 55% - 100%

    These are temporary prototype ROIs.
    They can later be calibrated to the actual motorcycle.
    """

    left_limit = int(width * 0.30)

    right_limit = int(width * 0.70)

    y_limit = int(height * 0.55)


    # Vehicle must be in lower portion
    if cy < y_limit:
        return None


    # Camera faces backward: image-left is physical RIGHT.
    if cx < left_limit:
        return "RIGHT"

    # Image-right is physical LEFT.
    if cx > right_limit:
        return "LEFT"


    # Outside blind spots
    return None


# ============================================================
# DRAW BLIND-SPOT REGIONS
# ============================================================

def draw_blindspot_regions(frame):

    height, width = frame.shape[:2]


    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    left_x1 = 0
    left_x2 = int(width * 0.30)

    right_x1 = int(width * 0.70)
    right_x2 = width

    y1 = int(height * 0.55)
    y2 = height


    # --------------------------------------------------------
    # Transparent overlay
    # --------------------------------------------------------

    overlay = frame.copy()


    # Left region
    cv2.rectangle(
        overlay,
        (left_x1, y1),
        (left_x2, y2),
        (0, 0, 255),
        -1
    )


    # Right region
    cv2.rectangle(
        overlay,
        (right_x1, y1),
        (right_x2, y2),
        (0, 0, 255),
        -1
    )


    # Apply transparency
    frame = cv2.addWeighted(
        overlay,
        0.12,
        frame,
        0.88,
        0
    )


    # --------------------------------------------------------
    # Region borders
    # --------------------------------------------------------

    cv2.rectangle(
        frame,
        (left_x1, y1),
        (left_x2, y2),
        (0, 0, 255),
        2
    )

    cv2.rectangle(
        frame,
        (right_x1, y1),
        (right_x2, y2),
        (0, 0, 255),
        2
    )


    # --------------------------------------------------------
    # Region labels
    # --------------------------------------------------------

    cv2.putText(
        frame,
        "PHYSICAL RIGHT (IMAGE LEFT)",
        (15, y1 + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.60,
        (0, 0, 255),
        2
    )


    cv2.putText(
        frame,
        "PHYSICAL LEFT (IMAGE RIGHT)",
        (right_x1 + 5, y1 + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.60,
        (0, 0, 255),
        2
    )


    return frame


# ============================================================
# DRAW ALERT BANNER
# ============================================================

def draw_alert_banner(frame, side):
    """Draw the current physical-side alert, including simultaneous alerts."""
    height, width = frame.shape[:2]

    if side == "LEFT":
        message = "!!! LEFT BLIND SPOT ALERT !!!"
        color = (0, 0, 255)
    elif side == "RIGHT":
        message = "!!! RIGHT BLIND SPOT ALERT !!!"
        color = (0, 0, 255)
    elif side == "BOTH":
        message = "!!! LEFT + RIGHT BLIND SPOT ALERT !!!"
        color = (0, 0, 255)
    else:
        message = "BLIND SPOT CLEAR"
        color = (0, 255, 0)

    if side:
        cv2.rectangle(frame, (0, 0), (width, 48), color, -1)
        text_scale = 0.62 if side == "BOTH" else 0.72
        text_size = cv2.getTextSize(
            message, cv2.FONT_HERSHEY_SIMPLEX, text_scale, 2
        )[0]
        text_x = max(10, (width - text_size[0]) // 2)
        cv2.putText(
            frame, message, (text_x, 33),
            cv2.FONT_HERSHEY_SIMPLEX, text_scale, (255, 255, 255), 2
        )
    else:
        cv2.putText(
            frame, message, (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.72, color, 2
        )


# ============================================================
# MAIN
# ============================================================

def main():

    global current_haptic


    # ========================================================
    # STARTUP
    # ========================================================

    print()
    print("==========================================")
    print("           RIDEGUARD SYSTEM")
    print("==========================================")
    print("Camera       : OV5647")
    print("Resolution   :", f"{CAMERA_WIDTH}x{CAMERA_HEIGHT}")
    print("Model        : YOLO11n")
    print("YOLO size    :", YOLO_SIZE)
    print("Confidence   :", CONFIDENCE)
    print("Confirmation :", CONFIRM_FRAMES, "frames")
    print("Bluetooth    :", RFCOMM_DEVICE)
    print("==========================================")
    print()


    # ========================================================
    # CHECK BLUETOOTH
    # ========================================================

    if not os.path.exists(RFCOMM_DEVICE):

        print("ERROR: ESP32 Bluetooth connection not found.")
        print()
        print("Run:")
        print("    ./connect_esp32.sh")
        print()

        return


    print("Bluetooth connection: OK")

    radar = None
    picam2 = None
    try:
        print("Starting ultrasonic radar (hardware PWM)...")
        radar = RadarController()
        radar.start()
    except Exception as error:
        print("ERROR starting radar:", error)
        print("Check the pwm-2chan overlay, hardware PWM library, and GPIO wiring.")
        return

    # ========================================================
    # LOAD YOLO
    # ========================================================

    print("Loading YOLO11n...")

    try:

        model = YOLO("yolo11n.pt")

    except Exception as error:

        print()
        print("ERROR loading YOLO11n:")
        print(error)
        print()
        if radar is not None:
            radar.stop()
        return


    print("YOLO11n loaded.")


    # ========================================================
    # CAMERA
    # ========================================================

    print("Starting camera...")


    # Create OpenCV window BEFORE starting camera
    cv2.namedWindow(
        "RIDEGUARD",
        cv2.WINDOW_NORMAL
    )

    # Large display window.
    # This DOES NOT change camera or YOLO resolution.
    cv2.resizeWindow(
        "RIDEGUARD",
        960,
        720
    )


    # Initialize camera
    picam2 = Picamera2()


    camera_config = picam2.create_preview_configuration(

        main={
            "size": (
                CAMERA_WIDTH,
                CAMERA_HEIGHT
            ),
            "format": "RGB888"
        }

    )


    picam2.configure(camera_config)


    # Start camera
    picam2.start()


    # Give camera time to initialize
    time.sleep(2)


    print("Camera started.")
    print()
    print("==========================================")
    print("          RIDEGUARD ACTIVE")
    print("==========================================")
    print("Press Q to stop.")
    print()


    # ========================================================
    # TEMPORAL CONFIRMATION - TRACK EACH PHYSICAL SIDE INDEPENDENTLY
    # ========================================================

    side_confirmation = {
        "LEFT": {"candidate_count": 0, "confirmed": False},
        "RIGHT": {"candidate_count": 0, "confirmed": False},
    }


    # ========================================================
    # FPS
    # ========================================================

    fps_start = time.time()

    fps_frames = 0

    fps = 0.0


    # ========================================================
    # MAIN LOOP
    # ========================================================

    try:

        while True:


            # ------------------------------------------------
            # Capture camera frame
            # ------------------------------------------------

            frame = picam2.capture_array()


            # ------------------------------------------------
            # YOLO inference
            # ------------------------------------------------

            results = model.predict(

                frame,

                imgsz=YOLO_SIZE,

                conf=CONFIDENCE,

                classes=list(
                    VEHICLE_CLASSES.keys()
                ),

                verbose=False
            )


            result = results[0]
            radar_status = radar.get_status() if radar is not None else {}

            # ------------------------------------------------
            # Draw blind-spot regions
            # ------------------------------------------------

            display = draw_blindspot_regions(
                frame.copy()
            )


            # ------------------------------------------------
            # Find blind-spot vehicles
            # ------------------------------------------------

            blindspot_candidates = []


            if result.boxes is not None:


                for box in result.boxes:


                    # ----------------------------------------
                    # Class
                    # ----------------------------------------

                    cls_id = int(
                        box.cls[0].item()
                    )


                    # ----------------------------------------
                    # Confidence
                    # ----------------------------------------

                    confidence = float(
                        box.conf[0].item()
                    )


                    # ----------------------------------------
                    # Bounding box
                    # ----------------------------------------

                    x1, y1, x2, y2 = (

                        box.xyxy[0]
                        .cpu()
                        .numpy()
                        .astype(int)

                    )


                    # ----------------------------------------
                    # Bounding box center
                    # ----------------------------------------

                    cx = int(
                        (x1 + x2) / 2
                    )

                    cy = int(
                        (y1 + y2) / 2
                    )


                    # ----------------------------------------
                    # Vehicle name
                    # ----------------------------------------

                    vehicle_name = VEHICLE_CLASSES.get(
                        cls_id,
                        "vehicle"
                    )


                    # ----------------------------------------
                    # Blind-spot side
                    # ----------------------------------------

                    side = get_blindspot_side(

                        cx,
                        cy,

                        CAMERA_WIDTH,
                        CAMERA_HEIGHT
                    )


                    # ----------------------------------------
                    # Blind-spot vehicle
                    # ----------------------------------------

                    if side is not None:

                        box_color = (
                            0,
                            0,
                            255
                        )


                        label = (
                            f"BLIND SPOT: "
                            f"{vehicle_name} "
                            f"{confidence:.2f}"
                        )


                        blindspot_candidates.append(

                            (
                                side,
                                confidence,
                                vehicle_name
                            )

                        )


                    # ----------------------------------------
                    # Normal vehicle
                    # ----------------------------------------

                    else:

                        box_color = (
                            0,
                            255,
                            0
                        )


                        label = (
                            f"{vehicle_name} "
                            f"{confidence:.2f}"
                        )


                    # ----------------------------------------
                    # Bounding box
                    # ----------------------------------------

                    cv2.rectangle(

                        display,

                        (x1, y1),

                        (x2, y2),

                        box_color,

                        2
                    )


                    # ----------------------------------------
                    # Label
                    # ----------------------------------------

                    cv2.putText(

                        display,

                        label,

                        (
                            x1,
                            max(
                                25,
                                y1 - 8
                            )
                        ),

                        cv2.FONT_HERSHEY_SIMPLEX,

                        0.50,

                        box_color,

                        2
                    )


                    # ----------------------------------------
                    # Center point
                    # ----------------------------------------

                    cv2.circle(

                        display,

                        (cx, cy),

                        5,

                        box_color,

                        -1
                    )


            # =================================================
            # DETECT AND CONFIRM EACH PHYSICAL SIDE INDEPENDENTLY
            # =================================================

            detected_sides = {
                item[0] for item in blindspot_candidates
                if item[0] in ("LEFT", "RIGHT")
            }

            for side in ("LEFT", "RIGHT"):
                state = side_confirmation[side]

                if side in detected_sides:
                    state["candidate_count"] += 1
                    if state["candidate_count"] >= CONFIRM_FRAMES:
                        state["confirmed"] = True
                else:
                    # Require consecutive detections.
                    state["candidate_count"] = 0
                    state["confirmed"] = False

            # Radar authorization is independent for each physical side.
            left_alert = (
                side_confirmation["LEFT"]["confirmed"]
                and radar_allows_physical_side(radar_status, "left")
            )
            right_alert = (
                side_confirmation["RIGHT"]["confirmed"]
                and radar_allows_physical_side(radar_status, "right")
            )

            if left_alert and right_alert:
                active_alert = "BOTH"
            elif left_alert:
                active_alert = "LEFT"
            elif right_alert:
                active_alert = "RIGHT"
            else:
                active_alert = None

            send_haptic(active_alert if active_alert is not None else "OFF")
            draw_alert_banner(display, active_alert)

            # Radar diagnostics (distances in centimetres).
            left_data = radar_status.get("left", {})
            right_data = radar_status.get("right", {})
            def radar_text(data):
                if data.get("stale") or not data.get("valid") or data.get("distance_cm") is None:
                    return "Unknown"
                return f"{data['distance_cm']:.1f}cm" + (" THREAT" if data.get("threat") else "")
            cv2.putText(display, f"RADAR Physical LEFT: {radar_text(left_data)}", (10, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 2)
            cv2.putText(display, f"RADAR Physical RIGHT: {radar_text(right_data)}", (10, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 2)


            # =================================================
            # HAPTIC STATUS
            # =================================================

            cv2.putText(

                display,

                f"HAPTIC: {current_haptic}",

                (
                    10,
                    CAMERA_HEIGHT - 40
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.60,

                (255, 255, 255),

                2
            )


            # =================================================
            # FPS
            # =================================================

            fps_frames += 1


            elapsed = (
                time.time()
                - fps_start
            )


            if elapsed >= 1.0:


                fps = (
                    fps_frames
                    / elapsed
                )


                fps_frames = 0

                fps_start = time.time()


            cv2.putText(

                display,

                f"FPS: {fps:.1f}",

                (
                    CAMERA_WIDTH - 120,
                    CAMERA_HEIGHT - 15
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                (255, 255, 255),

                2
            )


            # =================================================
            # DISPLAY CAMERA
            # =================================================

            cv2.imshow(

                "RIDEGUARD",

                display
            )


            # =================================================
            # KEYBOARD
            # =================================================

            key = (
                cv2.waitKey(1)
                & 0xFF
            )


            if key == ord("q"):

                break


    # ========================================================
    # CTRL+C
    # ========================================================

    except KeyboardInterrupt:

        print()
        print("Stopping RIDEGUARD...")


    # ========================================================
    # CLEANUP
    # ========================================================

    finally:


        print()
        print("Shutting down...")


        # ALWAYS turn motors OFF
        try:
            # Force OFF transmission even if the last command was already OFF.
            current_haptic = None
            send_haptic("OFF")
        except Exception:
            pass

        # Stop camera
        try:

            picam2.stop()

        except Exception:

            pass


        # Stop radar worker and release servo/sensor GPIO.
        try:
            if radar is not None:
                radar.stop()
        except Exception as error:
            print("Radar shutdown warning:", error)

        # Close OpenCV
        cv2.destroyAllWindows()


        print("HAPTIC: OFF")
        print("Camera stopped.")
        print("RIDEGUARD stopped.")
        print()


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
