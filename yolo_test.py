from ultralytics import YOLO

# Load lightweight YOLO model
model = YOLO("yolo11n.pt")

print("YOLO model loaded!")
print("Model classes:")
print(model.names)

# Test the model on a sample image
results = model.predict(
    source="https://ultralytics.com/images/bus.jpg",
    imgsz=640,
    conf=0.4,
    save=True
)

print("Detection completed!")
