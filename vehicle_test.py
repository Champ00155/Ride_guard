from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import time

# -----------------------------
# Load YOLO model
# -----------------------------
model = YOLO("yolo11n.pt")

# -----------------------------
# Initialize camera
# -----------------------------
picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={
        "size": (640, 480),
        "format": "RGB888"
    }
)

picam2.configure(config)
picam2.start()

print("RIDEGUARD vehicle detection started!")
print("Press Q to quit.")

# FPS calculation
prev_time = time.time()

while True:

    # Capture frame
    frame = picam2.capture_array()

    # YOLO detection
    results = model(
        frame,
        imgsz=640,
        conf=0.4,
        verbose=False
    )

    # Draw detections
    annotated_frame = results[0].plot()

    # Calculate FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    cv2.putText(
        annotated_frame,
        f"FPS: {fps:.1f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    # Show frame
    cv2.imshow(
        "RIDEGUARD - Vehicle Detection",
        annotated_frame
    )

    # Quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
picam2.stop()
