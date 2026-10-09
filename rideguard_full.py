import os
import time
import cv2

from picamera2 import Picamera2
from ultralytics import YOLO


# ============================================================
# RIDEGUARD CONFIGURATION
# ============================================================

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

YOLO_SIZE = 416
CONFIDENCE = 0.40

# Number of consecutive frames required before changing haptic state
CONFIRM_FRAMES = 3

# Bluetooth RFCOMM device
RFCOMM_DEVICE = "/dev/rfcomm0"


# ============================================================
# VEHICLE CLASSES
# ============================================================

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


# ============================================================
# HAPTIC CONTROL
# ============================================================

current_haptic = "OFF"


def send_haptic(command):
    """
    Send LEFT / RIGHT / OFF to the ESP32.

    A command is only transmitted when the haptic state changes.
    """

    global current_haptic

    command = command.upper()

    if command not in ("LEFT", "RIGHT", "OFF"):
        return

    # Don't repeatedly transmit the same command
    if command == current_haptic:
        return

    if not os.path.exists(RFCOMM_DEVICE):
        print("WARNING: /dev/rfcomm0 not found.")
        print("Run ./connect_esp32.sh first.")
        return

    try:

        with open(RFCOMM_DEVICE, "w") as bluetooth:

            bluetooth.write(command + "\n")
            bluetooth.flush()

        current_haptic = command

        print(f"HAPTIC -> {command}")

    except Exception as e:

        print(f"Bluetooth error: {e}")


# ============================================================
# BLIND-SPOT LOGIC
# ============================================================

def get_blindspot_side(cx, cy, width, height):
    """
    Determine whether the center of a detected vehicle
    is inside the temporary left/right blind-spot regions.

    Current prototype regions:

    LEFT:
        x = 0% to 30%
        y = 55% to 100%

    RIGHT:
        x = 70% to 100%
        y = 55% to 100%
    """

    left_limit = int(width * 0.30)
    right_limit = int(width * 0.70)
    y_limit = int(height * 0.55)

    # Vehicle must be in the lower portion of the image
    if cy < y_limit:
        return None

    if cx < left_limit:
        return "LEFT"

    if cx > right_limit:
        return "RIGHT"

    return None


# ============================================================
# DRAW BLIND-SPOT REGIONS
# ============================================================

def draw_blindspot_regions(frame):

    height, width = frame.shape[:2]

    left_x1 = 0
    left_x2 = int(width * 0.30)

    right_x1 = int(width * 0.70)
    right_x2 = width

    y1 = int(height * 0.55)
    y2 = height

    # Temporary prototype blind-spot regions
    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (left_x1, y1),
        (left_x2, y2),
        (0, 0, 255),
        -1
    )

    cv2.rectangle(
        overlay,
        (right_x1, y1),
        (right_x2, y2),
        (0, 0, 255),
        -1
    )

    # Make the regions transparent
    frame = cv2.addWeighted(
        overlay,
        0.12,
        frame,
        0.88,
        0
    )

    # Region borders
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

    # Labels
    cv2.putText(
        frame,
        "LEFT BLIND SPOT",
        (20, y1 + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 0, 255),
        2
    )

    cv2.putText(
        frame,
        "RIGHT BLIND SPOT",
        (right_x1 + 10, y1 + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 0, 255),
        2
    )

    return frame


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print()
    print("==========================================")
    print("           RIDEGUARD SYSTEM")
    print("==========================================")
    print("Camera: OV5647")
    print("Model: YOLO11n")
    print("Image size:", YOLO_SIZE)
    print("Confidence:", CONFIDENCE)
    print("Bluetooth:", RFCOMM_DEVICE)
    print("==========================================")
    print()

    # --------------------------------------------------------
    # Check Bluetooth connection
    # --------------------------------------------------------

    if not os.path.exists(RFCOMM_DEVICE):

        print("ERROR: Bluetooth serial device not found:")
        print(RFCOMM_DEVICE)
        print()
        print("Run:")
        print("./connect_esp32.sh")
        print()

        return

    print("Bluetooth connection: OK")


    # --------------------------------------------------------
    # Load YOLO
    # --------------------------------------------------------

    print("Loading YOLO11n...")

    model = YOLO("yolo11n.pt")

    print("YOLO11n loaded.")


    # --------------------------------------------------------
    # Camera setup
    # --------------------------------------------------------

    print("Starting camera...")

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

    picam2.start()

    time.sleep(2)

    print("Camera started.")
    print()
    print("RIDEGUARD ACTIVE")
    print("Press Q to quit.")
    print()


    # --------------------------------------------------------
    # Temporal confirmation state
    # --------------------------------------------------------

    candidate_side = None
    candidate_count = 0

    confirmed_side = None

    absent_count = 0


    # --------------------------------------------------------
    # FPS
    # --------------------------------------------------------

    fps_start = time.time()
    fps_frames = 0
    fps = 0.0


    try:

        while True:

            # ------------------------------------------------
            # Capture frame
            # ------------------------------------------------

            frame = picam2.capture_array()


            # ------------------------------------------------
            # YOLO inference
            # ------------------------------------------------

            results = model.predict(
                frame,
                imgsz=YOLO_SIZE,
                conf=CONFIDENCE,
                classes=list(VEHICLE_CLASSES.keys()),
                verbose=False
            )


            result = results[0]


            # ------------------------------------------------
            # Draw blind-spot regions
            # ------------------------------------------------

            display = draw_blindspot_regions(frame.copy())


            # ------------------------------------------------
            # Find vehicles in blind spots
            # ------------------------------------------------

            blindspot_candidates = []


            if result.boxes is not None:

                for box in result.boxes:

                    cls_id = int(
                        box.cls[0].item()
                    )

                    confidence = float(
                        box.conf[0].item()
                    )

                    x1, y1, x2, y2 = (
                        box.xyxy[0]
                        .cpu()
                        .numpy()
                        .astype(int)
                    )

                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)


                    vehicle_name = VEHICLE_CLASSES.get(
                        cls_id,
                        "vehicle"
                    )


                    # Determine blind-spot side
                    side = get_blindspot_side(
                        cx,
                        cy,
                        CAMERA_WIDTH,
                        CAMERA_HEIGHT
                    )


                    # ----------------------------------------
                    # Detection box
                    # ----------------------------------------

                    if side is not None:

                        # Blind-spot vehicle
                        box_color = (0, 0, 255)

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

                    else:

                        # Normal vehicle
                        box_color = (0, 255, 0)

                        label = (
                            f"{vehicle_name} "
                            f"{confidence:.2f}"
                        )


                    cv2.rectangle(
                        display,
                        (x1, y1),
                        (x2, y2),
                        box_color,
                        2
                    )


                    cv2.putText(
                        display,
                        label,
                        (x1, max(25, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.50,
                        box_color,
                        2
                    )


                    # Center point
                    cv2.circle(
                        display,
                        (cx, cy),
                        5,
                        box_color,
                        -1
                    )


            # ------------------------------------------------
            # Decide which side is currently dangerous
            # ------------------------------------------------

            detected_side = None


            if blindspot_candidates:

                # If both sides contain vehicles,
                # choose the strongest detection.
                strongest = max(
                    blindspot_candidates,
                    key=lambda item: item[1]
                )

                detected_side = strongest[0]


            # ------------------------------------------------
            # TEMPORAL CONFIRMATION
            # ------------------------------------------------

            if detected_side is not None:

                # A blind-spot vehicle exists
                absent_count = 0


                if detected_side == candidate_side:

                    candidate_count += 1

                else:

                    candidate_side = detected_side
                    candidate_count = 1


                # Confirm after required number of frames
                if candidate_count >= CONFIRM_FRAMES:

                    if confirmed_side != candidate_side:

                        confirmed_side = candidate_side

                        if confirmed_side == "LEFT":

                            send_haptic("LEFT")

                        elif confirmed_side == "RIGHT":

                            send_haptic("RIGHT")


            else:

                # No blind-spot vehicle
                candidate_side = None
                candidate_count = 0

                absent_count += 1


                # Turn motors OFF after confirmation
                # that the blind spot is clear.
                if absent_count >= CONFIRM_FRAMES:

                    if confirmed_side is not None:

                        confirmed_side = None
                        send_haptic("OFF")


            # ------------------------------------------------
            # Alert banner
            # ------------------------------------------------

            if confirmed_side == "LEFT":

                cv2.rectangle(
                    display,
                    (0, 0),
                    (CAMERA_WIDTH, 45),
                    (0, 0, 255),
                    -1
                )

                cv2.putText(
                    display,
                    "!!! LEFT BLIND SPOT ALERT !!!",
                    (70, 31),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (255, 255, 255),
                    2
                )


            elif confirmed_side == "RIGHT":

                cv2.rectangle(
                    display,
                    (0, 0),
                    (CAMERA_WIDTH, 45),
                    (0, 0, 255),
                    -1
                )

                cv2.putText(
                    display,
                    "!!! RIGHT BLIND SPOT ALERT !!!",
                    (65, 31),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (255, 255, 255),
                    2
                )


            else:

                cv2.putText(
                    display,
                    "BLIND SPOT CLEAR",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 0),
                    2
                )


            # ------------------------------------------------
            # Haptic status
            # ------------------------------------------------

            cv2.putText(
                display,
                f"HAPTIC: {current_haptic}",
                (10, CAMERA_HEIGHT - 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                (255, 255, 255),
                2
            )


            # ------------------------------------------------
            # FPS
            # ------------------------------------------------

            fps_frames += 1

            elapsed = time.time() - fps_start

            if elapsed >= 1.0:

                fps = fps_frames / elapsed

                fps_frames = 0
                fps_start = time.time()


            cv2.putText(
                display,
                f"FPS: {fps:.1f}",
                (CAMERA_WIDTH - 120, CAMERA_HEIGHT - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )


            # ------------------------------------------------
            # Display
            # ------------------------------------------------

            cv2.imshow(
                "RIDEGUARD",
                display
            )


            # ------------------------------------------------
            # Quit
            # ------------------------------------------------

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):

                break


    except KeyboardInterrupt:

        print()
        print("Stopping RIDEGUARD...")


    finally:

        # ALWAYS turn motors OFF
        try:
            send_haptic("OFF")
        except Exception:
            pass

        picam2.stop()

        cv2.destroyAllWindows()

        print()
        print("RIDEGUARD stopped.")
        print("Haptic: OFF")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
