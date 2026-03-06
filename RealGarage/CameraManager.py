import cv2
import time

from EntranceProcessor2 import EntranceSystem


class CameraManager:
    def __init__(self, src, camera_id, reconnect_delay=5):
        self.src = src
        self.camera_id = camera_id
        self.reconnect_delay = reconnect_delay
        self.cap = None

    def connect(self):
        print(f"🎥 Connecting to camera {self.camera_id}")
        self.cap = cv2.VideoCapture(self.src)

        if not self.cap.isOpened():
            print("❌ Camera not opened")
            self.cap = None

    def get_frame(self):
        if self.cap is None or not self.cap.isOpened():
            self.connect()
            time.sleep(self.reconnect_delay)
            return None

        ret, frame = self.cap.read()
        if not ret:
            print("Frame failed, reconnecting...")
            self.cap.release()
            self.cap = None
            return None

        return frame

    def release(self):
        if self.cap:
            self.cap.release()

entrance_cam = CameraManager(
    "rtsp://entrance_cam",
    camera_id="ENTRANCE_CAM"
)

exit_cam = CameraManager(
    "rtsp://exit_cam",
    camera_id="EXIT_CAM"
)

entrance_system = EntranceSystem(manager=entrance_cam,
                                 car_model_path="Models/car_detection/yolov8m.pt",
                                 plate_detection_model_path="Models/plate_detection/best.pt",
                                 plate_recognition_model_path="Models/plate_recognition/best.pt"
                                 )
entrance_system.run()
