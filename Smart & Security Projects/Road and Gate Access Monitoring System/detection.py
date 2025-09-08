import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import pytesseract
import re
from datetime import datetime

model = YOLO('yolov8n.pt')  # Nano for Pi 4 efficiency

def init_camera():
    picam = Picamera2()
    config = picam.create_video_configuration(main={"size": (640, 480)})  # Low res for speed
    picam.configure(config)
    picam.start()
    return picam

def capture_frame(picam, low_light=False):
    frame = picam.capture_array()
    if low_light:
        # Night mode: Increase exposure (adjust as needed)
        picam.set_controls({"ExposureTime": 100000, "AnalogueGain": 8.0})
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

def extract_plate_number(image):
    results = model(image)
    for result in results:
        boxes = result.boxes
        for box in boxes:
            if int(box.cls) in [2, 3, 5, 7]:  # COCO classes: car, motorcycle, bus, truck
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # Geofencing: Only center ROI (e.g., 1/3 of frame)
                if x1 > image.shape[1]/3 and x2 < 2*image.shape[1]/3:
                    plate_region = image[y1:y2, x1:x2]
                    text = pytesseract.image_to_string(plate_region, config='--psm 8')
                    plate_number = re.sub(r'[^A-Z0-9]', '', text.strip())
                    if re.match(r'^[A-Z0-9]{5,8}$', plate_number):
                        # Classify type/color (stub; use box.cls for type, histogram for color)
                        car_type = 'Sedan' if int(box.cls) == 2 else 'Truck'
                        color = 'Red'  # Implement cv2 color detection
                        return plate_number, car_type, color
    return None, None, None

# Test: if __name__ == '__main__': picam = init_camera(); frame = capture_frame(picam); print(extract_plate_number(frame))
