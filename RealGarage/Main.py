from EntranceProcessor2 import EntranceSystem
import sys
sys.path.append(r'D:\python_packages')

entrance = EntranceSystem(
    source="car_clips/cars/car_2.mp4",
    car_model_path="Models/car_detection/yolov8m.pt",
    plate_detection_model_path="Models/plate_detection/best.pt",
    plate_recognition_model_path = "Models/plate_recognition/best.pt"
)

entrance.run()

# entrance = EntranceSystem(
#     source="rtsp://user:pass@ip:port/stream",
#     car_model_path="Models/car_detection/yolov8m.pt",
#     plate_detection_model_path="Models/plate_detection/best.pt",
#     plate_recognition_model_path="Models/plate_recognition/best.pt"
# )
#
# entrance.run()

