from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import time

# ============================================================
# SETTINGS
# ============================================================

MODEL = "yolo11n.pt"

# Vehicle classes from COCO / YOLO
VEHICLE_CLASSES = {
    2: "CAR",
    3: "MOTORCYCLE",
    5: "BUS",
    7: "TRUCK"
}

CONFIDENCE = 0.4

# ============================================================
# LOAD YOLO
# ============================================================

model = YOLO(MODEL)

# ============================================================
# CAMERA
# ============================================================

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={
        "size": (640, 480),
        "format": "RGB888"
    }
)

picam2.configure(config)
picam2.start()

print("RIDEGUARD Blind-Spot Detection")
print("Press Q to quit.")

# ============================================================
# MAIN LOOP
# ============================================================

previous_time = time.time()

while True:

    frame = picam2.capture_array()

    height, width = frame.shape[:2]

    # --------------------------------------------------------
    # Define blind spots
    # --------------------------------------------------------

    # Left blind spot
    left_x1 = 0
    left_x2 = int(width * 0.30)

    # Right blind spot
    right_x1 = int(width * 0.70)
    right_x2 = width

    # Start blind spots around lower 55% of image
    roi_y1 = int(height * 0.55)
    roi_y2 = height

    # --------------------------------------------------------
    # Draw blind-spot regions
    # --------------------------------------------------------

    cv2.rectangle(
        frame,
        (left_x1, roi_y1),
        (left_x2, roi_y2),
        (0, 255, 255),
        2
    )

    cv2.rectangle(
        frame,
        (right_x1, roi_y1),
        (right_x2, roi_y2),
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "LEFT BLIND SPOT",
        (10, roi_y1 + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "RIGHT BLIND SPOT",
        (right_x1 + 5, roi_y1 + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2
    )

    # --------------------------------------------------------
    # YOLO
    # --------------------------------------------------------

    results = model(
        frame,
        imgsz=416,
        conf=CONFIDENCE,
	classes=[2,3,5,7],
        verbose=False
    )

    alert = False

    # --------------------------------------------------------
    # Process detections
    # --------------------------------------------------------

    for box in results[0].boxes:

        class_id = int(box.cls[0])

        # Ignore people and other objects
        if class_id not in VEHICLE_CLASSES:
            continue

        confidence = float(box.conf[0])

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )

        # Bounding-box center
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        vehicle_name = VEHICLE_CLASSES[class_id]

        # ----------------------------------------------------
        # Is vehicle inside left/right blind spot?
        # ----------------------------------------------------

        in_left_blindspot = (
            left_x1 <= center_x <= left_x2
            and roi_y1 <= center_y <= roi_y2
        )

        in_right_blindspot = (
            right_x1 <= center_x <= right_x2
            and roi_y1 <= center_y <= roi_y2
        )

        in_blindspot = (
            in_left_blindspot or
            in_right_blindspot
        )

        # ----------------------------------------------------
        # Draw vehicle
        # ----------------------------------------------------

        if in_blindspot:

            alert = True

            box_color = (0, 0, 255)

            label = f"BLIND SPOT: {vehicle_name}"

        else:

            box_color = (0, 255, 0)

            label = f"{vehicle_name} {confidence:.2f}"

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            box_color,
            2
        )

        cv2.circle(
            frame,
            (center_x, center_y),
            5,
            box_color,
            -1
        )

        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            box_color,
            2
        )

    # ========================================================
    # ALERT
    # ========================================================

    if alert:

        cv2.rectangle(
            frame,
            (0, 0),
            (width, 55),
            (0, 0, 255),
            -1
        )

        cv2.putText(
            frame,
            "!!! BLIND SPOT ALERT !!!",
            (90, 37),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2
        )

    else:

        cv2.putText(
            frame,
            "SAFE",
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

    # ========================================================
    # FPS
    # ========================================================

    current_time = time.time()

    fps = 1 / (current_time - previous_time)

    previous_time = current_time

    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (width - 110, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # ========================================================
    # DISPLAY
    # ========================================================

    cv2.imshow(
        "RIDEGUARD - Blind Spot Detection",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ============================================================
# CLEANUP
# ============================================================

cv2.destroyAllWindows()
picam2.stop()
