from picamera2 import Picamera2
import cv2

# Initialize camera
picam2 = Picamera2()

# Configure camera
config = picam2.create_preview_configuration(
    main={
        "size": (640, 480),
        "format": "RGB888"
    }
)

picam2.configure(config)

# Start camera
picam2.start()

print("RIDEGUARD camera started!")
print("Press Q to quit.")

while True:
    # Capture frame
    frame = picam2.capture_array()

    # Convert RGB to BGR for OpenCV

    # Display frame
    cv2.imshow("RIDEGUARD Camera Test", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
picam2.stop()
