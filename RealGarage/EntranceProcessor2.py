import cv2
import time
import os
import numpy as np
from ultralytics import YOLO
from APIClient import APIClient


class EntranceSystem:

    def __init__(self, source,
                 car_model_path,
                 plate_detection_model_path,
                 plate_recognition_model_path,
                 save_dir="captures"):

        self.cap = cv2.VideoCapture(source)

        self.car_model = YOLO(car_model_path)
        self.plate_model = YOLO(plate_detection_model_path)
        self.plate_recognition = YOLO(plate_recognition_model_path)
        self.capture_delay = {}
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

        self.processed_ids = set()
        self.previous_side = {}

        self.api = APIClient("backend_url")

        cv2.namedWindow("Entrance System", cv2.WINDOW_NORMAL)

    # =============================
    # Save Car
    # =============================
    def save_car(self, car_crop, track_id):
        if car_crop is None or car_crop.size == 0:
            return None

        filename = f"{self.save_dir}/car_{track_id}_{int(time.time())}.jpg"
        cv2.imwrite(filename, car_crop)
        print("Saved:", filename)
        return filename

    # =============================
    # Plate Detection
    # =============================
    def detect_and_draw_plate(self, frame):

        plate_results = self.plate_model(frame, verbose=False)

        for r in plate_results:
            for box in r.boxes:

                px1, py1, px2, py2 = map(int, box.xyxy[0])

                if px2 <= px1 or py2 <= py1:
                    continue

                plate_crop = frame[py1:py2, px1:px2]
                if plate_crop.size == 0:
                    continue

                cv2.rectangle(frame,
                              (px1, py1),
                              (px2, py2),
                              (0, 255, 0), 2)

                plate_text = self.recognize_plate(
                    plate_crop, frame, px1, py1
                )

                return plate_text

        return "None"

    # =============================
    # Plate Recognition
    # =============================
    def recognize_plate(self, plate_crop, frame, abs_x1, abs_y1):

        ocr_results = self.plate_recognition(plate_crop, verbose=False)
        plate_text = ""

        for ocr_res in ocr_results:

            if ocr_res.boxes is None:
                continue

            chars = ocr_res.boxes.data.tolist()
            chars.sort(key=lambda x: x[0])

            for char in chars:
                cls_id = int(char[5])
                plate_text += str(ocr_res.names[cls_id])

        if plate_text:
            cv2.putText(frame,
                        plate_text,
                        (abs_x1, abs_y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 255, 0),
                        2)

        return plate_text

    # =============================
    # Crop Car
    # =============================

    # =============================
    # Line Side Function
    # =============================
    def is_crossing_line(self, point, line_start, line_end):

        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end

        position = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
        return position

    # =============================
    # Main Loop
    # =============================
    def run(self):

        # ROI Lines
        start_left = (87, 986)
        end_left = (1359, 652)

        start_right = (2180, 1668)
        end_right = (2331, 467)

        # Trigger Line (Red)
        start_trigger = (744,745)
        end_trigger = (2244, 1110)

        roi_polygon = np.array([
            start_left,
            end_left,
            end_right,
            start_right
        ], dtype=np.int32)

        while True:

            ret, frame = self.cap.read()
            if not ret:
                break

            # Draw ROI
            cv2.line(frame, start_left, end_left, (0, 255, 0), 2)
            cv2.line(frame, start_right, end_right, (0, 255, 0), 2)

            # Draw Trigger Line
            cv2.line(frame, start_trigger, end_trigger, (0, 0, 255), 3)

            # ================= TRACKING ON FULL FRAME =================
            results = self.car_model.track(
                frame,
                persist=True,
                classes=[2],  # car class
                conf=0.5,
                verbose=False
            )

            if results[0].boxes.id is not None:

                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)

                for box, track_id in zip(boxes, track_ids):

                    x1, y1, x2, y2 = map(int, box)

                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2

                    # ================= CHECK ROI =================
                    if cv2.pointPolygonTest(roi_polygon, (cx, cy), False) < 0:
                        continue
                    frame_h, frame_w = frame.shape[:2]

                    if x1 <= 5 or y1 <= 5 or x2 >= frame_w - 5 or y2 >= frame_h - 5:
                        continue
                    cv2.rectangle(frame,
                                  (x1, y1),
                                  (x2, y2),
                                  (255, 0, 0), 2)

                    # ================= CROSSING LOGIC =================
                    current_position = self.is_crossing_line(
                        (cx, cy),
                        start_trigger,
                        end_trigger
                    )

                    previous_position = self.previous_side.get(track_id)

                    if previous_position is not None:

                        if previous_position < 0 and current_position >= 0:

                            if track_id not in self.processed_ids:

                                print(f"\nENTRY Car ID: {track_id}")

                                plate_text = self.detect_and_draw_plate(frame)

                                # car_crop = self.crop_car_from_frame(
                                #     frame, x1, y1, x2, y2
                                # )

                                self.save_car(frame, track_id)
                                print("Detected Text:"+plate_text)

                                # self.api.send_to_backend(...)

                                self.processed_ids.add(track_id)

                    self.previous_side[track_id] = current_position

            cv2.imshow("Entrance System", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()